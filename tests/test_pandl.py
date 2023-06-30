import numpy as np
import pandas as pd
from fentu.strategyservices.pair_trading import generate_dailyreturns, calculate_pandl

def test_pandl():
    positions = pd.DataFrame({
        0: [1.0,1.0],
        1: [-1.0,-1.0],
    })
    dailyret = pd.DataFrame(
        {"GLD": [np.NaN, 0.5],
        "GDX": [np.NaN, -0.5]}
    )
    expectedpl =[np.NaN, 1.0]
    actualpl = calculate_pandl(positions, dailyret)
    result = expectedpl == actualpl
    result == [False, True]

def test_generate_dailyreturns():
    input_df = pd.DataFrame(
        {"Date": ["2013-01-02", "2013-01-03"],
         "GLD": [100, 150],
         "GDX": [100, 50]}
    )
    actual = generate_dailyreturns(input_df)
    print(actual)
    expected = pd.DataFrame(
        {"GLD": [np.NaN, 0.5],
        "GDX": [np.NaN, -0.5]}
    )
    pd.testing.assert_frame_equal(actual, expected)

def test_calculate_sharpe(train_size):
    sharpeTrainset = np.sqrt(train_size) * np.mean(returns) / np.std(returns)


if __name__ == '__main__':
    test_pandl()
