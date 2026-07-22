"""High/low levels over decision windows — where the stop clusters sit.

Paul Tudor Jones on moving volume (Market Wizards interview,
teams/paultudorjones.pdf, verbatim):

    "Tullis taught me about moving volume. When you are trading size, you
    have to get out when the market lets you out, not when you want to get
    out. He taught me that if you want to move a large position, you don't
    wait until the market is in new high or low ground because very little
    volume may trade there if it is a turning point."

    "One thing I learned as a floor trader was that if, for example, the old
    high was at 56.80, there are probably going to be a lot of buy stops at
    56.85. ... I will always liquidate half my position below new highs or
    lows and the remaining half beyond that point."

    "By watching Eli, I learned that even though markets look their very best
    when they are setting new highs, that is often the best time to sell."

How this tool uses that wisdom: it prints the OLD HIGH / OLD LOW over two
decision windows — the trailing two calendar months (recent congestion) and
the regime since the 2026-02-28 US-Iran war start — because stops cluster
just beyond those prints (old high 56.80 -> buy stops at 56.85). You cannot
stage exits against stop clusters you cannot see. The signed % distance from
the last close to each level is the "room to run" before price enters new
high/low ground — the turning-point zone where, per Tullis, very little
volume may trade, so you get out when the market lets you out (half below
the level, half beyond) instead of waiting for the print. And the war-regime
window is the contrarian lens: a market looking its very best at new highs
is often the best time to sell.

Built for USO (oil, the war instrument), but `instrument` is any yfinance
ticker — the same levels logic applies to BNO, CL=F, GLD, SPY, ...

CLI
---
* ``python -m fentu.explatoryservices.high_low_levels [TICKER]`` — print the
  two-window high/low levels report (default USO), or ``<TICKER> unavailable``
  on a network hiccup.
"""

from __future__ import annotations

import sys
from datetime import date

import pandas as pd

from fentu.explatoryservices.volcalculator import ReturnsRepository

DEFAULT_INSTRUMENT = "USO"
WAR_START = date(2026, 2, 28)  # US-Iran war start
LOOKBACK_MONTHS = 2
STOP_BUFFER_PCT = 0.01  # illustrative stop-cluster width just beyond a level


def stop_zone(level, side):
    """(lower, upper) band where stops cluster just beyond `level`.

    PTJ's floor lesson: old high 56.80 -> buy stops at 56.85. Buy stops sit
    ABOVE an old high (shorts cover / breakout buyers trigger there); sell
    stops sit BELOW an old low. The 1% width shades the cluster zone for the
    chart; it is illustrative, not a precise estimate of stop density.
    """
    if side == "buy":
        return (level, level * (1.0 + STOP_BUFFER_PCT))
    if side == "sell":
        return (level * (1.0 - STOP_BUFFER_PCT), level)
    raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")


def window_high_low(ohlc, start, end):
    """High/low prints and their dates for rows with start <= index <= end."""
    window = ohlc[(ohlc.index >= pd.Timestamp(start)) & (ohlc.index <= pd.Timestamp(end))]
    if window.empty:
        return None
    high = float(window["High"].max())
    low = float(window["Low"].min())
    return {
        "high": high,
        "high_date": window["High"].idxmax().date(),
        "low": low,
        "low_date": window["Low"].idxmin().date(),
    }


def _windows(today):
    """(short_name, label, start) per decision window, both ending at `today`."""
    two_mo_back = (pd.Timestamp(today) - pd.DateOffset(months=LOOKBACK_MONTHS)).date()
    return [
        ("2mo", f"past {LOOKBACK_MONTHS}mo (since {two_mo_back})", two_mo_back),
        ("war", f"since {WAR_START} (war start)", WAR_START),
    ]


def levels_view(ohlc, today=None):
    """View-model for the chart: one entry per old high/low per window.

    Each entry: {label, kind, price, date, stop_side, stop_zone} where
    stop_side is "buy" above old highs and "sell" below old lows — where
    PTJ says the stops cluster.
    """
    today = today if today is not None else date.today()
    entries = []
    for short, _label, start in _windows(today):
        stats = window_high_low(ohlc, start, today)
        if stats is None:
            continue
        entries.append(_level_entry(short, "high", stats))
        entries.append(_level_entry(short, "low", stats))
    return entries


