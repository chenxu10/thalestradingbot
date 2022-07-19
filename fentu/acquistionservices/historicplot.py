import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gmean

def calculate_geometric_mean(x):
    ans = []
    
    for i in range(1, len(x) + 1):
        ans.append(gmean(x[i-3:i]))

    ans = [round(s,2) for s in ans]

    return ans

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

    def calculate_geometric_columns(df):
        for c in ["corp_eqt_lblt","corp_net_worth"]:
            df["geo_" + c] = calculate_geometric_mean(list(df[c]))
        return df

    def add_geo_q_ratio(df):
        df['geo_q_ratio'] = df['geo_corp_eqt_lblt']/df['geo_corp_net_worth']
        return df

    df =(load_data().
        pipe(pick_interested_columns).
        pipe(rename_column).
        pipe(delete_null_values).
        pipe(calculate_geometric_columns).
        pipe(add_geo_q_ratio)
        )

    return df

def plot_q_ratio():
    df = pd.read_csv("tests/mockdata/qratio.csv",index_col=0)
    print(df)
    x = df['date']
    y = df['geo_q_ratio']
    plt.plot(x,y)
    #df['geo_q_ratio'].plot()
    plt.axhline(y=1.0, color='black', linestyle="--")
    plt.xticks(x[::10],  rotation='vertical')
    plt.show()


if __name__ == '__main__':
    #get_running_gmean_qratio()
    plot_q_ratio()
