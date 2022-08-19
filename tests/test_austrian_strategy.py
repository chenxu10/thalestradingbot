"""
TODO: able to compare with two portfolios
TODO: start date and end date
TODO: simulate continouous rebalancing
TODO: visualize the performance
TODO: Input
Download or put option price/
TODO: Get free historical option prices
"""
import os
import sys
from datetime import datetime
import backtrader as bt

class SmaCross(bt.SignalStrategy):
    def __init__(self):
        sma1, sma2 = bt.ind.SMA(period=10), bt.ind.SMA(period=30)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)


if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(9999.0)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # cerebro.addstrategy(SmaCross)
    cerebro.run()
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    print(modpath)
    datapath = os.path.join(modpath, '../../datas/orcl-1995-2014.txt')
    print(datapath)


# print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
# data0 = bt.feeds.YahooFinanceData(
#     dataname='MSFT', 
#     fromdate=datetime(2011, 1, 1),
#     todate=datetime(2012, 12, 31))

# cerebro.adddata(data0)
# cerebro.run()
# cerebro.plot()