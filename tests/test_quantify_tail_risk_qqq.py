



class TailHedger:
    def __init__(self, ticker, volume, market_price) -> None:
        self.ticker = ticker
        self.volume = volume
        self.market_price = market_price

    def output_ticker(self):
        return 'qqq'

def to_tail_hedger(ticker, volume, market_price):
    return TailHedger('tqqq',1,)

def main():
    ticker = 'tqqq'
    volume = 1
    market_price = 51.65
    assert to_tail_hedger(ticker, volume, market_price).output_ticker() == 'qqq'


if __name__ == "__main__":
    main()