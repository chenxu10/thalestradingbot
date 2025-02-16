import pytest
import pandas as pd
import numpy as np
from backtest.core import backtest_strategy

@pytest.fixture
def mock_financial_data():
    """生成模拟的TQQQ和SPY数据"""
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='B')
    return {
        'tqqq': pd.DataFrame({
            'Adj Close': np.linspace(50, 150, len(dates)),
            '30d_vol': np.random.uniform(0.3, 0.6, len(dates)),
            'Low': np.random.uniform(0.3, 0.6, len(dates)),
            'High': np.random.uniform(0.3, 0.6, len(dates),)
        }, index=dates),
        'spy': pd.DataFrame({
            'Adj Close': np.linspace(300, 500, len(dates))
        }, index=dates)
    }

def test_backtest_strategy(mock_financial_data):
    """测试完整的回测流程"""
    results = backtest_strategy(
        mock_financial_data['tqqq'],
        mock_financial_data['spy']
    )
   
    # 验证收益曲线长度
    assert len(results['strategy_returns']) == len(mock_financial_data['tqqq'])
    
