
import yfinance as yf
import fentu.explatoryservices.volcalculator as vc
from fentu.explatoryservices.plotting_service import qq_plot



if __name__ == '__main__':
    x = input("Please input the ETF you want to visualize e.g TLT... ")
    df = vc.VolatilityFacade(x)
    print(df)
    