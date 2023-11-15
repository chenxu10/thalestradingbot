"""maxium_loss, maximum_profit, risk_and_reward issue, impact on the whole portfolio"""
import pandas as pd
import matplotlib.pyplot as plt
from fentu.explatoryservices.plotting_service import callspread_pandl_plot

def test_callspread_pandl_plot():
    test_df = pd.DataFrame(
        {"price_at_expiration":[108,107,106,105,104,103,102,101,100,99,98],
         "pandl":[3.2,3.2,3.2,3.2,2.2,1.2,0.2,-0.8,-1.8,-1.8,-1.8]}
    )
    callspread_pandl_plot(test_df)
    plt.show()
    # ax = plt.gca()
    # lines = ax.get_children()
    # x_data, y_data = lines[0].get_xydata().T
    # maximum_loss = min(y_data)
    # maximum_profit = max(y_data)
    # assert maximum_loss == -2
    # assert maximum_profit == 3

if __name__ == "__main__":
    test_callspread_pandl_plot()
