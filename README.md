# Thales Trading Bot
> It's much better to be convex than to be right, of course in a cost-effective way.

## Main Features

- **Realized-volatility analysis** — daily/weekly/monthly/yearly return distributions, QQ plots, histograms, and power-law tail fits via `see_change.py`.
- **IV term-structure monitor** — ATM implied-vol curve (1D / 3D / 1W / 3M / 1M / 3M / 6M) from yfinance option chains, rendered alongside the realized-vol panels. 
- **VIX subplot** — full `^VIX` history (1990→today) rendered as a separate subplot in `see_change`, plus a current-value annotation: today's 9:30 ET open if the market has opened, otherwise the last trading day's close. Network-failure-safe.


## Hello World

Visualize QQQ daily returns plus its IV term structure:

```bash
uv run fentu/explatoryservices/seechange.py daily QQQ
```

Run the test suite:

```bash
uv run pytest
```

## Story
1. As s trader, I want to able to see VIX(historical low, medium and high region) and short term treasury notes
so that I can make decison about dynamic zhanqi, open and close


---

# 泰利斯交易机器人
> 凸性远比正确更重要，当然要以成本可控的方式。


## 主要功能

- **已实现波动率分析** — 通过 `see_change.py` 给出日/周/月/年收益分布、QQ 图、直方图与幂律尾部拟合。
- **隐含波动率期限结构监控** — 从 yfinance 期权链提取 ATM 隐含波动率曲线（1日/3日/1周/3周/1月/3月/6月），与已实现波动率面板同屏渲染。


## 快速开始

可视化 QQQ 日度收益及其隐含波动率期限结构：

```bash
uv run fentu/explatoryservices/seechange.py daily QQQ
```

运行测试：

```bash
uv run pytest
```
