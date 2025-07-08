import yfinance as yf
import requests
import pandas as pd

def download_ticker_range(ticker, start_date, end_date):
    if start_date and end_date:
        data = yf.download(ticker, start=start_date, end=end_date)["Close"]
        date_range_str = f"({start_date} to {end_date})"
    else:
        data = yf.download(ticker, period="1y")["Close"]
        date_range_str = f"({data.index[0].date()} to {data.index[-1].date()})"

    print(date_range_str)
    return data, date_range_str

# Data Access Layer - Single Responsibility: Data Retrieval
class DataRetriever:
    """Responsible for fetching price data from external sources"""
    
    def __init__(self):
        self.session = requests.Session(impersonate="chrome")
    
    def get_prices(self, instrument: str) -> pd.Series:
        """
        Fetch historical price data for a given instrument
        
        Args:
            instrument: Financial instrument ticker symbol
            
        Returns:
            pandas.Series: Historical closing prices
        """
        ticker = yf.Ticker(instrument, session=self.session)
        hist_data = ticker.history(period="max")
        return hist_data['Close']