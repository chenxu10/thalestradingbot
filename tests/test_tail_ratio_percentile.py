from fentu.pricingservices.tail_ratio import percentile


def test_percentile_25th_known_series():
    series = [0.05 + 0.01 * i for i in range(10)]  # 10 annual ratios, 2016-2026
    assert round(percentile(series, 25), 4) == 0.0725


def test_percentile_75th_known_series():
    series = [0.05 + 0.01 * i for i in range(10)]  # 10 annual ratios, 2016-2026
    assert round(percentile(series, 75), 4) == 0.1175
