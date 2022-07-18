import pandas as pd
from fentu.acquistionservices.historicplot import get_qratio

def test_get_qratio():
    """
    ROIC(return on invested capital)
    """
    actual = get_qratio()
    print(actual)
    expected = [1 for _ in range(73 * 4 - 4)]
    assert len(actual['q_ratio']) == len(expected)
    
def test_plot_qratio():
    """
    """
    raise notImplementedError

if __name__ == '__main__':
    test_get_qratio()