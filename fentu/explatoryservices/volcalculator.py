"""
This script calculates volatility and return metrics for financial instruments
Refactored to follow SOLID principles with separated concerns
"""

import pandas as pd
pd.set_option('display.max_rows', None)

import fentu.explatoryservices.plotting_service as ps   
from fentu.dataservices.download_data_range import DataRetriever
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Union, Dict, Any


# Business Logic Layer - Single Responsibility: Return Calculations
class ReturnCalculator:
    """Responsible for calculating returns at different time periods"""
    
    def __init__(self, data_retriever: DataRetriever):
        self.data_retriever = data_retriever
    
    def calculate_returns(self, prices: pd.Series, period_length: int) -> pd.Series:
        """
        Calculate percentage returns for given period length
        
        Args:
            prices: Historical price data
            period_length: Number of days for the period (1=daily, 5=weekly, etc.)
            
        Returns:
            pandas.Series: Percentage returns
        """
        return prices.pct_change(period_length)[period_length:]
    
    def get_all_returns(self, instrument: str) -> Dict[str, pd.Series]:
        """
        Get returns for all standard time periods
        
        Args:
            instrument: Financial instrument ticker
            
        Returns:
            Dict containing returns for different periods
        """
        prices = self.data_retriever.get_prices(instrument)
        
        return {
            'daily': self.calculate_returns(prices, 1),
            'weekly': self.calculate_returns(prices, 5),
            'monthly': self.calculate_returns(prices, 21),
            'yearly': self.calculate_returns(prices, 252)
        }


# Enhanced Volatility Calculation - Open/Closed Principle
class VolatilityCalculator(ABC):
    """Abstract base class for different volatility calculation strategies"""
    
    @abstractmethod
    def calculate_volatility(self, returns_data: pd.Series) -> float:
        """Calculate volatility from returns data"""
        pass


class StandardDeviationVolatility(VolatilityCalculator):
    """Standard deviation based volatility calculation"""
    
    def calculate_volatility(self, returns_data: pd.Series) -> float:
        return returns_data.std()


class VolatilityService:
    """Service for calculating different types of volatility"""
    
    def __init__(self, calculator: VolatilityCalculator = None):
        self.calculator = calculator or StandardDeviationVolatility()
    
    def calculate_daily_volatility(self, daily_returns: pd.Series) -> float:
        """Calculate daily volatility using the configured calculator"""
        return self.calculator.calculate_volatility(daily_returns)


# Analysis Layer - Single Responsibility: Worst Returns Analysis
class WorstReturnAnalyzer:
    """Responsible for finding and analyzing worst returns"""
    
    def __init__(self, return_calculator: ReturnCalculator):
        self.return_calculator = return_calculator
    
    def find_worst_returns(self, returns: pd.Series, k: Optional[int] = None, 
                          threshold: Optional[float] = None) -> pd.Series:
        """
        Find worst returns either by count (k) or threshold
        
        Args:
            returns: Return data to analyze
            k: Number of worst returns to find
            threshold: Threshold below which returns are considered "worst"
            
        Returns:
            pandas.Series: Filtered returns sorted from worst to best
        """
        if k is not None and threshold is not None:
            raise ValueError("Please specify either k or threshold, not both")
        
        if k is not None:
            return returns.sort_values().head(k)
        
        if threshold is not None:
            return returns.loc[returns < threshold].sort_values()
            
        raise ValueError("Either k or threshold must be specified")
    
    def find_worst_k_by_period(self, returns_dict: Dict[str, pd.Series], 
                              period: str, k: int) -> pd.Series:
        """Find k worst returns for a specific period"""
        if period not in returns_dict:
            raise ValueError(f"Period must be one of {list(returns_dict.keys())}")
        
        return self.find_worst_returns(returns_dict[period], k=k)
    
    def find_worst_by_threshold(self, returns_dict: Dict[str, pd.Series], 
                               period: str, threshold: float) -> pd.Series:
        """Find returns below threshold for a specific period"""
        if period not in returns_dict:
            raise ValueError(f"Period must be one of {list(returns_dict.keys())}")
        
        return self.find_worst_returns(returns_dict[period], threshold=threshold)


