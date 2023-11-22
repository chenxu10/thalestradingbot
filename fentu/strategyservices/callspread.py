from abc import ABC, abstractmethod


def before_cs_trade():
    input_strategy = input("""Why do you want to express your bullish view on it?
              Do you want to express this view in an attacking way, defensive way or balanced way?
              'a' for attackive
              'd' for defensive
              'b' for balanced
              """)
    if input_strategy == "a":
        s = "attactive"
    return s


class Strategy(ABC):
    def before_trade(self):
        pass

    def execute(self):
        pass

    def after_trader(self):
        pass


class CallSpreadStrategy(Strategy):
    def before_trade(self):
        input_strategy = input("""Why do you want to express your bullish view on it?
            Do you want to express this view in an attacking way, defensive way or balanced way?
            'a' for attackive
            'd' for defensive
            'b' for balanced
            """)
        if input_strategy == "a":
            s = "attactive"
            input("""
            Do not make your strike price difference too small so that you
            will not cover the loss of spread.
            You choose attack so make sure your midpoint of two strike difference
            is larger than the current spot price.    
            """)
            long_strike = float(input("buy a long strike at ?"))
            short_strike = float(input("buy a short strike at ?"))
        return s, long_strike, short_strike
