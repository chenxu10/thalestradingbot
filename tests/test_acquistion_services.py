import pandas as pd
import pytest
import matplotlib.pyplot as plt
from fentu.acquistionservices.historicplot import get_running_gmean_qratio, calculate_geometric_mean, plot_q_ratio
def test_get_qratio():
    """
    ROIC(return on invested capital)
    """
    actual = get_running_gmean_qratio()
    print(actual)
    expected = [1 for _ in range(73 * 4 - 4)]
    assert len(actual['geo_q_ratio']) == len(expected)

def test_calculate_geomtric_mean():
    input = [1.2,1.3,0.5,0.7]
    actual = calculate_geometric_mean(input)
    print(actual)
    expected = [1.2,1.25,0.92,0.86]
    assert actual == expected

def test_plot_qratio(monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda: None)
    plot_q_ratio()

# def test_plot_qratio():
#     """
#     """
#     raise notImplementedError

if __name__ == '__main__':
    print(test_calculate_geomtric_mean())
    # test_get_qratio()