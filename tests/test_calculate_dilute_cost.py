
# TODO calculate breakeven price
# For status call exercised, call not exercised, put exercised and put not exercised
import pytest

def calculate_dilueted_cost(x):
    status_end_state = x["status"]["end_state"]
    cur_diluted_cost = x["cur_diluted_cost"]
    cur_position = x["cur_position"]
    preimum = x["preimum"]
    if status_end_state == "not_exercised":
        new_diluted_cost = cur_diluted_cost - preimum / cur_position
    return new_diluted_cost

def test_calculate_dilute_cost():
    actual = calculate_dilueted_cost(
        {
            "cur_diluted_cost": 100,
            "cur_position":200,
            "status":{
                "type":"call",
                "volume":1,
                "end_state":"not_exercised"},
            "preimum":20,
        })                                                         
    expected = 99.9
    assert actual == expected
    

def main():
    test_calculate_dilute_cost()

if __name__ == '__main__':
    main()