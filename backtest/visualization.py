import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import PercentFormatter

def plot_backtest_results(results, save_path=None):
    """绘制回测结果图表"""
    plt.style.use('seaborn')
    sns.set_palette("husl")
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示问题
    plt.rcParams['axes.unicode_minus'] = False
    
    fig = plt.figure(figsize=(16, 12))
    
    # 累计收益对比
    ax1 = plt.subplot2grid((3, 2), (0, 0), colspan=2)
    plot_cumulative_returns(ax1, results)
    
    # 等效成本变化
    ax2 = plt.subplot2grid((3, 2), (1, 0))
    plot_equivalent_cost(ax2, results)
    
    # 最大回撤
    ax3 = plt.subplot2grid((3, 2), (1, 1))
    plot_drawdown(ax3, results)
    
    # 保护性Put成本
    ax4 = plt.subplot2grid((3, 2), (2, 0))
    plot_put_protection(ax4, results)
    
    # 资金使用情况
    ax5 = plt.subplot2grid((3, 2), (2, 1))
    plot_cash_usage(ax5, results)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()

def plot_cumulative_returns(ax, results):
    """绘制累计收益曲线"""
    results['strategy_returns'].plot(ax=ax, label='策略收益', linewidth=2)
    results['benchmark_returns'].plot(ax=ax, label='SP500收益', linestyle='--')
    ax.set_title('累计收益对比', fontsize=14)
    ax.set_ylabel('累计收益倍数', fontsize=12)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.legend()
    ax.grid(True, alpha=0.3)

def plot_equivalent_cost(ax, results):
    """绘制等效成本变化"""
    if 'equivalent_cost_history' in results:
        results['equivalent_cost_history'].ffill().plot(ax=ax)
        ax.set_title('等效成本变化趋势', fontsize=14)
        ax.set_ylabel('等效成本 (USD)', fontsize=12)
        ax.grid(True, alpha=0.3)

def plot_drawdown(ax, results):
    """绘制回撤曲线"""
    drawdown = results['strategy_returns'] / results['strategy_returns'].cummax() - 1
    drawdown.plot(ax=ax, color='r', alpha=0.8)
    ax.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.1)
    ax.set_title('最大回撤', fontsize=14)
    ax.set_ylabel('回撤幅度', fontsize=12)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.grid(True, alpha=0.3)

def plot_put_protection(ax, results):
    """绘制保护性Put成本"""
    if 'put_protection_history' in results:
        results['put_protection_history'].cumsum().plot(ax=ax)
        ax.set_title('累计保护性Put成本', fontsize=14)
        ax.set_ylabel('成本 (USD)', fontsize=12)
        ax.grid(True, alpha=0.3)

def plot_cash_usage(ax, results):
    """绘制资金使用情况"""
    if 'cash_history' in results and 'shares_history' in results:
        (results['cash_history']/INITIAL_CAPITAL).plot(ax=ax, label='现金比例')
        (results['shares_history']*results['price_history']/INITIAL_CAPITAL).plot(ax=ax, label='持仓价值')
        ax.set_title('资金分配比例', fontsize=14)
        ax.set_ylabel('比例', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3) 