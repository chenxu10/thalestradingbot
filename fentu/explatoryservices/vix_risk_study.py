from dataclasses import dataclass

# 什么是逃生套利时机？
# 赚到多少可以逃生？

@dataclass
class OptionTicket:
    option_type: str
    expiration: str
    strike_price: float
    current_market_price: float
    cost_of_option: float

def calculate_uvxy_otm_put_exp_return(uvxy_year_change, option_ticket):
    current_market_price = option_ticket.current_market_price
    strike_price = option_ticket.strike_price
    cost_of_option = option_ticket.cost_of_option
    year_end_absolute_return = [
        max(strike_price - current_market_price * (1 + i),0) * 100 for i in uvxy_year_change
    ]
    print(year_end_absolute_return)
    year_end_relative_return = [
        i/(cost_of_option * 100) for i in  year_end_absolute_return
    ]
    print(year_end_relative_return)
    return 4000

def main():
    option_ticket = OptionTicket(
        'Put',
        '2026-01-01',
        10, 
        21.03,
        3.04)
    principle = 10000
    historical_uvxy_yearly_change = [-0.5,-0.87,-0.41,-0.89,-0.12,-0.83,0.72,-0.93]
    uxvy_year_expected_return = calculate_uvxy_otm_put_exp_return(
        historical_uvxy_yearly_change,option_ticket
    )
    
    assert 0.2 < uxvy_year_expected_return/principle < 0.5


if __name__ == "__main__":
    main()