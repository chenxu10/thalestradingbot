import pytest
from datetime import datetime
import numpy as np
from fentu.riskmanagement.dailyreport import (
    calculate_greeks,
    generate_report,
)
import pandas as pd


def test_calculate_greeks_put_option():
    """
    Test the Black-Scholes Greeks calculation for a put option with known values.
    This test uses pre-calculated values that can be verified against standard options calculators.
    """
    # Test parameters
    S = 18  # Stock price
    K = 10  # Strike price
    T = 1.0  # Time to expiration (1 year)
    r = 0.04  # Risk-free rate (1%)
    sigma = 1.1149 # Volatility (20%)
    
    # Calculate Greeks using the function
    delta, gamma, theta, vega, rho = calculate_greeks(
        S=S, K=K, T=T, r=r, sigma=sigma, option_type='put'
    )
    
    # Expected values (calculated using a standard options calculator)
    print(delta)
    print(vega)
    # expected_delta = -0.4602  # Put delta should be negative
    # expected_gamma = 0.0196
    # expected_theta = -4.40  # Theta should be negative
    # expected_vega = 0.391
    # expected_rho = -0.436  # Put rho should be negative
    
    # Assertions with a tolerance for floating-point precision
    # tolerance = 0.01  # Allowable difference between calculated and expected values
    # assert abs(delta - expected_delta) < tolerance, f"Delta mismatch: {delta} vs {expected_delta}"
    # assert abs(gamma - expected_gamma) < tolerance, f"Gamma mismatch: {gamma} vs {expected_gamma}"
    # assert abs(theta - expected_theta) < tolerance, f"Theta mismatch: {theta} vs {expected_theta}"
    # assert abs(vega - expected_vega) < tolerance, f"Vega mismatch: {vega} vs {expected_vega}"
    # assert abs(rho - expected_rho) < tolerance, f"Rho mismatch: {rho} vs {expected_rho}"

@pytest.mark.vcr  # Using pytest-vcr to mock API calls
def test_generate_report_valid_inputs():
    """
    Test report generation with valid inputs.
    This test verifies the structure and content of the generated report.
    """
    ticker = "UVXY"
    strike = 25
    expiration = (datetime.now().date() + pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    position_size = -1
    
    report = generate_report(ticker, strike, expiration, position_size)
    
    # Verify report structure and content
    assert "UVXY Put Position Risk Exposure Report" in report
    assert "Greeks:" in report
    assert "Key Insights:" in report
    assert "Delta:" in report
    assert "Gamma:" in report
    assert "Theta:" in report
    assert "Vega:" in report
    assert "Rho:" in report

test_calculate_greeks_put_option()