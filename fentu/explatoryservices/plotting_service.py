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

def fit_with_normal(close_price):
    mu, sigma = stats.norm.fit(close_price)
    x = np.linspace(min(close_price), max(close_price), 100)
    fitted_data = stats.norm.pdf(x, mu, sigma)
    plt.plot(x, fitted_data, 'r-', lw=2, label=f'Normal Distribution\n(μ={mu:.2f}, σ={sigma:.2f})')

def histgram_plot(data):
    calculate_within_onestrd_prop(data)
    sns.histplot(data, x='Close', kde=True, bins=50)
    close_price = list(data['Close'])
    fit_with_normal(close_price)
    plt.show()

