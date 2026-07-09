"""
Test the three extracted seams of volcalculator.py:

  1. ReturnsRepository  — the only object that touches the network.
  2. MarketClock        — DST/market-open logic, pure of I/O.
  3. VolatilityDashboard — presentation, pure of fetching.

These tests are written test-first (Kent Beck, TDD By Example) to drive the
God-Object `VolatilityFacade` apart along its seams. Existing tests in
test_volcalculator_time_range.py / test_vix_subplot.py / test_iv_term_structure.py
/ test_volatility_metric.py / test_price_log_returns.py stay green throughout:
the facade keeps delegating shims so its observed behaviour is preserved while
the new seams are extracted.
"""
import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fentu.explatoryservices.volcalculator import (
    VolatilityFacade,
    ReturnsRepository,
    MarketClock,
    VolatilityDashboard,
)


# ---------------------------------------------------------------------------
# Seam 1: ReturnsRepository — construction of the facade must do NO network I/O
# ---------------------------------------------------------------------------


class TestFacadeConstructionDoesNoNetworkIO:
    """The headline smell: `__init__` eagerly fired 4 yfinance round-trips.
    After extraction, constructing the facade touches no network at all.
    """

    def test_no_yf_ticker_call_during_construction(self):
        with patch("fentu.explatoryservices.volcalculator.yf.Ticker") as m:
            VolatilityFacade("FAKE")
            m.assert_not_called()

    def test_no_requests_session_during_construction(self):
        with patch("fentu.explatoryservices.volcalculator.requests.Session") as m:
            VolatilityFacade("FAKE")
            m.assert_not_called()


class TestReturnsRepositoryWindowing:
    """ReturnsRepository owns the start/end date window and tz stripping."""

    @pytest.fixture
    def prices(self):
        dates = pd.date_range("2025-01-01", "2025-12-31", freq="B")
        rng = np.random.default_rng(0)
        return pd.Series(
            100 + np.cumsum(rng.normal(0, 0.5, len(dates))),
            index=dates, name="Close",
        )

    def _repo(self, prices, start_date=None, end_date=None):
        repo = ReturnsRepository(start_date=start_date, end_date=end_date)
        # Feed tz-naive data: tz-stripping is _raw_ohlc's job, tested separately.
        repo._raw_ohlc = MagicMock(return_value=pd.DataFrame({"Close": prices}))
        return repo

    def test_get_prices_applies_start_and_end_window(self, prices):
        repo = self._repo(prices, "2025-03-01", "2025-06-01")
        out = repo.get_prices("FAKE")
        assert out.index.min() >= pd.Timestamp("2025-03-01")
        assert out.index.max() <= pd.Timestamp("2025-06-01")

    def test_raw_ohlc_strips_tz_from_index(self, prices):
        """tz-stripping is the responsibility of _raw_ohlc (the network seam)."""
        tz = prices.copy()
        tz.index = tz.index.tz_localize("UTC")
        repo = ReturnsRepository()
        with patch("fentu.explatoryservices.volcalculator.requests.Session"):
            with patch("fentu.explatoryservices.volcalculator.yf.Ticker") as m:
                m.return_value = MagicMock(
                    history=MagicMock(return_value=pd.DataFrame({"Close": tz}))
                )
                out = repo._raw_ohlc("FAKE")
        assert out.index.tz is None

    def test_get_vix_prices_returns_full_history_unfiltered(self):
        """The VIX subplot deliberately ignores the ETF's start/end window."""
        index = pd.bdate_range("1990-01-02", "2026-06-24")
        vix = pd.Series(range(len(index)), index=index, name="Close")
        repo = ReturnsRepository(start_date="2025-03-01", end_date="2025-06-01")
        repo._raw_ohlc = MagicMock(return_value=pd.DataFrame({"Close": vix}))
        out = repo.get_vix_prices()
        assert out.index.min().year <= 1992
        assert out.index.max().year >= 2026
        # NOT filtered to the facade's 2025-03-01..2025-06-01 window
        assert (out.index < pd.Timestamp("2025-03-01")).any()
        assert (out.index > pd.Timestamp("2025-06-01")).any()


class TestFacadeReturnsAreLazy:
    """Returns are computed on first access, not in __init__."""

    def test_daily_returns_not_present_until_accessed(self):
        facade = VolatilityFacade("FAKE")
        assert "_returns_cache" not in facade.__dict__ or "daily" not in facade.__dict__.get("_returns_cache", {})

    def test_daily_returns_fetched_on_first_access(self, monkeypatch):
        dates = pd.date_range("2025-01-01", periods=5, freq="B")
        prices = pd.Series([1.0, 2.0, 4.0, 8.0, 16.0], index=dates, name="Close")
        repo = MagicMock(spec=ReturnsRepository)
        repo.get_returns.return_value = np.log(
            prices / prices.shift(1))[1:]
        facade = VolatilityFacade("FAKE", repository=repo)
        daily = facade.daily_returns
        repo.get_returns.assert_called_once_with("FAKE", 1)
        assert len(daily) == 4  # one shift dropped
        # second access does NOT re-fetch
        repo.get_returns.reset_mock()
        _ = facade.daily_returns
        repo.get_returns.assert_not_called()


# ---------------------------------------------------------------------------
# Seam 2: MarketClock — pure DST / market-open logic
# ---------------------------------------------------------------------------


