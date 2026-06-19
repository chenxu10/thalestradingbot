"""
Rendering for the IV term-structure curve.

Plots bucket rows (output of build_bucket_rows) onto a matplotlib Axes:
tenor labels on x, ATM IV on y, skipping buckets whose atm_iv is None.
Matches the ax/show conventions of fentu.explatoryservices.plotting_service.
"""

from __future__ import annotations

import matplotlib.pyplot as plt


def plot_term_structure(bucket_rows, ax=None, show=True, title=None):
    """Render bucket rows as a term-structure line on a matplotlib Axes.

    Args:
        bucket_rows: list of dicts from build_bucket_rows, each shaped
            {label, target_days, ..., atm_iv, ...}. Buckets with atm_iv None
            are skipped.
        ax: existing Axes to draw on; if None a new figure/Axes is created.
        show: if True, call plt.show() (mirrors plotting_service convention).
        title: axes title; defaults to "IV Term Structure".

    Returns: the Axes the curve was drawn on.
    """
    if ax is None:
        _, ax = plt.subplots()

    valid = [
        row for row in (bucket_rows or [])
        if isinstance(row, dict) and row.get("atm_iv") is not None
    ]

    if valid:
        x_positions = list(range(len(valid)))
        y_values = [row["atm_iv"] for row in valid]
        labels = [str(row.get("label") or "") for row in valid]

        ax.plot(x_positions, y_values, marker="o", linestyle="-")
        ax.set_xticks(x_positions)
        ax.set_xticklabels(labels)

    ax.set_ylabel("ATM IV")
    ax.set_xlabel("Tenor")
    ax.set_title(title if title is not None else "IV Term Structure")

    if show:
        plt.show()
    return ax
