"""
This script provides tools to plot on a sample of data set on log-log scale
with power law fitting.

It helps you to see whether underlying data set has a power law potential
by fitting a linear slope in log-log space to estimate alpha.

Author: Xu.Shen<xs286@cornell.edu>
"""

import numpy as np
from scipy.stats import linregress
import matplotlib.pyplot as plt


def create_log_space_bins(x_min, samples) -> np.ndarray:
    """
    Creates an array of numbers that are evenly distrbuted on log space
    """
    bins = np.logspace(np.log10(x_min), np.log10(np.max(samples)), 100)
    return bins


def compute_histogram_with_bins(samples, bins, method='numpy_density'):
    """
    Unified histogram computation pipeline with different density calculation methods

    This function centralizes histogram computation logic to eliminate duplication
    between different plotting methods.

    Parameters:
    samples: Array of samples to create histogram from
    bins: Array of bin edges
    method: Density calculation method
        - 'numpy_density': Use np.histogram with density=True (faster, standard)
        - 'manual_density': Manual normalization by bin width (more control, reduces noise)

    Returns:
    tuple: (values, bin_centers, bin_edges)
        - values: Density values for each bin
        - bin_centers: Center position of each bin
        - bin_edges: Original bin edges array
    """
    if method == 'numpy_density':
        # Standard numpy density calculation
        values, bin_edges = np.histogram(samples, bins=bins, density=True)
        # Use arithmetic mean for bin centers
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    elif method == 'manual_density':
        # Manual density normalization for better control
        counts, bin_edges = np.histogram(samples, bins=bins, density=False)

        # Calculate bin widths and normalize manually
        bin_widths = bin_edges[1:] - bin_edges[:-1]
        values = counts / (bin_widths * len(samples))

        # Use geometric mean for bin centers (correct for log-scale bins)
        bin_centers = np.sqrt(bin_edges[:-1] * bin_edges[1:])

    else:
        raise ValueError(f"Unknown method: {method}. Use 'numpy_density' or 'manual_density'")

    return values, bin_centers, bin_edges


def _positive_density_mask(density):
    """Boolean mask of bins with positive density (log-log needs log10(y) > -inf)."""
    return density > 0


def _tail_start_index(n_valid, tail_percent):
    """Index at which the extreme tail begins (rightmost tail_percent of points)."""
    n_tail = max(int(n_valid * tail_percent), 2)
    return n_valid - n_tail


def _fit_loglog_line(x, y):
    """Fit log10(y) = slope * log10(x) + intercept; return slope, intercept."""
    slope, intercept, _, _, _ = linregress(np.log10(x), np.log10(y))
    return slope, intercept


def _tail_mask(n_valid, tail_start_idx):
    """Boolean mask of length n_valid, True over the tail window."""
    mask = np.zeros(n_valid, dtype=bool)
    mask[tail_start_idx:] = True
    return mask


def fit_power_law_slope(bin_centers, density, tail_percent=0.2):
    """
    Fit a log-log line to the extreme tail; return slope and intercept.

    Uses extreme value theory approach: fits only the tail portion of the data
    where power law behavior is most prominent.

    For power law p(x) ~ x^(-alpha), in log-log space:
    log(p) = -alpha * log(x) + const
    So alpha = -slope (derived by the caller; not returned to avoid redundancy).

    Selection of which bins belong to the tail is a separate concern, exposed
    by tail_mask(). This function's single responsibility is the fit.

    Parameters:
    bin_centers: Array of bin center values
    density: Array of density values
    tail_percent: Fraction of extreme tail data to use for fitting (default 0.2 = 20%)
                  Uses the largest x values (rightmost portion of log-log plot)

    Returns:
    tuple: (slope, intercept)
        - slope: Slope of linear fit in log-log space (alpha = -slope)
        - intercept: Intercept of linear fit
    """
    valid_mask = _positive_density_mask(density)
    valid_centers = bin_centers[valid_mask]
    valid_density = density[valid_mask]

    tail_start_idx = _tail_start_index(len(valid_centers), tail_percent)

    return _fit_loglog_line(
        valid_centers[tail_start_idx:], valid_density[tail_start_idx:]
    )


def tail_mask(bin_centers, density, tail_percent=0.2):
    """
    Boolean mask over positive-density bins, True over the extreme tail window.

    Companion to fit_power_law_slope(): the same tail_percent selects the same
    bins, so callers can fit and color points consistently. This function's
    single responsibility is tail selection; it performs no fitting.

    Parameters:
    bin_centers: Array of bin center values
    density: Array of density values
    tail_percent: Fraction of extreme tail data to mark (default 0.2 = 20%)

    Returns:
    np.ndarray: Boolean mask aligned to the positive-density bins, True over the
                rightmost tail_percent of those bins.
    """
    valid_mask = _positive_density_mask(density)
    n_valid = int(valid_mask.sum())
    tail_start_idx = _tail_start_index(n_valid, tail_percent)
    return _tail_mask(n_valid, tail_start_idx)


def plot_loglog_with_fit(samples, x_min, ax=None, title=None, tail_percent=0.2):
    """
    Plot log-log histogram with linear fit to estimate power law alpha.

    Uses extreme value theory: fits only the tail portion of the distribution.

    Parameters:
    samples: Power-law distributed samples
    x_min: Minimum value of the distribution
    ax: Matplotlib axes object. If None, uses current axes
    title: Optional custom title for the plot
    tail_percent: Fraction of extreme tail to use for fitting (default 0.2 = 20%)

    Returns:
    ax: The axes object used for plotting
    alpha: Estimated power law exponent
    """
    if ax is None:
        ax = plt.gca()

    bins = create_log_space_bins(x_min, samples)
    density, bin_centers, _ = compute_histogram_with_bins(
        samples, bins, method='manual_density'
    )

    mask = density > 0
    valid_centers = bin_centers[mask]
    valid_density = density[mask]

    slope, intercept = fit_power_law_slope(bin_centers, density, tail_percent)
    alpha = -slope
    tmask = tail_mask(bin_centers, density, tail_percent)

    ax.loglog(
        valid_centers[~tmask], valid_density[~tmask],
        'o', alpha=0.4, color='gray', label='Data (not fitted)'
    )
    ax.loglog(
        valid_centers[tmask], valid_density[tmask],
        'o', alpha=0.7, color='blue', label=f'Tail ({int(tail_percent*100)}%)'
    )

    fit_x = valid_centers[tmask]
    fit_y = 10 ** (slope * np.log10(fit_x) + intercept)
    ax.loglog(fit_x, fit_y, 'r-', linewidth=2, label=f'Fit (α={alpha:.2f})')

    ax.set_xlabel('x (log scale)')
    ax.set_ylabel('Probability density (log scale)')
    if title:
        ax.set_title(f'{title}: α={alpha:.2f}')
    else:
        ax.set_title(f'Power-law fit: α={alpha:.2f}')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, which='both')

    return ax, alpha
