import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from pandas.tseries.offsets import BDay

def fetch_data(tickers, start_date):
    """获取历史价格数据并进行预处理"""
    data = yf.download(tickers, start=start_date)['Close']
    return data.ffill().dropna()

def calculate_strategy_returns(data, leveraged_ticker, base_ticker, leverage_ratio, initial_cash=10000):
    """计算两种策略的收益"""
    # 计算初始份额
    lev_initial = data[leveraged_ticker].iloc[0]
    base_initial = data[base_ticker].iloc[0]
    
    return pd.DataFrame({
        leveraged_ticker: data[leveraged_ticker] * (initial_cash / lev_initial),
        f'{leverage_ratio}x {base_ticker}': data[base_ticker] * (initial_cash * leverage_ratio / base_initial)
    })

def plot_comparison(pnl_df, leverage_ratio, events, stats_date, output_path):
    """绘制比较图表"""
    plt.figure(figsize=(14, 7))
    
    # 绘制损益曲线
    lev_ticker = pnl_df.columns[0]
    base_label = pnl_df.columns[1]
    
    plt.plot(pnl_df.index, pnl_df[lev_ticker], label=f'{lev_ticker} (Actual {leverage_ratio}x ETF)', color='#1f77b4')
    plt.plot(pnl_df.index, pnl_df[base_label], label=base_label, color='#ff7f0e', linestyle='--')
    
    # 添加事件标注
    for date, info in events.items():
        if date in pnl_df.index:
            plt.annotate(info['text'], 
                        xy=(pd.to_datetime(date), pnl_df.loc[date, lev_ticker]),
                        xytext=(-40, info['y_offset']), 
                        arrowprops=dict(arrowstyle='->', color='grey'),
                        textcoords='offset points',
                        bbox=dict(boxstyle="round", fc="w"))
    
    # 图表美化
    title = f'Volatility Decay Effect: {lev_ticker} vs {leverage_ratio}x {base_label.split()[1]}'
    plt.title(title, fontsize=16, pad=20)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Profit/Loss (USD)', fontsize=12)
    plt.legend(fontsize=12, loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # 填充区域
    plt.fill_between(pnl_df.index, pnl_df[lev_ticker], pnl_df[base_label], 
                    where=(pnl_df[lev_ticker] > pnl_df[base_label]),
                    facecolor='green', alpha=0.1, label=f'{lev_ticker} Outperforming Area')
    plt.fill_between(pnl_df.index, pnl_df[lev_ticker], pnl_df[base_label],
                    where=(pnl_df[lev_ticker] <= pnl_df[base_label]),
                    facecolor='red', alpha=0.1, label=f'{leverage_ratio}x {base_label.split()[1]} Outperforming Area')
    
    # 添加统计信息
    stats_text = f"""Statistics ({pnl_df.index[0].year}-{pnl_df.index[-1].year}):
{lev_ticker} Final P/L: ${pnl_df[lev_ticker].iloc[-1]:,.0f}
{base_label} Final P/L: ${pnl_df[base_label].iloc[-1]:,.0f}
Max Difference: ${(pnl_df[lev_ticker] - pnl_df[base_label]).max():,.0f}"""
    
    try:
        stats_date = pd.to_datetime(stats_date)
    except:
        stats_date = pnl_df.index[-1] - BDay(10)
    
    plt.annotate(stats_text, 
                xy=(stats_date, pnl_df.min().min()),
                xytext=(20, 20), 
                textcoords='offset points',
                bbox=dict(boxstyle="round", fc="w"))
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def analyze_leverage_decay(config):
    """
    主分析函数
    config = {
        'leveraged_ticker': 'TQQQ',
        'base_ticker': 'QQQ',
        'leverage_ratio': 3,
        'start_date': '2010-02-11',
        'events': {
            '2011-08-08': {'text': 'US Debt Downgrade', 'y_offset': -40},
            ...
        },
        'stats_date': '2021-01-04',
        'output_path': 'figures/comparison.png'
    }
    """
    data = fetch_data([config['leveraged_ticker'], config['base_ticker']], config['start_date'])
    strategy_returns = calculate_strategy_returns(
        data, 
        config['leveraged_ticker'],
        config['base_ticker'],
        config['leverage_ratio']
    )
    pnl = strategy_returns - 10000  # 假设初始投资都是$10,000
    plot_comparison(pnl, config['leverage_ratio'], config['events'], config['stats_date'], config['output_path'])

# 示例用法：分析TQQQ vs QQQ
tqqq_config = {
    'leveraged_ticker': 'TQQQ',
    'base_ticker': 'QQQ',
    'leverage_ratio': 3,
    'start_date': '2010-02-11',
    'events': {
        '2011-08-08': {'text': 'US Debt Downgrade', 'y_offset': -40},
        '2015-08-24': {'text': 'CNY Devaluation Crisis', 'y_offset': 20},
        '2018-12-24': {'text': 'Christmas Eve Crash', 'y_offset': -50},
        '2020-03-23': {'text': 'COVID Bottom', 'y_offset': 30},
        '2022-10-14': {'text': 'Bear Market Bottom', 'y_offset': -60}
    },
    'stats_date': '2021-01-04',
    'output_path': 'figures/tqqq_vs_qqq.png'
}

analyze_leverage_decay(tqqq_config)

# 分析TLT vs TMF示例
tmf_config = {
    'leveraged_ticker': 'TMF',
    'base_ticker': 'TLT',
    'leverage_ratio': 3,
    'start_date': '2010-01-01',
    'events': {
        '2013-05-22': {'text': 'Taper Tantrum', 'y_offset': -40},
        '2020-03-18': {'text': 'Fed QE Announcement', 'y_offset': 30},
        '2022-10-21': {'text': 'Rate Hike Peak', 'y_offset': -50}
    },
    'stats_date': '2019-01-02',
    'output_path': 'figures/tmf_vs_tlt.png'
}

analyze_leverage_decay(tmf_config)
