"""
Test price and log returns calculation for instruments.
Log returns: log(St/St-1)

Network-free: the yfinance layer is mocked with synthetic prices, following
the same convention as test_volcalculator_time_range.py. This keeps the tests
fast and deterministic (no live yfinance round-trips, no period="max" fetches).
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from fentu.explatoryservices.volcalculator import VolatilityFacade


class TestPriceLogReturns:
    @pytest.fixture
    def mock_prices(self):
        """A tz-naive price series long enough for the year test (>= 252 rows)."""
        dates = pd.date_range(start='2024-01-01', end='2025-12-31', freq='B')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
        # guarantee strictly positive prices for log returns
        prices = np.abs(prices) + 1.0
        return pd.Series(prices, index=dates, name='Close')

    @pytest.fixture
    def facade(self, mock_prices):
        """A VolatilityFacade whose yfinance layer returns synthetic prices.

        Mocks both requests.Session and yf.Ticker so no network call is made.
        The same mock history is returned for every internal _get_prices call
        (constructor's 4 periods + each test method's fetch).
        """
        with patch('fentu.explatoryservices.volcalculator.requests.Session'):
            with patch('fentu.explatoryservices.volcalculator.yf.Ticker') as mock_ticker_class:
                mock_hist = pd.DataFrame({'Close': mock_prices})
                mock_instance = MagicMock()
                mock_instance.history.return_value = mock_hist
                mock_ticker_class.return_value = mock_instance

                yield VolatilityFacade("FAKE")

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
