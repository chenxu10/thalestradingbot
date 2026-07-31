"""
Test the portfolio signal monitor — Taleb's trick, Fooled by Randomness p.166
(PDF page 93 of teams/2005-01-01-nassim-nicolas-taleb-fooled-by-randomness.pdf):

  1. Display price + percentage change of the holdings in a FIXED panel.
  2. "Unless something moves by more than its usual daily percentage change,
     the event is deemed to be noise."  (usual = MAD, the headline metric)
  3. "A 2% move is not twice as significant an event as 1%, it is rather
     like four times."  (significance scales with the SQUARE of the move)

Network I/O is faked through the injectable `repository` seam, mirroring the
conventions in test_volatility_metric.py / test_vix_subplot.py.
"""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

import matplotlib
matplotlib.use("Agg")  # headless rendering for tests
import matplotlib.pyplot as plt

from fentu.explatoryservices.portfolio_monitor import (
    DEFAULT_PORTFOLIO,
    PortfolioMonitor,
    is_signal,
    noise_multiple,
    plot_signal_panel,
    significance,
    _bar_color,
)


def _prices_from_returns(returns, start=100.0):
    """Build a Close-price series whose log returns are exactly `returns`."""
    prices = start * np.exp(np.concatenate([[0.0], np.cumsum(returns)]))
    index = pd.bdate_range("2025-01-01", periods=len(prices))
    return pd.Series(prices, index=index, name="Close")


def _prices_on_index(returns, index, start=100.0):
    """Close prices on a caller-chosen index (e.g. month-end / year-end)."""
    prices = start * np.exp(np.concatenate([[0.0], np.cumsum(returns)]))
    return pd.Series(prices, index=index, name="Close")


class FakeRepository:
    """ReturnsRepository-shaped fake: no network, deterministic prices."""

    def __init__(self, prices_by_ticker):
        self._prices = prices_by_ticker
        self.requested = []

    def get_prices(self, ticker):
        self.requested.append(ticker)
        return self._prices[ticker]

    def get_returns(self, ticker, period_length):
        prices = self.get_prices(ticker)
        return np.log(prices / prices.shift(period_length))[period_length:]


def _tqqq_prices():
    """40 calm returns of +-0.01 (mean 0, MAD 0.01) then a +0.05 event."""
    returns = [0.01, -0.01] * 20 + [0.05]
    return _prices_from_returns(returns)


def _calm_prices():
    """40 calm returns of +-0.005 (MAD 0.005) then a small -0.004 move."""
    returns = [0.005, -0.005] * 20 + [-0.004]
    return _prices_from_returns(returns)


@pytest.fixture
def fake_repository():
    calm = _calm_prices()
    return FakeRepository({
        "TQQQ": _tqqq_prices(),
        "USO": calm,
        "IAU": calm,
        "BRK-B": calm,
    })


class TestNonLinearInterpretation:
    def test_two_percent_is_four_times_one_percent_not_twice(self):
        # Taleb: "a 2% move ... is rather like four times" a 1% move.
        assert significance(2.0, 1.0) == pytest.approx(4.0)

    def test_significance_is_quadratic_in_the_mad_multiple(self):
        assert significance(3.0, 1.0) == pytest.approx(9.0)
        assert significance(-3.0, 1.0) == pytest.approx(9.0)

    def test_noise_multiple_is_signed(self):
        assert noise_multiple(-0.5, 1.0) == pytest.approx(-0.5)

    def test_noise_multiple_undefined_when_usual_is_zero_or_nan(self):
        assert noise_multiple(1.0, 0.0) is None
        assert noise_multiple(1.0, float("nan")) is None
        assert significance(1.0, 0.0) is None


class TestNoiseFilter:
    def test_move_within_usual_change_is_noise(self):
        assert not is_signal(0.9, 1.0)
        assert not is_signal(-0.9, 1.0)

    def test_move_beyond_usual_change_is_signal(self):
        assert is_signal(1.1, 1.0)
        assert is_signal(-1.1, 1.0)

    def test_bar_colors_gray_noise_red_down_green_up(self):
        assert _bar_color(0.5, 1.0) == "0.75"   # noise -> gray
        assert _bar_color(2.0, 1.0) == "green"  # up signal
        assert _bar_color(-2.0, 1.0) == "red"   # down signal


