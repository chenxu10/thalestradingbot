import numpy as np
import pandas as pd
from fentu.strategyservices.pair_trading import generate_dailyreturns, calculate_pandl, calculate_cagr

def test_pandl():
    positions = pd.DataFrame({
        0: [1.0,1.0,1],
        1: [-1.0,-1.0,1],
    })
    dailyret = pd.DataFrame(
        {"GLD": [np.NaN, 0.5,0.3],
        "GDX": [np.NaN, -0.5,0.3]}
    )
    expectedpl =[np.NaN, 1.0]
    actualpl = calculate_pandl(positions, dailyret)
    result = expectedpl == actualpl
    result == [False, True]

def test_cagr():
    # Test case 1: Positive growth
    initial_value = 1000
    final_value = 2500
    years = 5
    expected_cagr = 0.2011
    assert round(calculate_cagr(initial_value, final_value, years), 4) == expected_cagr

    # Test case 2: Zero growth
    initial_value = 5000
    final_value = 5000
    years = 10
    expected_cagr = 0.0
    assert round(calculate_cagr(initial_value, final_value, years), 4) == expected_cagr

    # Test case 3: Negative growth
    initial_value = 2000
    final_value = 1500
    years = 3
    expected_cagr = -0.0914
    assert round(calculate_cagr(initial_value, final_value, years), 4) == expected_cagr

def test_generate_dailyreturns():
    input_df = pd.DataFrame(
        {"Date": ["2013-01-02", "2013-01-03"],
         "GLD": [100, 150],
         "GDX": [100, 50]}
    )
    actual = generate_dailyreturns(input_df)
    expected = pd.DataFrame(
        {"GLD": [np.NaN, 0.5],
        "GDX": [np.NaN, -0.5]}
    )
    pd.testing.assert_frame_equal(actual, expected)

if __name__ == '__main__':
    test_pandl()
