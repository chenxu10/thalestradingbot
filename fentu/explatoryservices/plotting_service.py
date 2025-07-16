import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import probplot
from scipy.stats import norm
from scipy import stats
import fentu.constants as const
import pandas as pd
from fentu.dataservices import download_data_range as ddr

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

def validate_date_formats(start_date, end_date):
    if start_date:
        pd.to_datetime(start_date)
    if end_date:
        pd.to_datetime(end_date)

def plot_index_performance(ticker, start_date: str = None, end_date: str = None):
    """Plot performance of one or more indices with customizable date range"""
    try:
        # Accept ticker as str or list of str
        if isinstance(ticker, str):
            tickers = [ticker]
        elif isinstance(ticker, list):
            tickers = ticker
        else:
            raise ValueError("ticker must be a string or a list of strings")

        validate_date_formats(start_date, end_date)
        data_dict, date_range_str = download_and_align_data(start_date, end_date, tickers)
        print(data_dict)
        print(date_range_str)
        combined_df = combine_into_single_dataframe(data_dict)
        return create_plot(tickers, date_range_str, combined_df)

    except Exception as e:
        if "Unknown string format" in str(e):
            raise ValueError(f"Invalid date format: {str(e)}")
        raise RuntimeError(f"Failed to plot {ticker} performance: {str(e)}")

def create_plot(tickers, date_range_str, combined_df):
    fig, ax = plt.subplots(figsize=(10, 6))
    combined_df.plot(ax=ax, lw=2)
    ax.set_title(f"{' vs '.join(tickers)} Performance {date_range_str}")
    ax.set_ylabel("Price ($)")
    ax.grid(True)
    ax.legend(title="Ticker")
    plt.show()
    plt.close(fig)
    return fig

def combine_into_single_dataframe(data_dict):
    combined_df = pd.DataFrame(data_dict)
    return combined_df

def download_and_align_data(start_date, end_date, tickers):
    data_dict = {}
    date_range_str = None
    for t in tickers:
        data, drs = ddr.download_ticker_range(t, start_date, end_date)
        data_dict[t] = data.squeeze()  # Squeeze in case it's a DataFrame with one column
        if date_range_str is None:
            date_range_str = drs
    return data_dict,date_range_str



