def wing_to_body_ratio(wing_price: float, straddle_price: float) -> float:
    """Ratio of far-OTM wing price to ATM straddle price, same date."""
    return wing_price / straddle_price
