import math
import numpy as np
from scipy.stats import norm

class OptionData:
    def __init__(self, spot_price, strike_price, time_to_expire, interest_rate, volatility):
        self.spot_price = spot_price
        self.strike_price = strike_price
        self.time_to_expire = time_to_expire  
        self.interest_rate = interest_rate
        self.volatility = volatility

class BlackScholesPricer():
    def __init__(self, opdata) -> None:
        self.opdata = opdata

    def price_empty():
        raise NotImplementedError
    
    def nostrike_change_at_expiration(self):
        return 0
    
    def how_far_asset_price_to_strike_price(self):
        ratio_of_spot_and_stock = self.opdata.spot_price / self.opdata.strike_price
        distance_between_strike_and_spot = math.log(ratio_of_spot_and_stock)
        return distance_between_strike_and_spot
    
    def what_is_expected_return_adjusted_for_riskness(self):
        return (self.opdata.interest_rate + 0.5 * (self.opdata.volatility ** 2)) * self.opdata.time_to_expire

    def calculate_d1(self):
        """
        Calculate how likely option is going to expire in the money based on current
        asset price
        """
        distance_between_strike_and_spot = self.how_far_asset_price_to_strike_price()
        expected_return_adjusted_for_riskness = self.what_is_expected_return_adjusted_for_riskness()
        expected_fluctuation_in_the_life_of_option = self.opdata.volatility * np.sqrt(self.opdata.time_to_expire)
        d1 = (distance_between_strike_and_spot + expected_return_adjusted_for_riskness) / expected_fluctuation_in_the_life_of_option
        return d1
    
    def calculate_d2(self):
        d1 = self.calculate_d1()
        d2 = d1 - self.opdata.volatility * np.sqrt(self.opdata.time_to_expire)
        return d2
    
    def calculate_option_price_given(self, d1, d2):
        S = self.opdata.spot_price
        K = self.opdata.strike_price
        r = self.opdata.interest_rate
        T = self.opdata.time_to_expire
        expected_stockpricewhenexpired_income = S*norm.cdf(d1)
        expected_discountedstrikeprice_expense = K*np.exp(-r*T)*norm.cdf(d2)
        price = expected_stockpricewhenexpired_income - expected_discountedstrikeprice_expense
        return price

    def option_pricing_formula(self, type="call"):
        if type == "call":
            d1 = self.calculate_d1()
            d2 = self.calculate_d2()
            call_price = self.calculate_option_price_given(d1, d2)
            return call_price