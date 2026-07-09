"""
This module holds the pure, IBKR-free selection and bucketing logic:
- calculate_calendar_dte     : expiry code -> days to expiry
- pick_strike_window         : strike list + spot -> ATM strike + window
- build_expiry_detail_rows   : per-expiry quotes -> detail rows with atmIv
- build_bucket_rows          : detail rows -> normalized tenor curve

No yfinance, no IBKR, no network. Everything operates on plain Python
data structures so it stays trivially unit-testable.
"""

from __future__ import annotations

from datetime import date, datetime


DEFAULT_BUCKET_DEFINITIONS = (
    {"label": "1D", "targetDays": 1},
    {"label": "3D", "targetDays": 3},
    {"label": "1W", "targetDays": 7},
    {"label": "3W", "targetDays": 21},
    {"label": "1M", "targetDays": 30},
    {"label": "3M", "targetDays": 90},
    {"label": "6M", "targetDays": 180},
)


def _parse_anchor_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    normalized = str(value or "").strip()
    if not normalized:
        return None

    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue

    return None


def normalize_expiry_code(value) -> str:
    normalized = str(value or "").strip()
    if len(normalized) == 10 and normalized[4] == "-" and normalized[7] == "-":
        normalized = normalized.replace("-", "")
    return normalized if len(normalized) == 8 and normalized.isdigit() else ""


def calculate_calendar_dte(anchor_date, expiry_code):
    anchor = _parse_anchor_date(anchor_date)
    expiry = normalize_expiry_code(expiry_code)
    if anchor is None or not expiry:
        return None

    try:
        expiry_date = datetime.strptime(expiry, "%Y%m%d").date()
    except ValueError:
        return None

    return (expiry_date - anchor).days


def _parse_spot(underlying_price):
    """Coerce the underlying price to a finite float, else None.

    Used to short-circuit pick_strike_window when no valid spot is available.
    """
    try:
        spot = float(underlying_price)
    except (TypeError, ValueError):
        return None
    if spot != spot:  # NaN guard (NaN != NaN)
        return None
    return spot


def _normalize_strikes(strikes):
    """Coerce raw strikes to a sorted list of unique finite floats.

    Drops any non-numeric, NaN, or duplicate values so the ATM finder only sees
    clean, deduped, ordered data.
    """
    normalized = []
    seen = set()
    for raw_strike in strikes or []:
        try:
            strike = float(raw_strike)
        except (TypeError, ValueError):
            continue
        if strike != strike:  # NaN guard
            continue
        if strike in seen:
            continue
        seen.add(strike)
        normalized.append(strike)
    normalized.sort()
    return normalized


def _nearest_strike_index(sorted_strikes, target_price):
    """Index of the strike closest to `target_price`.

    Tie-break by preferring the lower strike (`sorted_strikes[index]` is the
    secondary sort key) so an equidistant down-strike wins over the up-strike.
    """
    return min(
        range(len(sorted_strikes)),
        key=lambda index: (
            abs(sorted_strikes[index] - target_price),
            sorted_strikes[index],
        ),
    )


def _clamp_radius_window(sorted_strikes, center_index, radius):
    """Slice `sorted_strikes` to +/- `radius` around `center_index`, clamped to
    list edges so a wide radius at the bottom/top never under/overflows.
    """
    safe_radius = max(0, int(radius or 0))
    start = max(0, center_index - safe_radius)
    end = min(len(sorted_strikes), center_index + safe_radius + 1)
    return sorted_strikes[start:end]


def pick_strike_window(strikes, underlying_price, radius=1):
    """Pick the ATM strike (nearest to spot) and a +/- radius window around it.

    Returns {"atm_strike": float|None, "window_strikes": list[float]}.
    On any invalid input (bad spot, no numeric strikes, NaN) returns
    {"atm_strike": None, "window_strikes": []}.
    """
    spot = _parse_spot(underlying_price)
    if spot is None:
        return {"atm_strike": None, "window_strikes": []}

    sorted_strikes = _normalize_strikes(strikes)
    if not sorted_strikes:
        return {"atm_strike": None, "window_strikes": []}

    best_index = _nearest_strike_index(sorted_strikes, spot)
    window = _clamp_radius_window(sorted_strikes, best_index, radius)

    return {
        "atm_strike": sorted_strikes[best_index],
        "window_strikes": window,
    }


