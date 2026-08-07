def wing_to_body_ratio(wing_price: float, straddle_price: float) -> float:
    """Ratio of far-OTM wing price to ATM straddle price, same date."""
    return wing_price / straddle_price


def percentile(series, pct):
    """pct-th percentile (0-100) with linear interpolation."""
    data = sorted(series)
    n = len(data)
    rank = (n - 1) * pct / 100.0
    lo = int(rank)
    hi = min(lo + 1, n - 1)
    frac = rank - lo
    return data[lo] + frac * (data[hi] - data[lo])


def daily_series(wing_quotes: dict, straddle_quotes: dict) -> dict:
    """Per maturity: (date, ratio) pairs for dates present in both quote sets, sorted."""
    series = {}
    for maturity in wing_quotes:
        wings = wing_quotes[maturity]
        straddles = straddle_quotes[maturity]
        common_dates = set(wings) & set(straddles)
        series[maturity] = sorted(
            (d, wing_to_body_ratio(wings[d], straddles[d])) for d in common_dates
        )
    return series
