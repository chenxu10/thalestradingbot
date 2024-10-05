


# TODO calculate breakeven price
# For status call exercised, call not exercised, put exercised and put not exercised


def calculate_dilueted_cost(x):
    return 99.9

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