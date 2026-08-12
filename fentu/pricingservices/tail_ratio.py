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
