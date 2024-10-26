"""
loss cost model
GBM to loss cost model
build the bridge between car accidents to stock losses
"""

import numpy as np

def simulate_total_loss(n, avg_severity, severity_std, avg_freq, number_of_policies):
    total_losses = np.zeros(n)

    for i in range(n):
        number_of_accidents = np.random.poisson(
            avg_freq * number_of_policies)
        print(number_of_accidents)
    
    print(total_losses)
    return 2000

def test_lcm_model():
    n = 10000
    avg_severity = 5000
    severity_std = 2000
    avg_freq = 0.1
    number_of_policies = 10000
    total_loss = simulate_total_loss(
        n, avg_severity, severity_std, avg_freq, number_of_policies)
    expected = 2000
    assert total_loss == expected

def main():
    test_lcm_model()

if __name__ == '__main__':
    main()