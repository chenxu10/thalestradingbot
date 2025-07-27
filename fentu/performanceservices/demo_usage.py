"""
Demo script for PerformanceCalculator usage with NDX100 data

This demonstrates how to use the performance calculator to benchmark
hedge fund managers against the NDX100 index.
"""

from datetime import date
import pandas as pd
import numpy as np
from fentu.performanceservices.performance_calculator import PerformanceCalculator


def create_mock_ndx100_data():
    """Create mock NDX100 data for demonstration"""
    # Generate dates from 2023-01-01 to 2024-12-31
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
    
    # Generate realistic price data with some volatility
    np.random.seed(42)  # For reproducible results
    
    # Starting price
    start_price = 350.0
    
    # Generate daily returns with some drift (upward trend)
    daily_returns = np.random.normal(0.0008, 0.02, len(dates))  # ~0.08% daily mean return, 2% volatility
    
    # Calculate cumulative prices
    price_changes = np.cumprod(1 + daily_returns)
    prices = start_price * price_changes
    
    return pd.Series(prices, index=dates)


def main():
    """Demonstrate performance calculation with NDX100 data"""
    
    # Initialize performance calculator
    calculator = PerformanceCalculator()
    
    print("📊 NDX100 Performance Analysis Demo")
    print("=" * 50)
    
    # Create mock NDX100 data for demonstration
    print("📥 Creating mock NDX100 data...")
    try:
        ndx100_prices = create_mock_ndx100_data()
        print(f"✅ Data created: {len(ndx100_prices)} data points")
        print(f"📅 Data range: {ndx100_prices.index[0].date()} to {ndx100_prices.index[-1].date()}")
        print(f"💰 Price range: ${ndx100_prices.min():.2f} - ${ndx100_prices.max():.2f}")
        
    except Exception as e:
        print(f"❌ Error creating data: {e}")
        return
    
    # Calculate performance metrics for a specific date
    reference_date = date(2024, 6, 30)  # End of Q2 2024
    
    print(f"\n📈 Performance Metrics for {reference_date}")
    print("-" * 40)
    
    try:
        # Calculate MTD performance
        mtd_perf = calculator.calculate_mtd_performance(
            ndx100_prices, reference_date
        )
        print(f"📅 Month-to-Date:   {mtd_perf:+.2f}%")
        
        # Calculate QTD performance
        qtd_perf = calculator.calculate_qtd_performance(
            ndx100_prices, reference_date
        )
        print(f"📅 Quarter-to-Date: {qtd_perf:+.2f}%")
        
        # Calculate YTD performance
        ytd_perf = calculator.calculate_ytd_performance(
            ndx100_prices, reference_date
        )
        print(f"📅 Year-to-Date:    {ytd_perf:+.2f}%")
        
    except Exception as e:
        print(f"❌ Error calculating performance: {e}")
        return
    
    # Example hedge fund comparison
    print(f"\n🏆 Hedge Fund vs NDX100 Comparison")
    print("-" * 40)
    
    # Sample hedge fund monthly returns (4 months)
    hedge_fund_returns = [0.025, 0.035, -0.015, 0.045]  # 2.5%, 3.5%, -1.5%, 4.5%
    
    try:
        comparison = calculator.compare_to_benchmark(
            hedge_fund_returns, ndx100_prices, reference_date
        )
        
        print(f"📊 Excess Return:    {comparison['excess_return']:+.4f}")
        print(f"📊 Tracking Error:   {comparison['tracking_error']:.4f}")
        
        if comparison['excess_return'] > 0:
            print("🎯 Hedge fund outperformed NDX100!")
        else:
            print("📉 Hedge fund underperformed NDX100")
            
    except Exception as e:
        print(f"❌ Error in comparison: {e}")
    
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    main() 