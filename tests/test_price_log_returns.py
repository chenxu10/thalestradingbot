"""
Test price and log returns calculation for instruments.
Log returns: log(St/St-1)
"""
import pytest
import pandas as pd
import numpy as np
from fentu.explatoryservices.volcalculator import VolatilityFacade


class TestPriceLogReturns:
    @pytest.fixture
    def facade(self):
        return VolatilityFacade("SPY")

    def test_get_past_week_price_and_log_returns(self, facade):
        """Test most recent past week prices with daily log returns"""
        df = facade.get_past_week_price_and_log_returns()

        assert 'price' in df.columns
        assert 'log_return' in df.columns
        assert len(df) == 5

        expected = np.log(df['price'].iloc[1] / df['price'].iloc[0])
        assert abs(df['log_return'].iloc[1] - expected) < 1e-10

    def test_get_past_year_price_and_log_returns(self, facade):
        """Test most recent past year prices with daily log returns"""
        df = facade.get_past_year_price_and_log_returns()

        assert 'price' in df.columns
        assert 'log_return' in df.columns
        assert 240 <= len(df) <= 260

        expected = np.log(df['price'].iloc[1] / df['price'].iloc[0])
        assert abs(df['log_return'].iloc[1] - expected) < 1e-10
