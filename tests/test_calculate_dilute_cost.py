"""
This script calculated the breakeven price or diluted cost
for the spot equity you owned

Author: Xu Shen <xs286@cornell.edu>
"""
from fentu.accountingservices import calculate_stock_dilute_cost as csdc

def test_calculate_exercised_order():
    exercised_order_data = {
        "cur_diluted_cost":float('-inf'),
        "cur_position":0,
        "type":"put",
        "volume":-1,
        "end_state":"exercised",
        "premium":20,
        "strikeprice":90,
        "closeorderprice":90
    }
    calculator = csdc.DilutedCostCalculator(exercised_order_data)
    actual = calculator.calculate()
    expected = 89.8
    assert actual == expected

def test_calculate_filled_order():
    put_filled_order_data = {
        "cur_diluted_cost":100,
        "cur_position":100,
        "type":"put",
        "volume":-1,
        "end_state":"filled",
        "premium":100,
        "strikeprice":90,
        "closeorderprice":9
    }
    calculator = csdc.DilutedCostCalculator(put_filled_order_data)
    actual = calculator.calculate()
    expected = (100 * 100 - 100 + 9)/100
    assert actual == expected

def test_calculate_dilute_cost():
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
    calculator = csdc.DilutedCostCalculator(put_exercised_order_data)
    actual = calculator.calculate()
    expected = 96.6
    assert actual == expected
    
def main():
    test_calculate_dilute_cost()
    to_calculate_order = {
        "cur_diluted_cost":34.04,
        "cur_position":612,
        "type":"put",
        "volume":9,
        "end_state":"filled",
        "premium":9.7,
        "strikeprice":30,
        "closeorderprice":None
    }
    calculator = csdc.DilutedCostCalculator(to_calculate_order)
    di = calculator.calculate()
    print(di)

if __name__ == '__main__':
    main()