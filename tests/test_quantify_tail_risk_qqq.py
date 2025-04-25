



class TailHedger:
    def __init__(self, ticker, volume, market_price) -> None:
        self.ticker = ticker
        self.volume = volume
        self.market_price = market_price
        self.hedge_ratio = 3

    def output_ticker(self):
        return 'qqq'

    def output_volume(self):
        return round(self.volume * self.hedge_ratio)
    
    def output_strike_price(self):
        return 45
   

def to_tail_hedger(ticker, volume, market_price):
    return TailHedger(ticker, volume, market_price)

def main():
    ticker = 'tqqq'
    volume = 1
    market_price = 51.65

    TailHedger = to_tail_hedger(ticker, volume, market_price)
    
    assert TailHedger.output_ticker() == 'qqq'
    assert TailHedger.output_volume() == 3
    assert TailHedger.output_strike_price() == 45



if __name__ == "__main__":
    main()