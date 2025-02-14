"""
This script helps you to figure out pricing of options behind the fidelity's
option chain pricing
"""
from fentu.explatoryservices.volcalculator import black_scholes_put

class BSMPricer:
    def __init__(self, data_for_option_pricing):
        self.data_for_option_pricing = data_for_option_pricing

    def calculate_price(self):
        """
        Implement the pricing formula of Black-Scholes-Merton
        """
        S = self.data_for_option_pricing["S"]
        K = self.data_for_option_pricing["K"]
        T = self.data_for_option_pricing["T"]
        r = self.data_for_option_pricing["r"]
        sigma = self.data_for_option_pricing["sigma"]
        return black_scholes_put(S, K, T, r, sigma)

class TailHedgePricer:
    def __init__(self, data_for_option_pricing):
        self.data_for_option_pricing = data_for_option_pricing

    def calculate_price(self):
        return 1
    
def main():
    data_for_option_pricing = {
        "S": 88.79,
        "K": 50,
        "T": 0.08,
        "r": 0.04,
        "sigma": 48.9
    }
    bs_price = BSMPricer(data_for_option_pricing).calculate_price()
    print(bs_price)
    taleb_result3_price = TailHedgePricer(data_for_option_pricing).calculate_price()
    #assert bs_price > taleb_result3_price


if __name__ == "__main__":
    main()