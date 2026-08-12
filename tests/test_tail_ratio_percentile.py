import numpy as np

ANNUAL_RATIOS_2016_2026 = [0.05 + 0.01 * i for i in range(10)]


def test_percentile_25th_known_series():
    assert round(np.percentile(ANNUAL_RATIOS_2016_2026, 25), 4) == 0.0725


def test_percentile_75th_known_series():
    assert round(np.percentile(ANNUAL_RATIOS_2016_2026, 75), 4) == 0.1175