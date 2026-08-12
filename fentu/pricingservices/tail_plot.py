"""Tail-cheapness plot: is today's far-OTM wing cheap vs the ATM body?

Run it:
    uv run python -m fentu.pricingservices.tail_plot

Output: figures/tail_cheapness_<date>.png (named after today's date)

Reconstruction assumptions (stated on the chart):
- 10y history: wing/body ratio reconstructed from REAL VXN (Nasdaq-100 vol,
  ^VXN) and REAL QQQ closes via BSM, with TODAY's real skew offsets held
  constant and a flat term structure. The vol LEVEL is anchored to today's
  real ATM IV (the market's vol premium) — NOT to today's wing ratio, so
  today's real wing quote stays an independent, out-of-sample test point.
- The tenor is the REAL option's actual calendar DTE (~90 days), so the
  model prices the same maturity as the quotes it is compared against.
- Today's dots: REAL mid-market quotes from the yfinance chain, compared
  against the model-implied point at today's real ATM IV + skew offsets.

TOFIX:
10year to 1999
"""

import logging
import math
import os
from datetime import date, datetime, timedelta

import matplotlib
if not os.environ.get("DISPLAY"):
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf
from py_vollib.black_scholes import black_scholes

from fentu.pricingservices.option_quotes import (
    atm_strike,
    call_iv,
    days_to_expiry,
    fetch_spot,
    otm_put_mid,
    otm_strike,
    pick_expiry,
    put_iv,
    straddle_mid,
)
from fentu.pricingservices.tail_ratio import percentile

logger = logging.getLogger(__name__)

MATURITIES = {"3m": 90}  # calendar days to expiry (pick_expiry matches calendar DTE); ~3 months ~ 63 trading days
WING_LEVELS = [0.20, 0.25, 0.30]  # OTM fractions
DECISION_LEVEL = 0.25  # the wing this plot decides on
LEVEL_COLORS = {0.20: "#1f77b4", 0.25: "#ff7f0e", 0.30: "#9467bd"}


def bs_call(spot, strike, vol, t_years, rate=0.0):
    if vol <= 0 or t_years <= 0:
        return max(spot - strike, 0.0)
    return black_scholes("c", spot, strike, t_years, rate, vol)


def bs_put(spot, strike, vol, t_years, rate=0.0):
    if vol <= 0 or t_years <= 0:
        return max(strike - spot, 0.0)
    return black_scholes("p", spot, strike, t_years, rate, vol)


def bs_straddle(spot, vol, t_years, rate=0.0):
    return bs_call(spot, spot, vol, t_years, rate) + bs_put(spot, spot, vol, t_years, rate)


def fetch_today_quotes():
    """Real mid-market quotes for today: spot, ATM straddle, OTM wings."""
    ticker = yf.Ticker("QQQ")
    spot = fetch_spot("QQQ")

    quotes = {}
    for label, days in MATURITIES.items():
        expiry = pick_expiry(ticker, days)
        if expiry is not None:
            chain = ticker.option_chain(expiry)
            atm_k = atm_strike(chain, spot)
            wing = {pct: otm_put_mid(chain, otm_strike(spot, pct)) for pct in WING_LEVELS}
            atm_iv = call_iv(chain, atm_k)
            quotes[label] = {
                "expiry": expiry,
                "dte": days_to_expiry(expiry),
                "spot": spot,
                "atm_iv": atm_iv,
                "straddle": straddle_mid(chain, atm_k),
                "wing": wing,
                "skew_pts": {pct: (put_iv(chain, otm_strike(spot, pct)) - atm_iv) * 100.0 for pct in WING_LEVELS},
            }
    return quotes


def _close(series_or_df, day):
    """Scalar close on a date from a yfinance Series or DataFrame (multi-col feeds)."""
    value = series_or_df.loc[day]
    return float(value.iloc[0]) if hasattr(value, "iloc") else float(value)


class PriceHistory:
    """Aligned VXN/QQQ closes over the window: the (dates, vxn, qqq) data clump."""

    def __init__(self, dates, vxn, qqq):
        self.dates = dates
        self.vxn = vxn
        self.qqq = qqq


def download_price_history(years=10):
    """Phase A: download and align VXN/QQQ closes over the window."""
    end = datetime.now().date()
    start = end - timedelta(days=int(years * 365.25))
    vxn = yf.download("^VXN", start=start, end=end, progress=False, auto_adjust=False)["Close"]
    qqq = yf.download("QQQ", start=start, end=end, progress=False, auto_adjust=False)["Close"]
    dates = vxn.index.intersection(qqq.index)
    if len(dates) == 0:
        raise RuntimeError("no overlapping VXN/QQQ history downloaded — check network and retry")
    return PriceHistory(dates, vxn.loc[dates], qqq.loc[dates])


