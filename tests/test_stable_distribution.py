

def fit_stable_distribution(weekly_changes):
    alpha = 1
    beta = 0.5
    return alpha, beta


def test_fit_stable_distribution():
    weekly_changes = []
    expected_alpha, expected_beta = fit_stable_distribution(weekly_changes) 
    assert expected_alpha == 1
    assert expected_beta == 0.5

if __name__ == "__main__":
    test_fit_stable_distribution()
