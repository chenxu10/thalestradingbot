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
        self.weekly_returns = self._get_weekly_returns(instrument)
        self.monthly_returns = self._get_monthly_returns(instrument)

    def _get_daily_returns(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']  
        returns = prices.pct_change()[1:].reset_index()
        return returns

    def _get_weekly_returns(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']  
        weekly_returns = prices.pct_change(5)[5:].reset_index()
        return weekly_returns
    
    def _get_monthly_returns(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']  
        weekly_returns = prices.pct_change(21)[21:].reset_index()
        return weekly_returns

    def get_past_five_days(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']
        return prices.tail(5)
    
    def calculate_daily_volatility(self):
        daily_volatility_calculator = DailyVolatility()
        return daily_volatility_calculator.calculate_1std_daily_volatility(self.daily_returns)
    
    def visualize_weekly_percentage_change(self):
        """
        This function plots out a qq plot of daily percentage change
        """
        ps.qq_plot(self.weekly_returns['Close'])
        ps.histgram_plot(self.weekly_returns)
    
    def visualize_monthly_percentage_change(self):
        """
        This function plots out a qq plot of daily percentage change
        """
        ps.qq_plot(self.monthly_returns['Close'])
        ps.histgram_plot(self.monthly_returns)

    def _get_monthly_returns(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']  
        monthly_returns = prices.pct_change(21)[21:].reset_index()
        return monthly_returns

    def visualize_daily_percentage_change(self):
        """
        This function plots out a qq plot of daily percentage change
        """
        ps.qq_plot(self.daily_returns['Close'])
        ps.histgram_plot(self.daily_returns)
    
    def find_worst_k_days(self,k=20):
        return self.daily_returns.sort_values('Close').head(k)
    
    def find_worst_k_months(self,k=3):
        return self.monthly_returns.sort_values('Close').head(k)

    def find_worst_weeks(self,threshold=-0.1):
        return self.weekly_returns.loc[self.weekly_returns['Close']<threshold,:]
    
    def find_worst_months(self,threshold=-0.2):
        return self.monthly_returns.loc[self.monthly_returns['Close']<threshold,:]

    def show_today_return(self):
        print(self.daily_returns.tail(10))

if __name__ == "__main__":
    volatility = VolatilityFacade("FXI")
    #volatility.show_today_return()
    #print(volatility. et_past_five_days("FXI"))
    volatility.visualize_daily_percentage_change()
    #volatility.visualize_weekly_percentage_change()
    #volatility.visualize_monthly_percentage_change()
    #print(volatility.find_worst_months(threshold=-0.3))
    #print(volatility.find_worst_k_months(k=20))