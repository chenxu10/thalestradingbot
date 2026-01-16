"""
This script calculates volatility and return metrics for financial instruments
"""

import yfinance as yf
import pandas as pd
pd.set_option('display.max_rows', None)

import fentu.explatoryservices.plotting_service as ps
import fentu.explatoryservices.see_power_law as spl
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm, t
from curl_cffi import requests

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
        session = requests.Session(impersonate="chrome")
        instrument = yf.Ticker(instrument, session=session)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']
        return prices

    def calculate_yearly_return_list(self, prices, yearly_returns_list, years):
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
        return yearly_returns_list
    
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
        
        yearly_returns_list = self.calculate_yearly_return_list(
            prices, yearly_returns_list, years)
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
    
    def _prepare_percentage_change_data(self, period='daily'):
        """
        Prepare data for percentage change visualization.

        Returns:
            dict with 'returns', 'left_tail', 'right_tail', 'period', 'instrument'
        """
        if period not in self.return_periods:
            raise ValueError(f"Period must be one of {list(self.return_periods.keys())}")

        returns_data = self.return_periods[period]
        return {
            'returns': returns_data,
            'left_tail': np.abs(returns_data[returns_data < 0].values),
            'right_tail': returns_data[returns_data > 0].values,
            'period': period,
            'instrument': self.instrument,
        }

    def visualize_percentage_change(self, period='daily', tail_percent=0.10):
        """
        Visualize percentage changes for a specific period using QQ plot, histogram,
        and log-log plots for left and right tail analysis.
        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            tail_percent: Fraction of extreme tail to fit for alpha estimation (default 0.2)
                          Based on extreme value theory, only the tail exhibits power law behavior
        """
        data = self._prepare_percentage_change_data(period)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        ps.qq_plot(data['returns'], ax=axes[0, 0], show=False)
        ps.histgram_plot(data['returns'], ax=axes[0, 1], show=False)

        tails = [
            (data['left_tail'], axes[1, 0], 'Left Tail (Negative Returns)'),
            (data['right_tail'], axes[1, 1], 'Right Tail (Positive Returns)'),
        ]

        for tail_data, ax, title in tails:
            if len(tail_data) > 0:
                x_min = np.min(tail_data)
                spl.plot_loglog_with_fit(
                    tail_data, x_min, ax=ax,
                    title=title,
                    tail_percent=tail_percent
                )

        fig.suptitle(f"{data['instrument']} {data['period'].capitalize()} Returns")
        plt.tight_layout()
        plt.show()

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
        returns = self.return_periods[period]

        if period not in self.return_periods:
            raise ValueError(f"Period must be one of {list(self.return_periods.keys())}")
        
        if k is not None:
            return returns.sort_values().head(k)
        
        if threshold is not None:
            return returns.loc[returns < threshold].sort_values()
            
        raise ValueError("Either k or threshold must be specified")

    def show_today_return(self):
        """Show recent daily returns"""
        print(self.daily_returns.tail(20))

if __name__ == "__main__":
    volatility = VolatilityFacade("IAU")
    # Visualize different time-frame return distributions
    volatility.visualize_percentage_change('weekly')
    #volatility.visualize_percentage_change('daily')
    #volatility.visualize_percentage_change('yearly')
    #print(volatility.yearly_returns)

    # Calculate volatility metrics
    # print(f"Daily volatility: {volatility.calculate_daily_volatility()}")

    # Find extreme returns
    #print(f"Worst weeks: {volatility.find_worst_returns('weekly', k=3)}")
    #print(f"Worst days: {volatility.find_worst_returns('daily', k=30)}")
    #print(f"Worst months: {volatility.find_worst_returns('monthly', k=30)}")
    # print(f"Worst months (below -20%): {volatility.find_worst_returns('monthly', threshold=-0.2)}")

    # Show recent returns
    #volatility.show_today_return()

    # Calculate calendar year returns
    #calendar_returns = volatility.get_calendar_year_returns(ticker)
    # calendar_returns['TLT 3X'] = calendar_returns['Close'] * 3
    # print(calendar_returns)
    


