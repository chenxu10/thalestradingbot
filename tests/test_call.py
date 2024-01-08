


def test_call_pnl_base():
    current_stock_price = 96
    long_strike = 97
    time_to_expire = 3
    interest_rate = 0.05
    volatility = 0.1
    price_per_options = 0.35

    pnl_val = [i for i in range(10)]
    assert len(pnl_val) == 10
    assert pnl_val[0] < pnl_val[-1]


if __name__ == '__main__':
    test_call_pnl_base()