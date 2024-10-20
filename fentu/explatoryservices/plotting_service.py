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

def histgram_plot(data):
    calculate_within_onestrd_prop(data)
    sns.histplot(data, x='Close', kde=True, bins=30)
    plt.show()
