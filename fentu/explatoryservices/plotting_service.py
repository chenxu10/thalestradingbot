import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import probplot
from scipy import stats

def calculate_four_moments(x):
    """Calculate the four moments of the data"""
    mean = x.mean()
    std = x.std()
    # Calculate MAD manually since .mad() is deprecated
    mad = (x - x.mean()).abs().mean()
    skew = x.skew()
    kurtosis = x.kurtosis()
    return mean, std, mad, skew, kurtosis

def qq_plot(x, ax=None, show=True):
    if ax is None:
        fig, ax = plt.subplots()
    probplot(x, plot=ax)
    mean, std, mad, skew, kurtosis = calculate_four_moments(x)
    ax.text(0.05, 0.7,
            f'Mean: {mean:.4f}\n'
            f'SD: {std:.4f}\n'
            f'MAD:{mad:.4f}\n'
            f'Skew: {skew:.4f}\n'
            f'Kurtosis: {kurtosis:.4f}',
            transform=ax.transAxes, fontsize=12)
    if show:
        plt.show()
    return ax

def calculate_within_onestrd_prop(data):
    close = data
    mean = close.mean()
    std = close.std()
    print("mean close price change is {}".format(mean))
    print("1 standard deviation close close price change is {}".format(std))


def fit_normal_distribution(data):
    """Fit normal distribution and return parameters and PDF."""
    mu, sigma = stats.norm.fit(data)
    x = np.linspace(min(data), max(data), 100)
    fitted_pdf = stats.norm.pdf(x, mu, sigma)
    return x, fitted_pdf, mu, sigma

def fit_lognormal_distribution(data):
    """Fit log-normal distribution and return parameters and PDF."""
    shape, loc, scale = stats.lognorm.fit(data)
    mu = np.log(scale)  # Mean of log(X)
    sigma = shape       # Standard deviation of log(X)
    x = np.linspace(min(data), max(data), 100)
    fitted_pdf = stats.lognorm.pdf(x, shape, loc, scale)
    return x, fitted_pdf, mu, sigma

def fit_student_t_distribution(x):
    df, loc, scale = stats.t.fit(x)
    x_sorted = np.sort(x)
    pdf_t = stats.t.pdf(x_sorted, df, loc, scale)
    return x_sorted, pdf_t


def prepare_histogram_data(data, bins=100):
    x = np.array(data)
    bin_width = (max(x) - min(x)) / bins
    scale_factor = len(x) * bin_width

    x_norm, pdf_norm, _, _ = fit_normal_distribution(x)
    x_t, pdf_t = fit_student_t_distribution(x)

    return {
        'data': data,
        'bins': bins,
        'scale_factor': scale_factor,
        'normal_fit': {'x': x_norm, 'pdf': pdf_norm * scale_factor},
        'student_t_fit': {'x': x_t, 'pdf': pdf_t * scale_factor},
    }


def render_histogram(view_model, ax=None, show=True, title=None):
    if ax is None:
        fig, ax = plt.subplots()

    sns.histplot(data=view_model['data'], bins=view_model['bins'], ax=ax, stat='count')

    normal = view_model['normal_fit']
    ax.plot(normal['x'], normal['pdf'], color='orange', lw=2, label='Normal Fit')

    student_t = view_model['student_t_fit']
    ax.plot(student_t['x'], student_t['pdf'], color='green', lw=2, label='Student T Fit')

    ax.legend()
    if title:
        ax.set_title(title)
    if show:
        plt.tight_layout()
        plt.show()
    return ax


def histogram_plot(data, ax=None, show=True, title=None, bins=100):
    view_model = prepare_histogram_data(data, bins)
    return render_histogram(view_model, ax, show, title)


# Backward compatibility alias
histgram_plot = histogram_plot

