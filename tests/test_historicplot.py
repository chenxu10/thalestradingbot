import pandas as pd
import matplotlib.pyplot as plt
from fentu.acquisitionservices.historicplot import get_running_gmean_qratio, plot_q_ratio, extraploate

def test_get_qratio():
    """
    ROIC(return on invested capital)
    """
    actual = get_running_gmean_qratio()
    print(actual)
    expected = [1 for _ in range(73 * 4 - 4)]
    assert len(actual['geo_q_ratio']) == len(expected)

def test_extraploate():
    expected = 39870152
    input = 48113902
    guessedrecenteqli = extraploate(input, 188.62, 227.62)
    print(guessedrecenteqli)
    assert guessedrecenteqli == expected

def test_plot_qratio(monkeypatch):
    monkeypatch.setattr(plt, 'show', lambda: None)
    plot_q_ratio()

if __name__ == "__main__":
    test_extraploate()
