"""Daily orchestration: portfolio signal scan -> high/low levels -> QQQ tail/body.

One run, every day, reusing the three existing tools as-is. Every phase prints
its report AND pops its plot out on screen (close a window to advance):

1. ``see_change daily portfolio`` — Taleb's noise filter (Fooled by Randomness
   p.166): each holding's last move vs its usual (MAD) move. Beyond ±1 usual
   move is a SIGNAL, inside is noise. Reuses
   ``fentu.explatoryservices.portfolio_monitor.PortfolioMonitor`` — the same
   object ``see_change daily portfolio`` drives, then its 2x2 signal panel via
   ``PortfolioMonitor.visualize``.
2. Once a ticker prints a SIGNAL (not noise), see its high/low levels — PTJ
   moving volume: where the stops cluster above old highs / below old lows.
   Reuses ``fentu.explatoryservices.high_low_levels`` report + plot.
3. Every day, present the NDX100 (QQQ) tail-to-body ratio chart — is the
   far-OTM wing cheap vs the ATM body? Reuses
   ``fentu.pricingservices.tail_plot.plot_tail_cheapness``, which saves
   ``figures/tail_cheapness_<date>.png`` and pops the chart up.

Run it:
    uv run python -m fentu.orchestrator.orchestrate_daily

Flags:
    --skip-tail   run only the signal scan + high/low levels (no option chain)
    --no-show     print reports only, no plots pop out (headless/cron runs)
"""

from __future__ import annotations

import logging
import sys
from datetime import date

from fentu.explatoryservices.high_low_levels import (
    _report_from_open_high_low_close,
    plot_high_low_levels,
)
from fentu.explatoryservices.portfolio_monitor import PortfolioMonitor
from fentu.explatoryservices.volcalculator import ReturnsRepository
from fentu.pricingservices import tail_plot

logger = logging.getLogger(__name__)


def signal_panels(panels):
    """Panels whose last move is a SIGNAL, not noise (available holdings only)."""
    return [panel for panel in panels
            if panel.get("available") and panel.get("signal")]


def format_panel_line(panel):
    """One report line per holding: last move vs usual, verdict SIGNAL/noise."""
    if not panel.get("available"):
        return f"{panel['label']}: unavailable"
    multiple = panel["multiple"]
    if multiple is None:
        reading = "usual change undefined"
    else:
        reading = f"{multiple:+.1f}x usual, significance {panel['significance']:.1f}x"
    verdict = "SIGNAL" if panel["signal"] else "noise"
    return (f"{panel['label']}: last {panel['last_move']:+.2f}% "
            f"({reading}) -> {verdict}")


def main(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    skip_tail = "--skip-tail" in args
    show = "--no-show" not in args
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    monitor = PortfolioMonitor(period="daily")
    ticker_of = dict(monitor.holdings)  # label -> yfinance ticker
    repository = ReturnsRepository()

    print("=== daily orchestration ===")
    print("\n--- see_change daily portfolio (Taleb noise filter) ---")
    panels = monitor.prepare_panels()
    for panel in panels:
        print(format_panel_line(panel))
    if show:
        monitor.visualize(panels)  # the 2x2 signal panel pops out

    signals = signal_panels(panels)
    if not signals:
        print("\nno SIGNAL today: every holding stayed inside its usual band "
              "(noise)")
    for panel in signals:
        ticker = ticker_of[panel["label"]]
        print(f"\n--- {ticker} SIGNAL today -> high/low levels ---")
        frame = repository.try_fetch_open_high_low_close(ticker)
        print(_report_from_open_high_low_close(frame, ticker, date.today()))
        if show and frame is not None and not frame.empty:
            plot_high_low_levels(frame, ticker, show=True)

    if skip_tail:
        logger.info("--skip-tail: skipping the QQQ tail-to-body chart")
        return 0

    print("\n--- NDX100 QQQ tail-to-body ratio (every day) ---")
    try:
        save_path, today_ratio, q25 = tail_plot.plot_tail_cheapness(show=show)
    except Exception as exc:  # noqa: BLE001 — a broken chart must not kill the day
        print(f"QQQ tail chart skipped: {exc}")
        return 0
    # Reuse the tail_plot verdict wording — the single source of the decision.
    verdict = tail_plot._verdict(today_ratio, q25)
    decision_level = int(tail_plot.DECISION_LEVEL * 100)
    print(f"QQQ: {decision_level}% OTM put / ATM straddle today = "
          f"{today_ratio:.4f} vs 25th pct buy line {q25:.4f} -> {verdict}")
    print(f"chart: {save_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
