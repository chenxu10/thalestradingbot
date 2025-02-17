import numpy as np
import pandas as pd
import yfinance as yf
from datetime import timedelta

# 策略参数
INITIAL_CAPITAL = 50000  # 初始资金5万美金
RISK_RESERVE = 10000     # 风险准备金
TARGET_DELTA = 33000     # 目标delta值
MONTHLY_TARGET = 8325    # 月建仓目标
STRIKE_OFFSET = 0.05     # 执行价偏移5%
BASE_PREMIUM_RATIO = 0.3 # 基础权利金比率
PUT_PROTECTION_RATIO = 0.4  # 期权收入用于买put保护的比例

def calculate_iv(ticker, date):
    """计算隐含波动率（简化版）"""
    try:
        opts = ticker.option_chain(date.strftime('%Y-%m-%d'))
        atm_puts = opts.puts[opts.puts['strike'] > ticker.history(start=date).iloc[0]['Close']*0.95]
        return atm_puts.iloc[0]['impliedVolatility']
    except:
        return np.nan

def calculate_max_drawdown(returns):
    """计算最大回撤"""
    peak = returns.expanding().max()
    return (returns / peak - 1).min()

def calculate_option_params(price, iv, strike_offset_modifier):
    """Calculate option parameters for both put/call selling"""
    strike = price * (1 + strike_offset_modifier * STRIKE_OFFSET)
    premium_rate = iv / np.sqrt(52) * BASE_PREMIUM_RATIO
    premium = price * premium_rate
    return strike, premium
    
def backtest_strategy(tqqq_data, spy_data):
    """
    回测核心逻辑
    :param tqqq_data: 包含OHLC和30天波动率的数据
    :param spy_data: SP500基准数据
    :return: 回测结果字典
    """
    cash = INITIAL_CAPITAL
    shares = 0
    portfolio = pd.Series(index=tqqq_data.index, dtype=float)
    weekly_dates = pd.date_range(start=tqqq_data.index[0], end=tqqq_data.index[-1], freq='W-FRI')
    
    # 保护性put跟踪
    put_protection_cost = 0
    put_protection_value = 0
    
    # 成本跟踪
    total_cost = 0
    equivalent_cost = 0
    
    # 历史记录跟踪
    equivalent_cost_history = pd.Series(index=weekly_dates)
    put_protection_history = pd.Series(index=weekly_dates)
    cash_history = pd.Series(index=weekly_dates)
    shares_history = pd.Series(index=weekly_dates)
    price_history = pd.Series(index=weekly_dates)
    
    tqqq_ticker = yf.Ticker('TQQQ')
    
    for i, date in enumerate(weekly_dates):
        if date in tqqq_data.index:
            # 当前价格和可用资金
            price = tqqq_data.loc[date, 'Adj Close']
            available_cash = max(cash - RISK_RESERVE, 0)
            
            # 计算目标持仓
            iv = calculate_iv(tqqq_ticker, date)
            if np.isnan(iv):
                iv = tqqq_data.loc[date, '30d_vol']
                
            # 动态调整目标持仓（4个月建仓期）
            elapsed_months = min(i // 4, 4)  # 每周调整一次
            target_shares = min((elapsed_months+1)*MONTHLY_TARGET / price, TARGET_DELTA/price)
            
            # 期权交易逻辑
            if shares < target_shares:  # 吸货阶段：卖出put
                strike, premium = calculate_option_params(price, iv, -1)
                cash += premium
                
                # 购买保护性put（使用期权收入的40%）
                put_cost = premium * PUT_PROTECTION_RATIO
                put_protection_cost += put_cost
                cash -= put_cost
                
                # 检查行权
                next_week = date + timedelta(days=7)
                if next_week in tqqq_data.index and tqqq_data.loc[next_week, 'Low'] < strike:
                    shares_to_buy = available_cash // strike
                    shares += shares_to_buy
                    cash -= shares_to_buy * strike
                    total_cost += shares_to_buy * strike - premium  # 计算等效成本
                    
            else:  # 超额阶段：卖出call
                strike, premium = calculate_option_params(price, iv, 1)
                cash += premium
                
                # 检查行权
                next_week = date + timedelta(days=7)
                if next_week in tqqq_data.index and tqqq_data.loc[next_week, 'High'] > strike:
                    shares_to_sell = min(shares - target_shares, available_cash//strike)
                    shares -= shares_to_sell
                    cash += shares_to_sell * strike
                    total_cost -= shares_to_sell * strike - premium  # 调整等效成本
                    
            # 更新等效成本
            if shares > 0:
                equivalent_cost = total_cost / shares
                
            # 计算当日净值（包含保护性put价值）
            portfolio.loc[date] = shares * price + cash + put_protection_value
            
            # 历史记录跟踪
            equivalent_cost_history[date] = equivalent_cost
            put_protection_history[date] = put_cost if shares < target_shares else 0
            cash_history[date] = cash
            shares_history[date] = shares
            price_history[date] = price

    # 计算基准回报
    spy_returns = spy_data['Adj Close'].pct_change().add(1).cumprod()
    strategy_returns = portfolio.ffill().pct_change().add(1).cumprod()
    
    # 生成报告
    report = {
        'strategy_returns': strategy_returns,
        'benchmark_returns': spy_returns,
        'equivalent_cost': equivalent_cost,
        'max_drawdown': calculate_max_drawdown(strategy_returns),
        'put_protection_cost': put_protection_cost,
        'equivalent_cost_history': equivalent_cost_history,
        'put_protection_history': put_protection_history,
        'cash_history': cash_history,
        'shares_history': shares_history,
        'price_history': price_history
    }
    
    return report

def add_historical_volatility_column(df, price_col='Adj Close'):
    """
    Calculate 30-day historical volatility for given price series
    :param df: DataFrame containing price data
    :param price_col: Name of column containing price values
    :return: DataFrame with '30d_vol' column added and NaN rows removed
    """
    df['30d_vol'] = (
        df[price_col].pct_change()
        .rolling(30, min_periods=1).std() 
        * np.sqrt(252)  # Annualize
    )
    return df.dropna()

def main():
    start_date = '2020-01-01'
    tqqq_data = yf.download('TQQQ', start=start_date)
    spy_data = yf.download('SPY', start=start_date)
    tqqq_data = add_historical_volatility_column(tqqq_data)   
    report = backtest_strategy(tqqq_data, spy_data)
    print(report["benchmark_returns"])
    print(report["benchmark_returns"].iloc[1])
    assert abs(report["benchmark_returns"].iloc[1] - 0.992428) <= 0.0001
    
if __name__ == "__main__":
    main()
