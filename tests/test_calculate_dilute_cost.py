
# TODO calculate breakeven price
# Diluted price the price you can break even when you close
# For status call exercised, call not exercised, put exercised and put not exercised
# (持有期内买入总金额 - 持有期内期权总收入)/持有数量
# Find low p/b and high volatility stocks
import pytest

def calculate_dilueted_cost(x):
    status_end_state = x["end_state"]
    cur_diluted_cost = x["cur_diluted_cost"]
    cur_position = x["cur_position"]
    preimum = x["preimum"]

    if status_end_state == "not_exercised":
        if cur_position == 0:
            new_diluted_cost = -preimum
        else:
            new_diluted_cost = cur_diluted_cost - preimum / cur_position
    return new_diluted_cost

def test_calculate_dilute_cost():
    not_exercised_order_data = {
        "cur_diluted_cost":100,
        "cur_position":200,
        "type":"call",
        "volume":1,
        "end_state":"not_exercised",
        "preimum":20
    } 
    actual = calculate_dilueted_cost(not_exercised_order_data)                                                         
    expected = 99.9
    assert actual == expected  

    put_exercised_order_data = {
        "cur_diluted_cost":100,
        "cur_position":200,
        "type":"call",
        "volume":1,
        "end_state":"not_exercised",
        "preimum":20,
        "strikeprice":90

    }
    expected = 96.6


def main():
    test_calculate_dilute_cost()

if __name__ == '__main__':
    main()