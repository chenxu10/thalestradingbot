"""Tail-cheapness plot: is today's far-OTM wing cheap vs the ATM body?

Run it:
    uv run python -m fentu.pricingservices.tail_plot

Output: figures/tail_cheapness_<date>.png (named after today's date)

Reconstruction assumptions (stated on the chart):
- 10y history: wing/body ratio reconstructed from REAL VIX (the body's own
  price) and REAL QQQ closes via BSM, with TODAY's real skew offsets held
  constant and a flat term structure, anchored to today's real ratio.
- Today's dots: REAL mid-market quotes from the yfinance chain.
"""

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

MATURITIES = {"3m": 63}  # trading days to expiry
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

    today = datetime.now().date()
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
                "straddle": straddle_mid(chain, atm_k),
                "wing": wing,
                "skew_pts": {pct: (put_iv(chain, otm_strike(spot, pct)) - atm_iv) * 100.0 for pct in WING_LEVELS},
            }
    return quotes


def historical_ratios(years=10):
    """Wing/body ratio history reconstructed from real VIX + QQQ closes."""
    end = datetime.now().date()
    start = end - timedelta(days=int(years * 365.25))
    vix = yf.download("^VIX", start=start, end=end, progress=False)["Close"]
    qqq = yf.download("QQQ", start=start, end=end, progress=False)["Close"]
    dates = vix.index.intersection(qqq.index)
    if len(dates) == 0:
        raise RuntimeError("no overlapping VIX/QQQ history downloaded — check network and retry")
    vix = vix.loc[dates]
    qqq = qqq.loc[dates]

    quotes = fetch_today_quotes()
    hist = {}
    for label, days in MATURITIES.items():
        skew = quotes[label]["skew_pts"]
        t_years = days / 252.0
        ratios = []
        for idx in dates:
            s = float(qqq.loc[idx].iloc[0])
            v = float(vix.loc[idx].iloc[0]) / 100.0
            if not (math.isfinite(s) and math.isfinite(v)) or v <= 0:
                continue
            body = bs_straddle(s, v, t_years)
            for pct in WING_LEVELS:
                w = bs_put(s, s * (1 - pct), v + skew[pct] / 100.0, t_years)
                ratios.append((idx.date(), pct, w / body if body > 0 else float("nan")))
        hist[label] = ratios
    return hist, quotes


def plot_tail_cheapness(save_path=None):
    hist, quotes = historical_ratios()
    fig, ax = plt.subplots(figsize=(13, 7))
    today = date.today()
    if save_path is None:
        save_path = f"figures/tail_cheapness_{today.strftime('%b').lower()}{today.day}_{today.year}.png"

    anchor = {}
    for label in hist:
        for pct in WING_LEVELS:
            recon_today = [r for d, p_, r in hist[label] if p_ == pct and math.isfinite(r)][-1]
            real_today = quotes[label]["wing"][pct] / quotes[label]["straddle"]
            anchor[(label, pct)] = real_today / recon_today

    for pct in WING_LEVELS:
        series = [(d, r * anchor[("3m", pct)]) for d, p_, r in hist["3m"] if p_ == pct]
        dates = [d for d, r in series]
        vals = [r for d, r in series if math.isfinite(r)]
        color = LEVEL_COLORS[pct]
        lw = 1.6 if pct == DECISION_LEVEL else 0.8
        ax.plot(dates, [r for d, r in series], lw=lw, color=color, alpha=0.8, label=f"{int(pct*100)}% OTM wing / body (reconstructed)")

        if pct == DECISION_LEVEL:
            q25 = percentile(vals, 25)
            q75 = percentile(vals, 75)
            ax.axhline(q25, color="#d62728", ls="--", lw=1.5, label=f"red line: 25th pct of 10y ratio, {int(pct*100)}% OTM wing -> buy line ({q25:.4f})")
            ax.axhline(q75, color="#2ca02c", ls="--", lw=1.5, label=f"green line: 75th pct of 10y ratio, {int(pct*100)}% OTM wing -> expensive line ({q75:.4f})")
            ax.fill_between(dates, 0, q25, color="#d62728", alpha=0.12)
            ax.fill_between(dates, q25, q75, color="#cccccc", alpha=0.15)
            ax.text(dates[len(dates) // 5], q25 * 0.6, "BUY ZONE\n(tail cheaper than 75%\nof the last 10 years)", color="#d62728", fontsize=8, va="center")
            ax.text(dates[len(dates) // 5], (q25 + q75) / 2, "normal range", color="#666666", fontsize=8, va="center")
            ax.text(dates[len(dates) // 5], q75 * 1.5, "expensive zone\n(tail pricier than 75%\nof the last 10 years)", color="#2ca02c", fontsize=8, va="center")

    real_ratio = quotes["3m"]["wing"][DECISION_LEVEL] / quotes["3m"]["straddle"]
    ax.scatter(
        [date.today()],
        [real_ratio],
        marker="o",
        s=140,
        color=LEVEL_COLORS[DECISION_LEVEL],
        edgecolors="black",
        zorder=5,
        label=f"TODAY real (3m, {int(DECISION_LEVEL*100)}% OTM): {real_ratio:.4f}",
    )

    today_ratio = quotes["3m"]["wing"][DECISION_LEVEL] / quotes["3m"]["straddle"]
    vals_decision = [r * anchor[("3m", DECISION_LEVEL)] for d, p_, r in hist["3m"] if p_ == DECISION_LEVEL and math.isfinite(r)]
    q25 = percentile(vals_decision, 25)
    verdict = "CHEAP - buy the tail" if today_ratio < q25 else "NOT cheap - wait, let the strangles fund"
    ax.set_title(
        f"QQQ tail cheapness - {today.strftime('%b')} {today.day} {today.year} (spot ${quotes['3m']['spot']:.2f})\n"
        f"{int(DECISION_LEVEL*100)}% OTM put / ATM straddle today = {today_ratio:.4f} vs 25th pct buy line {q25:.4f} -> {verdict}"
    )
    ax.set_ylabel("far-OTM put price / ATM straddle price (log scale)")
    ax.set_xlabel("10 years of history (reconstructed: real VIX + QQQ closes, BSM, anchored to today's real ratio)")
    ax.set_yscale("log")
    ax.set_yticks([0.01, 0.02, 0.05, 0.1, 0.2])
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    print(f"saved {save_path}")
    return save_path, today_ratio, q25


if __name__ == "__main__":
    path, today_ratio, q25 = plot_tail_cheapness()
    plt.show()
