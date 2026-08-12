import math

import pandas as pd

from fentu.pricingservices.tail_plot import (
    PriceHistory,
    _verdict,
    download_price_history,
    historical_ratios,
    percentile,
    reconstruct_ratios,
    wing_series,
)

SKEW = {0.20: 5.0, 0.25: 5.0, 0.30: 5.0}


def fake_history(n=120):
    idx = pd.date_range("2020-01-02", periods=n, freq="B")
    vix = pd.DataFrame({"Close": [20.0 + (i % 10) * 0.5 for i in range(n)]}, index=idx)
    qqq = pd.DataFrame({"Close": [300.0 + i for i in range(n)]}, index=idx)
    return PriceHistory(idx, vix, qqq)


def test_reconstruct_ratio_rises_with_vol_anchor():
    hist = fake_history()
    r_low = [r for d, p_, r in reconstruct_ratios(hist, SKEW, 0.25, 1.0) if p_ == 0.25]
    r_high = [r for d, p_, r in reconstruct_ratios(hist, SKEW, 0.25, 1.6) if p_ == 0.25]
    assert all(h > l for l, h in zip(r_low, r_high))


def _hist():
    return {"3m": reconstruct_ratios(fake_history(), SKEW, 0.25)}


def _fake_close_prices(n=100):
    idx = pd.date_range("2025-01-02", periods=n, freq="B")
    return pd.DataFrame({"Close": [22.0] * n}, index=idx)

def test_verdict_responds_to_real_quote_while_history_fixed():
    series = wing_series(_hist())
    q25 = percentile([r for d, r in series[0.25]], 25)

    assert _verdict(q25 * 0.5, q25) == "CHEAP - buy the tail"
    assert _verdict(q25 * 2, q25) == "NOT cheap - wait, let the strangles fund"

def test_download_price_history_uses_vxn_not_vix(monkeypatch):
    symbols_seen = []

    def fake_download(symbol, start=None, end=None, progress=False, auto_adjust=False):
        symbols_seen.append(symbol)
        return _fake_close_prices()

    monkeypatch.setattr("fentu.pricingservices.tail_plot.yf.download", fake_download)
    hist = download_price_history(years=1)
    assert "^VXN" in symbols_seen
    assert "^VIX" not in symbols_seen
    assert len(hist.vxn) > 0


def test_historical_ratios_flows_vxn_seam(monkeypatch):
    monkeypatch.setattr(
        "fentu.pricingservices.tail_plot.yf.download",
        lambda symbol, start=None, end=None, progress=False, auto_adjust=False: _fake_close_prices(),
    )
    quotes = {"3m": {"atm_iv": 0.24, "skew_pts": SKEW, "dte": 90}}
    ratios = historical_ratios(quotes, years=1)
    assert len(ratios["3m"]) == 300
    assert all(math.isfinite(r) for d, p_, r in ratios["3m"])
