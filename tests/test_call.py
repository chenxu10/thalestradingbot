from fentu.strategyservices.black_scholes_model import OptionData, BlackScholesPricer


def test_call_pnl_base():
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
    #assert len(pnl_val) == 10
    #assert pnl_val[0] < pnl_val[-1]


if __name__ == '__main__':
    test_call_pnl_base()