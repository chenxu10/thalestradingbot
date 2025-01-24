import pytest
from datetime import datetime
import numpy as np
from fentu.riskmanagement.dailyreport import (
    calculate_greeks,
    generate_report,
)
import pandas as pd

# def test_calculate_greeks_put_option():
#     """
#     Test the Black-Scholes Greeks calculation for a put option with known values.
#     This test uses pre-calculated values that can be verified against standard options calculators.
#     """
#     # Test parameters
#     S = 18  # Stock price
#     K = 10  # Strike price
#     T = 1.0  # Time to expiration (1 year)
#     r = 0.04  # Risk-free rate (1%)
#     sigma = 89.8  # Volatility (20%)
    
#     delta, gamma, theta, vega, rho = calculate_greeks(
#         S=S, K=K, T=T, r=r, sigma=sigma, option_type='put'
#     )
#     print(delta)
#     print(gamma)
#     print(theta)
    
#     # Expected values (calculated using standard options calculator)
#     assert abs(delta + 0.4602) < 0.01  # Put delta should be negative
#     assert abs(gamma - 0.0196) < 0.01
#     assert abs(theta + 4.40) < 0.1  # Theta should be negative
#     assert abs(vega - 0.391) < 0.01
#     assert abs(rho + 0.436) < 0.01  # Put rho should be negative

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

