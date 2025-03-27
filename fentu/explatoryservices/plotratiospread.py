import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

def plot_ratio_spread_payoff():
    # Parameters
    S0 = 100  # Current underlying price
    K_atm = S0  # ATM strike
    K_otm = S0 * 1.1  # OTM strike (10% out)
    T = 0.5  # Time to expiration in years
    r = 0.05  # Risk-free rate
    volatilities = [0.2, 0.3, 0.4]  # Different volatility scenarios
    colors = ['red', 'gold', 'blue']
    
    # Price range for analysis
    S = np.linspace(S0*0.5, S0*1.5, 500)
    
    # Black-Scholes formula for call options
    def bs_call(S, K, T, r, sigma):
        d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        return S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)
    
    plt.figure(figsize=(10, 6))
    
    # Plot volatility scenarios
    for sigma, color in zip(volatilities, colors):
        long_call = bs_call(S, K_atm, T, r, sigma)
        short_calls = 2 * bs_call(S, K_otm, T, r, sigma)
        plt.plot(S, long_call - short_calls, color=color, 
                label=f'Volatility {sigma*100:.0f}%')
    
    # Expiration payoff (dashed line)
    payoff = np.maximum(S - K_atm, 0) - 2 * np.maximum(S - K_otm, 0)
    plt.plot(S, payoff, 'k--', label='Expiration Payoff')
    
    plt.title('Ratio Spread Strategy Payoff\n(Long 1 ATM Call, Short 2 OTM Calls)')
    plt.xlabel('Underlying Price')
    plt.ylabel('Strategy Value')
    plt.legend()
    plt.grid(True)
    plt.savefig("figures/ratiospread.png")
    plt.show()
    plt.close()
# Generate the plot when executed directly
if __name__ == "__main__":
    plot_ratio_spread_payoff()
