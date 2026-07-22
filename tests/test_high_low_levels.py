"""High/low levels tool — test-first (Kent Beck, TDD By Example).

Drives a tiny feature: given any instrument's OHLC history, report the high
and low prints (and their dates) over two decision windows — the trailing two
calendar months and the regime since the 2026-02-28 US-Iran war start — plus
the current price's distance to each level (where the stop clusters sit, per
Paul Tudor Jones's moving-volume lesson).
"""
from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest

from fentu.explatoryservices.high_low_levels import (
    levels_report,
    levels_view,
    main,
    stop_zone,
    window_high_low,
)
from fentu.explatoryservices.volcalculator import ReturnsRepository


def _ohlc(rows):
    """Build a tz-naive OHLC frame from (date_str, high, low, close) tuples."""
    idx = pd.DatetimeIndex([r[0] for r in rows])
    return pd.DataFrame(
        {
            "High": [r[1] for r in rows],
            "Low": [r[2] for r in rows],
            "Close": [r[3] for r in rows],
        },
        index=idx,
    )


class TestWindowHighLow:
    def test_returns_high_and_low_with_dates_inside_window(self):
        ohlc = _ohlc(
            [
                ("2026-06-05", 72.0, 70.0, 71.0),
                ("2026-06-30", 83.0, 79.0, 80.0),
            ]
        )

        result = window_high_low(ohlc, date(2026, 6, 1), date(2026, 6, 30))

        assert result == {
            "high": 83.0,
            "high_date": date(2026, 6, 30),
            "low": 70.0,
            "low_date": date(2026, 6, 5),
        }

    def test_excludes_rows_outside_the_window(self):
        # The 99/1 prints sit outside [2026-06-01, 2026-06-30] and must not leak
        ohlc = _ohlc(
            [
                ("2026-05-31", 99.0, 90.0, 95.0),
                ("2026-06-05", 72.0, 70.0, 71.0),
                ("2026-06-30", 83.0, 79.0, 80.0),
                ("2026-07-01", 95.0, 1.0, 50.0),
            ]
        )

        result = window_high_low(ohlc, date(2026, 6, 1), date(2026, 6, 30))

        assert result["high"] == 83.0
        assert result["low"] == 70.0

    def test_returns_none_when_window_is_empty(self):
        ohlc = _ohlc([("2026-01-15", 75.0, 70.0, 72.0)])

        assert window_high_low(ohlc, date(2026, 6, 1), date(2026, 6, 30)) is None


class TestStopZone:
    """PTJ: old high 56.80 -> buy stops at 56.85. The zone sits JUST BEYOND the
    level: buy stops above old highs, sell stops below old lows."""

    def test_buy_stops_cluster_above_the_level(self):
        assert stop_zone(100.0, "buy") == (100.0, 101.0)

    def test_sell_stops_cluster_below_the_level(self):
        assert stop_zone(100.0, "sell") == (99.0, 100.0)

    def test_unknown_side_rejected(self):
        with pytest.raises(ValueError):
            stop_zone(100.0, "sideways")


class TestLevelsView:
    """The view-model the plot renders: every window's old high/low, its print
    date, and the stop cluster zone just beyond it (buy above highs, sell
    below lows). Driven by the same _uso_history fixture as the text report."""

    TODAY = date(2026, 7, 22)

    def test_emits_one_entry_per_level_per_window(self):
        view = levels_view(_uso_history(), today=self.TODAY)

        assert [(e["label"], e["kind"]) for e in view] == [
            ("2mo high", "high"),
            ("2mo low", "low"),
            ("war high", "high"),
            ("war low", "low"),
        ]

    def test_entries_carry_price_date_and_stop_zone(self):
        view = levels_view(_uso_history(), today=self.TODAY)
        by_label = {e["label"]: e for e in view}

        two_mo_high = by_label["2mo high"]
        assert two_mo_high["price"] == 88.0
        assert two_mo_high["date"] == date(2026, 5, 25)
        assert two_mo_high["stop_side"] == "buy"
        assert two_mo_high["stop_zone"] == pytest.approx((88.0, 88.88))

        war_low = by_label["war low"]
        assert war_low["price"] == 66.0
        assert war_low["date"] == date(2026, 4, 8)
        assert war_low["stop_side"] == "sell"
        assert war_low["stop_zone"] == pytest.approx((65.34, 66.0))


class TestPlotHighLowLevels:
    """The chart: close since war start, the four old high/low levels as
    signal lines with markers at their print dates, and the shaded stop
    clusters just beyond them (buy above highs, sell below lows)."""

    TODAY = date(2026, 7, 22)

    def test_renders_close_levels_stop_zones_and_print_markers(self):
        import matplotlib.pyplot as plt

        from fentu.explatoryservices.high_low_levels import plot_high_low_levels

        fig, ax = plt.subplots()
        plot_high_low_levels(
            _uso_history(), "USO", today=self.TODAY, ax=ax, show=False
        )

        # 1 close line + 4 level lines + 4 print-date markers
        assert len(ax.lines) == 9
        # 4 shaded stop-cluster bands, one beyond each level
        # (axhspan artists live in ax.patches, not ax.collections)
        assert len(ax.patches) == 4
        texts = [t.get_text() for t in ax.texts]
        assert texts.count("buy stops") == 2
        assert texts.count("sell stops") == 2
        assert "USO" in ax.get_title()
        plt.close(fig)