class TestPreparePanels:
    def test_fixed_panel_order_and_brkb_ticker_mapping(self, fake_repository):
        monitor = PortfolioMonitor(repository=fake_repository)
        panels = monitor.prepare_panels()
        assert [p["label"] for p in panels] == ["TQQQ", "USO", "IAU", "BRKB"]
        assert "BRK-B" in fake_repository.requested  # yfinance ticker
        assert [h[1] for h in DEFAULT_PORTFOLIO][-1] == "BRK-B"

    def test_tqqq_big_move_is_highlighted_signal(self, fake_repository):
        panel = PortfolioMonitor(repository=fake_repository).prepare_panels()[0]
        # usual = MAD of the calm calibration window = 0.01 -> 1.0 percent;
        # the last +0.05 event never calibrates its own denominator.
        assert panel["usual"] == pytest.approx(1.0)
        assert panel["last_move"] == pytest.approx(5.0)
        assert panel["multiple"] == pytest.approx(5.0)
        assert panel["significance"] == pytest.approx(25.0)
        assert panel["signal"] is True
        assert panel["last_price"] == pytest.approx(100.0 * np.exp(0.05))

    def test_calm_move_is_deemed_noise(self, fake_repository):
        panel = PortfolioMonitor(repository=fake_repository).prepare_panels()[1]
        assert panel["usual"] == pytest.approx(0.5)
        assert panel["multiple"] == pytest.approx(-0.8)
        assert panel["signal"] is False

    def test_window_is_trimmed_to_lookback(self, fake_repository):
        monitor = PortfolioMonitor(repository=fake_repository, lookback=10)
        panel = monitor.prepare_panels()[0]
        assert len(panel["window"]) == 10

    def test_weekly_bars_are_non_overlapping_calendar_weeks(
            self, fake_repository):
        monitor = PortfolioMonitor(repository=fake_repository, period="weekly")
        panel = monitor.prepare_panels()[0]
        # 42 business days (Wed 2025-01-01 -> Thu 2025-02-27) resample to 9
        # Friday buckets -> 8 NON-overlapping weekly returns (the old rolling
        # 5-day window faked 37 mostly-redundant bars from the same data).
        assert len(panel["window"]) == 8
        assert (panel["window"].index.weekday == 4).all()  # all Fridays
        # Each full week sums five alternating +-0.01 daily returns -> +-1.0%.
        assert panel["window"].iloc[0] == pytest.approx(1.0)
        # The last (still-open) week holds the +0.05 event: -1+1-1+5 -> +4.0%.
        assert panel["last_move"] == pytest.approx(4.0)
        assert panel["incomplete_label"] == "WTD"
        assert panel["signal"] is True

    def test_monthly_bars_are_calendar_months_trimmed_to_lookback(self):
        index = pd.date_range("2020-01-31", periods=72, freq="ME")
        prices = _prices_on_index([0.02, -0.02] * 35 + [0.09], index)
        repo = FakeRepository({t: prices for _, t in DEFAULT_PORTFOLIO})
        panel = PortfolioMonitor(
            repository=repo, period="monthly").prepare_panels()[0]
        assert len(panel["window"]) == 60  # 71 months available, capped at 60
        assert panel["window"].index.is_month_end.all()
        # Non-overlapping: every completed bar is exactly one month's +-2.0%.
        assert set(np.round(panel["window"].values[:-1], 6)) == {2.0, -2.0}
        assert panel["usual"] == pytest.approx(2.0)  # MAD of 70 alternating
        assert panel["last_move"] == pytest.approx(9.0)
        assert panel["multiple"] == pytest.approx(4.5)
        assert panel["incomplete_label"] == "MTD"

    def test_yearly_history_is_never_truncated(self):
        index = pd.date_range("1961-12-31", periods=65, freq="YE")
        prices = _prices_on_index([0.10, -0.05] * 32, index)
        repo = FakeRepository({t: prices for _, t in DEFAULT_PORTFOLIO})
        panel = PortfolioMonitor(
            repository=repo, period="yearly").prepare_panels()[0]
        # 64 yearly bars — MORE than the old fixed 60: yearly is uncapped,
        # cutting old years would amputate the deep-tail observations.
        assert len(panel["window"]) == 64
        assert panel["window"].index[0] == index[1]
        assert panel["n_calibration"] == 63
        assert panel["insufficient_history"] is False
        assert panel["incomplete_label"] == "YTD"
        assert panel["last_move"] == pytest.approx(-5.0)

    def test_yearly_aggregates_daily_prices_and_flags_thin_history(self):
        prices = _prices_from_returns([0.001] * 756)  # ~3 years of calm days
        repo = FakeRepository({t: prices for _, t in DEFAULT_PORTFOLIO})
        panel = PortfolioMonitor(
            repository=repo, period="yearly").prepare_panels()[0]
        assert len(panel["window"]) == 2  # 3 year-end buckets -> 2 yearly bars
        # Honest small sample: 1 calibration point, no fake MAD precision.
        assert panel["n_calibration"] == 1
        assert panel["insufficient_history"] is True
        assert panel["multiple"] is None  # MAD of one point is 0 -> undefined

    def test_invalid_period_rejected(self):
        with pytest.raises(ValueError):
            PortfolioMonitor(period="hourly")


