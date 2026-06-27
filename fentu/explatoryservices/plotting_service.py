import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import probplot
from scipy import stats

# Taleb (SCoFT / "Life Is Not in L2"): kurtosis is a 4th-moment estimator that
# loses scientific validity under fat tails -- one observation can dominate it
# (one day ≈ 80% of SP500 kurtosis over 56 yr). Printing it as a clean point
# estimate is misleading. We therefore also report the leave-one-out kurtosis
# with the single most extreme observation (max |x - mean|) dropped, so the
# reader sees directly how much one day swings the headline number. See
# .opencode/skills/taleb/SKILL.md "Preasymptotics Is the Real World" + row 44
# (kurtosis is not a robust gauge of fatness; prefer MAD / kappa).
def _kurtosis_dropping_outlier(x):
    """Kurtosis of the series after removing the single most extreme obs.

    Returns None if the reduced series is too short (< 4 pts) or if the data
    has no dispersion (the outlier is undefined).
    """
    if x is None or len(x) < 5:
        return None
    mean = x.mean()
    if x.std(ddof=0) == 0:
        return None
    worst = (x - mean).abs().idxmax()
    reduced = x.drop(worst)
    if len(reduced) < 4:
        return None
    return reduced.kurtosis()


def calculate_four_moments(x):
    """Calculate the four moments of the data.

    Also returns the leave-one-out (drop-worst-obs) kurtosis so the caller can
    surface single-observation influence rather than a misleading clean digit.
    """
    mean = x.mean()
    std = x.std()
    mad = (x - x.mean()).abs().mean()
    skew = x.skew()
    kurtosis = x.kurtosis()
    kurtosis_no_worst = _kurtosis_dropping_outlier(x)
    return mean, std, mad, skew, kurtosis, kurtosis_no_worst

def qq_plot(x, ax=None, show=True):
    if ax is None:
        fig, ax = plt.subplots()
    probplot(x, plot=ax)
    mean, std, mad, skew, kurtosis, kurtosis_no_worst = calculate_four_moments(x)
    kurt_line = f'Kurt: {kurtosis:.2f}'
    if kurtosis_no_worst is not None:
        kurt_line += f'\nKurt (drop 1 worst): {kurtosis_no_worst:.2f}'
    ax.text(0.05, 0.7,
            f'Mean: {mean:.4f}\n'
            f'SD: {std:.4f}\n'
            f'MAD:{mad:.4f}\n'
            f'Skew: {skew:.4f}\n'
            f'{kurt_line}',
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


def histgram_plot(data, ax=None, show=True, title=None, bins=100):
    view_model = prepare_histogram_data(data, bins)
    return render_histogram(view_model, ax, show, title)

