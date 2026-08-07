from fentu.pricingservices.tail_ratio import wing_to_body_ratio


def test_wing_to_body_ratio_known_case():
    assert round(wing_to_body_ratio(4.46, 69.83), 3) == 0.064
