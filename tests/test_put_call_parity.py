from enum import Enum

class OptionType(Enum):
    CALL = "call"
    PUT = "put"

def option_price(stock_price: float, strike_price: float, known_price: float, solve_for: OptionType) -> float:
    """
    Calculate option price using put-call parity formula: C = P + S - K
    where C = call price, P = put price, S = stock price, K = strike price
    
    Args:
        stock_price: Current stock price (S)
        strike_price: Strike price (K)
        known_price: Price of the known option (either put or call)
        solve_for: OptionType.CALL or OptionType.PUT to specify which price to calculate
    """
    if solve_for == OptionType.CALL:
        return stock_price - strike_price + known_price  # C = S - K + P
    return -stock_price + strike_price + known_price    # P = -S + K + C

def test_call_from_put():
    stock_price = 220
    strike_price = 180
    put_price = 20
    expected_call_price = 60  # 220 - 180 + 20
    actual_call_price = option_price(stock_price, strike_price, put_price, OptionType.CALL)
    assert expected_call_price == actual_call_price

def test_put_from_call():
    stock_price = 100
    strike_price = 95
    call_price = 15
    expected_put_price = 10  # -100 + 95 + 15
    actual_put_price = option_price(stock_price, strike_price, call_price, OptionType.PUT)
    assert expected_put_price == actual_put_price