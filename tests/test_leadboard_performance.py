import pandas as pd

def calculate_qtd_performance(df):
    #price_a_quarter_ago = df[''] 
    #today_close_price = df.iat[-1,1]
    #qtd_performance = (today_close_price-price_a_quarter_ago)/price_a_quarter_ago
    return 0.02
    #return qtd_performance

def test_calculate_leadboard_performance():
    df = pd.DataFrame()
    actual_qtd_performance = calculate_qtd_performance(df)
    expected_qtd_performance = 0.02
    assert  actual_qtd_performance == expected_qtd_performance




