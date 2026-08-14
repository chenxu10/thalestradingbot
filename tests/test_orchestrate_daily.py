"""
Test the daily orchestrator: signal gate -> high/low levels -> QQQ tail chart.

All three reused tools are mocked at their seams (no network):

- ``PortfolioMonitor.prepare_panels`` supplies the signal/noise view-model.
- ``levels_report`` is the high/low report for SIGNAL tickers only.
- ``tail_plot.plot_tail_cheapness`` runs every day (unless ``--skip-tail``).
"""
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


class _FakeMonitor:
    """PortfolioMonitor-shaped fake: fixed holdings, injected panels."""

    holdings = (("TQQQ", "TQQQ"), ("USO", "USO"),
                ("IAU", "IAU"), ("BRKB", "BRK-B"))

    def __init__(self, panels):
        self.panels = panels

    def prepare_panels(self):
        return self.panels


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


def test_main_runs_levels_for_signal_only_and_tail_every_day(capsys):
    monitor = _FakeMonitor([
        _panel(label="TQQQ", signal=True),
        _panel(label="USO", signal=False, multiple=0.5),
    ])
    with patch(
        "fentu.orchestrator.orchestrate_daily.PortfolioMonitor",
        return_value=monitor,
    ), patch(
        "fentu.orchestrator.orchestrate_daily.levels_report",
        return_value="TQQQ @ 100.00\n2mo: high ...",
    ) as fake_levels, patch(
        "fentu.pricingservices.tail_plot.plot_tail_cheapness",
        return_value=("figures/tail_cheapness_aug14_2026.png", 0.03, 0.04),
    ) as fake_tail:
        assert main([]) == 0

    out = capsys.readouterr().out
    assert "TQQQ: last +1.20%" in out
    assert "SIGNAL" in out and "noise" in out
    fake_levels.assert_called_once_with("TQQQ")
    fake_tail.assert_called_once_with()
    # 0.03 < q25 0.04 -> cheap, the reused tail_plot verdict.
    assert "CHEAP - buy the tail" in out
    assert "chart: figures/tail_cheapness_aug14_2026.png" in out


def test_main_no_signal_still_runs_tail(capsys):
    monitor = _FakeMonitor([_panel(label="USO", signal=False, multiple=0.5)])
    with patch(
        "fentu.orchestrator.orchestrate_daily.PortfolioMonitor",
        return_value=monitor,
    ), patch(
        "fentu.orchestrator.orchestrate_daily.levels_report",
    ) as fake_levels, patch(
        "fentu.pricingservices.tail_plot.plot_tail_cheapness",
        return_value=("figures/tail_cheapness_aug14_2026.png", 0.05, 0.04),
    ):
        assert main([]) == 0

    out = capsys.readouterr().out
    assert "no SIGNAL today" in out
    fake_levels.assert_not_called()
    assert "NOT cheap - wait, let the strangles fund" in out


def test_main_skip_tail_skips_option_chain(capsys):
    monitor = _FakeMonitor([_panel(label="USO", signal=False, multiple=0.5)])
    with patch(
        "fentu.orchestrator.orchestrate_daily.PortfolioMonitor",
        return_value=monitor,
    ), patch(
        "fentu.pricingservices.tail_plot.plot_tail_cheapness",
    ) as fake_tail:
        assert main(["--skip-tail"]) == 0

    out = capsys.readouterr().out
    assert "QQQ tail-to-body ratio" not in out
    fake_tail.assert_not_called()
