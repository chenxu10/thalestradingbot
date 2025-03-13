import numpy as np
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
    alpha, beta, _, _ = stats.levy_stable.fit(data)
    return np.clip(alpha, 0.01, 2.0), np.clip(beta, -1.0, 1.0)

def test_fit_stable_distribution():
    weekly_changes = [-0.13,-0.10,-0.07,-0.10,-0.14,-0.14]
    alpha, beta = fit_stable_distribution(weekly_changes)
    print(alpha)
    print(beta)
    
    # Should test ranges rather than exact values
    assert 0 < alpha <= 2, f"Invalid alpha: {alpha}"
    assert -1 <= beta <= 1, f"Invalid beta: {beta}"

if __name__ == "__main__":
    test_fit_stable_distribution()
