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

## Taleb-lens TODO — `see_change daily QQQ` plot audit

Evaluated against `.opencode/skills/taleb-convexity-tailhedge/SKILL.md`
(distillation of *Dynamic Hedging* + *Statistical Consequences of Fat Tails*).

### Correct — aligns with Taleb

- [x] QQ plot vs Normal — the **Masquerade asymmetry** ruler; reject Gaussianity as soon as tails overshoot 4–5σ (`plotting_service.py:17`)
- [x] Histogram with Normal + Student-T overlays — Taleb's canonical comparison (`plotting_service.py:48`,`:94`)
- [x] **Separate** left-tail and right-tail power-law fits — "netting hides the 3rd moment" (`volcalculator.py:302`)
- [x] α reported per tail (slope = −α) — feeds the relative pricing `C(K₂)=(K₂/K₁)^{1−α}·C(K₁)` (`see_power_law.py:194`)
- [x] **MAD** computed and shown alongside SD (`plotting_service.py:12`)
- [x] Log returns — consistent with power-law / Karamata work (`volcalculator.py:285`)

### Wrong / missing — against Taleb

- [x] **`StandardDeviationVolatility` is the headline volatility.** Skill: "Retire SD, use MAD." `volcalculator.py:135-145`, displayed `:288` — DONE: `MeanAbsoluteDeviationVolatility` is now the default in `DailyVolatility`; `StandardDeviationVolatility` kept for `*_gaussian_only` comparison. Tests: `tests/test_volatility_metric.py` (10 passed).
- [x] **Kurtosis printed as a clean digit** — misleading; one day = 80% of SP500 kurtosis over 56 yr (`plotting_service.py:14`) — DONE: `calculate_four_moments` now also returns the leave-one-out (drop single most extreme obs) kurtosis; `qq_plot` displays `Kurt: X.XX` alongside `Kurt (drop 1 worst): Y.YY` so single-obs influence is visible. Tests: `tests/test_plotting_service_kurtosis.py` (5 passed).
- [ ] **No κ (Kappa) gauge** — "Report κ beside every sample mean; κ>0.15 ⇒ normal approx unreliable; SP500≈0.2, single stocks 0.3–0.7". QQQ > SP500 concentration. **Absent**
- [ ] **Tail α estimated by OLS on binned histogram density, not Hill MLE** — α̂=n/Σlog(xᵢ/L) is inverse-gamma (low variance); OLS-on-bins is biased & high-variance (`see_power_law.py:78`). Also inconsistent tail_percent defaults: `visualize_percentage_change` 0.10 vs `fit_power_law_slope` 0.20 (`volcalculator.py:438` vs `see_power_law.py:91`)
- [ ] **Realized vol uses full history with no λ≈0.97 exponential decay** — "Traders have GARCH in their heads"; equal-weighting mixes vol regimes silently (`volcalculator.py:155`)
- [ ] **IV term-structure panel is ATM-only** — "VIX is a body/2nd-moment metric; a true 4th-moment/tail bet = sell ATM straddles + buy OTM wings". Missing the entire convexity story (`volcalculator.py:369`)
- [ ] **VIX panel labeled "tail context" without caveat** — VIX measures the 2nd moment, not the tail (`volcalculator.py:421`)
- [ ] **No IV-vs-realized overlay** — the bot's thesis ("better convex than right, cost-effectively") turns on IV-rich/realized-poor *in the tails*; the two are never on the same axis (`volcalculator.py:363`)
- [ ] **QQ reference line is Normal-only** — useful as the Wittgenstein ruler to *reject* Gaussianity, but the actionable ruler for a fat-tailed asset is the Student-T line whose slope yields df/α. Partial (`plotting_service.py:20`)

### Quick fix priority (Taleb-weighted)

1. [x] Rename/demote `StandardDeviationVolatility` → MAD headline, keep STD as `*_gaussian_only` for comparison (`volcalculator.py:135`)
2. [ ] Display Student-T `df` on the histogram; add implied `α=df` to the histogram legend (`plotting_service.py:48`)
3. [ ] Add κ to the QQ annotation block beside Mean/MAD (`plotting_service.py:21`)
4. [ ] Replace the binned-loglog OLS α estimator with a Hill MLE (`see_power_law.py:78`)
5. [ ] Overlay a 25Δ OTM put IV term structure on the ATM term-structure panel — that's the 4th-moment / tail-bet curve (`volcalculator.py:369`)
6. [ ] Overlay realized-vol term structure on the IV curve, or write IV−realized explicitly (`volcalculator.py:363`)
7. [ ] Add a `λ≈0.97` exponentially-weighted returns pass; show plain and EW distributions side-by-side (`volcalculator.py:155`)


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
