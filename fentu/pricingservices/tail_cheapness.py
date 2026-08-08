"""Pure logic of the wing-to-body tail cheapness gauge (story/tail_cheapness_gauge.md).

Self-checking asserts at module top level: xingjian executes this file on every
save, so these are the honest red/green gate for T2.
"""


def percentile(series, q):
    """q-th percentile of series, linear interpolation (numpy/Excel INC style).

    Method pinned here and in tests: q=10 of [0.30, 0.29, 0.25, 0.24, 0.26]
    is 0.244 under linear interpolation, 0.24 under nearest-rank — a silent
    method swap cannot pass.
    """
    if not series:
        raise ValueError("percentile of an empty series is undefined")
    if not 0 <= q <= 100:
        raise ValueError(f"q must be in [0, 100], got {q}")
    s = sorted(series)
    pos = (len(s) - 1) * (q / 100)
    lo = int(pos)
    if lo == len(s) - 1:
        return s[lo]
    frac = pos - lo
    return s[lo] + frac * (s[lo + 1] - s[lo])


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
