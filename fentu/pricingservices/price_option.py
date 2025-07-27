import math
from scipy.stats import norm

def calculate_discounted_k_price(k, base_rate, time_to_expiration):
    return k * math.exp(-base_rate * time_to_expiration/ 365)


def calculate_vol_time_factor(vol, time_to_expiration):
    return vol * math.sqrt(time_to_expiration/365)

def calculate_ln_ratio(stock, strike):
    return math.log(stock/strike)

def calculate_d1(stock, strike, vol, rate, time_to_expiration):
    """
    #TODO: What's meanring of d1 and drift
    #TODO: why calculate in this way
    d1: how far the stock price is far awaat from strike
    """
    ln_ratio = calculate_ln_ratio(stock, strike)
    drift = (rate + vol**2/2) * time_to_expiration / 365  # Fixed: normalize time to years
    vol_time = calculate_vol_time_factor(vol, time_to_expiration)
    n1 = (ln_ratio + drift) / vol_time
    return n1

def calculate_normal_cdf(x):
    return norm.cdf(x) 


def calculate_first_term(stock, strike, vol, rates, time_to_expiration):
    """Calculate S₀ * N(d₁) - present value of stock if exercised"""
    d1 = calculate_d1(stock, strike, vol, rates, time_to_expiration)
    nd1 = calculate_normal_cdf(d1)
    return stock * nd1


def calculate_d2(stock, strike, vol, rate, time_to_expiration):
    """
    d2 means the risk adjusted probability that the option will be
    in the money
    """
    d1 = calculate_d1(stock, strike, vol, rate, time_to_expiration)
    vol_time = calculate_vol_time_factor(vol, time_to_expiration) 
    d2 = d1 - vol_time
    return d2