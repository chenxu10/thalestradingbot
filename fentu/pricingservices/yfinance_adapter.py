"""
yfinance option-chain adapter for the IV term-structure pipeline.

Bridges yfinance's ticker.options + ticker.option_chain() shape into the pure
build_expiry_detail_rows / build_bucket_rows core. This module imports no
yfinance and hits no network: it only consumes the dict/DataFrame shape that
yfinance produces, so it stays fully unit-testable with a fake chain.

Contract of chain_data:
    {
        "expiries": ["YYYY-MM-DD", ...],
        "chains": {
            "YYYY-MM-DD": {
                "calls": <calls-side>,
                "puts":  <puts-side>,
            },
            ...
        }
    }
<calls-side> / <puts-side> may be:
  - a pandas DataFrame (real yfinance shape),
  - a list-of-dict records (test/fake shape),
  - OR an object with .calls / .puts attributes (real yfinance option_chain()
    returns a namedtuple-like; such an object can be passed directly as the
    whole chain entry instead of a {"calls":..,"puts":..} dict).

IV column is read as "iv" first, then "impliedVolatility" (the real yfinance
column name), so both fake-chain tests and real yfinance data work.
"""

from __future__ import annotations

from datetime import date, datetime

from fentu.pricingservices.iv_term_structure import (
    build_expiry_detail_rows,
    calculate_calendar_dte,
    pick_strike_window,
)


def _to_records(sides):
    if sides is None:
        return []
    if hasattr(sides, "to_dict"):
        return sides.to_dict("records")
    return list(sides)


def _side_records(side_data, side_key):
    """Extract call/put records from a chain entry.

    Accepts either a dict {"calls": df, "puts": df} or an object exposing
    .calls / .puts attributes (the real yfinance option_chain() return).
    """
    if side_data is None:
        return []
    if isinstance(side_data, dict):
        return _to_records(side_data.get(side_key))
    return _to_records(getattr(side_data, side_key, None))


def _find_quote_at_strike(records, target_strike):
    for row in records:
        try:
            strike = float(row.get("strike"))
        except (TypeError, ValueError, AttributeError):
            continue
        if strike == target_strike:
            return row
    return None


def _read_iv(row):
    """IV is 'iv' in the fake chain, 'impliedVolatility' in real yfinance."""
    if not isinstance(row, dict):
        return None
    value = row.get("iv")
    if value is None:
        value = row.get("impliedVolatility")
    return value


def yfinance_chain_to_detail_rows(
    chain_data,
    underlying_price,
    anchor_date,
    max_dte=200,
    strike_radius=1,
):
    """Convert a yfinance-shaped option chain into detail rows.

    Args:
        chain_data: dict with "expiries" and "chains" (see module docstring).
        underlying_price: current spot of the underlying.
        anchor_date: date/datetime/ISO-string the DTE is measured from.
        max_dte: expiries with dte outside [0, max_dte] are dropped.
        strike_radius: +/- strike window radius around ATM (passed to
            pick_strike_window; the ATM call/put are taken at the ATM strike).

    Returns: detail rows (output of build_expiry_detail_rows), shaped
        {expiry, dte, atm_strike, call_iv, put_iv, atm_iv, has_complete_pair,
         call_mark, put_mark, atm_call_sub_id, atm_put_sub_id}.
    """
    if not isinstance(chain_data, dict):
        return []

    expiries = chain_data.get("expiries") or []
    chains = chain_data.get("chains") or {}
    if not isinstance(chains, dict):
        chains = {}

    expiry_rows = []
    quotes_by_sub_id = {}

    for raw_expiry in expiries:
        dte = calculate_calendar_dte(anchor_date, raw_expiry)
        if dte is None or dte < 0 or dte > max(0, int(max_dte or 0)):
            continue

        expiry_code = _normalize_expiry_for_key(raw_expiry)
        side_data = chains.get(raw_expiry) or chains.get(expiry_code)
        if side_data is None:
            continue

        calls = _side_records(side_data, "calls")
        puts = _side_records(side_data, "puts")

        all_strikes = []
        for records in (calls, puts):
            for row in records:
                try:
                    strike = float(row.get("strike"))
                    if strike == strike:
                        all_strikes.append(strike)
                except (TypeError, ValueError, AttributeError):
                    continue

        window = pick_strike_window(all_strikes, underlying_price, strike_radius)
        atm_strike = window.get("atm_strike")
        if atm_strike is None:
            continue

        call_quote = _find_quote_at_strike(calls, atm_strike)
        put_quote = _find_quote_at_strike(puts, atm_strike)

        call_sub_id = ""
        put_sub_id = ""
        if call_quote is not None:
            call_sub_id = str(call_quote.get("contractSymbol") or "").strip()
            if call_sub_id:
                quotes_by_sub_id[call_sub_id] = {
                    "iv": _read_iv(call_quote),
                    "mark": call_quote.get("lastPrice"),
                }
        if put_quote is not None:
            put_sub_id = str(put_quote.get("contractSymbol") or "").strip()
            if put_sub_id:
                quotes_by_sub_id[put_sub_id] = {
                    "iv": _read_iv(put_quote),
                    "mark": put_quote.get("lastPrice"),
                }

        expiry_rows.append({
            "expiry": expiry_code,
            "dte": dte,
            "atm_strike": atm_strike,
            "atm_call_sub_id": call_sub_id,
            "atm_put_sub_id": put_sub_id,
        })

    return build_expiry_detail_rows(expiry_rows, quotes_by_sub_id)


def _normalize_expiry_for_key(value):
    normalized = str(value or "").strip()
    if len(normalized) == 10 and normalized[4] == "-" and normalized[7] == "-":
        return normalized.replace("-", "")
    return normalized
