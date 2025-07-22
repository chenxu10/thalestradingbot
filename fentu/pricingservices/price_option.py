import math


def calculate_discounted_k_price(k, base_rate, time_to_expiration):
    return k * math.exp(-base_rate * time_to_expiration/ 365)


def calculate_vol_time_factor(vol, time_to_expiration):
    return vol * math.sqrt(time_to_expiration/365)

def calculate_ln_ratio(stock, strike):
    return math.log(stock/strike)