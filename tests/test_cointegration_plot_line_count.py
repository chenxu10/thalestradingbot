import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import io
import sys
import pytest

from fentu.strategyservices.pair_trading import plot_cointegration
@pytest.fixture()
def data():
    # Load test data
    gld_data = pd.read_csv("tests/mockdata/test_gld.csv")
    gdx_data = pd.read_csv("tests/mockdata/test_gdx.csv")
    merged_data = pd.merge(gld_data, gdx_data, on="Date").reset_index()
    return merged_data

def test_cointegration_plot_line_count(data):
    # Verify number of lines in cointegration plot
    fig = plot_cointegration(data)
    line_counts = fig.get_axes()[0].get_lines()
    assert len(fig.get_axes()[0].get_lines()) == 2