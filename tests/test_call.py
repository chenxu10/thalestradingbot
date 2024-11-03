from fentu.strategyservices.black_scholes_model import OptionData, BlackScholesPricer


def test_call_pnl_base():
    """
    Given properties of an option, you should calculate out the theortical
    value of it, it should be roughly the same as the broker you are using
    or main tools
    """
    long_strike = 97
    time_to_expire = 3
    interest_rate = 0.05
    volatility = 0.1
    
    theortical_value = []
    for s in range(95,105):
        opdata = OptionData(s, long_strike, time_to_expire, 
                        interest_rate, volatility)
        long_call_pricer = BlackScholesPricer(opdata)
        long_call_price_in_stockprice = long_call_pricer.option_pricing_formula("call")
        theortical_value.append(long_call_price_in_stockprice)

    print(theortical_value)
    assert len(theortical_value) == 10
    assert theortical_value[0] < theortical_value[-1]

#sd

if __name__ == '__main__':
    test_call_pnl_base()