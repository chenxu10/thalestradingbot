"""
历史回测降本速度是否降低了50%
"""

def test_explore_qixian_cuopei():

    def calculate_three_months_daily_option_cost():
        """
        Expire at 09/30 Strike at 473
        """
        return 473 / 14
    
    three_months_daily_option_cost = calculate_three_months_daily_option_cost()
    print(three_months_daily_option_cost)
    daily_option_preimum = 100

    assert three_months_daily_option_cost < daily_option_preimum


def main():
    test_explore_qixian_cuopei()

if __name__ == "__main__":
    main()