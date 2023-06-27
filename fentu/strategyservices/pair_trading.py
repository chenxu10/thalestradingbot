"""
Pair trading strategy for GLD and GDX
"""

import pandas as pd
import numpy as np
import yfinance as yf
import statsmodels.api as sm
import matplotlib.pyplot as plt

pd.set_option('display.max_columns', None)
# TODO:hedge ratio, exit point and entry point
# TODO:correlation of return to calculate hedge ratio
# TODO:source Edward Thorp/Dynamic Hedging/pair trading
# TODO:second order and third order

def read_in_gld_gdx_price():
    """
    Use past four years of data of price Adj close fromm 2019-06-24 to 2023-06-22
    """
    tickers = ['GLD', 'GDX']
    data = yf.download(tickers, start='2013-01-01',interval='1d')['Adj Close']
    data = data.reset_index()
    return data

def generate_train_and_test_set(data):
    """
    Sort data bt 'Date' and generate train and test set
    """
    data.set_index("Date", inplace=True)
    data.sort_index(inplace=True)
    train_set = np.arange(0, 252)
    test_set = np.arange(train_set.shape[0], data.shape[0])
    return train_set, test_set

def plot_cointegration(data):
    spread = data["GLD"] - data["GDX"]
    results = sm.OLS(spread, sm.add_constant(data["GDX"])).fit()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data["Date"], spread, label="Spread")
    ax.plot(data["Date"], results.params[0] + results.params[1] * data["GDX"], label="Cointegration Line")
    ax.legend()
    plt.title("Cointegration Plot")
    return fig

def train_test_split(data, train_frac=0.8):
    data = data.sort_values(by="Date")
    split_index = int(len(data) * train_frac)
    train_data = data[:split_index]
    test_data = data[split_index:]
    return train_data, test_data

def calculate_hedge_ratio(assetonereturn, assettworeturn):
    # Calculate the returns for both assets over the given period
    model = sm.OLS(assetonereturn, assettworeturn)
    results = model.fit()
    hedge_ratio = results.params[0]
    return hedge_ratio

def plot_spread():
    raise NotImplementedError

def calculate_spread_mean_and_std(spreaddf, train_set):
    spreadmean = np.mean(spreaddf.iloc[train_set])
    spreadstd = np.std(spreaddf.iloc[train_set])
    return spreadmean, spreadstd

def main():
    data = read_in_gld_gdx_price()
    plot_cointegration(data)

def calculate_pandl():
    raise NotImplementedError

def generate_positions_basedon_spread_zscore(data):
    data["zscore"] = (spread - spreadmean) / spreadstd
    data["positions_GLD_Long"] = 0
    data["positiions_GDX_Long"] = 0
    data["positions_GLD_Short"] = 0
    data["positions_GDX_Short"] = 0
    # Short Spread
    data.loc[data["zscore"] >= 2, ("positions_GLD_Short","positions_GDX_Short")]=[-1,1]
    # Long Spread
    data.loc[data["zscore"] <= -2, ("positions_GLD_Long","positions_GDX_Long")]=[1,-1]
    # Exit Short Spread
    data.loc[data["zscore"] <= 1, ("positions_GLD_Short","positions_GDX_Short")]=0
    # Exit Long Spread
    data.loc[data["zscore"] >= -1, ("positions_GLD_Long","positions_GDX_Long")]=0
    newdata = data.fillna(method="ffill")
    positions_Long = newdata.loc[:,("positions_GLD_Long","positions_GDX_Long")]
    positions_Short = newdata.loc[:,("positions_GLD_Short","positions_GDX_Short")]
    positions = np.array(positions_Long) + np.array(positions_Short)
    positions = pd.DataFrame(positions)   
    return positions

def generate_dailyreturns(df):
    dailyret = df.loc[:,("GLD","GDX")].pct_change() 
    return dailyret
    
if __name__ == '__main__':
    data = read_in_gld_gdx_price()
    train_set, test_set = generate_train_and_test_set(data)

    #Calculate hedge ratio
    GLD = data.loc[:,"GLD"].iloc[train_set]
    GDX = data.loc[:,"GDX"].iloc[train_set]
    hedge_ratio = calculate_hedge_ratio(GLD, GDX)

    spread = data.loc[:,"GLD"] - hedge_ratio * data.loc[:,"GDX"]
    spreadmean, spreadstd = calculate_spread_mean_and_std(spread, train_set)
    
    positions = generate_positions_basedon_spread_zscore(data)
    print(positions)
    print(positions.shift())
    #dailyret = generate_dailyreturns(data)

