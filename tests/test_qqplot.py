import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

def qq_plot(x):
    return sm.qqplot(x, line='45')

def test_qqplot():
    x = np.array([0, 1, 2])
    qq_plot(x)
    ax = plt.gca()
    lines = ax.get_children()
    x_data, y_data = lines[0].get_xydata().T
    np.testing.assert_array_almost_equal(x_data, np.array([-0.67,0,0.67]), decimal=2)