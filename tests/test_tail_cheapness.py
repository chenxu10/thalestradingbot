import pytest

from fentu.pricingservices.tail_cheapness import percentile

SERIES = [0.30, 0.29, 0.25, 0.24, 0.26]


def test_percentile_25th_of_hand_built_series():
    assert percentile(SERIES, 25) == 0.25


def test_percentile_75th_of_hand_built_series():
    assert percentile(SERIES, 75) == 0.29


def test_percentile_pins_linear_interpolation_method():
    assert round(percentile(SERIES, 10), 4) == 0.244


def test_percentile_boundaries():
    assert percentile(SERIES, 0) == 0.24
    assert percentile(SERIES, 100) == 0.30


def test_percentile_single_element():
    assert percentile([0.0639], 50) == 0.0639


def test_percentile_empty_raises():
    with pytest.raises(ValueError):
        percentile([], 25)
