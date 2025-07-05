import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import probplot
from scipy.stats import norm
from scipy import stats
import fentu.constants as const
import pandas as pd
import yfinance as yf

def calculate_four_moments(x):
    """Calculate the four moments of the data"""
    mean = x.mean()
    std = x.std()
    # Calculate MAD manually since .mad() is deprecated
    mad = (x - x.mean()).abs().mean()
    skew = x.skew()
    kurtosis = x.kurtosis()
    return mean, std, mad, skew, kurtosis


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

def histgram_plot(data):
    print("histgram_plot data looks like", data.sample(2))
    calculate_within_onestrd_prop(data)
    # Plot histogram directly from Series
    sns.histplot(data=data, kde=True, bins=50)
    
    # Convert Series to list for distribution fitting
    x = list(data)
    x_log, pdf_log, mu_log, sigma_log = fit_lognormal_distribution(x)
    plt.plot(x_log, pdf_log, 'g--', lw=2, 
            label=f'Log-Normal Fit\n(μ_log={mu_log:.2f}, σ_log={sigma_log:.2f})')
    
    plt.tight_layout()
    plt.show()

def plot_index_performance(ticker: str, start_date: str = None, end_date: str = None):
    """Plot performance of an index with customizable date range"""
    try:
        # Validate date formats if provided
        if start_date:
            pd.to_datetime(start_date)
        if end_date:
            pd.to_datetime(end_date)
            
        # Fetch data
        if start_date and end_date:
            data = yf.download(ticker, start=start_date, end=end_date)["Close"]
            date_range_str = f"({start_date} to {end_date})"
        else:
            data = yf.download(ticker, period="1y")["Close"]
            date_range_str = f"({data.index[0].date()} to {data.index[-1].date()})"
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        data.plot(ax=ax, title=f"{ticker} Performance {date_range_str}", lw=2)
        ax.set_ylabel("Price ($)")
        ax.grid(True)
        plt.show()
        plt.close(fig)  # Prevent display during tests
        return fig
        
    except Exception as e:
        if "Unknown string format" in str(e):
            raise ValueError(f"Invalid date format: {str(e)}")
        raise RuntimeError(f"Failed to plot {ticker} performance: {str(e)}")


