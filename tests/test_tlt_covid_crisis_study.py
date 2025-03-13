import yfinance as yf
import matplotlib.pyplot as plt

def get_price_in_crisis():
    tlt = yf.Ticker("TLT")
    data = tlt.history(start="2020-03-01", end="2020-05-01")
    return data

def test_get_price_in_crisis_range():
    start = "2020-03-01" 
    end = "2020-04-01"
    data = get_price_in_crisis()
    print(data)
    #assert data.shape[0] == 22

    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['Close'], label='TLT Close Price')
    plt.title('TLT Price in March 2020')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    test_get_price_in_crisis_range()

if __name__ == '__main__':
    main()