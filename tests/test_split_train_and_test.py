import pandas as pd
from fentu.strategyservices.pair_trading import train_test_split

def test_split_train_and_test():
    data = {
        'Date': ['2022-01-01', '2022-01-02', '2022-01-03', '2022-01-04', '2022-01-05'],
        'gld': [100, 102, 103, 105, 107],
        'gdx': [50, 55, 52, 57, 60]
    }
    df = pd.DataFrame(data)
    train, test = train_test_split(df, train_frac=0.8)
    assert len(train) == 4
    assert len(test) == 1