from enum import Enum
import math

class OptionType(Enum):
    CALL = "call"
    PUT = "put"

def calculate_present_value(future_value: float, rate: float, time_years: float) -> float:
    """
    Calculate present value using continuous compounding
    PV = FV * e^(-rt)
    """
    return future_value * math.exp(-rate * time_years)

def option_price(stock_price: float, strike_price: float, known_price: float, 
                solve_for: OptionType, interest_rate: float = 0.02, time_years: float = 1.0) -> float:
    """
    Calculate option price using put-call parity formula: C + PV(K) = P + S
    where:
    C = call price
    P = put price
    S = stock price
    PV(K) = present value of strike price
    
    Args:
        stock_price: Current stock price (S)
        strike_price: Strike price (K)
        known_price: Price of the known option (either put or call)
        solve_for: OptionType.CALL or OptionType.PUT to specify which price to calculate
        interest_rate: Annual interest rate (default 2%)
        time_years: Time to expiration in years (default 1 year)
    """
    pv_strike = calculate_present_value(strike_price, interest_rate, time_years)
    
    if solve_for == OptionType.CALL:
        # P + S - PV(K) = C
        return known_price + stock_price - pv_strike
    # C - S + PV(K) = P
    return known_price - stock_price + pv_strike

def test_call_from_put():
    stock_price = 220
    strike_price = 180
    put_price = 20
    interest_rate = 0.02  # 2% interest rate
    time_years = 1.0
    
    # Calculate expected call price using C = P + S - PV(K)
    pv_strike = calculate_present_value(strike_price, interest_rate, time_years)
    expected_call_price = put_price + stock_price - pv_strike
    
    actual_call_price = option_price(
        stock_price, 
        strike_price, 
        put_price, 
        OptionType.CALL,
        interest_rate,
        time_years
    )
    
    assert round(expected_call_price, 2) == round(actual_call_price, 2)

def test_put_from_call():
    stock_price = 100
    strike_price = 95
    call_price = 15
    interest_rate = 0.02  # 2% interest rate
    time_years = 1.0
    
    # Calculate expected put price using P = C - S + PV(K)
    pv_strike = calculate_present_value(strike_price, interest_rate, time_years)
    expected_put_price = call_price - stock_price + pv_strike
    
    actual_put_price = option_price(
        stock_price, 
        strike_price, 
        call_price, 
        OptionType.PUT,
        interest_rate,
        time_years
    )
    
    assert round(expected_put_price, 2) == round(actual_put_price, 2)

def test_call_from_put_high_interest():
    stock_price = 220
    strike_price = 180
    put_price = 20
    interest_rate = 0.05  # 5% interest rate
    time_years = 1.0
    
    # Calculate expected call price using C = P + S - PV(K)
    pv_strike = calculate_present_value(strike_price, interest_rate, time_years)
    expected_call_price = put_price + stock_price - pv_strike
    
    actual_call_price = option_price(
        stock_price, 
        strike_price, 
        put_price, 
        OptionType.CALL,
        interest_rate,
        time_years
    )
    
    assert round(expected_call_price, 2) == round(actual_call_price, 2)