class TestVerdictStyling:
    """The verdict word carries the color: green SIGNAL, red noise."""

    def _verdict_text(self, panel):
        fig, ax = plt.subplots()
        plot_signal_panel(ax, panel)
        plt.close(fig)
        verdicts = [t for t in ax.texts if t.get_text() in ("SIGNAL", "noise")]
        assert len(verdicts) == 1
        return verdicts[0]

    def test_signal_word_is_green(self, fake_repository):
        panel = PortfolioMonitor(repository=fake_repository).prepare_panels()[0]
        verdict = self._verdict_text(panel)
        assert verdict.get_text() == "SIGNAL"
        assert verdict.get_color() == "green"

    def test_noise_word_is_red(self, fake_repository):
        panel = PortfolioMonitor(repository=fake_repository).prepare_panels()[1]
        verdict = self._verdict_text(panel)
        assert verdict.get_text() == "noise"
        assert verdict.get_color() == "red"


class TestExpressiveAxes:
    """The chart itself answers 'what period does this cover, and what does
    a bar mean?' — date-span titles, period-named axes, intention legend."""

    def test_daily_panel_title_axes_and_span(self, fake_repository):
        panel = PortfolioMonitor(repository=fake_repository).prepare_panels()[0]
        fig, ax = plt.subplots()
        plot_signal_panel(ax, panel)
        plt.close(fig)
        assert ax.get_title() == "TQQQ  (Jan–Feb 2025)"
        assert ax.get_xlabel() == "Day ending"
        assert ax.get_ylabel() == "% change per day"

    def test_yearly_panel_title_shows_year_span(self):
        index = pd.date_range("2006-12-31", periods=20, freq="YE")
        prices = _prices_on_index([0.08] * 19, index)
        repo = FakeRepository({t: prices for _, t in DEFAULT_PORTFOLIO})
        panel = PortfolioMonitor(
            repository=repo, period="yearly").prepare_panels()[0]
        fig, ax = plt.subplots()
        plot_signal_panel(ax, panel)
        plt.close(fig)
        assert ax.get_title() == "TQQQ  (2007–2025)"
        assert ax.get_xlabel() == "Year ending"
        assert ax.get_ylabel() == "% change per year"

    def test_figure_legend_states_the_intention(self, fake_repository):
        fig = PortfolioMonitor(repository=fake_repository).visualize()
        plt.close(fig)
        assert len(fig.legends) == 1
        labels = [t.get_text() for t in fig.legends[0].get_texts()]
        assert any("usual band (±1 MAD)" in label for label in labels)
        assert any("noise" in label for label in labels)
        assert any("up signal" in label for label in labels)
        assert any("down signal" in label for label in labels)

    def test_annotation_marks_open_period_and_calibration_size(self):
        index = pd.date_range("2006-12-31", periods=20, freq="YE")
        prices = _prices_on_index([0.08, -0.04] * 9 + [0.08], index)
        repo = FakeRepository({t: prices for _, t in DEFAULT_PORTFOLIO})
        panel = PortfolioMonitor(
            repository=repo, period="yearly").prepare_panels()[0]
        fig, ax = plt.subplots()
        plot_signal_panel(ax, panel)
        plt.close(fig)
        note = max(ax.texts, key=lambda t: len(t.get_text())).get_text()
        assert "YTD +8.00%" in note           # the still-open year is tagged
        assert "MAD of 18 years" in note      # honest calibration sample size
        assert "as of 31 Dec 2025" in note

    def test_insufficient_history_warning_is_rendered(self):
        prices = _prices_from_returns([0.001] * 756)
        repo = FakeRepository({t: prices for _, t in DEFAULT_PORTFOLIO})
        panel = PortfolioMonitor(
            repository=repo, period="yearly").prepare_panels()[0]
        fig, ax = plt.subplots()
        plot_signal_panel(ax, panel)
        plt.close(fig)
        note = max(ax.texts, key=lambda t: len(t.get_text())).get_text()
        assert "insufficient history" in note


