import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import probplot

def calculate_four_moments(x):
    mean = x.mean()
    std = x.std()
    skew = x.skew()
    kurtosis = x.kurtosis()
    return mean, std, skew, kurtosis

def qq_plot(x):
    fig = probplot(x, plot=plt)
    mean, std, skew, kurtosis = calculate_four_moments(x)
    plt.text(0.05, 0.7, f'Mean: {mean:.4f}\nSD: {std:.4f}\nSkew: {skew:.4f}\nKurtosis: {kurtosis:.4f}', 
         transform=plt.gca().transAxes, fontsize=12)
    plt.ylabel("Returns ETF BAC")
    return fig

def callspread_pandl_plot(df):
    x = df["price_at_expiration"]
    y = df["pandl"]
    #y = 1 / (1 + np.exp(-y))
    fig = plt.plot(x,y)
    return fig


