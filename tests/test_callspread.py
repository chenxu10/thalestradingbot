"""
This script tests the maximum_loss, maximum_profit, 
risk_and_reward_issue, and the impact on the whole portfolio
of callspread strategy
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fentu.explatoryservices.plotting_service import callspread_pandl_plot

def test_callspread_pandl_plot():
    short_strike = 95
    long_strike = 91
    stock_price = 90
    short_premium = 0.39
    long_premium = 0.41
    difference_between_strike = short_strike - long_strike
    netcost_of_spread = long_premium - short_premium
    commission = 0.01
    
    exp_max_profit = difference_between_strike - netcost_of_spread
    exp_max_loss = long_premium - short_premium + commission
    
    test_df = pd.DataFrame(
        {"price_at_expiration":[87,88,89,90,91,92,93],
         "pandl":[22,22,22,32,32,32,32]}
    )
    callspread_pandl_plot(test_df)
    # ax = plt.gca()
    # lines = ax.get_children()
    # x_data, y_data = lines[0].get_xydata().T
    assert exp_max_profit == 3.98
    np.testing.assert_almost_equal(exp_max_loss,0.03,decimal=3)
    plt.show()


if __name__ == "__main__":
    test_callspread_pandl_plot()
