from fentu.tradingservices.bot import download_prices_change

def test_download_prices_change():
    ftx_pricechange_sincestart = download_prices_change()
    expected_mostrecent = (27.15 - 27.57) / 27.15
    assert abs(expected_mostrecent - ftx_pricechange_sincestart) < 0.01

def test_timeframe():
    # underlying volatitlity
    pass