"""
This script calculated the breakeven price or diluted cost
for the spot equity you owned

Author: Xu Shen <xs286@cornell.edu>
"""
import pytest

class DilutedCostCalculator:
    def __init__(self, data):
        self.status_end_state = data["end_state"]
        self.cur_diluted_cost = data["cur_diluted_cost"]
        self.cur_position_after_option_change = data["cur_position"]
        self.premium = data["premium"]
        self.strikeprice = data["strikeprice"]
        self.volume = data["volume"]
        self.option_type = data["type"]
        self.closeprice = data["closeorderprice"]

    def calculate(self):
        if self.volume < 0:
            self.volume = abs(self.volume)
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
    calculator = DilutedCostCalculator(not_exercised_order_data)
    actual = calculator.calculate()                                                        
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
    calculator = DilutedCostCalculator(put_exercised_order_data)
    actual = calculator.calculate()
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
    calculator = DilutedCostCalculator(put_exercised_order_data)
    actual = calculator.calculate()
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
    calculator = DilutedCostCalculator(put_fxi_order)
    di = calculator.calculate()

if __name__ == '__main__':
    main()