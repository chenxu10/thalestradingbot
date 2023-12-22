from abc import ABC, abstractmethod
import matplotlib.pyplot as plt

class Strategy(ABC):
    def before_trade(self):
        pass

    def execute(self):
        pass

    def after_trader(self):
        pass

class CallSpreadStrategy(Strategy):
    def callspread_pandl_plot(self, long_call_strike, short_call_strike, long_call_premium, short_call_premium):
        comission = 0.5
        difference_between_strike = short_call_strike - long_call_strike
        netcost_of_spread = long_call_premium - short_call_premium + comission

        exp_max_profit = difference_between_strike - netcost_of_spread
        exp_max_loss = netcost_of_spread
        breakeven_point = long_call_strike + comission + exp_max_loss
        risk_and_reward_ratio = exp_max_loss / exp_max_profit
        return exp_max_profit, exp_max_loss, breakeven_point, risk_and_reward_ratio

    def before_trade_metrics(self):
        before_trade_metrics = {}
        input_strategy = input("""
            Why do you want to express your bullish view on it?
            Do you want to express this view in an attacking way, defensive way or balanced way?
            'a' for attackive
            'd' for defensive
            'b' for balanced
            """)
        if input_strategy == "a":
            input("""
            Do not make your strike price difference too small so that you
            will not cover the loss of spread.
            You choose attack so make sure your midpoint of two strike difference
            is larger than the current spot price.    
            """)
            long_strike = float(input("input your long call strike price"))
            short_strike = float(input("input your short call strike price"))
            long_premium = float(input("input your long call premium price"))
            short_premium = float(input("input your short call premium price"))
            
            exp_max_profit, exp_max_loss, breakeven_point, risk_and_reward_ratio = self.callspread_pandl_plot(
                long_strike, short_strike, long_premium, short_premium
            )
            before_trade_metrics["expected_max_profit"] = exp_max_profit
            before_trade_metrics["expected_max_loss"] = exp_max_loss
            before_trade_metrics["breakeven_point"] = breakeven_point
            before_trade_metrics["risk_and_reward_ratio"] = risk_and_reward_ratio
        return before_trade_metrics
    
    def before_etrade_plot(self):
        min_stock = int(input("Please input your minimum stock price "))
        max_stock = int(input("Please input your maximum stock price "))
        stock_range = range(min_stock, max_stock)
        pnl_base = range(100, 115)
        fig = plt.plot(stock_range, pnl_base)
        return fig

if __name__ == "__main__":
    call_spread_strategy = CallSpreadStrategy()
    before_trade_metrics = call_spread_strategy.before_trade()
    print(before_trade_metrics)