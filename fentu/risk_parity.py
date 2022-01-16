import webbrowser
from datetime import datetime, date, timedelta
import math
import numpy as np
import time
import sys
import requests
from pandas_datareader import data
from datetime import date

NUM_TRADING_DAYS_PER_YEAR = 252

def get_volatility_and_performance(symbol,start,end, window_size):
    lines = data.DataReader(symbol,
        start=start, 
        end=end,
        data_source='yahoo')

    prices = list(lines['Close'])
    prices.reverse()

    volatilities_in_window = []

    for i in range(len(prices)-1):
        volatilities_in_window.append(math.log(prices[i] / prices[i+1]))

    return np.std(volatilities_in_window, ddof = 1) * np.sqrt(NUM_TRADING_DAYS_PER_YEAR), prices[0] / prices[len(prices)-1] - 1.0

def open_m1finance(brokerage="m1"):
    if brokerage == "m1":
        webbrowser.open('https://dashboard.m1finance.com/d/invest/portfolio', new=2)
    return


def calculate_allocation(symbols):
    window_size = 30
    date_format = "%Y-%m-%d"
    end_timestamp = date.today()
    start_timestamp = end_timestamp - timedelta(days=window_size)
    
    volatilities = []
    performances = []
    sum_inverse_volatility = 0.0

    for symbol in symbols:
        volatility, performance = get_volatility_and_performance(symbol,start_timestamp, end_timestamp, window_size=window_size)
        sum_inverse_volatility += 1 / volatility
        volatilities.append(volatility)
        performances.append(performance)
    

    print ("Portfolio: {}, as of {} (window size is {} days)".format(str(symbols), date.today().strftime('%Y-%m-%d'), window_size))
    for i in range(len(symbols)):
        print ('{} allocation ratio: {:.2f}% (anualized volatility: {:.2f}%, performance: {:.2f}%)'.format(symbols[i], float(100 / (volatilities[i] * sum_inverse_volatility)), float(volatilities[i] * 100), float(performances[i] * 100)))

if __name__ == "__main__":
    symbols = ['UPRO', 'TMF']      
    calculate_allocation(symbols)
    open_m1finance()

