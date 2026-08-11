import pandas as pd

from fentu.pricingservices.tail_plot import (
    PriceHistory,
    _verdict,
    percentile,
    reconstruct_ratios,
    split_terminal,
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
    return {"3m": reconstruct_ratios(fake_history(), SKEW, 0.25, 1.3)}


def test_split_terminal_excludes_last_close_from_series():
    series, model_today = split_terminal(_hist())
    assert series[0.25][-1][0] < model_today[0.25][0]
    assert (model_today[0.25][0] - series[0.25][-1][0]).days == 1
    assert model_today[0.25] not in series[0.25]


def test_verdict_responds_to_real_quote_while_history_fixed():
    series, model_today = split_terminal(_hist())
    q25 = percentile([r for d, r in series[0.25]], 25)
    assert _verdict(q25 * 0.5, q25) == "CHEAP - buy the tail"
    assert _verdict(q25 * 2.0, q25) == "NOT cheap - wait, let the strangles fund"
