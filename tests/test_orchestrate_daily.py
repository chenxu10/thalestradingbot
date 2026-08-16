"""
Test the daily orchestrator: signal gate -> high/low levels -> QQQ tail chart.

All reused tools are mocked at their seams (no network, no GUI):

- ``PortfolioMonitor.prepare_panels`` supplies the signal/noise view-model and
  ``visualize`` pops the 2x2 panel (only when plots are shown).
- ``ReturnsRepository.try_fetch_open_high_low_close`` supplies price frames;
  ``_report_from_open_high_low_close`` the text and ``plot_high_low_levels``
  the chart for SIGNAL tickers only.
- ``tail_plot.plot_tail_cheapness`` runs every day (unless ``--skip-tail``)
  with ``show=`` matching the ``--no-show`` flag.
"""
import pandas as pd
from unittest.mock import patch

from fentu.orchestrator.orchestrate_daily import (
    format_panel_line,
    main,
    signal_panels,
)


def _panel(label="TQQQ", available=True, signal=True, multiple=2.0,
           last_move=1.2, usual=0.6, significance=4.0):
    return {
        "label": label,
        "available": available,
        "signal": signal,
        "multiple": multiple,
        "last_move": last_move,
        "usual": usual,
        "significance": significance,
    }


def _frame():
    """Non-empty open_high_low_close-shaped frame (so plots are attempted)."""
    return pd.DataFrame({"Close": [100.0, 101.0]})


class _FakeMonitor:
    """PortfolioMonitor-shaped fake: fixed holdings, injected panels."""

    holdings = (("TQQQ", "TQQQ"), ("USO", "USO"),
                ("IAU", "IAU"), ("BRKB", "BRK-B"))

    def __init__(self, panels):
        self.panels = panels
        self.shown_panels = None

    def prepare_panels(self):
        return self.panels

    def visualize(self, panels=None):
        self.shown_panels = panels if panels is not None else self.panels
        return None


class _FakeRepository:
    """ReturnsRepository-shaped fake: frames by ticker, no network."""

    def __init__(self, frames=None):
        self._frames = frames or {}

    def try_fetch_open_high_low_close(self, instrument):
        return self._frames.get(instrument)


def test_signal_panels_keep_only_available_signals():
    panels = [
        _panel(label="TQQQ", signal=True),
        _panel(label="USO", signal=False, multiple=0.5),
        _panel(label="IAU", available=False, signal=True),
    ]
    assert [p["label"] for p in signal_panels(panels)] == ["TQQQ"]


def test_format_panel_line_signal_and_noise():
    assert "SIGNAL" in format_panel_line(_panel())
    assert "noise" in format_panel_line(_panel(signal=False, multiple=0.5))


def test_format_panel_line_unavailable_and_undefined_usual():
    assert "unavailable" in format_panel_line(_panel(available=False))
    assert ("usual change undefined" in
            format_panel_line(_panel(signal=False, multiple=None)))


def test_main_no_show_reports_levels_for_signal_only_and_runs_tail(capsys):
    monitor = _FakeMonitor([
        _panel(label="TQQQ", signal=True),
        _panel(label="USO", signal=False, multiple=0.5),
    ])
    repository = _FakeRepository({"TQQQ": _frame()})
    with patch(
        "fentu.orchestrator.orchestrate_daily.PortfolioMonitor",
        return_value=monitor,
    ), patch(
        "fentu.orchestrator.orchestrate_daily.ReturnsRepository",
        return_value=repository,
    ), patch(
        "fentu.orchestrator.orchestrate_daily._report_from_open_high_low_close",
        return_value="TQQQ @ 101.00\n2mo: high ...",
    ) as fake_report, patch(
        "fentu.orchestrator.orchestrate_daily.plot_high_low_levels",
    ) as fake_plot, patch(
        "fentu.pricingservices.tail_plot.plot_tail_cheapness",
        return_value=("figures/tail_cheapness_aug14_2026.png", 0.03, 0.04),
    ) as fake_tail:
        assert main(["--no-show"]) == 0

    out = capsys.readouterr().out
    assert "TQQQ: last +1.20%" in out
    assert "SIGNAL" in out and "noise" in out
    assert "TQQQ SIGNAL today -> high/low levels" in out
    monitor.shown_panels is None  # --no-show: the 2x2 panel never pops out
    fake_report.assert_called_once()
    assert fake_report.call_args[0][1] == "TQQQ"
    fake_plot.assert_not_called()
    fake_tail.assert_called_once_with(show=False)
    # 0.03 < q25 0.04 -> cheap, the reused tail_plot verdict.
    assert "CHEAP - buy the tail" in out
    assert "chart: figures/tail_cheapness_aug14_2026.png" in out


