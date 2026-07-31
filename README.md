# Thales Trading Bot
> It's much better to be convex than to be right, of course in a cost-effective way.

## Main Features

- **Realized-volatility analysis** — daily/weekly/monthly/yearly return distributions, QQ plots, histograms, and power-law tail fits via `see_change.py`.
- **IV term-structure monitor** — ATM implied-vol curve (1D / 3D / 1W / 3M / 1M / 3M / 6M) from yfinance option chains, rendered alongside the realized-vol panels. 
- **VIX subplot** — full `^VIX` history (1990→today) rendered as a separate subplot in `see_change`, plus a current-value annotation: today's 9:30 ET open if the market has opened, otherwise the last trading day's close. Network-failure-safe.
- **Portfolio signal monitor** — `see_change daily portfolio` shows a fixed 2x2 panel (TQQQ / USO / IAU / BRKB) of percentage changes with Taleb's *Fooled by Randomness* p.166 filter: moves inside the usual daily change (MAD) are grayed out as noise, only large moves are highlighted, and significance is non-linear (a 2x-usual move = a 4x event).


## Hello World

Visualize QQQ daily returns plus its IV term structure:

```bash
uv run fentu/explatoryservices/seechange.py daily QQQ
```

Portfolio signal monitor (Taleb large-change filter):

```bash
uv run fentu/explatoryservices/seechange.py daily portfolio
```

Run the test suite:

```bash
uv run pytest
```

# 泰利斯交易机器人
> 凸性远比正确更重要，当然要以成本可控的方式。


## 主要功能

- **已实现波动率分析** — 通过 `see_change.py` 给出日/周/月/年收益分布、QQ 图、直方图与幂律尾部拟合。
- **隐含波动率期限结构监控** — 从 yfinance 期权链提取 ATM 隐含波动率曲线（1日/3日/1周/3周/1月/3月/6月），与已实现波动率面板同屏渲染。
- **组合信号监控** — `see_change daily portfolio` 以固定 2x2 面板（TQQQ / USO / IAU / BRKB）展示百分比变化，应用塔勒布《随机漫步的傻瓜》第 166 页的过滤法：日常波动幅度（MAD）以内的变化视为噪音（灰色），仅高亮大幅变化；显著性为非线性（2 倍日常波幅 = 4 倍事件）。


## 快速开始

可视化 QQQ 日度收益及其隐含波动率期限结构：

```bash
uv run fentu/explatoryservices/seechange.py daily QQQ
```

组合信号监控（塔勒布大幅变化过滤器）：

```bash
uv run fentu/explatoryservices/seechange.py daily portfolio
```

运行测试：

```bash
uv run pytest
```
