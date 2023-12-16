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
    def test_before_trade(self,mock_input):
        mock_input.return_value = "a"
        call_spread_strategy = cs.CallSpreadStrategy()
        s = call_spread_strategy.before_trade()
        assert s == 'attactive'
    
        # call_spread_strategt = cs.CallSpreadStrategy()       
        # before_trade_metrics = call_spread_strategt.before_trade()
        # np.testing.assert_almost_equal(
        #     before_trade_metrics["expected_max_loss"],0.03,decimal=3)
        # np.testing.assert_almost_equal(
        #     before_trade_metrics["expected_max_profit"],3.97)
        # np.testing.assert_almost_equal(
        #     before_trade_metrics["expected_max_profit"], 0.00755, decimal=5)