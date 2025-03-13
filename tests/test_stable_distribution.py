import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from fentu.explatoryservices.levy_process_alpha_stable import fit_stable_distribution, plot_stable_fit

def test_fit_stable_distribution():
    weekly_changes = [-0.13,-0.10,-0.07,-0.10,-0.14,-0.14]
    alpha, beta = fit_stable_distribution(weekly_changes)
    
    # Should test ranges rather than exact values
    assert 0 < alpha <= 2, f"Invalid alpha: {alpha}"
    assert -1 <= beta <= 1, f"Invalid beta: {beta}"
    

if __name__ == "__main__":
    weekly_changes = [-0.13,-0.10,-0.07,-0.10,-0.14,-0.14]
    plot_stable_fit(weekly_changes)  # Uncomment to see plot
    test_fit_stable_distribution()

