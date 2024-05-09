import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import probplot
from scipy.stats import norm
import fentu.constants as const

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
    plt.show()
    return fig

def calculate_within_onestrd_prop(data):
    close = data['Close']
    mean = close.mean()
    std = close.std()
    mask = (close >= mean - 2 * std) & (close <= mean + 2 * std)
    proportion = mask.mean()
    print("stock price change days within 1 standard deviation{}".format(proportion))

def histgram_plot(data):
    calculate_within_onestrd_prop(data)
    sns.histplot(data, x='Close', kde=True, bins=30)
    plt.show()
