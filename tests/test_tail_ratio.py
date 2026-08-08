from fentu.pricingservices.tail_ratio import wing_to_body_ratio


def test_wing_to_body_ratio_known_case():
    """T1 acceptance: real Aug 7, 2026 data — 20% OTM 580 put $4.46 vs ATM 725 straddle $69.83."""
    assert round(wing_to_body_ratio(4.46, 69.83), 4) == 0.0639


def test_wing_to_body_ratio_zero_wing():
    assert wing_to_body_ratio(0.0, 69.83) == 0.0


def test_wing_to_body_ratio_at_the_money():
    assert wing_to_body_ratio(69.83, 69.83) == 1.0


def test_wing_to_body_ratio_linearity():
    assert wing_to_body_ratio(139.66, 69.83) == 2.0


def test_wing_to_body_ratio_scale_invariance():
    assert wing_to_body_ratio(4.46, 69.83) == wing_to_body_ratio(8.92, 139.66)