# Analysis Layer - Single Responsibility: Calendar Returns
class CalendarReturnCalculator:
    """Responsible for calculating calendar year returns"""
    
    def __init__(self, data_retriever: DataRetriever):
        self.data_retriever = data_retriever
    
    def get_calendar_year_returns(self, instrument: str) -> pd.DataFrame:
        """
        Calculate returns for each calendar year.
        Returns a DataFrame with yearly returns where each return represents
        buying on Jan 1st and selling on Dec 31st of the same year.
        
        Args:
            instrument: Financial instrument ticker
            
        Returns:
            pandas.DataFrame: Calendar year returns
        """
        prices = self.data_retriever.get_prices(instrument)
        
        yearly_returns_list = []
        years = prices.index.year.unique()
        
        for year in years:
            year_data = prices[prices.index.year == year]
            if not year_data.empty:
                first_price = year_data.iloc[0]
                last_price = year_data.iloc[-1]
                
                year_return = (last_price - first_price) / first_price
                
                yearly_returns_list.append({
                    'Date': pd.Timestamp(f'{year}-12-31'),
                    'Close': year_return
                })
        
        calendar_returns = pd.DataFrame(yearly_returns_list)
        return calendar_returns.sort_values('Date', ascending=False)


# Presentation Layer - Single Responsibility: Visualization Coordination
class VisualizationService:
    """Responsible for coordinating visualization of returns data"""
    
    def visualize_returns(self, returns_data: pd.Series):
        """Visualize returns using QQ plot and histogram"""
        ps.qq_plot(returns_data)
        ps.histgram_plot(returns_data)
    
    def visualize_period_returns(self, returns_dict: Dict[str, pd.Series], period: str):
        """Visualize returns for a specific period"""
        if period not in returns_dict:
            raise ValueError(f"Period must be one of {list(returns_dict.keys())}")
        
        self.visualize_returns(returns_dict[period])


# Main Service - Dependency Inversion Principle: High-level orchestration
class FinancialAnalysisService:
    """
    Main service that orchestrates financial analysis operations
    Follows Dependency Inversion Principle by depending on abstractions
    """
    
    def __init__(self, 
                 data_retriever: DataRetriever = None,
                 return_calculator: ReturnCalculator = None,
                 volatility_service: VolatilityService = None,
                 worst_return_analyzer: WorstReturnAnalyzer = None,
                 calendar_return_calculator: CalendarReturnCalculator = None,
                 visualization_service: VisualizationService = None):
        
        # Dependency injection - allows for easy testing and extension
        self.data_retriever = data_retriever or DataRetriever()
        self.return_calculator = return_calculator or ReturnCalculator(self.data_retriever)
        self.volatility_service = volatility_service or VolatilityService()
        self.worst_return_analyzer = worst_return_analyzer or WorstReturnAnalyzer(self.return_calculator)
        self.calendar_return_calculator = calendar_return_calculator or CalendarReturnCalculator(self.data_retriever)
        self.visualization_service = visualization_service or VisualizationService()
        
        self.instrument = None
        self.returns_data = None
    
    def initialize_instrument(self, instrument: str):
        """Initialize the service with a specific instrument"""
        self.instrument = instrument
        self.returns_data = self.return_calculator.get_all_returns(instrument)
    
    def get_returns_data(self) -> Dict[str, pd.Series]:
        """Get all returns data for the current instrument"""
        if self.returns_data is None:
            raise ValueError("No instrument initialized. Call initialize_instrument() first.")
        return self.returns_data
    
    def calculate_daily_volatility(self) -> float:
        """Calculate daily volatility for the current instrument"""
        if self.returns_data is None:
            raise ValueError("No instrument initialized. Call initialize_instrument() first.")
        return self.volatility_service.calculate_daily_volatility(self.returns_data['daily'])
    
    def visualize_returns(self, period: str = 'daily'):
        """Visualize returns for a specific period"""
        if self.returns_data is None:
            raise ValueError("No instrument initialized. Call initialize_instrument() first.")
        self.visualization_service.visualize_period_returns(self.returns_data, period)
    
    def find_worst_returns(self, period: str = 'daily', k: Optional[int] = None, 
                          threshold: Optional[float] = None) -> pd.Series:
        """Find worst returns for a specific period"""
        if self.returns_data is None:
            raise ValueError("No instrument initialized. Call initialize_instrument() first.")
        
        if k is not None:
            return self.worst_return_analyzer.find_worst_k_by_period(self.returns_data, period, k)
        else:
            return self.worst_return_analyzer.find_worst_by_threshold(self.returns_data, period, threshold)
    
    def get_calendar_year_returns(self) -> pd.DataFrame:
        """Get calendar year returns for the current instrument"""
        if self.instrument is None:
            raise ValueError("No instrument initialized. Call initialize_instrument() first.")
        return self.calendar_return_calculator.get_calendar_year_returns(self.instrument)
    
    def show_recent_returns(self, period: str = 'daily', n: int = 20):
        """Show recent returns for a specific period"""
        if self.returns_data is None:
            raise ValueError("No instrument initialized. Call initialize_instrument() first.")
        
        if period not in self.returns_data:
            raise ValueError(f"Period must be one of {list(self.returns_data.keys())}")
        
        print(self.returns_data[period].tail(n))


