import math

import numpy as np
import pandas as pd
import pytest

from fentu.pricingservices.tail_plot import (
    PriceHistory,
    _validate_today_quotes,
    _verdict,
    download_price_history,
    historical_ratios,
    bsm_model_today_ratio,
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

def _25th_percentile_wing_ratio(series_by_wing, pct):
    return np.percentile([ratio for day, ratio in series_by_wing[pct]], 25)

def test_verdict_responds_to_real_quote_while_history_fixed():
    series_by_wing = wing_series(_hist())
    q25 = _25th_percentile_wing_ratio(series_by_wing, 0.25)

    assert _verdict(q25 * 0.5, q25) == "CHEAP - buy the tail"
    assert _verdict(q25 * 2, q25) == "NOT cheap - wait, let the strangles fund"


def test_bsm_model_today_ratio_tracks_today_atm_iv():
    quote = {"spot": 500, "atm_iv": 0.2, "skew_pts": SKEW, "dte": 90}
    assert bsm_model_today_ratio(dict(quote, atm_iv=0.4))[0.25] > bsm_model_today_ratio(quote)[0.25]

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

def test_buy_line_ignores_today_atm_iv(monkeypatch):
    monkeypatch.setattr(
        "fentu.pricingservices.tail_plot.yf.download",
        lambda symbol, start=None, end=None, progress=False, auto_adjust=False: _fake_close_prices(),
    )
    cheap_vol = {"3m": {"atm_iv": 0.18, "skew_pts": SKEW, "dte": 90}}
    expensive_vol = {"3m": {"atm_iv": 0.36, "skew_pts": SKEW, "dte": 90}}
    cheap_series = wing_series(historical_ratios(cheap_vol, years=1))
    expensive_series = wing_series(historical_ratios(expensive_vol, years=1))
    q25_cheap = _25th_percentile_wing_ratio(cheap_series, 0.25)
    q25_expensive = _25th_percentile_wing_ratio(expensive_series, 0.25)
    assert q25_cheap == q25_expensive


def _quote(straddle=10.0, wing=2.0, atm_iv=0.20):
    return {"3m": {
        "straddle": straddle,
        "wing": {0.20: wing, 0.25: wing, 0.30: wing},
        "atm_iv": atm_iv,
    }}


def test_validate_today_quotes_accepts_live_market_quotes():
    _validate_today_quotes(_quote())  # must not raise


def test_validate_today_quotes_rejects_closed_market_zeros():
    with pytest.raises(RuntimeError, match="straddle=0.00"):
        _validate_today_quotes(_quote(straddle=0.0))
    with pytest.raises(RuntimeError, match="25% wing=0.00"):
        _validate_today_quotes(_quote(wing=0.0))
    with pytest.raises(RuntimeError, match="atm_iv=0.0000"):
        _validate_today_quotes(_quote(atm_iv=0.0))


def test_validate_today_quotes_rejects_missing_tenor():
    with pytest.raises(RuntimeError, match="market closed"):
        _validate_today_quotes({})