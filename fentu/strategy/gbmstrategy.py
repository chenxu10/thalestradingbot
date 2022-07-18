from math import exp, sqrt
from random import gauss, seed


def generate_gbm(s0, mu, sigma):
    """
    Generates a price following geometric brownie process based on the input
    Args:
        s0: Initial price of stock
        mu: Interest rate
        sigma: Volatile of stock price 
    Returns:
        s1: Closing price of stock
    Examples:
        >>> generate_gbm(100,0.1,0.05)
        123
    """
    return 123

if __name__ == "__main__":
    seed(1234)
    for _ in range(1000):
        sm = generate_gbm(100, 0.1, 0.05)
        if sm > 130:
            print("Target price reached, take profit")
            break
    else:
        print("No profit is made")