def reconstruct_ratios(history, skew, t_years, vol_anchor):
    """Phase B: wing/body price ratios per (date, OTM level) from the BSM reconstruction.

    Each day's VXN is scaled by vol_anchor (today's real ATM IV / VXN), so the
    reconstructed vol LEVEL matches today's market while each day's relative
    vol move stays real. Skew offsets are today's real ones, held constant.
    """
    ratios = []
    for idx in history.dates:
        s = _close(history.qqq, idx)
        v = _close(history.vxn, idx) / 100.0 * vol_anchor
        if not (math.isfinite(s) and math.isfinite(v)) or v <= 0:
            continue
        body = bs_straddle(s, v, t_years)
        for pct in WING_LEVELS:
            w = bs_put(s, s * (1 - pct), v + skew[pct] / 100.0, t_years)
            ratios.append((idx.date(), pct, w / body if body > 0 else float("nan")))
    return ratios


def historical_ratios(quotes, years=10):
    """Wing/body ratio history reconstructed from real VXN + QQQ closes.

    The vol level is anchored to today's real ATM IV (vol premium) — NOT to
    today's wing ratio — so the terminal reconstructed point is model-implied
    and today's real wing quote remains an independent test point. The tenor
    is the REAL option's calendar DTE (quotes[label]["dte"]), so model and
    real quote price the same maturity — wing/body ratios are tenor-sensitive.
    """
    history = download_price_history(years)
    vxn_last = _close(history.vxn, history.dates[-1])
    logger.info(
        "history: %d aligned VXN/QQQ closes (%s .. %s), vxn_last=%.2f",
        len(history.dates),
        history.dates[0].date(),
        history.dates[-1].date(),
        vxn_last,
    )
    ratios = {}
    for label in MATURITIES:
        vol_anchor = quotes[label]["atm_iv"] / (vxn_last / 100.0)
        t_years = quotes[label]["dte"] / 365.0
        ratios[label] = reconstruct_ratios(history, quotes[label]["skew_pts"], t_years, vol_anchor)
        logger.info(
            "label %s: atm_iv=%.4f, vol_anchor=%.3f, dte=%d days -> t=%.4f y, reconstructed %d points",
            label,
            quotes[label]["atm_iv"],
            vol_anchor,
            quotes[label]["dte"],
            t_years,
            len(ratios[label]),
        )
    return ratios


def split_terminal(hist):
    """Phase 1 (data): split off the terminal model point from each wing series.

    Returns (series, model_today): per-wing (date, ratio) pairs minus the last
    close, and the last-close model ratio per wing. The verdict compares
    today's REAL ratio against the series only, keeping it out-of-sample.
    """
    series, model_today = {}, {}
    for pct in WING_LEVELS:
        pts = [(d, r) for d, p_, r in hist["3m"] if p_ == pct and math.isfinite(r)]
        series[pct] = pts[:-1]
        model_today[pct] = pts[-1] if pts else None
    return series, model_today


def plot_tail_cheapness(save_path=None):
    quotes = fetch_today_quotes()
    for label, q in quotes.items():
        wings = ", ".join(f"{int(p * 100)}%: {w:.3f}" for p, w in q["wing"].items())
        logger.info(
            "label %s: expiry=%s dte=%d spot=%.2f atm_iv=%.4f straddle=%.2f wing {%s}",
            label,
            q["expiry"],
            q["dte"],
            q["spot"],
            q["atm_iv"],
            q["straddle"],
            wings,
        )
    hist = historical_ratios(quotes)
    series, model_today = split_terminal(hist)
    logger.info("series points per wing: %s", {pct: len(series[pct]) for pct in WING_LEVELS})
    today = date.today()
    if save_path is None:
        save_path = f"figures/tail_cheapness_{today.strftime('%b').lower()}{today.day}_{today.year}.png"

    fig, ax = plt.subplots(figsize=(13, 7))
    today_ratio = quotes["3m"]["wing"][DECISION_LEVEL] / quotes["3m"]["straddle"]
    logger.info("today real ratio (%d%% OTM wing/straddle) = %.4f", int(DECISION_LEVEL * 100), today_ratio)

    _plot_wing_series(ax, series)
    q25 = _plot_decision_annotations(ax, series)
    _plot_today_marker(ax, today_ratio, model_today)
    verdict = _verdict(today_ratio, q25)
    logger.info(
        "decision wing: q25 buy line=%.4f, model-implied today=%s, verdict=%s (today %.4f vs q25 %.4f)",
        q25,
        model_today[DECISION_LEVEL],
        verdict,
        today_ratio,
        q25,
    )
    _decorate_axes(ax, quotes, today, today_ratio, q25, verdict)

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    logger.info("saved %s", save_path)
    print(f"saved {save_path}")
    return save_path, today_ratio, q25


