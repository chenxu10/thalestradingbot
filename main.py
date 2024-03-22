
from fentu.explatoryservices.plotting_service import qq_plot
import yfinance as yf




if __name__ == '__main__':
    x = input("Please input the ETF you want to visualize e.g TLT... ")
    tltdf = yf.download(x)
    print(tltdf)