
import pytest
from datetime import datetime
import pandas as pd
from fentu.explatoryservices.volcalculator import VolatilityFacade

@pytest.fixture
def volatility():
    return VolatilityFacade("TLT")

def test_get_calendar_year_returns(volatility):
    # Get the yearly returns
    yearly_returns = volatility.get_calendar_year_returns("TLT")
    
    # Verify the data structure
    assert isinstance(yearly_returns, pd.DataFrame), "Output should be a pandas DataFrame"
    assert set(['Date', 'Close']) == set(yearly_returns.columns), "DataFrame should have 'Date' and 'Close' columns"
    
    # Convert Date column to datetime if it isn't already
    yearly_returns['Date'] = pd.to_datetime(yearly_returns['Date'])
    
    # Check if data extends to current year
    current_year = datetime.now().year
    latest_year = yearly_returns['Date'].max().year
    assert latest_year >= current_year - 1, f"Data should extend to at least {current_year-1}, but ends at {latest_year}"
    
    # Verify that returns are within reasonable bounds (-100% to +100%)
    assert all(yearly_returns['Close'].between(-1, 1)), "Yearly returns should be between -100% and 100%"
    
    # Verify the dates are all year-end dates
    assert all(yearly_returns['Date'].dt.month == 12), "All dates should be in December"
    assert all(yearly_returns['Date'].dt.day == 31), "All dates should be on the 31st"
    
    # Verify the data is sorted in descending order
    assert yearly_returns['Date'].is_monotonic_decreasing, "Data should be sorted by date in descending order"