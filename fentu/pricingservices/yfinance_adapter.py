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

Hierarchy (Herbert Simon, "The Architecture of Complexity"): the conversion is
decomposed into near-decomposable subsystems with narrow interfaces --
yfinance_chain_to_detail_rows (root) orchestrates _process_one_expiry (one per
expiry, a pure subsystem returning its row + quote updates), which in turn
composes leaf primitives (_expiry_dte_in_range, _resolve_chain_entry,
_collect_strikes, _atm_strike_for, _quote_entry). State is merged at exactly
one point (the root), so every subsystem below it is side-effect free and
independently testable.
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


def _normalize_expiry_for_key(value):
    normalized = str(value or "").strip()
    if len(normalized) == 10 and normalized[4] == "-" and normalized[7] == "-":
        return normalized.replace("-", "")
    return normalized


# --- leaf primitives (near-decomposable, side-effect free) -----------------


def _expiry_dte_in_range(anchor_date, raw_expiry, max_dte):
    """DTE gate: return the calendar dte if it lies in [0, max_dte], else None."""
    dte = calculate_calendar_dte(anchor_date, raw_expiry)
    if dte is None or dte < 0 or dte > max(0, int(max_dte or 0)):
        return None
    return dte


def _resolve_chain_entry(chains, raw_expiry):
    """Return (expiry_code, side_data) for an expiry, accepting either the raw
    YYYY-MM-DD key or the normalized YYYYMMDD key used in the row output."""
    expiry_code = _normalize_expiry_for_key(raw_expiry)
    side_data = chains.get(raw_expiry) or chains.get(expiry_code)
    return expiry_code, side_data


def _collect_strikes(*record_sets):
    """Collect every finite strike across one or more call/put record sets."""
    strikes = []
    for records in record_sets:
        for row in records:
            try:
                strike = float(row.get("strike"))
            except (TypeError, ValueError, AttributeError):
                continue
            if strike == strike:
                strikes.append(strike)
    return strikes


def _atm_strike_for(calls, puts, underlying_price, strike_radius):
    """Determine the ATM strike from available strikes, or None."""
    window = pick_strike_window(
        _collect_strikes(calls, puts), underlying_price, strike_radius
    )
    return window.get("atm_strike")


def _quote_entry(quote):
    """Return (sub_id, {"iv", "mark"}) for a quote, or None if it carries no
    contract symbol (so it cannot be registered)."""
    if quote is None:
        return None
    sub_id = str(quote.get("contractSymbol") or "").strip()
    if not sub_id:
        return None
    return sub_id, {"iv": _read_iv(quote), "mark": quote.get("lastPrice")}


# --- per-expiry subsystem --------------------------------------------------


def _process_one_expiry(raw_expiry, chains, anchor_date, underlying_price,
                        max_dte, strike_radius):
    """Convert one expiry into (row, quote_updates), or None if filtered out.

    A near-decomposable Simon subsystem: gates on DTE, resolves the chain
    entry, finds the ATM strike, locates the ATM call/put quotes, and assembles
    a detail row plus the quote entries to register. Pure -- it mutates no
    shared state; the root owns the single merge point.
    """
    dte = _expiry_dte_in_range(anchor_date, raw_expiry, max_dte)
    if dte is None:
        return None

    expiry_code, side_data = _resolve_chain_entry(chains, raw_expiry)
    if side_data is None:
        return None

    calls = _side_records(side_data, "calls")
    puts = _side_records(side_data, "puts")
    atm_strike = _atm_strike_for(calls, puts, underlying_price, strike_radius)
    if atm_strike is None:
        return None

    call_entry = _quote_entry(_find_quote_at_strike(calls, atm_strike))
    put_entry = _quote_entry(_find_quote_at_strike(puts, atm_strike))

    row = {
        "expiry": expiry_code,
        "dte": dte,
        "atm_strike": atm_strike,
        "atm_call_sub_id": call_entry[0] if call_entry else "",
        "atm_put_sub_id": put_entry[0] if put_entry else "",
    }
    quote_updates = {}
    for entry in (call_entry, put_entry):
        if entry is not None:
            quote_updates[entry[0]] = entry[1]
    return row, quote_updates


# --- root orchestrator -----------------------------------------------------


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
        result = _process_one_expiry(
            raw_expiry, chains, anchor_date, underlying_price, max_dte, strike_radius
        )
        if result is None:
            continue
        row, quote_updates = result
        expiry_rows.append(row)
        quotes_by_sub_id.update(quote_updates)

    return build_expiry_detail_rows(expiry_rows, quotes_by_sub_id)
