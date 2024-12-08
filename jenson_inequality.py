import pandas as pd
pd.set_option('display.max_columns', None) 

def test_add_hypothetical_prices(df):
    hypothetical_prices = [90,90.5,91,91.5,92,92.5,93,93.5,94.5,95]
    #short_call_gain = [0.14,0.14,0.14,0.14,0.14,0,0,0,0,0]
    short_call_gain = [0.06,0.06,0.06,0.06,0.06,0,0,0,0,0]
    short_call_pl = [0.05] * 10                     # short at 92
    spot_loss = [0,0,0,0,0,2.5,2,1.5,0.5,0]
    long_call_gain = [0,0,0,0.14,0.22,0.34,0.51,0.76,1.06,1.43] # long at 93.5
    long_call_gain = [i*2 for i in long_call_gain]
    #long_call_gain = [0,0,0,0,0,0,0,2.08,2.8,3.84] # long at 93.5 with 2
    simulation_df = pd.DataFrame(
        {'hypo_prices':hypothetical_prices,
        'short_call_at_92_gain':short_call_gain,
        'short_call_alone_p&l':short_call_pl,
         'spot_loss':spot_loss,
         'long_call_gain':long_call_gain}
    )
    simulation_df['jenson_inequality_pl'] = \
        simulation_df['short_call_at_92_gain'] + simulation_df['long_call_gain'] - \
        simulation_df['spot_loss']
    simulation_df.to_csv("reinsurance_strategy.csv")
    return simulation_df

def main():
    df = pd.read_csv("tltoptionchaindata.csv")
    test_add_hypothetical_prices(df)
    # print(df.sample(5))

if __name__ == '__main__':
    main()