import yfinance as yf

def download_ticker_range(ticker, start_date, end_date):
    if start_date and end_date:
        data = yf.download(ticker, start=start_date, end=end_date)["Close"]
        date_range_str = f"({start_date} to {end_date})"
    else:
        data = yf.download(ticker, period="1y")["Close"]
        date_range_str = f"({data.index[0].date()} to {data.index[-1].date()})"

    print(date_range_str)
    return data, date_range_str