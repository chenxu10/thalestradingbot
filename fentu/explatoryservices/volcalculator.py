"""
This script calculates volatility and return metrics for financial instruments
"""

import yfinance as yf
import pandas as pd
import fentu.explatoryservices.plotting_service as ps

class ReturnCalculator:
    """Base class for calculating different types of returns"""
    def __init__(self, prices):
        self.prices = prices

    def calculate_period_returns(self, period_length):
        """Calculate returns for a given period length"""
        return self.prices.pct_change(period_length)[period_length:]

    def calculate_calendar_returns(self):
        """Calculate returns for each calendar year"""
        yearly_returns = []
        years = self.prices.index.year.unique()
        
        for year in years:
            year_data = self.prices[self.prices.index.year == year]
            if not year_data.empty:
                year_return = (year_data.iloc[-1] - year_data.iloc[0]) / year_data.iloc[0]
                yearly_returns.append({
                    'Date': pd.Timestamp(f'{year}-12-31'),
                    'Close': year_return
                })
        
        calendar_returns = pd.DataFrame(yearly_returns)
        return calendar_returns.sort_values('Date', ascending=False)

class MarketDataFetcher:
    """Handles fetching market data from external sources"""
    @staticmethod
    def get_historical_prices(ticker):
        """Fetch historical price data for a given ticker"""
        instrument = yf.Ticker(ticker)
        return instrument.history(period="max")['Close']

class VolatilityAnalyzer:
    """Analyzes volatility and extreme events in return data"""
    def __init__(self, returns):
        self.returns = returns

    def calculate_volatility(self):
        """Calculate 1-standard deviation volatility"""
        return self.returns.std()

    def find_worst_events(self, k=None, threshold=None):
        """Find worst events either by count or threshold"""
        if k is not None:
            return self.returns.sort_values().head(k)
        if threshold is not None:
            return self.returns[self.returns < threshold]

class MarketAnalyzer:
    """Main class for analyzing market data and returns"""
    def __init__(self, ticker):
        self.ticker = ticker
        self.prices = MarketDataFetcher.get_historical_prices(ticker)
        self.calculator = ReturnCalculator(self.prices)
        
        # Calculate different period returns
        self.daily_returns = self.calculator.calculate_period_returns(1)
        self.weekly_returns = self.calculator.calculate_period_returns(5)
        self.monthly_returns = self.calculator.calculate_period_returns(21)
        self.yearly_returns = self.calculator.calculate_period_returns(252)

    def get_calendar_year_returns(self):
        """Get returns for each calendar year"""
        return self.calculator.calculate_calendar_returns()

    def get_recent_prices(self, days=5):
        """Get most recent price data"""
        return self.prices.tail(days)

    def visualize_returns(self, period='daily'):
        """Visualize return distribution for specified period"""
        returns_map = {
            'daily': self.daily_returns,
            'weekly': self.weekly_returns,
            'monthly': self.monthly_returns,
            'yearly': self.yearly_returns
        }
        returns_data = returns_map.get(period)
        if returns_data is not None:
            ps.qq_plot(returns_data)
            ps.histgram_plot(returns_data)

    def analyze_extreme_events(self, period='daily', k=None, threshold=None):
        """Analyze extreme events in returns"""
        returns_map = {
            'daily': self.daily_returns,
            'weekly': self.weekly_returns,
            'monthly': self.monthly_returns
        }
        returns_data = returns_map.get(period)
        if returns_data is not None:
            analyzer = VolatilityAnalyzer(returns_data)
            return analyzer.find_worst_events(k=k, threshold=threshold)

if __name__ == "__main__":
    analyzer = MarketAnalyzer("QQQ")
    
    # Example usage
    analyzer.visualize_returns('weekly')
    calendar_returns = analyzer.get_calendar_year_returns()
    print(calendar_returns)