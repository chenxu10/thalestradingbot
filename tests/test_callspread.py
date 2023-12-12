"""
This script tests the maximum_loss, maximum_profit, 
risk_and_reward_issue, and the impact on the whole portfolio
of callspread strategy
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pytest
from unittest import mock
from unittest import TestCase
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
        before_trade_metrics = call_spread_strategt.before_trade()
        
        np.testing.assert_almost_equal(
            before_trade_metrics["expected_max_loss"],0.03,decimal=3)
        np.testing.assert_almost_equal(
            before_trade_metrics["expected_max_profit"],3.97)
        np.testing.assert_almost_equal(
            before_trade_metrics["expected_max_profit"], 0.00755, decimal=5)