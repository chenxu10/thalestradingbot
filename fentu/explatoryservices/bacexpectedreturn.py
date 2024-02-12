import yfinance as yf
import statsmodels.api as sm
import matplotlib.pyplot as plt

from fentu.explatoryservices.plotting_service import qq_plot


class VolatilityFacade:
    def __init__(self, instrument):
        self.daily_returns = self._get_daily_returns(instrument)

    def _get_daily_returns(instrument):
        instrument = yf.Ticker(instrument)
        instru_hist = instrument.history(period="max")
        prices = instru_hist['Close']  
        returns = prices.pct_change()[1:]
        return returns


def prepare_price_returns(x="BAC"):
    # Download BAC data
    bac = yf.Ticker(x)
    bac_hist = bac.history(period="max")
    prices = bac_hist['Close']
    # Calculate returns  
    returns = prices.pct_change()[1:]
    return returns

if __name__ == "__main__":
    x = "TLT"
    returns = prepare_price_returns(x)
    print(returns)
    qq_plot(returns)
    plt.savefig("figures/qqplot_{}.png".format(x))
    plt.show()