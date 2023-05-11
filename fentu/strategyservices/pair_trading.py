# read in GLD and GDX price

import yfinance as yf
import pandas as pd
import statsmodels.api as sm
import numpy as np
import matplotlib.pyplot as plt

# TODO:hedge ratio, exit point and entry point
# TODO:correlation of return to calculate hedge ratio
# TODO:source Edward Thorp/Dynamic Hedging/pair trading
# TODO:second order and third order

def read_in_gld_gdx_price():
    # read in price from yahoo finance
    tickers = ['GLD', 'GDX']
    # Why we are using adj close price?
    data = yf.download(tickers, period='4y', interval='1d')['Adj Close']
    data = data.reset_index()
    return data

def plot_cointegration(data):
    spread = data["GLD"] - data["GDX"]
    results = sm.OLS(spread, sm.add_constant(data["GDX"])).fit()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data["Date"], spread, label="Spread")
    ax.plot(data["Date"], results.params[0] + results.params[1] * data["GDX"], label="Cointegration Line")
    ax.legend()
    plt.title("Cointegration Plot")
    return fig

def main():
    data = read_in_gld_gdx_price()
    plot_cointegration(data)

if __name__ == '__main__':
    main()