def _plot_wing_series(ax, series):
    """Plot only the decision wing's reconstructed ratio series (the 20%/30% lines removed)."""
    sr = series[DECISION_LEVEL]
    color = LEVEL_COLORS[DECISION_LEVEL]
    ax.plot(
        [d for d, r in sr],
        [r for d, r in sr],
        lw=1.6,
        color=color,
        alpha=0.8,
        label=f"{int(DECISION_LEVEL*100)}% OTM wing / body (reconstructed)",
    )


def _plot_decision_annotations(ax, series):
    """Buy/expensive bands and zone labels for the decision wing. Returns the 25th-pct buy line."""
    sr = series[DECISION_LEVEL]
    if not sr:
        return float("nan")
    dates = [d for d, r in sr]
    vals = [r for d, r in sr if math.isfinite(r)]
    q25 = percentile(vals, 25)
    q50 = percentile(vals, 50)
    q75 = percentile(vals, 75)
    for text, y, color, dash in [
        (f"red line: 25th pct of 10y ratio, {int(DECISION_LEVEL*100)}% OTM wing -> buy line ({q25:.4f})", q25, "#d62728", "--"),
        (f"blue line: 50th pct (median) of 10y ratio, {int(DECISION_LEVEL*100)}% OTM wing ({q50:.4f})", q50, "#1f77b4", "-."),
        (f"green line: 75th pct of 10y ratio, {int(DECISION_LEVEL*100)}% OTM wing -> expensive line ({q75:.4f})", q75, "#2ca02c", "--"),
    ]:
        ax.axhline(y, color=color, ls=dash, lw=1.5, label=text)
    ax.fill_between(dates, 0, q25, color="#d62728", alpha=0.12)
    ax.fill_between(dates, q25, q75, color="#cccccc", alpha=0.15)
    x_text = dates[len(dates) // 5]
    ax.text(x_text, q25 * 0.6, "BUY ZONE\n(tail cheaper than 75%\nof the last 10 years)", color="#d62728", fontsize=8, va="center")
    ax.text(x_text, q50, "median", color="#1f77b4", fontsize=8, va="bottom")
    ax.text(x_text, q75 * 1.5, "expensive zone\n(tail pricier than 75%\nof the last 10 years)", color="#2ca02c", fontsize=8, va="center")
    return q25


def _plot_today_marker(ax, today_ratio, model_today):
    m_date, m_ratio = model_today[DECISION_LEVEL]
    ax.scatter(
        [m_date],
        [m_ratio],
        marker="D",
        s=90,
        facecolors="none",
        edgecolors="gray",
        zorder=4,
        label=f"model-implied today (BSM, real ATM IV + skew): {m_ratio:.4f}",
    )
    ax.scatter(
        [date.today()],
        [today_ratio],
        marker="o",
        s=140,
        color=LEVEL_COLORS[DECISION_LEVEL],
        edgecolors="black",
        zorder=5,
        label=f"TODAY real (3m, {int(DECISION_LEVEL*100)}% OTM): {today_ratio:.4f}",
    )


def _verdict(today_ratio, q25):
    return "CHEAP - buy the tail" if today_ratio < q25 else "NOT cheap - wait, let the strangles fund"


def _decorate_axes(ax, quotes, today, today_ratio, q25, verdict):
    ax.set_title(
        f"QQQ tail cheapness - {today.strftime('%b')} {today.day} {today.year} (spot ${quotes['3m']['spot']:.2f})\n"
        f"{int(DECISION_LEVEL*100)}% OTM put / ATM straddle today = {today_ratio:.4f} vs 25th pct buy line {q25:.4f} -> {verdict}"
    )
    ax.set_ylabel("far-OTM put price / ATM straddle price (log scale)")
    ax.set_xlabel("10 years of history (reconstructed: real VXN + QQQ closes, BSM, vol anchored to today's real ATM IV)")
    ax.set_yscale("log")
    ax.set_yticks([0.01, 0.02, 0.05, 0.1, 0.2])
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.grid(alpha=0.3)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    path, today_ratio, q25 = plot_tail_cheapness()
    plt.show()