# Backward Compatibility Layer - Facade Pattern
class VolatilityFacade:
    """
    Backward compatibility facade that maintains the original interface
    while using the new refactored structure internally
    """
    
    def __init__(self, instrument: str):
        self.instrument = instrument
        self.analysis_service = FinancialAnalysisService()
        self.analysis_service.initialize_instrument(instrument)
        
        # Maintain backward compatibility by exposing the original attributes
        returns_data = self.analysis_service.get_returns_data()
        self.daily_returns = returns_data['daily']
        self.weekly_returns = returns_data['weekly']
        self.monthly_returns = returns_data['monthly']
        self.yearly_returns = returns_data['yearly']
        
        self.return_periods = returns_data
        self.prices = self.analysis_service.data_retriever.get_prices(instrument)
        
        # For backward compatibility with the old volatility calculator
        self.daily_volatility = self.analysis_service.volatility_service
    
    def calculate_daily_volatility(self) -> float:
        """Calculate daily volatility"""
        return self.analysis_service.calculate_daily_volatility()
    
    def visualize_percentage_change(self, period: str = 'daily'):
        """Visualize percentage changes for a specific period"""
        self.analysis_service.visualize_returns(period)
    
    def visualize_daily_percentage_change(self):
        """Visualize daily percentage changes"""
        self.visualize_percentage_change('daily')
    
    def visualize_weekly_percentage_change(self):
        """Visualize weekly percentage changes"""
        self.visualize_percentage_change('weekly')
    
    def visualize_monthly_percentage_change(self):
        """Visualize monthly percentage changes"""
        self.visualize_percentage_change('monthly')
    
    def visualize_yearly_percentage_change(self):
        """Visualize yearly percentage changes"""
        self.visualize_percentage_change('yearly')
    
    def find_worst_returns(self, period: str = 'daily', k: Optional[int] = None, 
                          threshold: Optional[float] = None) -> pd.Series:
        """Find worst returns for a specific period"""
        return self.analysis_service.find_worst_returns(period, k, threshold)
    
    def find_worst_k_days(self, k: int = 20) -> pd.Series:
        """Find k worst daily returns"""
        return self.find_worst_returns(period='daily', k=k)
    
    def find_worst_k_weeks(self, k: int = 3) -> pd.Series:
        """Find k worst weekly returns"""
        return self.find_worst_returns(period='weekly', k=k)
    
    def find_worst_k_months(self, k: int = 3) -> pd.Series:
        """Find k worst monthly returns"""
        return self.find_worst_returns(period='monthly', k=k)
    
    def find_worst_k_years(self, k: int = 3) -> pd.Series:
        """Find k worst yearly returns"""
        return self.find_worst_returns(period='yearly', k=k)
    
    def find_worst_weeks(self, threshold: float = -0.1) -> pd.Series:
        """Find weekly returns below threshold"""
        return self.find_worst_returns(period='weekly', threshold=threshold)
    
    def find_worst_months(self, threshold: float = -0.2) -> pd.Series:
        """Find monthly returns below threshold"""
        return self.find_worst_returns(period='monthly', threshold=threshold)
    
    def get_calendar_year_returns(self, instrument: Optional[str] = None) -> pd.DataFrame:
        """Get calendar year returns"""
        if instrument and instrument != self.instrument:
            # For different instrument, create new calculator
            temp_service = FinancialAnalysisService()
            temp_service.initialize_instrument(instrument)
            return temp_service.get_calendar_year_returns()
        return self.analysis_service.get_calendar_year_returns()
    
    def show_today_return(self):
        """Show recent daily returns"""
        self.analysis_service.show_recent_returns('daily', 20)
    
    # Legacy methods for backward compatibility
    def _get_prices(self, instrument: str) -> pd.Series:
        """Legacy method for backward compatibility"""
        return self.analysis_service.data_retriever.get_prices(instrument)
    
    def _get_returns(self, instrument: str, prices: pd.Series, period_length: int) -> pd.Series:
        """Legacy method for backward compatibility"""
        return self.analysis_service.return_calculator.calculate_returns(prices, period_length)


