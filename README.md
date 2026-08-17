# Thales Trade Baigui

> It's much better to be convex than to be right, of course in a cost-effective way.

> "For one whose wisdom is not equal to detecting and adapting to change, whose courage is not equal to decisive judgment, whose benevolence is not equal to knowing when to take and when to give, and whose strength is not equal to holding fast — even if he begs to learn my art, I will never teach him." — Sima Qian, *Records of the Grand Historian*.

## Main Features

- **Realized-volatility analysis** — daily/weekly/monthly/yearly return distributions, QQ plots, histograms, and power-law tail fits via `see_change.py`.
- **VIX subplot** — full `^VIX` history (1990→today) rendered as a separate subplot in `see_change`, plus a current-value annotation: today's 9:30 ET open if the market has opened, otherwise the last trading day's close. Network-failure-safe.
- **Portfolio signal monitor** — `see_change daily portfolio` shows a fixed 2x2 panel (TQQQ / USO / IAU / BRKB) of percentage changes with Taleb's *Fooled by Randomness* p.166 filter: moves inside the usual daily change (MAD) are grayed out as noise, only large moves are highlighted, and significance is non-linear (a 2x-usual move = a 4x event).


## Hello World

Visualize QQQ daily returns:

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

# 泰利斯与白圭
> 凸性远比正确更重要，当然要以成本可控的方式。

> 是故其智不足與權變，勇不足以決斷，仁不能以取予，彊不能有所守，雖欲學吾術，終不告之矣。《史记——货殖列传》


## 主要功能

- **已实现波动率分析** — 通过 `see_change.py` 给出日/周/月/年收益分布、QQ 图、直方图与幂律尾部拟合。
- **组合信号监控** — `see_change daily portfolio` 以固定 2x2 面板（TQQQ / USO / IAU / BRKB）展示百分比变化，应用塔勒布《随机漫步的傻瓜》第 166 页的过滤法：日常波动幅度（MAD）以内的变化视为噪音（灰色），仅高亮大幅变化；显著性为非线性（2 倍日常波幅 = 4 倍事件）。


## 快速开始

可视化 QQQ 日度收益：

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
