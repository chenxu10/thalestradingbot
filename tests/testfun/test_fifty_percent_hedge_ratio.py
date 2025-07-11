"""
历史回测降本速度是否降低了50%

Constrants:

持有长期期权看跌期权的张数
(1) 大于等于(已经吃货的量+义乌仓假设全部吃进的量) * 2
(2) 长期看跌期权的Theta开销，远远小于卖短期期权的日常权利金收入

把张数和Strike Price分开考虑
"""

def test_explore_qixian_cuopei():

    def calculate_three_months_daily_option_cost():
        """
        Expire at 09/30 Strike at 473
        Expire at 12/30 Strike at 473
        """
        oneqqqputweeklyaverage = 424/28
        threeqqqputsweeklyaverage = 3 * oneqqqputweeklyaverage
        return threeqqqputsweeklyaverage
    
    three_months_daily_option_cost = calculate_three_months_daily_option_cost()
    print(three_months_daily_option_cost)
    daily_option_preimum = 200

    assert three_months_daily_option_cost < daily_option_preimum

def main():
    test_explore_qixian_cuopei()

if __name__ == "__main__":
    main()