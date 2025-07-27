"""
Test suite for PerformanceCalculator class

Tests for calculating month-to-date, quarter-to-date, and year-to-date 
performance for NDX100 benchmarking.
"""

import pytest
import pandas as pd
from datetime import datetime, date
from fentu.performanceservices.performance_calculator import PerformanceCalculator


class TestPerformanceCalculator:
    """Test cases for performance calculations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.calculator = PerformanceCalculator()
        
        # Create sample NDX100 price data
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        # Sample increasing price series
        prices = [100 + i * 0.1 for i in range(len(dates))]
        
        self.sample_data = pd.Series(prices, index=dates)
    
    def test_month_to_date_performance(self):
        """Test MTD performance calculation"""
        result = self.calculator.calculate_mtd_performance(
            self.sample_data, 
            reference_date=date(2023, 6, 15)
        )
        
        assert isinstance(result, float)
        assert result > 0  # Should be positive for upward trend
        assert result < 100  # Reasonable percentage range

    def test_quarter_to_date_performance(self):
        """Test QTD performance calculation"""
        result = self.calculator.calculate_qtd_performance(
            self.sample_data,
            reference_date=date(2023, 6, 15)
        )
        
        assert isinstance(result, float)
        assert result > 0  # Should be positive for upward trend
        
    def test_year_to_date_performance(self):
        """Test YTD performance calculation"""
        result = self.calculator.calculate_ytd_performance(
            self.sample_data,
            reference_date=date(2023, 6, 15)
        )
        
        assert isinstance(result, float)
        assert result > 0  # Should be positive for upward trend
    
    def test_benchmark_comparison(self):
        """Test benchmark comparison for hedge fund performance"""
        hedge_fund_returns = [0.05, 0.03, 0.07, 0.02]  # Monthly returns
        
        result = self.calculator.compare_to_benchmark(
            hedge_fund_returns,
            self.sample_data,
            reference_date=date(2023, 4, 30)
        )
        
        assert isinstance(result, dict)
        assert 'excess_return' in result
        assert 'tracking_error' in result
        
    def test_invalid_date_handling(self):
        """Test handling of invalid dates"""
        with pytest.raises(ValueError):
            self.calculator.calculate_mtd_performance(
                self.sample_data,
                reference_date=date(2030, 1, 1)  # Future date
            ) 