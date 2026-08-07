"""Tail-cheapness plot: is today's far-OTM wing cheap vs the ATM body?

Run it:
    uv run python -m fentu.pricingservices.tail_plot

Output: figures/tail_cheapness_aug7_2026.png

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

from fentu.pricingservices.tail_ratio import percentile

MATURITIES = {"3m": 63, "6m": 126}  # trading days to expiry
WING_LEVELS = [0.20, 0.25, 0.30]  # OTM fractions


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
    spot = float(ticker.history(period="1d")["Close"].iloc[-1])

    today = datetime.now().date()
    quotes = {}
    for label, days in MATURITIES.items():
        expiry = None
        for exp in ticker.options:
            exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if 0 < dte <= days * 1.7 and (expiry is None or abs(dte - days) < abs((datetime.strptime(expiry, "%Y-%m-%d").date() - today).days - days)):
                expiry = exp
        if expiry is None:
            continue
        chain = ticker.option_chain(expiry)
        atm_k = min(set(chain.calls["strike"]), key=lambda k: abs(k - float(spot)))
        straddle = 0.0
        for side in (chain.calls, chain.puts):
            row = side[side["strike"] == atm_k].iloc[0]
            straddle += (row["bid"] + row["ask"]) / 2.0
        wing = {}
        atm_iv = None
        for pct in WING_LEVELS:
            k = int(round(spot * (1 - pct) / 5.0) * 5)
            row = chain.puts[chain.puts["strike"] == k].iloc[0]
            wing[pct] = (row["bid"] + row["ask"]) / 2.0
            if pct == 0.20:
                atm_iv = float(chain.calls[chain.calls["strike"] == atm_k].iloc[0]["impliedVolatility"])
                wing_iv = float(row["impliedVolatility"])
        quotes[label] = {
            "expiry": expiry,
            "dte": (datetime.strptime(expiry, "%Y-%m-%d").date() - today).days,
            "spot": spot,
            "straddle": straddle,
            "wing": wing,
            "skew_pts": {pct: (float(chain.puts[chain.puts["strike"] == int(round(spot * (1 - pct) / 5.0) * 5)].iloc[0]["impliedVolatility"]) - atm_iv) * 100.0 for pct in WING_LEVELS},
        }
    return quotes


def historical_ratios(years=10):
    """Wing/body ratio history reconstructed from real VIX + QQQ closes."""
    end = datetime.now().date()
    start = end - timedelta(days=int(years * 365.25))
    vix = yf.download("^VIX", start=start, end=end, progress=False)["Close"]
    qqq = yf.download("QQQ", start=start, end=end, progress=False)["Close"]
    dates = vix.index.intersection(qqq.index)
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


def plot_tail_cheapness(save_path="figures/tail_cheapness_aug7_2026.png"):
    hist, quotes = historical_ratios()
    fig, ax = plt.subplots(figsize=(13, 7))

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
        color = "#1f77b4" if pct == 0.20 else "#9ecae1"
        ax.plot(dates, [r for d, r in series], lw=1.0, color=color, alpha=0.8, label=f"{int(pct*100)}% OTM wing / body (reconstructed)")

        if pct == 0.20:
            q25 = percentile(vals, 25)
            q75 = percentile(vals, 75)
            ax.axhline(q25, color="#d62728", ls="--", lw=1.5, label=f"25th pct buy line ({q25:.4f})")
            ax.axhline(q75, color="#2ca02c", ls="--", lw=1.5, label=f"75th pct sell line ({q75:.4f})")
            ax.fill_between(dates, 0, q25, color="#d62728", alpha=0.12)

    for label, style in (("3m", "o"), ("6m", "^")):
        q = quotes[label]
        for pct in WING_LEVELS:
            real_ratio = q["wing"][pct] / q["straddle"]
            vals = [r * anchor[("3m", pct)] for d, p_, r in hist["3m"] if p_ == pct and math.isfinite(r)]
            marker_color = "#d62728" if real_ratio < percentile(vals, 25) else "#2ca02c"
            ax.scatter(
                [date.today()],
                [real_ratio],
                marker=style,
                s=140,
                color=marker_color,
                edgecolors="black",
                zorder=5,
                label=f"TODAY real ({label}, {int(pct*100)}% OTM): {real_ratio:.4f}" if pct == 0.20 else None,
            )

    today_3m = quotes["3m"]["wing"][0.20] / quotes["3m"]["straddle"]
    vals_3m = [r * anchor[("3m", 0.20)] for d, p_, r in hist["3m"] if p_ == 0.20 and math.isfinite(r)]
    q25_3m = percentile(vals_3m, 25)
    verdict = "CHEAP - buy the tail" if today_3m < q25_3m else "NOT cheap - wait, let the strangles fund"
    ax.set_title(
        f"QQQ tail cheapness - Aug 7 2026 (spot ${quotes['3m']['spot']:.2f})\n"
        f"20% OTM put / ATM straddle today = {today_3m:.4f} vs 25th pct {q25_3m:.4f} -> {verdict}"
    )
    ax.set_ylabel("far-OTM put price / ATM straddle price")
    ax.set_xlabel("10 years of history (reconstructed: real VIX + QQQ closes, BSM, anchored to today's real ratio)")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_yscale("log")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    print(f"saved {save_path}")
    return save_path, today_3m, q25_3m


if __name__ == "__main__":
    path, today_ratio, q25 = plot_tail_cheapness()
    plt.show()
