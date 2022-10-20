"""
Calculates mises stationary index
Reference:
    <Dao of Capital> by Mark Spitznagel
    https://msindex.net/
Author: xs286@cornell.edu
"""
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
from scipy.stats import gmean
from statsmodels.tsa.stattools import adfuller


def get_vticlose_vtistart():
    raise NotImplementedError

def extraploate(x, vticlose, vtistart):
    percentage = (vticlose - vtistart) / vtistart
    x = int(x + x * percentage)
    return x

def get_running_gmean_qratio():
    """
    Returns:
        Running geometric avaerage from 1944 to 2022
        A list of q ratio starting from 1944 to 2022
    """
    def load_data():
        return pd.read_csv("data/csv/b103.csv")

    def pick_interested_columns(df):
        df = df.loc[:,['date','LM103164103.Q','FL102090005.Q']]
        return df

    def rename_column(df):
        df = df.rename(
            columns={
                "LM103164103.Q":"corp_eqt_lblt",
                "FL102090005.Q":"corp_net_worth"}
            )
        return df

    def delete_null_values(df):
        for c in ["corp_eqt_lblt","corp_net_worth"]:
            df = df.loc[df[c].str.contains("ND")==False,:]
            df[c] = df[c].astype(int)
        return df

    def add_geo_q_ratio(df):
        df['geo_q_ratio'] = df['corp_eqt_lblt']/df['corp_net_worth']
        geomean = gmean(df['geo_q_ratio'])
        df['geo_q_ratio'] = df['geo_q_ratio']/geomean
        return df

    df =(load_data().
        pipe(pick_interested_columns).
        pipe(rename_column).
        pipe(delete_null_values).
        pipe(add_geo_q_ratio)
        )

    df.to_csv("tests/mockdata/qratio.csv")

    return df

def plot_q_ratio():
    df = pd.read_csv("tests/mockdata/qratio.csv",index_col=0)
    print(df)
    x = df['date']
    y = df['geo_q_ratio']
    y75quantile = np.percentile(y, 75)
    y25quantile = np.percentile(y, 25)
    plt.plot(x,y)
    plt.axhline(y=y75quantile, color='red', linestyle="--")
    plt.axhline(y=y25quantile, color='green', linestyle="--")
    plt.axhline(y=1.0, color='black', linestyle="--")
    plt.xticks(x[::10],  rotation='vertical')
    plt.ylim(0,3)
    plt.show()

def ducker_fuller_test_qratio():
    df = pd.read_csv("tests/mockdata/qratio.csv",index_col=0)
    qratio = df['geo_q_ratio'].values
    result = adfuller(qratio)
    print(result[1])

if __name__ == '__main__':
    #get_running_gmean_qratio()
    plot_q_ratio()
    # ducker_fuller_test_qratio()