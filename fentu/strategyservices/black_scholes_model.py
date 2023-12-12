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

    def option_pricing_formula(self, opdata, type="call"):
        if type == "call":
            S = opdata.spot_price
            K = opdata.strike_price
            r = opdata.interest_rate
            sigma = opdata.volatility
            T = opdata.time_to_expire
            d1 = (np.log(S/K)+(r+0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)
            call_price = S*norm.cdf(d1) -  K*np.exp(-r*T)*norm.cdf(d2)
            return call_price