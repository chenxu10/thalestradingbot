"""
Test MAD as the headline daily-volatility metric.

Taleg/skill prescription: retire Standard Deviation, use Mean Absolute
Deviation (MAD) as the headline volatility metric. StandardDeviationVolatility
is kept only for a `*_gaussian_only` comparison (DH/FT: SD breaks under fat
tails, MAD does not).

Test data: [1, 2, 3, 4, 5] -> mean 3, |dev| = [2, 1, 0, 1, 2] -> MAD = 6/5 = 1.2.
pandas std (ddof=1) = 1.5811. MAD != std so swapped args are caught.
"""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from fentu.explatoryservices.volcalculator import (
    VolatilityCalculator,
    MeanAbsoluteDeviationVolatility,
    StandardDeviationVolatility,
    DailyVolatility,
    VolatilityFacade,
)


class TestMeanAbsoluteDeviationVolatility:
    def test_calculate_volatility_returns_mad_on_simple_series(self):
        series = pd.Series([1, 2, 3, 4, 5])
        mad = MeanAbsoluteDeviationVolatility().calculate_volatility(series)
        assert mad == pytest.approx(1.2)

    def test_mad_differs_from_std_so_swap_is_caught(self):
        series = pd.Series([1, 2, 3, 4, 5])
        mad = MeanAbsoluteDeviationVolatility().calculate_volatility(series)
        std = StandardDeviationVolatility().calculate_volatility(series)
        assert mad == pytest.approx(1.2)
        assert std == pytest.approx(1.5811388300841898, rel=1e-9)
        assert mad != std

    def test_constant_series_has_zero_mad(self):
        series = pd.Series([7, 7, 7, 7])
        mad = MeanAbsoluteDeviationVolatility().calculate_volatility(series)
        assert mad == 0.0


class TestDailyVolatilityDefault:
    def test_default_calculator_is_mad_not_std(self):
        daily = DailyVolatility()
        assert isinstance(daily.calculator, MeanAbsoluteDeviationVolatility)
        assert not isinstance(daily.calculator, StandardDeviationVolatility)

    def test_can_inject_standard_for_gaussian_only_comparison(self):
        daily = DailyVolatility(calculator=StandardDeviationVolatility())
        assert isinstance(daily.calculator, StandardDeviationVolatility)

    def test_calculate_uses_mad_by_default(self):
        series = pd.Series([1, 2, 3, 4, 5])
        daily = DailyVolatility()
        result = daily.calculate_1std_daily_volatility(series)
        assert result == pytest.approx(1.2)


class TestFacadeHeadlineIsMad:
    @pytest.fixture
    def facade_with_known_returns(self):
        """Facade whose daily returns are exactly [1,2,3,4,5] (as log returns).

        We mock the yfinance layer to return a small price series whose
        1-period log returns reduce to values with a known MAD, so the headline
        metric is checkable by hand.
        """
        # prices so that log(p_i / p_{i-1}) = the values [1,2,3,4] (4 returns).
        # We just want a deterministic, small set; pick prices 1,2,4,8,16 so
        # log returns are ln(2),ln(2),ln(2),ln(2) -> MAD = 0.
        # To get distinct returns, use [1, 2, 4, 8, 16] is degenerate; instead
        # pick prices such that returns are [1,2,3,4] for an obvious MAD.
        # Simpler: bypass `_get_returns` by constructing the facade then
        # overwriting `daily_returns`.
        prices = pd.Series(
            [1.0, 2.0, 4.0, 8.0, 16.0],
            index=pd.date_range('2025-01-01', periods=5, freq='B'),
            name='Close',
        )
        with patch('fentu.explatoryservices.volcalculator.requests.Session'):
            with patch('fentu.explatoryservices.volcalculator.yf.Ticker') as m:
                m.return_value = MagicMock(
                    history=MagicMock(return_value=pd.DataFrame({'Close': prices}))
                )
                facade = VolatilityFacade("FAKE")
        # Overwrite daily_returns with a known series so MAD is hand-checkable.
        facade.daily_returns = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        return facade

    def test_calculate_daily_volatility_returns_mad(self, facade_with_known_returns):
        # mean=3, |dev|=[2,1,0,1,2] -> MAD = 6/5 = 1.2
        vol = facade_with_known_returns.calculate_daily_volatility()
        assert vol == pytest.approx(1.2)

    def test_calculate_daily_volatility_not_std(self, facade_with_known_returns):
        vol = facade_with_known_returns.calculate_daily_volatility()
        std_val = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0]).std()
        assert vol != pytest.approx(std_val)


class TestStandardDeviationKeptForComparison:
    def test_still_subclass_of_volatility_calculator(self):
        assert issubclass(StandardDeviationVolatility, VolatilityCalculator)

    def test_returns_std(self):
        series = pd.Series([1, 2, 3, 4, 5])
        std = StandardDeviationVolatility().calculate_volatility(series)
        assert std == pytest.approx(1.5811388300841898, rel=1e-9)