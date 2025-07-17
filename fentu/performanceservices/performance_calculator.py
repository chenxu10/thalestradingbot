"""
Performance Calculator for financial instruments

Calculates MTD, QTD, YTD performance for benchmarking hedge fund managers.
"""

import pandas as pd
import numpy as np
from datetime import date, datetime
from typing import Dict, List, Union


class PerformanceCalculator:
    """Calculator for various performance metrics"""
    
    def __init__(self):
        """Initialize the performance calculator"""
        pass
    
    def calculate_mtd_performance(self, prices: pd.Series, 
                                reference_date: date) -> float:
        """
        Calculate month-to-date performance
        
        Args:
            prices: Historical price data
            reference_date: Date for MTD calculation
            
        Returns:
            MTD performance as percentage
        """
        self._validate_date(prices, reference_date)
        
        month_start = date(reference_date.year, reference_date.month, 1)
        
        start_price = self._get_price_at_date(prices, month_start)
        end_price = self._get_price_at_date(prices, reference_date)
        
        return ((end_price - start_price) / start_price) * 100
    
    def calculate_qtd_performance(self, prices: pd.Series, 
                                reference_date: date) -> float:
        """
        Calculate quarter-to-date performance
        
        Args:
            prices: Historical price data
            reference_date: Date for QTD calculation
            
        Returns:
            QTD performance as percentage
        """
        self._validate_date(prices, reference_date)
        
        quarter_start = self._get_quarter_start(reference_date)
        
        start_price = self._get_price_at_date(prices, quarter_start)
        end_price = self._get_price_at_date(prices, reference_date)
        
        return ((end_price - start_price) / start_price) * 100
    
    def calculate_ytd_performance(self, prices: pd.Series, 
                                reference_date: date) -> float:
        """
        Calculate year-to-date performance
        
        Args:
            prices: Historical price data
            reference_date: Date for YTD calculation
            
        Returns:
            YTD performance as percentage
        """
        self._validate_date(prices, reference_date)
        
        year_start = date(reference_date.year, 1, 1)
        
        start_price = self._get_price_at_date(prices, year_start)
        end_price = self._get_price_at_date(prices, reference_date)
        
        return ((end_price - start_price) / start_price) * 100
    
    def compare_to_benchmark(self, hedge_fund_returns: List[float], 
                           benchmark_prices: pd.Series, 
                           reference_date: date) -> Dict[str, float]:
        """
        Compare hedge fund performance to benchmark
        
        Args:
            hedge_fund_returns: List of hedge fund returns
            benchmark_prices: Benchmark price data
            reference_date: Reference date for comparison
            
        Returns:
            Dict with excess return and tracking error
        """
        # Calculate benchmark returns
        benchmark_returns = self._calculate_returns(benchmark_prices)
        
        # Calculate excess return
        avg_hf_return = np.mean(hedge_fund_returns)
        avg_benchmark_return = np.mean(benchmark_returns)
        excess_return = avg_hf_return - avg_benchmark_return
        
        # Calculate tracking error
        tracking_error = np.std(np.array(hedge_fund_returns) - 
                              np.array(benchmark_returns[:len(hedge_fund_returns)]))
        
        return {
            'excess_return': excess_return,
            'tracking_error': tracking_error
        }
    
    def _validate_date(self, prices: pd.Series, reference_date: date) -> None:
        """Validate that reference date is within price data range"""
        if reference_date > date.today():
            raise ValueError("Reference date cannot be in the future")
        
        if reference_date < prices.index[0].date():
            raise ValueError("Reference date is before available data")
    
    def _get_quarter_start(self, reference_date: date) -> date:
        """Get the start date of the quarter for a given date"""
        quarter_starts = {1: 1, 2: 1, 3: 1, 4: 4, 5: 4, 6: 4, 
                         7: 7, 8: 7, 9: 7, 10: 10, 11: 10, 12: 10}
        
        start_month = quarter_starts[reference_date.month]
        return date(reference_date.year, start_month, 1)
    
    def _get_price_at_date(self, prices: pd.Series, target_date: date) -> float:
        """Get price at specific date, using nearest available date"""
        target_timestamp = pd.Timestamp(target_date)
        
        # Find the nearest available date
        nearest_date = prices.index[prices.index <= target_timestamp][-1]
        return prices[nearest_date]
    
    def _calculate_returns(self, prices: pd.Series) -> List[float]:
        """Calculate period returns from price series"""
        returns = prices.pct_change().dropna()
        return returns.tolist() 