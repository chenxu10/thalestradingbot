"""
Test the VIX subplot feature for see_change (story: as a trader, I want to see
VIX when I call see_change daily QQQ or any ETF, as a separate subplot).

Behavior under test:
  1. The VIX subplot plots the FULL ^VIX history (1990 -> today), NOT filtered
     to the ETF's date range.
  2. A "current VIX value" annotation is shown: if the US market has opened
     today (now >= 9:30 ET and today is a trading day in the data), use today's
     open; otherwise use the last trading day's close.

Four tests, red/green/refactor. Network I/O is mocked throughout, mirroring the
conventions in test_volcalculator_time_range.py.
"""
from datetime import datetime, timezone, timedelta
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

import matplotlib
matplotlib.use("Agg")  # headless rendering for tests
import matplotlib.pyplot as plt

from fentu.explatoryservices.volcalculator import VolatilityFacade

VIX_TICKER = "^VIX"
ET_OFFSET = timedelta(hours=-4)  # EDT (June) — Eastern Time


def _et(year, month, day, hour, minute=0):
    """Build a tz-aware Eastern Time datetime for deterministic tests."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone(ET_OFFSET))


def _ticker_side_effect(vix_ohlc, etf_prices):
    """yf.Ticker side_effect: serve VIX OHLC for ^VIX, ETF Close otherwise."""

    def _side_effect(symbol, session=None):
        inst = MagicMock()
        if symbol == VIX_TICKER:
            inst.history.return_value = vix_ohlc
        else:
            inst.history.return_value = pd.DataFrame({"Close": etf_prices})
        return inst

    return _side_effect


def _vix_ohlc_full_history(last_date, last_open, last_close):
    """Build a mock ^VIX OHLC DataFrame from 1990-01-02 up to `last_date`."""
    dates = pd.bdate_range("1990-01-02", last_date)
    rng = np.random.default_rng(42)
    close = 15 + np.cumsum(rng.normal(0, 0.3, len(dates)))
    close[-1] = last_close
    open_ = close - rng.normal(0, 0.2, len(dates))
    open_[-1] = last_open
    df = pd.DataFrame({"Open": open_, "Close": close}, index=dates)
    df.index.name = "Date"
    return df


class TestVixSubplot:
    @pytest.fixture
    def etf_prices(self):
        dates = pd.date_range("2024-01-01", "2026-06-24", freq="B")
        rng = np.random.default_rng(7)
        prices = 400 + np.cumsum(rng.normal(0, 1.0, len(dates)))
        return pd.Series(prices, index=dates, name="Close")

    @pytest.fixture
    def vix_ohlc(self):
        return _vix_ohlc_full_history("2026-06-24", last_open=18.5, last_close=19.0)

    @pytest.fixture
    def facade(self, etf_prices, vix_ohlc):
        with patch("fentu.explatoryservices.volcalculator.requests.Session"):
            with patch(
                "fentu.explatoryservices.volcalculator.yf.Ticker",
                side_effect=_ticker_side_effect(vix_ohlc, etf_prices),
            ):
                yield VolatilityFacade(
                    "QQQ", start_date="2025-03-01", end_date="2025-06-01"
                )

    def test_get_vix_prices_returns_full_history_unfiltered(self, facade):
        """VIX subplot data is the full ^VIX history, ignoring the ETF window."""
        vix = facade._get_vix_prices()

        assert vix.name == "Close"
        # spans 1990 (or earlier than 1992) up to today
        assert vix.index.min().year <= 1992
        assert vix.index.max().year >= 2026
        # NOT filtered to the facade's 2025-03-01..2025-06-01 window
        assert (vix.index < pd.Timestamp("2025-03-01")).any()
        assert (vix.index > pd.Timestamp("2025-06-01")).any()

    def test_current_vix_value_when_market_opened_today_uses_open(self, facade):
        """After 9:30 ET on a trading day present in the data, use today's open."""
        label, value = facade._get_current_vix_value(now_et=_et(2026, 6, 24, 10, 0))

        assert "open" in label.lower()
        assert "9:30" in label
        assert value == pytest.approx(18.5)

    def test_current_vix_value_before_market_open_uses_last_close(self, facade):
        """Before 9:30 ET (market not yet opened today), use last close."""
        # data's last row is 2026-06-24 (today), but it's 08:00 ET, pre-open
        label, value = facade._get_current_vix_value(now_et=_et(2026, 6, 24, 8, 0))

        assert "close" in label.lower()
        assert value == pytest.approx(19.0)

    def test_visualize_renders_vix_subplot_with_full_history_and_current_value(
        self, facade
    ):
        """End-to-end: the figure's VIX subplot shows the full-history line and
        a current-value annotation."""
        with patch(
            "fentu.explatoryservices.volcalculator._now_eastern",
            return_value=_et(2026, 6, 24, 10, 0),
        ):
            with patch("fentu.explatoryservices.volcalculator.plt.show"):
                facade.visualize_percentage_change("daily")

        fig = plt.gcf()
        vix_axes = [ax for ax in fig.axes if ax.get_title() == "VIX Index"]
        assert len(vix_axes) == 1
        ax_vix = vix_axes[0]

        # full-history line present, spanning 1990 -> 2026
        lines = ax_vix.get_lines()
        assert len(lines) >= 1
        xdata = np.asarray(lines[0].get_xdata(), dtype="datetime64[us]")
        assert xdata.min().astype("datetime64[Y]") <= np.datetime64("1992", "Y")
        assert xdata.max().astype("datetime64[Y]") >= np.datetime64("2026", "Y")

        # current-value annotation rendered as text containing the open value
        texts = [t.get_text() for t in ax_vix.texts]
        assert any("18.50" in t for t in texts), texts
        plt.close(fig)