def _coerce_positive_number(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not (parsed == parsed):  # NaN guard
        return None
    return parsed if parsed > 0 else None


# Yahoo (and some brokers) return a ~1e-5 sentinel "impliedVolatility" for
# stale / no-trade options; that is 0.001% vol -- physically impossible for an
# equity index (real ATM IV floor is ~5%, QQQ's is ~12-13%). Letting it through
# poisons the (call+put)/2 average, so reject anything below this floor. See
# Taleb SKILL.md Bachelier caveat ("ATM IV Term Structure" heuristics).
_MIN_PLAUSIBLE_IV = 0.001


def _coerce_plausible_iv(value):
    """Like _coerce_positive_number but also rejects implausibly low IVs."""
    parsed = _coerce_positive_number(value)
    if parsed is None:
        return None
    return parsed if parsed >= _MIN_PLAUSIBLE_IV else None


def _compute_average_iv(call_iv, put_iv):
    if call_iv is None or put_iv is None:
        return None
    return round((call_iv + put_iv) / 2, 6)


def _quote_value(quote, key):
    """Read a field from a quote that may be None or a non-dict."""
    return quote.get(key) if isinstance(quote, dict) else None


def _sub_id_of(entry, key):
    """Strip an ATM sub-id field from a selection row to a plain string."""
    return str(entry.get(key) or "").strip()


def _lookup_quote(sub_id, quotes):
    """Look up a quote by sub-id, returning None for an empty sub-id."""
    return quotes.get(sub_id) if sub_id else None


def _build_detail_row(entry, quotes):
    """Build one detail row from a selection entry + the quote table.

    Near-decomposable Simon subsystem: resolves the ATM call/put sub-ids,
    coerces their IV/mark fields, and assembles the row. Pure -- it touches no
    state outside its arguments.
    """
    call_sub_id = _sub_id_of(entry, "atm_call_sub_id")
    put_sub_id = _sub_id_of(entry, "atm_put_sub_id")
    call_quote = _lookup_quote(call_sub_id, quotes)
    put_quote = _lookup_quote(put_sub_id, quotes)

    call_iv = _coerce_plausible_iv(_quote_value(call_quote, "iv"))
    put_iv = _coerce_plausible_iv(_quote_value(put_quote, "iv"))

    return {
        "expiry": str(entry.get("expiry") or "").strip(),
        "dte": max(0, int(entry.get("dte") or 0)),
        "atm_strike": _coerce_positive_number(entry.get("atm_strike")),
        "call_iv": call_iv,
        "put_iv": put_iv,
        "atm_iv": _compute_average_iv(call_iv, put_iv),
        "has_complete_pair": call_iv is not None and put_iv is not None,
        "call_mark": _coerce_positive_number(_quote_value(call_quote, "mark")),
        "put_mark": _coerce_positive_number(_quote_value(put_quote, "mark")),
        "atm_call_sub_id": call_sub_id,
        "atm_put_sub_id": put_sub_id,
    }


def build_expiry_detail_rows(expiry_rows, quotes_by_sub_id):
    """Glue step 3: read call/put IV at the ATM strike, average -> atmIv per expiry.

    Args:
        expiry_rows: list of selection rows, each shaped
            {expiry, dte, atm_strike, atm_call_sub_id, atm_put_sub_id}.
            The sub_id fields are generic quote identifiers -- whatever the
            caller's data source uses to key a quote (yfinance row id, IBKR
            sub id, a stub key in tests). This module never touches a broker.
        quotes_by_sub_id: dict mapping sub_id -> {"iv": ..., "mark": ...}.
            iv / mark may be numeric strings; non-positive or non-finite IVs
            are coerced to None so they can't contaminate the average.

    Returns: list of detail rows sorted by (dte, expiry), each shaped
        {expiry, dte, atm_strike, call_iv, put_iv, atm_iv, has_complete_pair,
         call_mark, put_mark, atm_call_sub_id, atm_put_sub_id}.
        These rows are the input to build_bucket_rows.
    """
    quotes = quotes_by_sub_id if isinstance(quotes_by_sub_id, dict) else {}

    rows = []
    for entry in expiry_rows or []:
        if not isinstance(entry, dict):
            continue
        rows.append(_build_detail_row(entry, quotes))

    rows = [row for row in rows if row["expiry"]]
    rows.sort(key=lambda row: (row["dte"], str(row["expiry"])))
    return rows


def _clone_bucket_definitions(definitions):
    source = definitions if definitions else DEFAULT_BUCKET_DEFINITIONS
    normalized = []
    for entry in source or []:
        if not isinstance(entry, dict):
            entry = {}
        label = str(entry.get("label") or "").strip() or "Bucket"
        try:
            target_days = int(entry.get("targetDays"))
        except (TypeError, ValueError):
            target_days = 0
        normalized.append({"label": label, "targetDays": max(0, target_days)})
    return normalized


def _pick_nearest_detail_row(detail_rows, target_days):
    match = None
    match_distance = None
    for row in detail_rows or []:
        if not isinstance(row, dict):
            continue
        expiry = str(row.get("expiry") or "").strip()
        if not expiry:
            continue
        try:
            dte = int(row.get("dte"))
        except (TypeError, ValueError):
            continue

        distance = abs(dte - target_days)
        if (
            match is None
            or distance < match_distance
            or (distance == match_distance and dte < match["dte"])
            or (
                distance == match_distance
                and dte == match["dte"]
                and str(row.get("expiry") or "") < str(match.get("expiry") or "")
            )
        ):
            match = row
            match_distance = distance

    return match


def build_bucket_rows(detail_rows, bucket_definitions=None):
    """Fold per-expiry detail rows into normalized tenor buckets.

    Each bucket is matched to the detail row whose dte is nearest the bucket's
    targetDays.For the 1D bucket it scans every detail row's dte 
    (days-to-expiry, computed at yfinance_adapter.py:calculate_calendar_dte → 
    iv_term_structure.py:65) and finds the one with abs(dte - 1) 
    minimal. In practice yfinance's shortest QQQ expiry is 
    usually 1–2 calendar days out

    Args:
        detail_rows: output of build_expiry_detail_rows (or any list of dicts
            shaped {expiry, dte, atm_strike, call_iv, put_iv, atm_iv,
            has_complete_pair}). Rows with missing/blank expiry or non-integer
            dte are ignored.
        bucket_definitions: optional list of {label, targetDays}; defaults to
            DEFAULT_BUCKET_DEFINITIONS (1D/3D/1W/3W/1M/3M/6M). Malformed entries
            are coerced to safe defaults (label "Bucket", targetDays 0).

    Returns: list of bucket rows in bucket-definition order, each shaped
        {label, target_days, matched_expiry, matched_dte, atm_strike,
         call_iv, put_iv, atm_iv, has_complete_pair}.
        Buckets with no match (empty input) have None / False for all
        matched fields.
    """
    buckets = _clone_bucket_definitions(bucket_definitions)

    def field(row, key):
        value = row.get(key) if isinstance(row, dict) else None
        return value if value is not None else None

    output = []
    for bucket in buckets:
        match = _pick_nearest_detail_row(detail_rows, bucket["targetDays"])
        if match is None:
            output.append(
                {
                    "label": bucket["label"],
                    "target_days": bucket["targetDays"],
                    "matched_expiry": None,
                    "matched_dte": None,
                    "atm_strike": None,
                    "call_iv": None,
                    "put_iv": None,
                    "atm_iv": None,
                    "has_complete_pair": False,
                }
            )
            continue

        output.append(
            {
                "label": bucket["label"],
                "target_days": bucket["targetDays"],
                "matched_expiry": str(match.get("expiry") or "").strip() or None,
                "matched_dte": int(match.get("dte")) if match.get("dte") is not None else None,
                "atm_strike": match.get("atm_strike"),
                "call_iv": match.get("call_iv"),
                "put_iv": match.get("put_iv"),
                "atm_iv": match.get("atm_iv"),
                "has_complete_pair": bool(match.get("has_complete_pair")),
            }
        )

    return output
