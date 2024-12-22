"""
This script calculates volatility of price change of interested
instruments
"""

import yfinance as yf
import statsmodels.api as sm
import matplotlib.pyplot as plt

import fentu.explatoryservices.plotting_service as ps

class DailyVolatility:
    def calculate_1std_daily_volatility(self, daily_returns):
        return daily_returns['Close'].std()

class VolatilityFacade:
    """
    This class gets daily percentage change of an instrument
    """
    def __init__(self, instrument):
        self.daily_returns = self._get_returns(instrument, 1)
        self.weekly_returns = self._get_returns(instrument, 5)
        self.monthly_returns = self._get_returns(instrument, 21)
        self.yearly_returns = self._get_returns(instrument, 252)

    def _get_prices(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']
        return prices

    def _get_returns(self, instrument, period_length):
        """
        Helper method to get returns for different time periods
        Args:
            instrument: The financial instrument ticker
            period_length: Number of days for the period (1=daily, 5=weekly, 21=monthly, 252=yearly)
        """
        prices = self._get_prices(instrument)
        returns = prices.pct_change(period_length)[period_length:].reset_index()
        return returns

    def get_past_five_days(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']
        return prices.tail(5)
    
    def calculate_daily_volatility(self):
        daily_volatility_calculator = DailyVolatility()
        return daily_volatility_calculator.calculate_1std_daily_volatility(self.daily_returns)
    
    def _visualize_percentage_change(self, returns_data):
        """
        Helper method to visualize percentage changes
        Args:
            returns_data: DataFrame containing the returns data to visualize
        """
        ps.qq_plot(returns_data['Close'])
        ps.histgram_plot(returns_data)

    def visualize_daily_percentage_change(self):
        """
        Visualize daily percentage changes using QQ plot and histogram
        """
        self._visualize_percentage_change(self.daily_returns)
    
    def visualize_weekly_percentage_change(self):
        """
        Visualize weekly percentage changes using QQ plot and histogram
        """
        self._visualize_percentage_change(self.weekly_returns)
    
    def visualize_monthly_percentage_change(self):
        """
        Visualize monthly percentage changes using QQ plot and histogram
        """
        self._visualize_percentage_change(self.monthly_returns)

    def visualize_yearly_percentage_change(self):
        """
        Visualize yearly percentage changes using QQ plot and histogram
        """
        self._visualize_percentage_change(self.yearly_returns)
    
    def find_worst_k_days(self,k=20):
        return self.daily_returns.sort_values('Close').head(k)
    
    def find_worst_k_months(self,k=3):
        return self.monthly_returns.sort_values('Close').head(k)

    def find_worst_weeks(self,threshold=-0.1):
        return self.weekly_returns.loc[self.weekly_returns['Close']<threshold,:]
    
    def find_worst_months(self,threshold=-0.2):
        return self.monthly_returns.loc[self.monthly_returns['Close']<threshold,:]

    def show_today_return(self):
        print(self.daily_returns.tail(20))

if __name__ == "__main__":
    volatility = VolatilityFacade("TLT")
    prices = volatility._get_prices("TLT")
    print(prices)
    #volatilitiy.visualize_weekly_percentage_change()
    #print(volatility.find_worst_k_days(k=15))
    #volatility.show_today_return()
    #volatility.visualize_daily_percentage_change()
    #volatility.visualize_monthly_percentage_change()
    #volatility.visualize_yearly_percentage_change()
    #print(volatility.find_worst_months(threshold=-0.3))    
    #print(volatility.find_worst_k_months(k=20))