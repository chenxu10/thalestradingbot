import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import probplot
from scipy.stats import norm
from scipy import stats
import fentu.constants as const

def calculate_four_moments(x):
    mean = x.mean()
    std = x.std()
    mad = x.mad()
    skew = x.skew()
    kurtosis = x.kurtosis()
    return mean, mad, std, skew, kurtosis

def qq_plot(x):
    fig = probplot(x, plot=plt)
    mean, std, mad, skew, kurtosis = calculate_four_moments(x)
    plt.text(0.05, 0.7, 
             f'Mean: {mean:.4f}\
             \nSD: {std:.4f}\
             \nMAD:{mad:.4f}\
             \nSkew: {skew:.4f}\
             \nKurtosis: {kurtosis:.4f}', 
         transform=plt.gca().transAxes, fontsize=12)
    plt.show()
    return fig

def calculate_within_onestrd_prop(data):
    close = data['Close']
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

def histgram_plot(data):
    calculate_within_onestrd_prop(data)
    sns.histplot(data, x='Close', kde=True, bins=50)
    x = list(data['Close'])   
    x_log, pdf_log, mu_log, sigma_log = fit_lognormal_distribution(x)
    plt.plot(x_log, pdf_log, 'g--', lw=2, 
            label=f'Log-Normal Fit\n(μ_log={mu_log:.2f}, σ_log={sigma_log:.2f})')
    
    plt.tight_layout()
    plt.show()

