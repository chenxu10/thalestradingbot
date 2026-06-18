"""
This script calculates volatility and return metrics for financial instruments.

Topology Diagram (ASCII)
========================

 External Dependencies
 +---------------------------------------------------------------------------+
 | yfinance | pandas | numpy | scipy.stats(norm,t) | curl_cffi.requests     |
 | matplotlib.pyplot | plotting_service (ps) | see_power_law (spl)          |
 +---------------------------------------------------------------------------+
      |            |          |            |               |
      | prices     | data     | tails/log  | (unused)      | plotting
      v            v          v            v               v

 Class Hierarchy & Relationships
 +-------------------------------+
 |   VolatilityCalculator        |  <<abstract base>>
 |   calculate_volatility()      |  -> NotImplementedError
 +---------------+---------------+
                 |  inherits
                 v
 +-------------------------------+
 | StandardDeviationVolatility   |
 | calculate_volatility()        |  -> returns_data.std()
 +---------------+---------------+
                 |  used-by (Strategy pattern)
                 v
 +-------------------------------+
 | DailyVolatility               |  <<context>>
 | - calculator: VolatilityCalc  |
 | calculate_1std_daily_vol()    |
 +---------------+---------------+
                 |  composition
                 v
 +---------------------------------------------------------------------------+
 |                          VolatilityFacade                                 |
 |  instrument | start_date | end_date                                       |
 |  return_periods = {daily, weekly, monthly, yearly}                       |
 |                                                                           |
 |  [Data Acquisition]                    [Volatility]                       |
 |  _get_prices() ----> yf.Ticker          calculate_daily_volatility()      |
 |        |                 + curl_cffi            |                         |
 |        |                 session                v                         |
 |        +---> _get_returns() ----> DailyVolatility                          |
 |                  |  pct_change(period)                                     |
 |                  v                                                         |
 |            daily/weekly/monthly/yearly returns ----+                       |
 |                                                    |                     |
 |  [Calendar Returns]                                |                     |
 |  get_calendar_year_returns()                       |                     |
 |     +-> _get_prices()                              |                     |
 |     +-> calculate_yearly_return_list()             |                     |
 |                                                    |                     |
 |  [Extreme Returns]  <------------------------------+                     |
 |  find_negative_extreme_returns() (k | threshold)                         |
 |  find_positive_extreme_returns() (k | threshold)                         |
 |                                                                           |
 |  [Visualization: data-view-model pattern]                                 |
 |  visualize_percentage_change(period, tail_percent)                       |
 |     |                                                                     |
 |     +-> _prepare_percentage_change_data()  <<data prep>>                  |
 |     |       +-> return_periods, numpy (left/right tails)                  |
 |     |       +-> returns dict {returns, tails, period, instrument}         |
 |     |                                                                     |
 |     +-> _plot_percentage_change()  <<visualization>>                      |
 |             +-> ps.qq_plot()              (axes[0,0])                     |
 |             +-> ps.histgram_plot()        (axes[0,1])                     |
 |             +-> spl.plot_loglog_with_fit  (axes[1,0/1] - tail fits)       |
 |             +-> matplotlib subplots (2x2) + suptitle                      |
 |                                                                           |
 |  [Reporting]                                                              |
 |  show_today_return()                       -> daily_returns.tail(20)      |
 |  get_past_week_price_and_log_returns()     -> _get_prices + np.log       |
 |  get_past_year_price_and_log_returns()     -> _get_prices + np.log       |
 +---------------------------------------------------------------------------+

 Entry Point
 +---------------------------------------------------------------------------+
 | __main__: VolatilityFacade("ILS")                                         |
 |   -> get_past_week_price_and_log_returns()                                |
 |   -> calculate_daily_volatility()                                         |
 |   -> find_negative/positive_extreme_returns() (threshold=+-0.2)           |
 +---------------------------------------------------------------------------+
"""

import yfinance as yf
import pandas as pd
pd.set_option('display.max_rows', None)

