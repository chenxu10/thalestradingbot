import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
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
    plt.ylabel("Returns ETF BAC")
    return fig


# S = 100 # Underlying price
# K_short = 100 # Short strike  
# K_long = 105 # Long strike
# T = 30 / 365 # Years to expiry   
# r = 0.05 # Risk-free rate
# sigma = 0.2 # Volatility

# S_range = np.arange(80, 120, 1)
# pnl_base = []
# pnl_high_vol = [] 
# pnl_low_vol = []
# pnl_at_expiry = []

# for S in S_range:

#     # Calculate option prices
#     d1 = (np.log(S/K_short)+(r+0.5*sigma**2)*T) / (sigma*np.sqrt(T))
#     d2 = d1 - sigma*np.sqrt(T)
#     short_call = S*norm.cdf(d1) -  K_short*np.exp(-r*T)*norm.cdf(d2)

#     d1 = (np.log(S/K_long)+(r+0.5*sigma**2)*T) / (sigma*np.sqrt(T))
#     d2 = d1 - sigma*np.sqrt(T)
#     long_call = S*norm.cdf(d1) - K_long*np.exp(-r*T)*norm.cdf(d2)
    
#     # Compute P&L     
#     pnl_base.append(short_call - long_call + 2)  
#     pnl_high_vol.append(short_call * 1.1 - long_call* 1.1 + 2)
#     pnl_low_vol.append(short_call * 0.9 - long_call * 0.9 + 2)
       
# # Plot the P&L graphs  
# plt.plot(S_range, pnl_base, c='blue')
# plt.plot(S_range, pnl_high_vol, c='green') 
# plt.plot(S_range, pnl_low_vol, c='red')
# plt.plot(S_range, pnl_at_expiry, c='yellow')   

# plt.xlabel('Underlying Price')
# plt.ylabel('Profit & Loss')
# plt.title('Call Spread P&L Curves')

# plt.grid()
# plt.show()