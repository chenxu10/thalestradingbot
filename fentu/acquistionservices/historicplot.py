import pandas as pd
import matplotlib.pyplot as plt

def get_qratio():
    """
    Returns:
        A list of q ratio starting from 1944 to 2022
    """
    df = pd.read_csv("data/csv/b103.csv")
    df = df.loc[:,['LM103164103.Q','FL102090005.Q']]
    df.rename(
        columns={"LM103164103.Q":"corp_eqt_lblt","FL102090005.Q":"corp_net_worth"},
        inplace=True)
    df = df[df["corp_eqt_lblt"].str.contains("ND")==False]
    df = df[df["corp_net_worth"].str.contains("ND")==False]
    df['corp_eqt_lblt'] = df['corp_eqt_lblt'].astype(int)
    df['corp_net_worth'] = df['corp_net_worth'].astype(int)
    df['q_ratio'] =  df['corp_eqt_lblt']/df['corp_net_worth']
    df['q_ratio'].plot()
    plt.show()
    return df

if __name__ == '__main__':
    get_qratio()