class TestMarketClock:
    def test_now_eastern_is_tz_aware(self):
        now = MarketClock().now_eastern()
        assert now.tzinfo is not None

    def test_market_opened_today_true_after_930_on_trading_day(self):
        clock = MarketClock()
        last_date = pd.Timestamp("2026-06-24").date()
        now_et = datetime(2026, 6, 24, 10, 0, tzinfo=timezone(timedelta(hours=-4)))
        assert clock.market_opened_today(last_date, now_et) is True

    def test_market_opened_today_false_before_930(self):
        clock = MarketClock()
        last_date = pd.Timestamp("2026-06-24").date()
        now_et = datetime(2026, 6, 24, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
        assert clock.market_opened_today(last_date, now_et) is False

    def test_market_opened_today_false_when_last_date_is_yesterday(self):
        clock = MarketClock()
        last_date = pd.Timestamp("2026-06-23").date()
        now_et = datetime(2026, 6, 24, 10, 0, tzinfo=timezone(timedelta(hours=-4)))
        assert clock.market_opened_today(last_date, now_et) is False

    def _vix_ohlc(self, last_date, last_open, last_close):
        dates = pd.bdate_range("1990-01-02", last_date)
        df = pd.DataFrame(
            {"Open": np.arange(len(dates), dtype=float),
             "Close": np.arange(len(dates), dtype=float) + 1.0},
            index=dates,
        )
        df.iloc[-1, df.columns.get_loc("Open")] = last_open
        df.iloc[-1, df.columns.get_loc("Close")] = last_close
        return df

    def test_current_vix_value_uses_open_when_market_opened_today(self):
        clock = MarketClock()
        vix = self._vix_ohlc("2026-06-24", 18.5, 19.0)
        now_et = datetime(2026, 6, 24, 10, 0, tzinfo=timezone(timedelta(hours=-4)))
        label, value = clock.current_vix_value(vix, now_et=now_et)
        assert "open" in label.lower()
        assert "9:30" in label
        assert value == pytest.approx(18.5)

    def test_current_vix_value_uses_last_close_before_open(self):
        clock = MarketClock()
        vix = self._vix_ohlc("2026-06-24", 18.5, 19.0)
        now_et = datetime(2026, 6, 24, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
        label, value = clock.current_vix_value(vix, now_et=now_et)
        assert "close" in label.lower()
        assert value == pytest.approx(19.0)


# ---------------------------------------------------------------------------
# Seam 3: VolatilityDashboard — presentation never fetches
# ---------------------------------------------------------------------------


class TestVolatilityDashboard:
    def test_show_panel_unavailable_renders_note(self):
        fig, ax = plt.subplots()
        VolatilityDashboard().show_panel_unavailable(ax, "IV Term Structure", "unavailable", "RuntimeError")
        assert ax.get_title() == "IV Term Structure"
        texts = [t.get_text() for t in ax.texts]
        assert any("unavailable" in t and "RuntimeError" in t for t in texts)
        plt.close(fig)

    def test_plot_vix_panel_renders_from_prebuilt_ohlc(self):
        vix = pd.DataFrame(
            {"Open": np.arange(5.0), "Close": np.arange(5.0) + 1.0},
            index=pd.bdate_range("2026-06-18", periods=5),
        )
        fig, ax = plt.subplots()
        VolatilityDashboard().plot_vix_panel(ax, vix, current_value=("VIX @ open", 18.5))
        assert ax.get_title() == "VIX Index"
        assert len(ax.get_lines()) >= 1
        texts = [t.get_text() for t in ax.texts]
        assert any("18.50" in t for t in texts), texts
        plt.close(fig)

    def test_plot_vix_panel_handles_empty_ohlc(self):
        fig, ax = plt.subplots()
        VolatilityDashboard().plot_vix_panel(ax, pd.DataFrame(), current_value=None)
        assert ax.get_title() == "VIX Index"
        assert any("unavailable" in t.get_text() for t in ax.texts)
        plt.close(fig)

    def test_plot_term_structure_panel_uses_injected_fetcher(self, monkeypatch):
        from collections import namedtuple
        Chain = namedtuple("Chain", ["calls", "puts"])
        calls = pd.DataFrame([{
            "contractSymbol": "20260717C0400000", "strike": 400,
            "impliedVolatility": 0.23, "lastPrice": 3.0,
        }])
        puts = pd.DataFrame([{
            "contractSymbol": "20260717P0400000", "strike": 400,
            "impliedVolatility": 0.25, "lastPrice": 4.0,
        }])
        chain_data = {"expiries": ["2026-07-17"], "chains": {"2026-07-17": Chain(calls=calls, puts=puts)}}

        def _fetcher(sym, max_expiries=None):
            return chain_data, 400.0

        fig, ax = plt.subplots()
        VolatilityDashboard().plot_term_structure_panel(ax, "QQQ", fetcher=_fetcher)
        assert ax.get_title() == "QQQ IV Term Structure"
        assert len(ax.lines) == 1
        plt.close(fig)

    def test_plot_term_structure_panel_graceful_on_fetch_exception(self):
        def boom(sym, max_expiries=None):
            raise RuntimeError("network down")

        fig, ax = plt.subplots()
        VolatilityDashboard().plot_term_structure_panel(ax, "QQQ", fetcher=boom)
        assert ax.get_title() == "IV Term Structure"
        assert len(ax.lines) == 0
        texts = [t.get_text() for t in ax.texts]
        assert any("unavailable" in t and "RuntimeError" in t for t in texts)
        plt.close(fig)
