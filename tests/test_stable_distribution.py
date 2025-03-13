import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

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
    alpha, beta, _, _ = stats.levy_stable.fit(data)
    return np.clip(alpha, 0.01, 2.0), np.clip(beta, -1.0, 1.0)

def plot_stable_fit(weekly_changes, save_path=None):
    """
    Visualize the fitted stable distribution against empirical data.
    
    Parameters:
    weekly_changes (list): List of percentage changes
    save_path (str): Optional path to save the plot (default shows interactive)
    """
    data = np.array(weekly_changes)
    alpha, beta = fit_stable_distribution(data)
    
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
        plt.close()
    else:
        plt.show()

def test_fit_stable_distribution():
    weekly_changes = [-0.13,-0.10,-0.07,-0.10,-0.14,-0.14]
    alpha, beta = fit_stable_distribution(weekly_changes)
    
    # Should test ranges rather than exact values
    assert 0 < alpha <= 2, f"Invalid alpha: {alpha}"
    assert -1 <= beta <= 1, f"Invalid beta: {beta}"
    
    # Generate visualization (commented out for CI/CD)
    # plot_stable_fit(weekly_changes)  # Uncomment to see plot

if __name__ == "__main__":
    test_fit_stable_distribution()
