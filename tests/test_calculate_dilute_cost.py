
# TODO calculate breakeven price
# Diluted price the price you can break even when you close
# For status call exercised, call not exercised, put exercised and put not exercised
# (持有期内买入总金额 - 持有期内期权总收入)/持有数量
# Find low p/b and high volatility stocks

import pytest

def calculate_dilueted_cost(x):
    status_end_state = x["end_state"]
    cur_diluted_cost = x["cur_diluted_cost"]
    cur_position_after_option_change = x["cur_position"]
    preimum = x["preimum"]
    strikeprice = x["strikeprice"]
    volume = x["volume"]
    type = x["type"]

    if status_end_state == "not_exercised":
        if cur_position_after_option_change == 0:
            new_diluted_cost = -preimum
        else:
            new_diluted_cost = cur_diluted_cost - preimum / cur_position_after_option_change

    elif status_end_state == "exercised":
        if cur_position_after_option_change == 0:
            new_diluted_cost = strikeprice - preimum / (volume * 100)
        else:
            if type == "put":
                exercised_shares = volume * 100
                total_buy_cost = strikeprice * exercised_shares + cur_diluted_cost * (
                    cur_position_after_option_change - exercised_shares) 
                new_diluted_cost = (total_buy_cost - preimum) / cur_position_after_option_change
           
    return new_diluted_cost

def test_calculate_dilute_cost():
    not_exercised_order_data = {
        "cur_diluted_cost":100,
        "cur_position":200,
        "type":"call",
        "volume":1,
        "end_state":"not_exercised",
        "preimum":20,
        "strikeprice":90
    } 
    actual = calculate_dilueted_cost(not_exercised_order_data)                                                         
    expected = 99.9
    assert actual == expected  

    put_exercised_order_data = {
        "cur_diluted_cost":float('-inf'),
        "cur_position":0,
        "type":"put",
        "volume":1,
        "end_state":"exercised",
        "preimum":20,
        "strikeprice":90

    }
    actual = calculate_dilueted_cost(put_exercised_order_data)
    expected = 89.8
    assert actual == expected

    put_exercised_order_data = {
        "cur_diluted_cost":100,
        "cur_position":300,
        "type":"put",
        "volume":1,
        "end_state":"exercised",
        "preimum":20,
        "strikeprice":90

    }
    actual = calculate_dilueted_cost(put_exercised_order_data)
    expected = 96.6
    assert actual == expected

    
def main():
    test_calculate_dilute_cost()
    put_fxi_order = {
        "cur_diluted_cost":32.1803,
        "cur_position":412,
        "type":"put",
        "volume":2,
        "end_state":"exercised",
        "preimum":158.64,
        "strikeprice":35.5
    }
    di = calculate_dilueted_cost(put_fxi_order)
    print(di)


if __name__ == '__main__':
    main()