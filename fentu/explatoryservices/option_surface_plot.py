import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import norm

def black_scholes_call(S, K, t, r, sigma):
    """
    Calculate Black-Scholes call option price
    
    Args:
        S: Current stock price
        K: Strike price
        t: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Implied volatility
    """
    # Handle the case where t <= 0 using numpy where
    d1 = (np.log(S/K) + (r + sigma**2/2)*t) / (sigma*np.sqrt(t))
    d2 = d1 - sigma*np.sqrt(t)
    
    call_price = S*norm.cdf(d1) - K*np.exp(-r*t)*norm.cdf(d2)
    
    # Return max(0, S-K) when t <= 0
    return np.where(t <= 0, np.maximum(0, S - K), call_price)

def plot_long_call_surface():
    # Option parameters
    K = 100  # Strike price
    r = 0.05  # Risk-free rate
    initial_premium = 5  # Cost of buying the call
    
    # Create meshgrid for stock price and volatility
    stock_prices = np.linspace(80, 120, 40)
    volatilities = np.linspace(0.1, 0.6, 40)
    
    # Create time array for 1-month option (30 days to 0 days)
    # Convert days to years for Black-Scholes calculation
    days_to_expiry = np.linspace(30, 0, 31)  # 31 points for 30 to 0 days
    times = days_to_expiry / 365.0  # Convert to years
    
    S, V, T = np.meshgrid(stock_prices, volatilities, times)
    
    # Calculate option values
    call_values = black_scholes_call(S, K, T, r, V)
    
    # Calculate P&L (subtract initial premium)
    pnl = call_values - initial_premium
    
    # Create 3D plot
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot P&L surface for specific time slices
    time_slices = [0, 10, 20]  # Days remaining: 30, 20, 10
    colors = ['blue', 'green', 'red']
    alpha_values = [0.3, 0.5, 0.7]
    
    for idx, day in enumerate(time_slices):
        time_slice = day
        X, Y = np.meshgrid(stock_prices, volatilities)
        Z = pnl[:,:,time_slice]
        
        # Create surface plot
        surface = ax.plot_surface(X, Y, Z, 
                                cmap=plt.cm.viridis, 
                                alpha=alpha_values[idx],
                                label=f'{30-day} days to expiry')
    
    # Add color bar
    fig.colorbar(surface, ax=ax, label='Profit/Loss ($)')
    
    # Set labels and title
    ax.set_xlabel('Stock Price ($)')
    ax.set_ylabel('Implied Volatility')
    ax.set_zlabel('P&L ($)')
    ax.set_title('Long 1-Month Call Option P&L Surface\nAt Different Days to Expiration')
    
    # Add text annotations for time slices
    x_pos = 120
    y_pos = 0.6
    for idx, day in enumerate(time_slices):
        z_pos = np.max(pnl[:,:,day])
        ax.text(x_pos, y_pos, z_pos, 
                f'{30-day} days left',
                color=colors[idx])
    
    # Rotate the plot for better visualization
    ax.view_init(elev=25, azim=45)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_long_call_surface() 