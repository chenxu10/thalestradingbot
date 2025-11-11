#!/usr/bin/env python3

import sys
from fentu.explatoryservices.volcalculator import VolatilityFacade

def main():
    if len(sys.argv) < 3:
        print("Usage: see_change <timeframe> <ticker>")
        print("Timeframes: daily, weekly, monthly, yearly")
        print("Example: see_change monthly SPY")
        sys.exit(1)
    
    timeframe = sys.argv[1].lower()
    ticker = sys.argv[2].upper()
    
    volatility = VolatilityFacade(ticker)
    
    actions = {
        'daily': volatility.visualize_daily_percentage_change,
        'weekly': volatility.visualize_weekly_percentage_change,
        'monthly': volatility.visualize_monthly_percentage_change,
        'yearly': lambda: print(volatility.get_calendar_year_returns())
    }
    
    if timeframe not in actions:
        print(f"Unknown timeframe: {timeframe}")
        print("Valid options: daily, weekly, monthly, yearly")
        sys.exit(1)
    
    actions[timeframe]()

if __name__ == "__main__":
    main()