def test_main_shows_panel_level_plot_and_tail_chart(capsys):
    monitor = _FakeMonitor([_panel(label="TQQQ", signal=True)])
    repository = _FakeRepository({"TQQQ": _frame()})
    with patch(
        "fentu.orchestrator.orchestrate_daily.PortfolioMonitor",
        return_value=monitor,
    ), patch(
        "fentu.orchestrator.orchestrate_daily.ReturnsRepository",
        return_value=repository,
    ), patch(
        "fentu.orchestrator.orchestrate_daily._report_from_open_high_low_close",
        return_value="TQQQ @ 101.00",
    ), patch(
        "fentu.orchestrator.orchestrate_daily.plot_high_low_levels",
    ) as fake_plot, patch(
        "fentu.pricingservices.tail_plot.plot_tail_cheapness",
        return_value=("figures/tail_cheapness_aug14_2026.png", 0.03, 0.04),
    ) as fake_tail:
        assert main([]) == 0

    assert monitor.shown_panels is not None  # the 2x2 panel pops out
    fake_plot.assert_called_once()
    assert fake_plot.call_args[0][1] == "TQQQ"
    assert fake_plot.call_args[1]["show"] is True
    fake_tail.assert_called_once_with(show=True)


def test_main_no_signal_still_runs_tail(capsys):
    monitor = _FakeMonitor([_panel(label="USO", signal=False, multiple=0.5)])
    repository = _FakeRepository()
    with patch(
        "fentu.orchestrator.orchestrate_daily.PortfolioMonitor",
        return_value=monitor,
    ), patch(
        "fentu.orchestrator.orchestrate_daily.ReturnsRepository",
        return_value=repository,
    ), patch(
        "fentu.orchestrator.orchestrate_daily.plot_high_low_levels",
    ) as fake_plot, patch(
        "fentu.pricingservices.tail_plot.plot_tail_cheapness",
        return_value=("figures/tail_cheapness_aug14_2026.png", 0.05, 0.04),
    ):
        assert main(["--no-show"]) == 0

    out = capsys.readouterr().out
    assert "no SIGNAL today" in out
    fake_plot.assert_not_called()
    assert "NOT cheap - wait, let the strangles fund" in out


def test_main_skip_tail_skips_option_chain(capsys):
    monitor = _FakeMonitor([_panel(label="USO", signal=False, multiple=0.5)])
    repository = _FakeRepository()
    with patch(
        "fentu.orchestrator.orchestrate_daily.PortfolioMonitor",
        return_value=monitor,
    ), patch(
        "fentu.orchestrator.orchestrate_daily.ReturnsRepository",
        return_value=repository,
    ), patch(
        "fentu.pricingservices.tail_plot.plot_tail_cheapness",
    ) as fake_tail:
        assert main(["--skip-tail"]) == 0

    out = capsys.readouterr().out
    assert "QQQ tail-to-body ratio" not in out
    fake_tail.assert_not_called()


def test_main_survives_unusable_qqq_quotes(capsys):
    """Closed-market zero quotes must skip the chart, not crash the day."""
    monitor = _FakeMonitor([_panel(label="USO", signal=False, multiple=0.5)])
    repository = _FakeRepository()
    with patch(
        "fentu.orchestrator.orchestrate_daily.PortfolioMonitor",
        return_value=monitor,
    ), patch(
        "fentu.orchestrator.orchestrate_daily.ReturnsRepository",
        return_value=repository,
    ), patch(
        "fentu.pricingservices.tail_plot.plot_tail_cheapness",
        side_effect=RuntimeError(
            "QQQ option quotes unusable today (closed market returns zeros): "
            "straddle=0.00, 25% wing=0.00, atm_iv=0.0000"),
    ):
        assert main([]) == 0

    out = capsys.readouterr().out
    assert "QQQ tail chart skipped" in out
    assert "straddle=0.00" in out
