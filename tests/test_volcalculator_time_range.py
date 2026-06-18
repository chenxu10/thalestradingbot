"""
Test time range filtering in VolatilityFacade and seechange CLI.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from fentu.explatoryservices.volcalculator import VolatilityFacade
import fentu.explatoryservices.seechange as seechange
import sys


class TestTimeRange:
    @pytest.fixture
    def mock_prices(self):
        """Return a mock price series spanning multiple dates"""
        dates = pd.date_range(start='2025-01-01', end='2025-12-31', freq='B')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
        return pd.Series(prices, index=dates, name='Close')

    def test_volatility_facade_date_range_filtering(self, mock_prices):
        """Test that start_date and end_date filter returns correctly"""
        with patch('fentu.explatoryservices.volcalculator.requests.Session'):
            with patch('fentu.explatoryservices.volcalculator.yf.Ticker') as mock_ticker_class:
                mock_hist = pd.DataFrame({'Close': mock_prices})
                mock_instance = MagicMock()
                mock_instance.history.return_value = mock_hist
                mock_ticker_class.return_value = mock_instance

                facade = VolatilityFacade("FAKE", start_date='2025-03-01', end_date='2025-06-01')
                daily = facade.daily_returns

                assert daily.index.min() >= pd.Timestamp('2025-03-01')
                assert daily.index.max() <= pd.Timestamp('2025-06-01')

    def test_volatility_facade_timezone_aware_index(self, mock_prices):
        """Test that timezone-aware indices from yfinance do not raise InvalidComparison"""
        tz_aware_prices = mock_prices.copy()
        tz_aware_prices.index = tz_aware_prices.index.tz_localize('UTC')

        with patch('fentu.explatoryservices.volcalculator.requests.Session'):
            with patch('fentu.explatoryservices.volcalculator.yf.Ticker') as mock_ticker_class:
                mock_hist = pd.DataFrame({'Close': tz_aware_prices})
                mock_instance = MagicMock()
                mock_instance.history.return_value = mock_hist
                mock_ticker_class.return_value = mock_instance

                facade = VolatilityFacade("FAKE", start_date='2025-03-01', end_date='2025-06-01')
                daily = facade.daily_returns

                assert daily.index.min() >= pd.Timestamp('2025-03-01')
                assert daily.index.max() <= pd.Timestamp('2025-06-01')

    def test_seechange_cli_passes_date_range(self):
        """Test that seechange CLI correctly parses and passes date range"""
        with patch('fentu.explatoryservices.seechange.VolatilityFacade') as mock_facade_class:
            mock_instance = MagicMock()
            mock_facade_class.return_value = mock_instance

            test_args = ['seechange', 'daily', 'FAKE', '2025-03-01', '2025-06-01']
            with patch.object(sys, 'argv', test_args):
                seechange.main()

                mock_facade_class.assert_called_once_with(
                    'FAKE', start_date='2025-03-01', end_date='2025-06-01'
                )
                mock_instance.visualize_percentage_change.assert_called_once_with('daily')
