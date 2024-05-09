import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import probplot
from scipy.stats import norm

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