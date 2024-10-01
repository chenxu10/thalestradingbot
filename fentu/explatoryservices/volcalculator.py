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
        self.daily_returns = self._get_daily_returns(instrument)

    def _get_daily_returns(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']  
        returns = prices.pct_change()[1:].reset_index()
        return returns
    
    def get_past_five_days(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']
        return prices.tail(5)
    
    def calculate_daily_volatility(self):
        daily_volatility_calculator = DailyVolatility()
        return daily_volatility_calculator.calculate_1std_daily_volatility(self.daily_returns)
    
    def calculate_weekly_volatility(self):
        pass

    def visualize_daily_percentage_change(self):
        """
        This function plots out a qq plot of daily percentage change
        """
        ps.qq_plot(self.daily_returns['Close'])
        ps.histgram_plot(self.daily_returns)
        
    def show_today_return(self):
        print(self.daily_returns.tail(10))
        print(self.daily_returns.tail(1))

if __name__ == "__main__":
    volatility = VolatilityFacade("FXI")
    volatility.visualize_daily_percentage_change()
    volatility.show_today_return()
    print(volatility.get_past_five_days("FXI"))