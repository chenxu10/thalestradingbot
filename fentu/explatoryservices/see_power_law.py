"""
This script provides tools to plot on a sample of data set on liner, log-log and
log-binning scales.

It helps you to see whether underlying data set has a power law potential.

It plots on generated simulated data using power law when alpha=2.5.

It also plots on empircial data of daily SPY return to check slope vaguely.

TODO:
It's worth to separate seeing SPY data with left tail and right tail analyses

Author: Xu.Shen<xs286@cornell.edu>
"""

import numpy as np
from scipy.stats import uniform, norm
import matplotlib.pyplot as plt

def uniform_sample_r(loc, scale, size):
    """生成均匀分布的随机数"""
    return uniform.rvs(loc=loc, scale=scale, size=size)

def generate_gaussian_samples(mu=0, sigma=1, size=1000000):
    samples = norm.rvs(loc=mu, scale=sigma, size=size)
    return np.abs(samples)

def generate_transformative_power_law_samples(alpha, x_min=1.0, size=1000):
    """使用变换方法生成幂律分布样本
    
    参数:
    alpha: 幂律指数 (应该 > 1)
    x_min: 分布的下限
    size: 样本数量
    
    返回:
    幂律分布的样本数组
    """
    uniform_r = uniform_sample_r(0, 1, size)
    
    if alpha <= 1:
        raise ValueError("alpha 必须大于 1，否则分布无法归一化")
    
    power_law_samples = x_min * np.power(1.0 - uniform_r, -1.0/(alpha - 1))
    
    return power_law_samples

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

def plot_linear_histogram(samples, ax=None):
    """
    Plot linear scale histogram of power-law samples

    参数:
    samples: Power-law distributed samples
    ax: Matplotlib axes object. If None, uses current axes

    返回:
    ax: The axes object used for plotting
    """

    if ax is None:
        ax = plt.gca()

    ax.hist(samples, bins=30, density=True, alpha=0.7, color='blue')
    ax.set_xlim(left=None, right=max(samples)+0.01)
    ax.set_xlabel('x')
    ax.set_ylabel('Probability density')
    ax.set_title('Power-law distribution (linear scale)')
    ax.grid(True, alpha=0.3)

    return ax

def plot_loglog_histogram(samples, x_min, ax=None):
    """
    Plot log-log scale histogram of power-law samples

    Uses linear bins with standard numpy density calculation.
    This can produce noisier plots in the tail region (similar to Newman plot b).

    参数:
    samples: Power-law distributed samples
    x_min: Minimum value of the distribution
    ax: Matplotlib axes object. If None, uses current axes

    返回:
    ax: The axes object used for plotting
    hist: Histogram values
    bin_centers: Bin center values
    """

    if ax is None:
        ax = plt.gca()

    # Create linear bins
    bins = np.linspace(x_min, np.max(samples), 100)

    # Use unified histogram computation pipeline
    hist, bin_centers, _ = compute_histogram_with_bins(samples, bins, method='numpy_density')

    # Plot only positive histogram values
    ax.loglog(bin_centers[hist > 0], hist[hist > 0], 'o-', alpha=0.7)
    ax.set_xlabel('x (log scale)')
    ax.set_ylabel('Probability density (log scale)')
    ax.set_title('Power-law distribution (log-log scale)')
    ax.grid(True, alpha=0.3, which='both')

    return ax, hist, bin_centers

def plot_loglog_histogram_log_binning(samples, x_min, ax=None):
    """
    Plot log-log scale histogram with proper log binning method

    This method produces cleaner plots like Newman's plot (c) by:
    - Using log-spaced bins
    - Using manual density normalization by bin width
    - Using geometric mean for bin centers (correct for log scale)
    - Reducing noise in the tail region

    参数:
    samples: Power-law distributed samples
    x_min: Minimum value of the distribution
    ax: Matplotlib axes object. If None, uses current axes

    返回:
    ax: The axes object used for plotting
    density: Density values
    bin_centers: Bin center values
    """

    if ax is None:
        ax = plt.gca()

    # Create log-spaced bins
    bins = create_log_space_bins(x_min, samples)

    # Use unified histogram computation pipeline with manual density method
    density, bin_centers, _ = compute_histogram_with_bins(samples, bins, method='manual_density')

    # Plot only bins with positive density
    mask = density > 0
    ax.loglog(bin_centers[mask], density[mask], 'o-', alpha=0.7)
    ax.set_xlabel('x (log scale)')
    ax.set_ylabel('Probability density (log scale)')
    ax.set_title('Power-law distribution with log binning')
    ax.grid(True, alpha=0.3, which='both')

    return ax, density, bin_centers


def plot_loglog_histogram_spy(samples, x_min, ax=None):
    """
    Plot log-log scale histogram of power-law samples

    Uses linear bins with standard numpy density calculation.
    This can produce noisier plots in the tail region (similar to Newman plot b).

    参数:
    samples: Power-law distributed samples
    x_min: Minimum value of the distribution
    ax: Matplotlib axes object. If None, uses current axes

    返回:
    ax: The axes object used for plotting
    hist: Histogram values
    bin_centers: Bin center values
    """

    if ax is None:
        ax = plt.gca()

    # Create linear bins
    bins = np.linspace(x_min, np.max(samples), 100)

    # Use unified histogram computation pipeline
    hist, bin_centers, _ = compute_histogram_with_bins(samples, bins, method='numpy_density')

    # Plot only positive histogram values
    ax.loglog(bin_centers[hist > 0], hist[hist > 0], 'o-', alpha=0.7)
    ax.set_xlabel('x (log scale)')
    ax.set_ylabel('Probability density (log scale)')
    ax.set_title('Power-law distribution (log-log scale) on Historical SPY Daily Returns')
    ax.grid(True, alpha=0.3, which='both')

    return ax, hist, bin_centers

def calculate_sample_statistics(samples, x_min):
    """
    Calculate statistical metrics for power-law samples

    参数:
    samples: Power-law distributed samples
    x_min: Expected minimum value of the distribution

    返回:
    dict: Dictionary containing statistical metrics
    """
    return {
        'count': len(samples),
        'min': np.min(samples),
        'max': np.max(samples),
        'median': np.median(samples),
        'mean': np.mean(samples),
        'x_min': x_min
    }

def print_sample_statistics(stats):
    """
    Print formatted statistical metrics for power-law samples

    参数:
    stats: Dictionary containing statistical metrics from calculate_sample_statistics
    """
    print(f"生成的样本统计:")
    print(f"  样本数: {stats['count']}")
    print(f"  最小值: {stats['min']:.4f} (应该接近 x_min={stats['x_min']})")
    print(f"  最大值: {stats['max']:.4f}")
    print(f"  中位数: {stats['median']:.4f}")
    print(f"  均值: {stats['mean']:.4f}")