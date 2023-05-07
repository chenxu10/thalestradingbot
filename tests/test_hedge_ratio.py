import numpy as np
import pandas as pd
import pytest

def calculate_hedge_ratio(assetonereturn, assettworeturn):
    # Calculate the returns for both assets over the given period
    corr = np.corrcoef(assetonereturn, assettworeturn)[0, 1]
    # Calculate the hedge ratio using the formula
    hedge_ratio = round((corr * np.std(assetonereturn)) / np.std(assettworeturn),2)
    return hedge_ratio

def test_calculate_hedge_ratio():
    assetonereturn = [0.02, -0.01, -0.002, -0.007]
    assettworeturn = [0.003, -0.002, 0.002, 0.001]
    actual = calculate_hedge_ratio(assetonereturn, assettworeturn)
    expected = 4.86
    assert actual == expected
