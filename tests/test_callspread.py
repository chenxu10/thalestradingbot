"""
This script tests the maximum_loss, maximum_profit, 
risk_and_reward_issue, and the impact on the whole portfolio
of callspread strategy
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from unittest import mock
from unittest import TestCase
from fentu.explatoryservices.plotting_service import callspread_pandl_plot
from fentu.strategyservices import callspread as cs

class OptionPrice:
    short_strike = 95
    long_strike = 91
    stock_price = 90
    short_premium = 0.39
    long_premium = 0.41
    commission = 0.01

class TestCallSpreadStrategy:
    @mock.patch('fentu.strategyservices.callspread.before_cs_trade.input_strategy', create=True)
    def test_before_trade(self, mocked_input):
        mocked_input.side_effect = 'b'
        call_spread_strategt = cs.CallSpreadStrategy()       
        s, long_strike, short_strike = call_spread_strategt.before_trade()
        assert s == "attactive"

def test_callspread_pandl_plot():
    op = OptionPrice()
    test_df = pd.DataFrame(
        {"price_at_expiration":[87,88,89,90,91,92,93],
         "pandl":[22,22,22,32,32,32,32]}
    )
    exp_max_profit, exp_max_loss, risk_and_reward_ratio = callspread_pandl_plot(test_df,op)

    np.testing.assert_almost_equal(exp_max_profit,3.97)
    np.testing.assert_almost_equal(exp_max_loss,0.03,decimal=3)
    np.testing.assert_almost_equal(risk_and_reward_ratio, 0.00755, decimal=5)


if __name__ == "__main__":
    test_callspread_pandl_plot()
