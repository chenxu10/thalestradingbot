"""
Test that kurtosis is no longer surfaced as a misleading clean point estimate.

Taleb-lens issue (README "Taleb-lens TODO"): kurtosis is a 4th-moment estimator
that loses scientific validity under fat tails -- one observation can dominate it
(one day approximately 80% of SP500 kurtosis over 56 yr). The fix in
`plotting_service.calculate_four_moments` is to also report the leave-one-out
(drop single most extreme obs) kurtosis, so the single-observation influence is
visible rather than hidden behind a clean `X.XXXX` digit.
"""
import numpy as np
import pandas as pd
import pytest

from fentu.explatoryservices.plotting_service import (
    calculate_four_moments,
    _kurtosis_dropping_outlier,
)


def _series_with_one_extreme():
    # Mild Gaussian-ish body plus one catastrophic outlier, mimicking the
    # "one day = 80% of SP500 kurtosis" phenomenon.
    rng = np.random.default_rng(0)
    body = rng.normal(0, 1, size=500)
    body[0] = 40
    return pd.Series(body)


class TestCalculateFourMoments:
    def test_returns_six_values_including_drop_worst_kurtosis(self):
        out = calculate_four_moments(_series_with_one_extreme())
        assert len(out) == 6
        mean, std, mad, skew, kurtosis, kurtosis_no_worst = out
        assert isinstance(kurtosis_no_worst, float)

    def test_drop_worst_kurtosis_is_far_smaller_than_full_kurtosis(self):
        # The whole point: a single obs inflates kurtosis; dropping it must
        # collapse the headline by an order of magnitude or more.
        _, _, _, _, kurtosis, kurtosis_no_worst = calculate_four_moments(
            _series_with_one_extreme()
        )
        assert kurtosis > 10 * kurtosis_no_worst

    def test_drop_worst_uses_most_extreme_observation(self):
        # The outlier (40.0) is the global max abs deviation and must be the
        # one dropped -- so the helper's result must equal a manual drop of that
        # exact obs, and must NOT equal dropping a benign body obs.
        x = _series_with_one_extreme()
        worst = (x - x.mean()).abs().idxmax()
        assert x.iloc[worst] == 40.0  # the crash day is the most extreme
        assert _kurtosis_dropping_outlier(x) == pytest.approx(
            x.drop(worst).kurtosis()
        )

    def test_too_short_series_returns_none_drop_worst(self):
        # < 5 pts cannot drop one and still estimate kurtosis.
        assert _kurtosis_dropping_outlier(pd.Series([1.0, 2.0, 3.0, 4.0])) is None

    def test_zero_dispersion_returns_none_drop_worst(self):
        assert _kurtosis_dropping_outlier(pd.Series([7.0] * 10)) is None