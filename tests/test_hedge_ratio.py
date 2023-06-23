import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

def calculate_hedge_ratio(assetonereturn, assettworeturn):
    # Calculate the returns for both assets over the given period
    model = sm.OLS(assetonereturn, assettworeturn)
    results = model.fit()
    hedge_ratio = results.params[0]
    return hedge_ratio

def test_calculate_hedge_ratio():
    assetonereturn = [1,2]
    assettworeturn = [2,4]
    actual = calculate_hedge_ratio(assetonereturn, assettworeturn)
    tolerance = 1e-3
    expected = 0.5
    assert abs(actual - expected) < tolerance



