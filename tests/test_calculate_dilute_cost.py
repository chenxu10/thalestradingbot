
# TODO calculate breakeven price
# Diluted price the price you can break even when you close
# For status call exercised, call not exercised, put exercised and put not exercised
# (持有期内买入总金额 - 持有期内期权总收入)/持有数量
# Find low p/b and high volatility stocks

import pytest


class DilutedCostCalculator:
    def __init__(self, data):
        self.status_end_state = data["end_state"]
        self.cur_diluted_cost = data["cur_diluted_cost"]
        self.cur_position_after_option_change = data["cur_position"]
        self.premium = data["premium"]
        self.strikeprice = data["strikeprice"]
        self.volume = abs(data["volume"])  # Ensure volume is positive
        self.option_type = data["type"]
        self.closeprice = data["closeorderprice"]

    def calculate(self):
        if self.volume < 0:
            return self._calculate_new_diluted_cost()
        return None  # or some default value if volume is not negative

    def _calculate_new_diluted_cost(self):
        if self.status_end_state == "filled":
            return self._calculate_filled_diluted_cost()
        elif self.status_end_state == "not_exercised":
            return self._calculate_not_exercised_diluted_cost()
        elif self.status_end_state == "exercised":
            return self._calculate_exercised_diluted_cost()

    def _calculate_filled_diluted_cost(self):
        return self.cur_diluted_cost - (self.premium - self.closeprice) / self.cur_position_after_option_change

    def _calculate_not_exercised_diluted_cost(self):
        if self.cur_position_after_option_change == 0:
            return -self.premium
        return self.cur_diluted_cost - self.premium / self.cur_position_after_option_change

    def _calculate_exercised_diluted_cost(self):
        exercised_shares = self.volume * 100
        if self.cur_position_after_option_change == 0:
            return self.strikeprice - self.premium / (self.volume * 100)

        total_buy_cost = self._calculate_total_buy_cost(exercised_shares)
        return (total_buy_cost - self.premium) / self.cur_position_after_option_change

    def _calculate_total_buy_cost(self, exercised_shares):
        if self.option_type == "put":
            return (self.strikeprice * exercised_shares +
                    self.cur_diluted_cost * (self.cur_position_after_option_change - exercised_shares))
        elif self.option_type == "call":
            return (self.cur_diluted_cost * (self.cur_position_after_option_change + exercised_shares) -
                    self.strikeprice * exercised_shares)

# Usage
def calculate_diluted_cost(data):
    calculator = DilutedCostCalculator(data)
    return calculator.calculate()


def calculate_dilueted_cost(x):
    status_end_state = x["end_state"]
    cur_diluted_cost = x["cur_diluted_cost"]
    cur_position_after_option_change = x["cur_position"]
    preimum = x["premium"]
    strikeprice = x["strikeprice"]
    volume = x["volume"]
    type = x["type"]
    closeprice = x["closeorderprice"]

    if volume < 0:
        volume = abs(volume)
        if status_end_state == "filled":
            new_diluted_cost = cur_diluted_cost - (preimum - closeprice) / cur_position_after_option_change
            
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
                elif type == "call":
                    exercised_shares = volume * 100
                    total_buy_cost = cur_diluted_cost * (cur_position_after_option_change 
                        + exercised_shares) - strikeprice * exercised_shares
                    new_diluted_cost = (total_buy_cost - preimum) / cur_position_after_option_change

    return new_diluted_cost

def test_calculate_dilute_cost():
    not_exercised_order_data = {
        "cur_diluted_cost":100,
        "cur_position":200,
        "type":"call",
        "volume":-1,
        "end_state":"not_exercised",
        "premium":20,
        "strikeprice":90,
        "closeorderprice":0
    } 
    actual = calculate_dilueted_cost(not_exercised_order_data)                                                         
    expected = 99.9
    assert actual == expected  

    put_exercised_order_data = {
        "cur_diluted_cost":float('-inf'),
        "cur_position":0,
        "type":"put",
        "volume":-1,
        "end_state":"exercised",
        "premium":20,
        "strikeprice":90,
        "closeorderprice":90
    }
    actual = calculate_dilueted_cost(put_exercised_order_data)
    expected = 89.8
    assert actual == expected

    put_exercised_order_data = {
        "cur_diluted_cost":100,
        "cur_position":300,
        "type":"put",
        "volume":-1,
        "end_state":"exercised",
        "premium":20,
        "strikeprice":90,
        "closeorderprice":90

    }
    actual = calculate_dilueted_cost(put_exercised_order_data)
    expected = 96.6
    assert actual == expected

    
def main():
    test_calculate_dilute_cost()
    put_fxi_order = {
        "cur_diluted_cost":33.89,
        "cur_position":612,
        "type":"put",
        "volume":-1,
        "end_state":"exercised",
        "premium":115.32,
        "strikeprice":36,
        "closeorderprice":0
    }
    di = calculate_dilueted_cost(put_fxi_order)
    print(di)

    calculator = DilutedCostCalculator(put_fxi_order)
    di = calculator.calculate()
    print(di)



if __name__ == '__main__':
    main()