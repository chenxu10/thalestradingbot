import statsmodels.api as sm
import matplotlib.pyplot as plt
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

def callspread_pandl_plot(df,op):
    x = df["price_at_expiration"]
    y = df["pandl"]
    difference_between_strike = op.short_strike - op.long_strike
    netcost_of_spread = op.long_premium - op.short_premium + op.commission
    
    exp_max_profit = difference_between_strike - netcost_of_spread
    exp_max_loss = netcost_of_spread
    risk_and_reward_ratio = exp_max_loss / exp_max_profit
    return exp_max_profit, exp_max_loss, risk_and_reward_ratio


