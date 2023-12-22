"""
This script tests the maximum_loss, maximum_profit, 
risk_and_reward_issue, and the impact on the whole portfolio
of callspread strategy
"""
import numpy as np
import matplotlib.pyplot as plt
from fentu.strategyservices import callspread as cs
from unittest.mock import patch

class OptionPrice:
    short_strike = 95
    long_strike = 91
    stock_price = 90
    short_premium = 0.39
    long_premium = 0.41
    commission = 0.01

class TestCallSpreadStrategy:
    @patch('builtins.input') 
    def test_before_trade_metrics(self,mock_input):
        mock_input.side_effect = ["a","","91","95","0.41","0.39"]
        call_spread_strategy = cs.CallSpreadStrategy()         
        before_trade_metrics = call_spread_strategy.before_trade_metrics()
        np.testing.assert_almost_equal(
            before_trade_metrics["expected_max_profit"],3.48)
        np.testing.assert_almost_equal(
            before_trade_metrics["expected_max_loss"],0.52,decimal=3)
        np.testing.assert_almost_equal(
            before_trade_metrics["breakeven_point"],92.02)
        
    @patch('builtins.input')
    def test_before_trade_plot(self,mock_input):
        call_spread_strategy = cs.CallSpreadStrategy()
        mock_input.side_effect = ["100","115"]
        fig = call_spread_strategy.before_etrade_plot()

        ax = plt.gca()
        lines = ax.get_children()
        x_data, y_data = lines[0].get_xydata().T
        np.testing.assert_array_almost_equal(
        x_data, np.array(range(100, 115)), decimal=2)
        np.testing.assert_array_almost_equal(
        y_data, np.array(range(100, 115)), decimal=2)
        plt.close()
        # np.testing.assert_array_almost_equal(
        #     x_data, np.array([-0.819,0,0.819]), decimal=2)


if __name__=="__main__":
    tcs = TestCallSpreadStrategy()
    print(tcs.test_before_trade_plot())
