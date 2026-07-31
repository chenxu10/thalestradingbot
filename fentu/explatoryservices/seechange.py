#!/usr/bin/env python3

import sys
from fentu.explatoryservices.volcalculator import VolatilityFacade

def main():
    if len(sys.argv) < 3:
        print("Usage: see_change <timeframe> <ticker> [start_date] [end_date]")
        print("Timeframes: daily, weekly, monthly, yearly")
        print("Example: see_change monthly SPY")
        print("Example: see_change monthly SPY 2026-03-01 2026-06-01")
        print("Example: see_change daily portfolio")
        sys.exit(1)

    timeframe = sys.argv[1].lower()
    ticker = sys.argv[2].upper()

    if len(sys.argv) == 4:
        start_date = sys.argv[3]
        end_date = None
    elif len(sys.argv) == 5:
        start_date = sys.argv[3]
        end_date = sys.argv[4]
    else:
        start_date = None
        end_date = None

    valid_timeframes = {'daily', 'weekly', 'monthly', 'yearly'}

    if timeframe not in valid_timeframes:
        print(f"Unknown timeframe: {timeframe}")
        print("Valid options: daily, weekly, monthly, yearly")
        sys.exit(1)

    if ticker == "PORTFOLIO":
        from fentu.explatoryservices.portfolio_monitor import PortfolioMonitor
        PortfolioMonitor(period=timeframe).visualize()
        return

    volatility = VolatilityFacade(ticker, start_date=start_date, end_date=end_date)
    volatility.visualize_percentage_change(timeframe)

if __name__ == "__main__":
    main()
