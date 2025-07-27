# Thales 交易机器人

*阅读其他语言版本: [English](README.md), [中文](README_zh.md)*

> 当你错了的时候如何赚钱？凸性比正确性更重要。

## 使用 uv 进行环境设置

本项目使用 [uv](https://github.com/astral-sh/uv) 进行快速 Python 包管理。请按照以下步骤操作：

### 1. 安装 uv
```bash
# macOS/Linux（使用 curl 或 pip）
curl -LsSf https://astral.sh/uv/install.sh | sh || pip install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 设置项目
```bash
git clone <repository-url>
cd thalestradingbot
uv sync
```

### 3. 运行应用程序
```bash
# 使用 uv 运行（推荐）
uv run python -m fentu.explatoryservices.volcalculator

# 或者在激活环境后运行
python -m fentu.explatoryservices.volcalculator
```

## 主要功能

该应用程序旨在分析金融市场数据并识别历史最坏情况。核心功能包括：

### 📊 多时间框架收益分析
- **日收益率**：分析日常价格变动
- **周收益率**：检查每周表现模式  
- **月收益率**：跟踪月度表现趋势
- **年收益率**：评估年度表现指标

### 🔍 历史危机检测

应用程序识别和分析历史最坏情况市场事件：
- **最差K值分析**：找出K个表现最差的时期（例如，最差的5天）
- **阈值分析**：识别低于特定收益阈值的时期
- **蒙特卡罗模拟**：使用t分布建模预测潜在极端事件
- **左尾分析**：专注于收益分布中的最坏情况

### 📈 可视化与洞察
- 所有时间框架收益分布的交互式图表
- 用于分布分析的Q-Q图
- 历史与预期最坏情况比较
- 波动率曲面可视化

### 🎯 使用示例
```python
from fentu.explatoryservices.volcalculator import VolatilityFacade

# 分析股票代码（例如，TQQQ、SPY、QQQ）
ticker = "TQQQ"
volatility = VolatilityFacade(ticker)

# 可视化收益率
volatility.visualize_daily_percentage_change()
volatility.visualize_weekly_percentage_change()
volatility.visualize_monthly_percentage_change()

# 找出最坏情况
worst_days = volatility.find_worst_k_days(k=5)      # 最差的5天
worst_weeks = volatility.find_worst_k_weeks(k=3)    # 最差的3周
worst_months = volatility.find_worst_k_months(k=3)  # 最差的3个月

# 危机阈值分析
crisis_weeks = volatility.find_worst_weeks(threshold=-0.1)  # 损失超过-10%的周
```

此工具对风险管理特别有价值，帮助交易者和投资者了解历史危机模式，为潜在的未来极端市场事件做好准备。 