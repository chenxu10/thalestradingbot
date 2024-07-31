import yfinance as yf

def get_price_in_crisis():
    tlt = yf.Ticker("TLT")
    data = tlt.history(start="2020-03-01", end="2020-04-01")
    return data['Close']

def test_get_price_in_crisis_range():
    start = "2020-03-01" 
    end = "2020-04-01"
    data = get_price_in_crisis()
    print(data)
    assert data.shape[0] == 22

def main():
    test_get_price_in_crisis_range()

if __name__ == '__main__':
    main()