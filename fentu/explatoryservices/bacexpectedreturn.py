import yfinance as yf
import statsmodels.api as sm
import matplotlib.pyplot as plt

from fentu.explatoryservices.plotting_service import qq_plot



class DailyVolatility:
    def calculate_1std_daily_volatility(daily_returns):
        pass

class VolatilityFacade:
    def __init__(self, instrument):
        self.daily_returns = self._get_daily_returns(instrument)

    def _get_daily_returns(self, instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']  
        returns = prices.pct_change()[1:]
        return returns
    
    def calculate_daily_volatility(self):
        daily_volatility_calculator = DailyVolatility()
        return daily_volatility_calculator.calculate_1std_daily_volatility(self.daily_returns)
    


def prepare_price_returns(x="BAC"):
    # Download BAC data
    bac = yf.Ticker(x)
    bac_hist = bac.history(period="max")
    prices = bac_hist['Close']
    # Calculate returns  
    returns = prices.pct_change()[1:]
    return returns

if __name__ == "__main__":
    tltvolatility = VolatilityFacade("TLT")
    print(tltvolatility.daily_returns)