import pytest
from fentu.explatoryservices import levy_process_alpha_stable as lpas 

@pytest.mark.skip
def test_fit_stable_distribution():
    weekly_changes = [-0.13,-0.10,-0.07,-0.10,-0.14,-0.14]
    alpha, beta = lpas.fit_stable_distribution(weekly_changes)
    
    # Should test ranges rather than exact values
    assert 0 < alpha <= 2, f"Invalid alpha: {alpha}"
    assert -1 <= beta <= 1, f"Invalid beta: {beta}"
    

if __name__ == "__main__":
    test_fit_stable_distribution()