# Keep the old classes for backward compatibility
class DailyVolatility:
    """Legacy class for backward compatibility"""
    def __init__(self, calculator: VolatilityCalculator = None):
        self.calculator = calculator or StandardDeviationVolatility()
    
    def calculate_1std_daily_volatility(self, daily_returns: pd.Series) -> float:
        return self.calculator.calculate_volatility(daily_returns)


if __name__ == "__main__":   
    ticker = ["spy","qqq"]
    ps.plot_index_performance(ticker,'2025-02-17','2025-07-06')
    
    # Example usage of the new structure
    analysis_service = FinancialAnalysisService()
    analysis_service.initialize_instrument("TLT")
    print(f"Daily volatility: {analysis_service.calculate_daily_volatility()}")
    print(f"Worst 5 days: {analysis_service.find_worst_returns('daily', k=5)}")
    
    # Or use the backward-compatible facade
    ticker = "TLT"
    volatility = VolatilityFacade(ticker)
    print(volatility._get_prices(ticker))
    
    
    print(volatility.weekly_returns)
    volatility.visualize_daily_percentage_change()
    volatility.visualize_weekly_percentage_change()
    print(volatility.daily_returns[-10:])
    #print(volatility.weekly_returns[-10:])
    
    # Visualize different time-frame return distributions
    #volatility.visualize_weekly_percentage_change()
    #volatility.visualize_daily_percentage_change()
    # volatility.visualize_monthly_percentage_change()
    #volatility.visualize_yearly_percentage_change()
    #print(volatility.yearly_returns)
    
    # Calculate volatility metrics
    # print(f"Daily volatility: {volatility.calculate_daily_volatility()}")
    
    # Find extreme returns
    #print(f"Worst weeks: {volatility.find_worst_k_weeks()}")
    # print(f"Worst days: {volatility.find_worst_k_days(k=5)}")
    #print(f"Worst months: {volatility.find_worst_k_months(k=5)}")
    # print(f"Worst months (below -20%): {volatility.find_worst_months(threshold=-0.2)}")
    # print(f"Worst 3 months: {volatility.find_worst_k_months(k=3)}")
    # print(f"Worst 3 years: {volatility.find_worst_k_years(k=3)}")
    
    # Show recent returns
    #volatility.show_today_return()
    
    # Calculate calendar year returns
    #calendar_returns = volatility.get_calendar_year_returns(ticker)
    # calendar_returns['TLT 3X'] = calendar_returns['Close'] * 3
    # print(calendar_returns)
    


