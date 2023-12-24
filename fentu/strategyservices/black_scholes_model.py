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
    def price_empty():
        raise NotImplementedError

    def black_scholes_model_pricing(self, opdata):
        pass
    
    def nostrike_change_at_expiration(self, opdata):
        return 0
    
    def how_far_asset_price_to_strike_price(self, opdata):
        ratio_of_spot_and_stock = opdata.spot_price / opdata.strike_price
        distance_between_strike_and_spot = math.log(ratio_of_spot_and_stock)
        return distance_between_strike_and_spot
    
    def what_is_expected_return_adjusted_for_riskness(self, opdata):
        return (opdata.interest_rate + 0.5 * (opdata.volatility ** 2)) * opdata.time_to_expire

    def calculate_d1(self, opdata):
        """
        Calculate how likely option is going to expire in the money based on current
        asset price
        """
        distance_between_strike_and_spot = self.how_far_asset_price_to_strike_price(opdata)
        expected_return_adjusted_for_riskness = self.what_is_expected_return_adjusted_for_riskness(opdata)
        expected_fluctuation_in_the_life_of_option = opdata.volatility * np.sqrt(opdata.time_to_expire)
        d1 = (distance_between_strike_and_spot + expected_return_adjusted_for_riskness) / expected_fluctuation_in_the_life_of_option
        return d1
    
    def calculate_d2(self, opdata):
        d1 = self.calculate_d1(opdata)
        d2 = d1 - opdata.volatility * np.sqrt(opdata.time_to_expire)
        return d2
    
    def calculate_option_price_given(self, opdata, d1, d2):
        S = opdata.spot_price
        K = opdata.strike_price
        r = opdata.interest_rate
        T = opdata.time_to_expire
        price = S*norm.cdf(d1) -  K*np.exp(-r*T)*norm.cdf(d2)
        return price

    def option_pricing_formula(self, opdata, type="call"):
        if type == "call":
            d1 = self.calculate_d1(opdata)
            d2 = self.calculate_d2(opdata)
            call_price = self.calculate_option_price_given(opdata, d1, d2)
            return call_price