from dataclasses import dataclass

@dataclass
class OptionTicket:
    option_type: str
    expiration: str
    strike_price: float
    current_underlying_price: float

def calculate_uvxy_otm_put(uvxy_year_change, option_ticket):
    return 4000


def test_calculate_uvxy_otm_put():
    option_ticket = OptionTicket('Put','2026-01-01',3, 20.57)
    principle = 10000
    uxvy_year_expected_return = calculate_uvxy_otm_put(
    [-0.5,0.2,0.1],option_ticket)
    
    assert 0.2 < uxvy_year_expected_return/principle < 0.5

if __name__ == "__main__":
    test_calculate_uvxy_otm_put()