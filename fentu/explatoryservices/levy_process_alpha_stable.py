import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, t
from fentu.explatoryservices.volcalculator import VolatilityFacade
from scipy import stats


def fit_stable_distribution(weekly_changes):
    """
    Fit a Levy-stable distribution to weekly changes and return alpha and beta parameters.
    
    Parameters:
    weekly_changes (list): List of percentage changes in asset value
    
    Returns:
    tuple: (alpha, beta) where:
        - alpha (float): Stability parameter (0 < alpha ≤ 2)
        - beta (float): Skewness parameter (-1 ≤ beta ≤ 1)
    """
    data = np.array(weekly_changes)
    print("starts to fit ....")
    alpha, beta, _, _ = stats.levy_stable.fit(
        data,
        loc=np.mean(data),  # Provide initial guess
        scale=np.std(data), # Provide initial guess
        optimizer='powell'  # More robust for this problem
    )
    return alpha, beta
    #return np.clip(alpha, 0.01, 2.0), np.clip(beta, -1.0, 1.0)

def plot_stable_fit(weekly_changes, save_path=None):
    """
    Visualize the fitted stable distribution against empirical data.
    
    Parameters:
    weekly_changes (list): List of percentage changes
    save_path (str): Optional path to save the plot (default shows interactive)
    """
    data = np.array(weekly_changes)
    alpha, beta = fit_stable_distribution(data)
    print(alpha, beta)
    
    plt.figure(figsize=(10, 6))
    
    # Empirical data histogram
    plt.hist(data, bins=15, density=True, alpha=0.6, 
             color='blue', label='Empirical Data')
    
    # Fitted distribution curve
    x = np.linspace(np.min(data)-0.1, np.max(data)+0.1, 1000)
    pdf = stats.levy_stable.pdf(x, alpha, beta)
    plt.plot(x, pdf, 'r-', lw=2, 
             label=f'Fitted Stable\nα={alpha:.2f}, β={beta:.2f}')
    
    plt.title('Stable Distribution Fit')
    plt.xlabel('Weekly Price Changes')
    plt.ylabel('Probability Density')
    plt.legend()
    plt.grid(True)
    
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
    else:
        plt.show()

    plt.close()
 

if __name__ == "__main__":
    ticker = "QQQ"
    volatility = VolatilityFacade(ticker)
    weekly_changes = volatility.weekly_returns
    print(len(weekly_changes))
    plot_stable_fit(weekly_changes)

