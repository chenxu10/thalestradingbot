import numpy as np
import pytest

from fentu.explatoryservices import see_power_law as spl


@pytest.fixture
def synthetic_powerlaw_histogram():
    """Deterministic histogram fed to fit_power_law_slope in every test."""
    np.random.seed(0)
    samples = (np.random.pareto(3, 20000) + 1) * 0.1
    bins = spl.create_log_space_bins(np.min(samples), samples)
    density, bin_centers, _ = spl.compute_histogram_with_bins(
        samples, bins, method='manual_density'
    )
    return bin_centers, density


def test_fit_returns_three_tuple(synthetic_powerlaw_histogram):
    bin_centers, density = synthetic_powerlaw_histogram
    result = spl.fit_power_law_slope(bin_centers, density, tail_percent=0.2)
    assert len(result) == 3
    slope, intercept, tail_mask = result
    assert isinstance(slope, float)
    assert isinstance(intercept, float)
    assert tail_mask.dtype == bool


def test_fit_baseline_values_unchanged(synthetic_powerlaw_histogram):
    """Pin the exact numeric output captured before the refactor.

    alpha is derived as alpha = -slope at the call site.
    Baseline: slope=-1.057629 (=> alpha=1.057629), intercept=-2.783810.
    """
    bin_centers, density = synthetic_powerlaw_histogram
    slope, intercept, tail_mask = spl.fit_power_law_slope(
        bin_centers, density, tail_percent=0.2
    )
    assert slope == pytest.approx(-1.057629)
    assert -slope == pytest.approx(1.057629)  # alpha, derived
    assert intercept == pytest.approx(-2.783810)
    assert len(tail_mask) == 79
    assert tail_mask.sum() == 15


def test_alpha_derived_from_slope(synthetic_powerlaw_histogram):
    """alpha is not returned; callers derive it as alpha = -slope."""
    bin_centers, density = synthetic_powerlaw_histogram
    slope, _, _ = spl.fit_power_law_slope(bin_centers, density, tail_percent=0.2)
    alpha = -slope
    assert alpha > 0


def test_tail_mask_aligned_to_positive_density_bins(synthetic_powerlaw_histogram):
    bin_centers, density = synthetic_powerlaw_histogram
    _, _, tail_mask = spl.fit_power_law_slope(bin_centers, density, tail_percent=0.2)
    n_valid = int((density > 0).sum())
    assert len(tail_mask) == n_valid


def test_layer1_positive_density_mask_is_boolean(synthetic_powerlaw_histogram):
    _, density = synthetic_powerlaw_histogram
    mask = spl._positive_density_mask(density)
    assert mask.dtype == bool
    assert mask.sum() == int((density > 0).sum())


def test_layer1_tail_start_index_respects_floor():
    # tail_percent floor is 2 points
    assert spl._tail_start_index(5, 0.2) == 5 - max(int(5 * 0.2), 2)
    assert spl._tail_start_index(0, 0.2) == -2  # max(int(0), 2) = 2


def test_layer1_tail_mask_shape():
    mask = spl._tail_mask(10, 7)
    assert len(mask) == 10
    assert mask.sum() == 3
    assert not mask[:7].any()
    assert mask[7:].all()


def test_layer2_fit_loglog_line_returns_two():
    x = np.array([1.0, 10.0, 100.0, 1000.0])
    y = x ** (-2.0)  # perfect power law, slope = -2
    slope, intercept = spl._fit_loglog_line(x, y)
    assert slope == pytest.approx(-2.0)
    assert len((slope, intercept)) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