class TestMainCli:
    """CLI: text report always; --plot adds the chart off ONE fetch."""

    def _patched(self, mp, fetches):
        def _fake_raw_ohlc(self, ticker):
            fetches.append(ticker)
            return _uso_history()

        mp.setattr(
            "fentu.explatoryservices.high_low_levels.ReturnsRepository._raw_ohlc",
            _fake_raw_ohlc,
        )

    def test_plot_flag_prints_report_and_plots_off_one_fetch(self, capsys):
        fetches, plotted = [], []
        with pytest.MonkeyPatch.context() as mp:
            self._patched(mp, fetches)
            mp.setattr(
                "fentu.explatoryservices.high_low_levels.plot_high_low_levels",
                lambda ohlc, instrument: plotted.append(instrument),
            )
            main(["USO", "--plot"])

        assert fetches == ["USO"]  # exactly one fetch feeds report + chart
        assert plotted == ["USO"]
        assert capsys.readouterr().out.startswith("USO @ 77.00\n")

    def test_no_plot_flag_stays_text_only(self, capsys):
        fetches = []
        with pytest.MonkeyPatch.context() as mp:
            self._patched(mp, fetches)

            def _boom(*args, **kwargs):
                raise AssertionError("plot must not run without --plot")

            mp.setattr(
                "fentu.explatoryservices.high_low_levels.plot_high_low_levels", _boom
            )
            main(["USO"])

        assert fetches == ["USO"]
        assert capsys.readouterr().out.startswith("USO @ 77.00\n")


def _uso_history():
    """One OHLC history spanning pre-war, war-regime, and the trailing 2 months.

    Rows are chosen so each window's answer is hand-derivable: last close 77.00;
    2mo window [2026-05-22, 2026-07-22] -> high 88.00 (05-25), low 70.00 (06-05);
    war window [2026-02-28, 2026-07-22] -> high 90.00 (03-04), low 66.00 (04-08).
    """
    return _ohlc(
        [
            ("2026-01-15", 75.0, 70.0, 72.0),  # pre-war: excluded from both windows
            ("2026-03-04", 90.0, 80.0, 82.0),  # war regime only: the war high
            ("2026-04-08", 69.0, 66.0, 67.5),  # war regime only: the war low
            ("2026-05-25", 88.0, 84.0, 86.0),  # both windows: the 2mo high
            ("2026-06-05", 72.0, 70.0, 71.0),  # both windows: the 2mo low
            ("2026-06-30", 83.0, 79.0, 80.0),
            ("2026-07-21", 78.0, 76.0, 77.0),  # last close 77.00
        ]
    )


def _repo_with(ohlc):
    repo = MagicMock(spec=ReturnsRepository)
    repo._raw_ohlc.return_value = ohlc
    return repo


class TestLevelsReport:
    TODAY = date(2026, 7, 22)

    def test_reports_both_windows_with_distances(self):
        # distances from last close 77.00: 88/77-1=+14.3%, 70/77-1=-9.1%,
        # 90/77-1=+16.9%, 66/77-1=-14.3%
        report = levels_report(
            "USO", repository=_repo_with(_uso_history()), today=self.TODAY
        )

        assert report == (
            "USO @ 77.00\n"
            "past 2mo (since 2026-05-22): "
            "high 88.00 (2026-05-25, +14.3% above) | "
            "low 70.00 (2026-06-05, -9.1% below)\n"
            "since 2026-02-28 (war start): "
            "high 90.00 (2026-03-04, +16.9% above) | "
            "low 66.00 (2026-04-08, -14.3% below)"
        )

    def test_extensible_to_any_instrument(self):
        # Triangulate: a second ticker forces `instrument` to be a real
        # parameter — same history, different label, fetched ticker verified.
        repo = _repo_with(_uso_history())

        report = levels_report("BNO", repository=repo, today=self.TODAY)

        repo._raw_ohlc.assert_called_once_with("BNO")
        assert report.splitlines()[0] == "BNO @ 77.00"
        assert "high 88.00 (2026-05-25, +14.3% above)" in report

    def test_defaults_to_uso_when_no_instrument_given(self):
        repo = _repo_with(_uso_history())

        report = levels_report(repository=repo, today=self.TODAY)

        repo._raw_ohlc.assert_called_once_with("USO")
        assert report.splitlines()[0] == "USO @ 77.00"

    def test_unavailable_on_fetch_exception(self):
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.side_effect = RuntimeError("network down")

        assert (
            levels_report("USO", repository=repo, today=self.TODAY)
            == "USO unavailable"
        )

    def test_defaults_today_and_constructs_default_repository(self):
        class FakeDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 7, 22)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("fentu.explatoryservices.high_low_levels.date", FakeDate)
            mp.setattr(
                "fentu.explatoryservices.high_low_levels.ReturnsRepository._raw_ohlc",
                lambda self, ticker: _uso_history(),
            )
            report = levels_report()

        assert report.splitlines()[0] == "USO @ 77.00"
        assert "past 2mo (since 2026-05-22)" in report

    def test_unavailable_on_empty_history(self):
        empty = pd.DataFrame(
            {"High": pd.Series([], dtype=float), "Low": pd.Series([], dtype=float),
             "Close": pd.Series([], dtype=float)}
        )

        assert (
            levels_report("USO", repository=_repo_with(empty), today=self.TODAY)
            == "USO unavailable"
        )
