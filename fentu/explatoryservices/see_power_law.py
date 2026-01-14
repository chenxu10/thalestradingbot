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


def fit_power_law_slope(bin_centers, density):
    """
    Fit a linear slope on log-log data to estimate power law exponent alpha.

    For power law p(x) ~ x^(-alpha), in log-log space:
    log(p) = -alpha * log(x) + const
    So alpha = -slope

    Parameters:
    bin_centers: Array of bin center values
    density: Array of density values

    Returns:
    tuple: (alpha, slope, intercept, r_squared)
        - alpha: Estimated power law exponent
        - slope: Slope of linear fit in log-log space
        - intercept: Intercept of linear fit
        - r_squared: R-squared value of the fit
    """
    mask = density > 0
    log_x = np.log10(bin_centers[mask])
    log_y = np.log10(density[mask])

    slope, intercept, r_value, _, _ = linregress(log_x, log_y)
    alpha = -slope
    r_squared = r_value ** 2

    return alpha, slope, intercept, r_squared


def plot_loglog_with_fit(samples, x_min, ax=None, title=None):
    """
    Plot log-log histogram with linear fit to estimate power law alpha.

    Parameters:
    samples: Power-law distributed samples
    x_min: Minimum value of the distribution
    ax: Matplotlib axes object. If None, uses current axes
    title: Optional custom title for the plot

    Returns:
    ax: The axes object used for plotting
    alpha: Estimated power law exponent
    r_squared: R-squared value of the fit
    """
    if ax is None:
        ax = plt.gca()

    bins = create_log_space_bins(x_min, samples)
    density, bin_centers, _ = compute_histogram_with_bins(
        samples, bins, method='manual_density'
    )

    mask = density > 0
    ax.loglog(bin_centers[mask], density[mask], 'o', alpha=0.7, label='Data')

    alpha, slope, intercept, r_squared = fit_power_law_slope(bin_centers, density)

    fit_x = bin_centers[mask]
    fit_y = 10 ** (slope * np.log10(fit_x) + intercept)
    ax.loglog(fit_x, fit_y, 'r-', linewidth=2, label=f'Fit (α={alpha:.2f})')

    ax.set_xlabel('x (log scale)')
    ax.set_ylabel('Probability density (log scale)')
    if title:
        ax.set_title(f'{title}: α={alpha:.2f}, R²={r_squared:.3f}')
    else:
        ax.set_title(f'Power-law fit: α={alpha:.2f}, R²={r_squared:.3f}')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, which='both')

    return ax, alpha, r_squared