def _level_entry(short, kind, stats):
    stop_side = "buy" if kind == "high" else "sell"
    price = stats[kind]
    return {
        "label": f"{short} {kind}",
        "kind": kind,
        "price": price,
        "date": stats[f"{kind}_date"],
        "stop_side": stop_side,
        "stop_zone": stop_zone(price, stop_side),
    }


def _window_line(label, stats, last):
    if stats is None:
        return f"{label}: no data"
    high_pct = (stats["high"] / last - 1.0) * 100.0
    low_pct = (stats["low"] / last - 1.0) * 100.0
    return (
        f"{label}: high {stats['high']:.2f} ({stats['high_date']}, {high_pct:+.1f}% above)"
        f" | low {stats['low']:.2f} ({stats['low_date']}, {low_pct:+.1f}% below)"
    )


def levels_report(instrument=DEFAULT_INSTRUMENT, repository=None, today=None):
    """Multi-line high/low levels report for `instrument` (any yfinance ticker)."""
    repo = repository if repository is not None else ReturnsRepository()
    today = today if today is not None else date.today()
    ohlc = _safe_raw_ohlc(repo, instrument)
    if ohlc is None or ohlc.empty:
        return f"{instrument} unavailable"
    last = float(ohlc["Close"].iloc[-1])
    lines = [f"{instrument} @ {last:.2f}"]
    for _short, label, start in _windows(today):
        lines.append(_window_line(label, window_high_low(ohlc, start, today), last))
    return "\n".join(lines)


def _safe_raw_ohlc(repo, instrument):
    """Fetch OHLC, returning None on any exception (network hiccups stay green)."""
    try:
        return repo._raw_ohlc(instrument)
    except Exception:
        return None


_LEVEL_STYLE = {
    ("2mo", "high"): {"color": "darkred", "ls": "--"},
    ("war", "high"): {"color": "red", "ls": ":"},
    ("2mo", "low"): {"color": "darkgreen", "ls": "--"},
    ("war", "low"): {"color": "green", "ls": ":"},
}


def plot_high_low_levels(ohlc, instrument, today=None, ax=None, show=True):
    """Chart the regime: close since war start, old highs/lows, stop clusters.

    Each level is a signal line (2mo dashed, war dotted; highs red, lows
    green) with a marker at its print date; the shaded band JUST BEYOND it is
    where PTJ says the stops cluster — "buy stops" above old highs, "sell
    stops" below old lows. Pure of fetching: pass a pre-built OHLC frame.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(11, 6))
    today = today if today is not None else date.today()
    close = ohlc["Close"]
    regime = close[close.index >= pd.Timestamp(WAR_START)]
    if regime.empty:
        regime = close

    ax.plot(regime.index, regime.values, color="black", lw=1.2, label="close")
    for entry in levels_view(ohlc, today=today):
        short = entry["label"].split(" ")[0]
        style = _LEVEL_STYLE[(short, entry["kind"])]
        _draw_level(ax, entry, style, regime.index[-1])

    ax.set_title(f"{instrument} — old highs/lows & stop clusters (PTJ moving volume)")
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.3)
    if show:
        plt.show()
    return ax


def _draw_level(ax, entry, style, right_edge):
    """One signal line + its print-date marker + the stop-cluster band."""
    color, price = style["color"], entry["price"]
    ax.axhline(price, color=color, ls=style["ls"], lw=1.1,
               label=f"{entry['label']} {price:.2f}")
    ax.plot([pd.Timestamp(entry["date"])], [price], marker="o", color=color, ms=6)
    lo, hi = entry["stop_zone"]
    ax.axhspan(lo, hi, color=color, alpha=0.12)
    ax.text(right_edge, (lo + hi) / 2.0, f"{entry['stop_side']} stops",
            color=color, fontsize=8, ha="right", va="center")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    instrument = argv[0] if argv else DEFAULT_INSTRUMENT
    print(levels_report(instrument))


if __name__ == "__main__":
    main()
