# Thales Trading Bot
> How to make money when you are wrong? It's much better to be convex than to be right.

## Environment Setup with uv

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management. Follow these steps:

### 1. Install uv
```bash
# macOS/Linux (curl or pip)
curl -LsSf https://astral.sh/uv/install.sh | sh || pip install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Set up the project
```bash
git clone <repository-url>
cd thalestradingbot
uv sync
```

### 3. Run the application
```bash
# Run with uv (recommended)
uv run python -m fentu.explatoryservices.volcalculator

# Or after activating the environment
python -m fentu.explatoryservices.volcalculator
```

## Main Functionality

This application is designed to analyze financial market data and identify historical worst-case scenarios. The core functionality includes:

### 📊 Multi-Timeframe Return Analysis
- **Daily Returns**: Analyze day-to-day price movements
- **Weekly Returns**: Examine weekly performance patterns  
- **Monthly Returns**: Track monthly performance trends
- **Yearly Returns**: Assess annual performance metrics

### 🔍 Historical Crisis Detection

The application identifies and analyzes historical worst-case market events:
- **Worst-K Analysis**: Find the K worst performing periods (e.g., worst 5 days)
- **Threshold Analysis**: Identify periods below specific return thresholds
- **Monte Carlo Simulation**: Predict potential extreme events using t-distribution modeling
- **Left Tail Analysis**: Focus on worst-case scenarios in return distributions

### 📈 Visualization & Insights
- Interactive plots of return distributions for all timeframes
- Q-Q plots for distribution analysis
- Historical vs. expected worst-case comparisons
- Volatility surface visualization

### 🎯 Usage Example
```python
from fentu.explatoryservices.volcalculator import VolatilityFacade

# Analyze a ticker (e.g., TQQQ, SPY, QQQ)
ticker = "TQQQ"
volatility = VolatilityFacade(ticker)

# Visualize returns
volatility.visualize_daily_percentage_change()
volatility.visualize_weekly_percentage_change()
volatility.visualize_monthly_percentage_change()

# Find worst-case scenarios
worst_days = volatility.find_worst_k_days(k=5)      # 5 worst days
worst_weeks = volatility.find_worst_k_weeks(k=3)    # 3 worst weeks
worst_months = volatility.find_worst_k_months(k=3)  # 3 worst months

# Crisis threshold analysis
crisis_weeks = volatility.find_worst_weeks(threshold=-0.1)  # Weeks with -10%+ losses
```

This tool is particularly valuable for risk management, helping traders and investors understand historical crisis patterns and prepare for potential future extreme market events.


