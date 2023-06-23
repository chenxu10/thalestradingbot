import numpy as np

def test_pandl():
    positions = np.array([2,4])
    dailyret = np.array([0.2,0.5])
    actual = (positions * dailyret).sum()
    expected = 2 * 0.2 + 4 * 0.5
    assert expected == actual