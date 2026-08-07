from fentu.pricingservices.tail_ratio import wing_to_body_ratio


def test_wing_to_body_ratio_known_case():
    wing_price = 4.46  # QQQ Nov-20 2026 580 put (20% OTM), mid, Aug 7 2026
    straddle_price = 69.83  # QQQ Nov-20 2026 ATM 725 call + put mid, Aug 7 2026

    ratio = wing_to_body_ratio(wing_price, straddle_price)

    assert round(ratio, 4) == 0.0639
# MARKER-1786138595