class TestVisualize:
    def test_builds_a_two_by_two_figure_without_network(self, fake_repository):
        monitor = PortfolioMonitor(repository=fake_repository)
        fig = monitor.visualize()
        assert len(fig.axes) == 4
        titles = [ax.get_title() for ax in fig.axes]
        assert [t.split("  ")[0] for t in titles] == ["TQQQ", "USO", "IAU", "BRKB"]


class FlakyRepository(FakeRepository):
    """Fake whose fetch blows up for one ticker (spurious yfinance failure)."""

    def __init__(self, prices_by_ticker, fail_on):
        super().__init__(prices_by_ticker)
        self._fail_on = fail_on

    def get_prices(self, ticker):
        if ticker == self._fail_on:
            raise AttributeError("'Index' object has no attribute 'tz'")
        return super().get_prices(ticker)

    def get_returns(self, ticker, period_length):
        if ticker == self._fail_on:
            raise AttributeError("'Index' object has no attribute 'tz'")
        return super().get_returns(ticker, period_length)


class TestUnavailableHolding:
    """A network hiccup on one holding must never crash the monitor —
    it degrades to an 'unavailable' placeholder; the rest still render."""

    def test_failed_fetch_marks_panel_unavailable_and_keeps_others(
            self, fake_repository):
        repo = FlakyRepository(fake_repository._prices, fail_on="TQQQ")
        panels = PortfolioMonitor(repository=repo).prepare_panels()
        assert [p["label"] for p in panels] == ["TQQQ", "USO", "IAU", "BRKB"]
        assert panels[0]["available"] is False
        assert all(p["available"] for p in panels[1:])

    def test_empty_history_marks_panel_unavailable(self, fake_repository):
        prices = dict(fake_repository._prices)
        prices["TQQQ"] = pd.Series(dtype=float, name="Close")
        panels = PortfolioMonitor(
            repository=FakeRepository(prices)).prepare_panels()
        assert panels[0]["available"] is False

    def test_visualize_renders_placeholder_without_crashing(
            self, fake_repository):
        repo = FlakyRepository(fake_repository._prices, fail_on="TQQQ")
        fig = PortfolioMonitor(repository=repo).visualize()
        assert len(fig.axes) == 4
        assert any("unavailable" in t.get_text() for t in fig.axes[0].texts)


class TestSeeChangeCliDispatch:
    def test_portfolio_ticker_routes_to_monitor(self):
        with patch("sys.argv", ["see_change", "daily", "portfolio"]):
            with patch(
                "fentu.explatoryservices.portfolio_monitor.PortfolioMonitor"
            ) as mock_monitor:
                from fentu.explatoryservices.seechange import main
                main()
        mock_monitor.assert_called_once_with(period="daily")
        mock_monitor.return_value.visualize.assert_called_once_with()

    def test_invalid_timeframe_exits_before_dispatch(self):
        with patch("sys.argv", ["see_change", "bogus", "portfolio"]):
            with patch(
                "fentu.explatoryservices.portfolio_monitor.PortfolioMonitor"
            ) as mock_monitor:
                from fentu.explatoryservices.seechange import main
                with pytest.raises(SystemExit):
                    main()
        mock_monitor.assert_not_called()
