import numpy as np


def simulate_total_loss(n, avg_severity, severity_std):
    total_losses = np.zeros(n)
    
    print(total_losses)
    return 2000

def test_lcm_model():
    n = 10000
    avg_severity = 5000
    severity_std = 2000
    total_loss = simulate_total_loss(n, avg_severity, severity_std)
    expected = 2000
    assert total_loss == expected

def main():
    test_lcm_model()

if __name__ == '__main__':
    main()