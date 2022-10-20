from fentu.acquisitionservices.historic_option_price import get_sp500_putdata

def test_historic_option_price():
    df = get_sp500_putdata()
    print(df)


if __name__ == '__main__':
    test_historic_option_price()