import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
import pandas as pd
from fentu.explatoryservices.plotting_service import qq_plot

def test_qqplot():
    x = pd.Series([0,1,2])
    qq_plot(x)
    ax = plt.gca()
    lines = ax.get_children()
    x_data, y_data = lines[0].get_xydata().T
    np.testing.assert_array_almost_equal(
        x_data, np.array([-0.819,0,0.819]), decimal=2)