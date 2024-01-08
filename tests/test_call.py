from fentu.strategyservices.black_scholes_model import OptionData, BlackScholesPricer


def test_call_pnl_base():
    current_stock_price = 96
    long_strike = 97
    time_to_expire = 3
    interest_rate = 0.05
    volatility = 0.1
    opdata = OptionData(current_stock_price, long_strike, time_to_expire, 
                        interest_rate, volatility)
    long_call_pricer = BlackScholesPricer(opdata)
    pnl_val = [long_call_pricer.option_pricing_formula("call") for s in range(90,110)]
    print(pnl_val)
    #assert len(pnl_val) == 10
    #assert pnl_val[0] < pnl_val[-1]


if __name__ == '__main__':
    test_call_pnl_base()