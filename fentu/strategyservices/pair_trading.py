# read in GLD and GDX price

import yfinance as yf

# TODO:hedge ratio, exit point and entry point
# TODO:correlation of return to calculate hedge ratio
# TODO:source Edward Thorp/Dynamic Hedging/pair trading
# TODO:second order and third order

def read_in_gld_gdx_price():
    # read in price from yahoo finance
    tickers = ['GLD', 'GDX']
    # Why we are using adj close price?
    data = yf.download(tickers, period='4y', interval='1d')['Adj Close']
    return data

def main():
    data = read_in_gld_gdx_price()
    print(data.pct_change())

if __name__ == '__main__':
    main()