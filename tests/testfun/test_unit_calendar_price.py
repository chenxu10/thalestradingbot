from py_vollib.black_scholes import black_scholes

def calculate_back_months(stock, strike_price, time_to_expiration, interest_rate, volatility):
    return black_scholes(
        'c', 
        stock, 
        strike_price, 
        time_to_expiration/365, 
        interest_rate, 
        volatility)

def test_calendar_back_months():
    stock = 85.7
    time_to_expiration = 1
    interest_rate = 0.04
    strike_price = 86
    volatility = 0.02
    theortical_price = calculate_back_months(
        stock, strike_price, time_to_expiration, interest_rate, volatility
    )
    print(theortical_price)
    market_price = 3
    assert theortical_price < market_price

def main():
    test_calendar_back_months()

if __name__ == "__main__":
    main()