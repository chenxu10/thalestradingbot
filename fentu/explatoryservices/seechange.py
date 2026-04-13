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
    
    valid_timeframes = {'daily', 'weekly', 'monthly', 'yearly'}

    if timeframe not in valid_timeframes:
        print(f"Unknown timeframe: {timeframe}")
        print("Valid options: daily, weekly, monthly, yearly")
        sys.exit(1)

    volatility.visualize_percentage_change(timeframe)

if __name__ == "__main__":
    main()