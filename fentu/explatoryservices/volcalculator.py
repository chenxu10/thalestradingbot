"""
This script calculates volatility of price change of interested
instruments
"""

import yfinance as yf
import statsmodels.api as sm
import matplotlib.pyplot as plt

from fentu.explatoryservices.plotting_service import qq_plot

class DailyVolatility:
    def calculate_1std_daily_volatility(self, daily_returns):
        return daily_returns['Close'].std()

class VolatilityFacade:
    """
    This class gets daily percentage change of an instrument
    """
    def __init__(self, instrument):
        self.daily_returns = self._get_daily_returns(instrument)

    def _get_daily_returns(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']  
        returns = prices.pct_change()[1:].reset_index()
        return returns
    
    def calculate_daily_volatility(self):
        daily_volatility_calculator = DailyVolatility()
        return daily_volatility_calculator.calculate_1std_daily_volatility(self.daily_returns)
    
    def calculate_weekly_volatility(self):
        pass

    def visualize_daily_percentage_change(self):
        """
        This function plots out a qq plot of daily percentage change
        """
        qq_plot(self.daily_returns['Close'])

if __name__ == "__main__":
    #
    tltvolatility = VolatilityFacade("TLT")
    tltvolatility.visualize_daily_percentage_change()