import fentu.explatoryservices.plotting_service as ps
import fentu.explatoryservices.see_power_law as spl
import matplotlib.pyplot as plt
import numpy as np
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
    def __init__(self, instrument, start_date=None, end_date=None):
        self.instrument = instrument
        self.start_date = start_date
        self.end_date = end_date
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

        if prices.index.tz is not None:
            prices.index = prices.index.tz_localize(None)

        if self.start_date is not None:
            prices = prices[prices.index >= pd.Timestamp(self.start_date)]
        if self.end_date is not None:
            prices = prices[prices.index <= pd.Timestamp(self.end_date)]

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
        Helper method to get log returns for different time periods
        Args:
            instrument: The financial instrument ticker
            period_length: Number of days for the period (1=daily, 5=weekly, 21=monthly, 252=yearly)
        """
        prices = self._get_prices(instrument)
        returns = np.log(prices / prices.shift(period_length))[period_length:]
        return returns
    
    def calculate_daily_volatility(self):
        return self.daily_volatility.calculate_1std_daily_volatility(self.daily_returns)
    
    def _prepare_percentage_change_data(self, period='daily'):
        """
        Prepare data for percentage change visualization.

        Returns:
            dict with 'returns', 'tails', 'period', 'instrument'
        """
        if period not in self.return_periods:
            raise ValueError(f"Period must be one of {list(self.return_periods.keys())}")

        returns_data = self.return_periods[period]
        left_tail = np.abs(returns_data[returns_data < 0].values)
        right_tail = returns_data[returns_data > 0].values

        return {
            'returns': returns_data,
            'tails': [
                {'data': left_tail, 'x_min': np.min(left_tail) if len(left_tail) > 0 else None,
                 'title': 'Left Tail (Negative Returns)'},
                {'data': right_tail, 'x_min': np.min(right_tail) if len(right_tail) > 0 else None,
                 'title': 'Right Tail (Positive Returns)'},
            ],
            'period': period,
            'instrument': self.instrument,
        }

    def _plot_percentage_change(self, data, tail_percent):
        """
        Plot percentage change visualizations.

        Args:
            data: dict from _prepare_percentage_change_data
            tail_percent: Fraction of extreme tail to fit for alpha estimation
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        ps.qq_plot(data['returns'], ax=axes[0, 0], show=False)
        ps.histgram_plot(data['returns'], ax=axes[0, 1], show=False)

        tail_axes = [axes[1, 0], axes[1, 1]]
        for tail, ax in zip(data['tails'], tail_axes):
            if tail['x_min'] is not None:
                spl.plot_loglog_with_fit(
                    tail['data'], tail['x_min'], ax=ax,
                    title=tail['title'],
                    tail_percent=tail_percent
                )

        fig.suptitle(f"{data['instrument']} {data['period'].capitalize()} Returns")
        plt.tight_layout()
        plt.show()

    def visualize_percentage_change(self, period='daily', tail_percent=0.10):
        """
        Visualize percentage changes for a specific period using QQ plot, histogram,
        and log-log plots for left and right tail analysis.

        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            tail_percent: Fraction of extreme tail to fit for alpha estimation (default 0.1)
        """
        data = self._prepare_percentage_change_data(period)
        self._plot_percentage_change(data, tail_percent)

    def _find_extreme_returns(self, period='daily', k=None, threshold=None, side='negative'):
        """
        Find extreme returns for a specific period either by count (k) or threshold.

        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            k: int, number of extreme returns to find (mutually exclusive with threshold)
            threshold: float, threshold beyond which returns are considered extreme
            side: str, 'negative' (worst, sorted ascending) or 'positive' (best, sorted descending)

        Returns:
            pandas.Series: Filtered returns sorted from most extreme to least extreme
        """
        if period not in self.return_periods:
            raise ValueError(f"Period must be one of {list(self.return_periods.keys())}")
        returns = self.return_periods[period]
        ascending = (side == 'negative')
        compare = (lambda r, t: r < t) if side == 'negative' else (lambda r, t: r > t)
        if k is not None:
            return returns.sort_values(ascending=ascending).head(k)
        if threshold is not None:
            return returns.loc[compare(returns, threshold)].sort_values(ascending=ascending)
        raise ValueError("Either k or threshold must be specified")

    def find_negative_extreme_returns(self, period='daily', k=None, threshold=None):
        """
        Find negative extreme returns for a specific period either by count (k) or threshold

        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            k: int, number of worst returns to find (mutually exclusive with threshold)
            threshold: float, threshold below which returns are considered "worst"

        Returns:
            pandas.Series: Filtered returns sorted from worst to best
        """
        return self._find_extreme_returns(period, k, threshold, side='negative')

    def find_positive_extreme_returns(self, period='daily', k=None, threshold=None):
        """
        Find positive extreme returns for a specific period either by count (k) or threshold

        Args:
            period: str, one of 'daily', 'weekly', 'monthly', 'yearly'
            k: int, number of best returns to find (mutually exclusive with threshold)
            threshold: float, threshold above which returns are considered "best"

        Returns:
            pandas.Series: Filtered returns sorted from best to worst
        """
        return self._find_extreme_returns(period, k, threshold, side='positive')

    def show_today_return(self):
        """Show recent daily returns"""
        print(self.daily_returns.tail(20))

    def get_past_week_price_and_log_returns(self):
        """Get most recent 5 trading days prices with daily log returns"""
        prices = self._get_prices(self.instrument).tail(5)
        log_returns = np.log(prices / prices.shift(1))
        return pd.DataFrame({'price': prices, 'log_return': log_returns})

    def get_past_year_price_and_log_returns(self):
        """Get most recent ~252 trading days prices with daily log returns"""
        prices = self._get_prices(self.instrument).tail(252)
        log_returns = np.log(prices / prices.shift(1))
        return pd.DataFrame({'price': prices, 'log_return': log_returns})

if __name__ == "__main__":
    volatility = VolatilityFacade("ILS")
    # Visualize different time-frame return distributions
    # volatility.visualize_percentage_change('weekly')
    print(volatility.get_past_week_price_and_log_returns())

    # Calculate volatility metrics
    print(f"Daily volatility: {volatility.calculate_daily_volatility()}")

    # Find extreme returns
    #print(f"Worst months: {volatility.find_negative_extreme_returns('monthly', k=3)}")
    print(f"Worst days (below -20%): {volatility.find_negative_extreme_returns('daily', threshold=-0.2)}")
    print(f"Worst months (below -20%): {volatility.find_negative_extreme_returns('monthly', threshold=-0.2)}")
    print(f"Best days (above +20%): {volatility.find_positive_extreme_returns('daily', threshold=0.2)}")
    print(f"Best months (above +20%): {volatility.find_positive_extreme_returns('monthly', threshold=0.2)}")

    # Calculate calendar year returns
    #calendar_returns = volatility.get_calendar_year_returns(ticker)
    
    


