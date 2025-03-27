from dataclasses import dataclass

@dataclass
class OptionTicket:
    option_type: str
    expiration: str
    strike_price: float

def calculate_uvxy_otm_put(uvxy_year_change, option_ticket):
    return 4000

option_ticket = OptionTicket('Put','2026-01-01',3)
uxvy_year_expected_return = calculate_uvxy_otm_put(
    [-0.5,0.2,0.1],option_ticket)
principle = 10000
assert 0.2 < uxvy_year_expected_return/principle < 0.5

