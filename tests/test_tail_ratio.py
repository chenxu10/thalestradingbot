from fentu.pricingservices.tail_ratio import wing_to_body_ratio


def test_wing_to_body_ratio_known_case():
    assert round(wing_to_body_ratio(2.60, 9.40), 3) == 0.277
