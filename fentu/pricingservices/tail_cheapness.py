"""Pure logic of the wing-to-body tail cheapness gauge (story/tail_cheapness_gauge.md).

Self-checking asserts at module top level: xingjian executes this file on every
save, so these are the honest red/green gate for T2.
"""

import numpy as np


def percentile(series, q):
    """q-th percentile of series, linear interpolation, delegated to numpy.

    Method pinned: np.percentile(..., method="linear") — a silent method swap
    cannot pass the q=10 -> 0.244 assertion.
    """
    if not series:
        raise ValueError("percentile of an empty series is undefined")
    return float(np.percentile(series, q, method="linear"))


# T2: hand-built series from the story's T4 example, known percentile values.
assert percentile([0.30, 0.29, 0.25, 0.24, 0.26], 25) == 0.25
assert percentile([0.30, 0.29, 0.25, 0.24, 0.26], 75) == 0.29
assert percentile([0.30, 0.29, 0.25, 0.24, 0.26], 50) == 0.26

# Method pin: linear interpolation, not nearest-rank (nearest-rank would give 0.24).
assert round(percentile([0.30, 0.29, 0.25, 0.24, 0.26], 10), 4) == 0.244

# Boundaries and degenerate inputs:
assert percentile([0.30, 0.29, 0.25, 0.24, 0.26], 0) == 0.24
assert percentile([0.30, 0.29, 0.25, 0.24, 0.26], 100) == 0.30
assert percentile([0.0639], 50) == 0.0639

# Empty input must raise — no silent invented answer.
try:
    percentile([], 25)
except ValueError:
    pass
else:
    raise AssertionError("percentile of an empty series must raise ValueError")
