from abc import ABC, abstractmethod
from fentu.strategyservices.black_scholes_model import OptionData, BlackScholesPricer
import matplotlib.pyplot as plt

class Strategy(ABC):
    def __init__(self):
        self.long_strike = float(input("input your long call strike price "))
        self.short_strike = float(input("input your short call strike price "))
        self.long_premium = float(input("input your long call premium price "))
        self.short_premium = float(input("input your short call premium price "))

    def before_trade(self):
        pass

    def execute(self):
        pass

    def after_trader(self):
        pass

class CallSpreadStrategy(Strategy):
    def __init__(self):
        self.long_strike = float(input("input your long call strike price "))
        self.short_strike = float(input("input your short call strike price "))
        self.long_premium = float(input("input your long call premium price "))
        self.short_premium = float(input("input your short call premium price "))

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
        choose_strategy = input("""
            Do you want to apply an attack, defense or balanced call spread?
            'a' for attack
            'd' for defense
            'b' for balance""")
        exp_max_profit, exp_max_loss, breakeven_point, risk_and_reward_ratio = self.callspread_pandl_plot(
            self.long_strike, self.short_strike, self.long_premium, self.short_premium
        )
        before_trade_metrics["expected_max_profit"] = exp_max_profit
        before_trade_metrics["expected_max_loss"] = exp_max_loss
        before_trade_metrics["breakeven_point"] = breakeven_point
        before_trade_metrics["risk_and_reward_ratio"] = risk_and_reward_ratio
        return before_trade_metrics
    
    def calculate_pnl_base_with(
            self,  
            short_call_price_given_stock_price,
            long_call_price_given_stock_price,
            net_preimum=2):
        return short_call_price_given_stock_price - \
            long_call_price_given_stock_price + net_preimum

    def before_trade_plot(self):
        min_stock = int(input("Please input your minimum stock price that are likely to happen "))
        max_stock = int(input("Please input your maximum stock price that are likely to happen "))
        time_to_expire = int(input("Please input your time to expire "))
        interest_rate = float(input("Please input your current interest rate"))
        volatility = float(input("Please input your implied volatility "))
        net_preimum = float(input("Please input your net credit or net debit you received "))
        return net_preimum
        # stock_range = range(min_stock, max_stock, 1)
        # pnl_base = []
        # for s in stock_range:
        #     short_call_opdata  = OptionData(s,self.short_strike,time_to_expire,interest_rate,volatility)
        #     short_call_bspricer = BlackScholesPricer(short_call_opdata)
        #     short_call_price_in_stockprice = short_call_bspricer.option_pricing_formula("call")
        #     pnl_base.append(short_call_price_in_stockprice)
            # long_call_opdata  = OptionData(s,self.long_strike,time_to_expire,interest_rate,volatility)
            # long_call_bspricer = BlackScholesPricer(long_call_opdata)
            # long_call_price_in_stockprice = long_call_bspricer.option_pricing_formula("call")
            # pnl_base.append(self.calculate_pnl_base_with(short_call_price_in_stockprice,
            #                                              long_call_price_in_stockprice,
            #                                              net_preimum))
        
        # fig = plt.plot(stock_range, pnl_base)
        # plt.show()
        # return fig
    
if __name__ == "__main__":
    call_spread_strategy = CallSpreadStrategy()
    call_spread_strategy.before_trade_plot()