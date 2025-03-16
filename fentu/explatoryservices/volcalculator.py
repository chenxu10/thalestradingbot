"""
This script calculates volatility and return metrics for financial instruments
"""

import yfinance as yf
import statsmodels.api as sm
import matplotlib.pyplot as plt
import pandas as pd
pd.set_option('display.max_rows', None)

import fentu.explatoryservices.plotting_service as ps
import numpy as np
from scipy.stats import norm, t

class VolatilityCalculator:
    """Base class for different volatility calculation strategies"""
    def calculate_volatility(self, returns_data):
        raise NotImplementedError

class StandardDeviationVolatility(VolatilityCalculator):
    def calculate_volatility(self, returns_data):
        # Handle both Series and DataFrame inputs
        return returns_data.std()

class DailyVolatility:
    def __init__(self, calculator: VolatilityCalculator = None):
        self.calculator = calculator or StandardDeviationVolatility()
    
    def calculate_1std_daily_volatility(self, daily_returns):
        return self.calculator.calculate_volatility(daily_returns)

class VolatilityFacade:
    """
    This class gets daily percentage change of an instrument
    """
    def __init__(self, instrument):
        self.instrument = instrument
        self.daily_returns = self._get_returns(instrument, 1)
        self.weekly_returns = self._get_returns(instrument, 5)
        self.monthly_returns = self._get_returns(instrument, 21)
        self.yearly_returns = self._get_returns(instrument, 252)
        self.daily_volatility = DailyVolatility()
        self.return_periods = {
            'daily': self.daily_returns,
            'weekly': self.weekly_returns,
            'monthly': self.monthly_returns,
            'yearly': self.yearly_returns
        }

    def _get_prices(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']
        return prices
    
    def get_calendar_year_returns(self, instrument=None):
        """
        Calculate returns for each calendar year from 2003 to present.
        Returns a DataFrame with yearly returns where each return represents
        buying on Jan 1st and selling on Dec 31st of the same year.
        """
        instrument = instrument or self.instrument
        prices = self._get_prices(instrument)
        
        # Create empty list to store yearly returns
        yearly_returns_list = []
        
        # Get unique years from the price data
        years = prices.index.year.unique()
        
        for year in years:
            # Get first and last trading day prices for each year
            year_data = prices[prices.index.year == year]
            if not year_data.empty:
                first_price = year_data.iloc[0]
                last_price = year_data.iloc[-1]
                
                # Calculate return
                year_return = (last_price - first_price) / first_price
                
                yearly_returns_list.append({
                    'Date': pd.Timestamp(f'{year}-12-31'),
                    'Close': year_return
                })
        
        # Convert to DataFrame and sort by date
        calendar_returns = pd.DataFrame(yearly_returns_list)
        calendar_returns = calendar_returns.sort_values('Date', ascending=False)
        
        return calendar_returns

    def _get_returns(self, instrument, period_length):
        """
        Helper method to get returns for different time periods
        Args:
            instrument: The financial instrument ticker
            period_length: Number of days for the period (1=daily, 5=weekly, 21=monthly, 252=yearly)
        """
        prices = self._get_prices(instrument)
        returns = prices.pct_change(period_length)[period_length:]
        return returns
    
    def calculate_daily_volatility(self):
        return self.daily_volatility.calculate_1std_daily_volatility(self.daily_returns)
    
    def visualize_percentage_change(self, period='daily'):
        """
        Visualize percentage changes for a specific period using QQ plot and histogram
        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
        """
        if period not in self.return_periods:
            raise ValueError(f"Period must be one of {list(self.return_periods.keys())}")
        
        returns_data = self.return_periods[period]
        ps.qq_plot(returns_data)
        ps.histgram_plot(returns_data)

    def visualize_daily_percentage_change(self):
        """Visualize daily percentage changes using QQ plot and histogram"""
        self.visualize_percentage_change('daily')
    
    def visualize_weekly_percentage_change(self):
        """Visualize weekly percentage changes using QQ plot and histogram"""
        self.visualize_percentage_change('weekly')
    
    def visualize_monthly_percentage_change(self):
        """Visualize monthly percentage changes using QQ plot and histogram"""
        self.visualize_percentage_change('monthly')

    def visualize_yearly_percentage_change(self):
        """Visualize yearly percentage changes using QQ plot and histogram"""
        self.visualize_percentage_change('yearly')

    def find_worst_returns(self, period='daily', k=None, threshold=None):
        """
        Find worst returns for a specific period either by count (k) or threshold
        
        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            k: int, number of worst returns to find (mutually exclusive with threshold)
            threshold: float, threshold below which returns are considered "worst"
        
        Returns:
            pandas.Series: Filtered returns sorted from worst to best
        """
        if period not in self.return_periods:
            raise ValueError(f"Period must be one of {list(self.return_periods.keys())}")
            
        returns = self.return_periods[period]
        
        if k is not None and threshold is not None:
            raise ValueError("Please specify either k or threshold, not both")
        
        if k is not None:
            return returns.sort_values().head(k)
        
        if threshold is not None:
            return returns.loc[returns < threshold].sort_values()
            
        raise ValueError("Either k or threshold must be specified")
    
    def find_worst_k_days(self, k=20):
        """Find k worst daily returns"""
        return self.find_worst_returns(period='daily', k=k)
    
    def find_worst_k_weeks(self, k=3):
        """Find k worst weekly returns"""
        return self.find_worst_returns(period='weekly', k=k)
    
    def find_worst_k_months(self, k=3):
        """Find k worst monthly returns"""
        return self.find_worst_returns(period='monthly', k=k)
    
    def find_worst_k_years(self, k=3):
        """Find k worst yearly returns"""
        return self.find_worst_returns(period='yearly', k=k)

    def find_worst_weeks(self, threshold=-0.1):
        """Find weekly returns below threshold"""
        return self.find_worst_returns(period='weekly', threshold=threshold)
    
    def find_worst_months(self, threshold=-0.2):
        """Find monthly returns below threshold"""
        return self.find_worst_returns(period='monthly', threshold=threshold)

    def show_today_return(self):
        """Show recent daily returns"""
        print(self.daily_returns.tail(20))


if __name__ == "__main__":   
    ticker = "FXI"
    volatility = VolatilityFacade(ticker)
    #print(volatility.weekly_returns[-10:])
    
    # Visualize different time-frame return distributions
    #volatility.visualize_weekly_percentage_change()
    #volatility.visualize_daily_percentage_change()
    # volatility.visualize_monthly_percentage_change()
    # volatility.visualize_yearly_percentage_change()
    
    # Calculate volatility metrics
    # print(f"Daily volatility: {volatility.calculate_daily_volatility()}")
    
    # Find extreme returns
    #print(f"Worst weeks: {volatility.find_worst_k_weeks()}")
    # print(f"Worst days: {volatility.find_worst_k_days(k=5)}")
    print(f"Worst months: {volatility.find_worst_k_months(k=5)}")
    # print(f"Worst months (below -20%): {volatility.find_worst_months(threshold=-0.2)}")
    # print(f"Worst 3 months: {volatility.find_worst_k_months(k=3)}")
    # print(f"Worst 3 years: {volatility.find_worst_k_years(k=3)}")
    
    # Show recent returns
    #volatility.show_today_return()
    
    # Calculate calendar year returns
    #calendar_returns = volatility.get_calendar_year_returns(ticker)
    #print(calendar_returns)