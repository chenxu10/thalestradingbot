# Wing-to-Body Tail Cheapness Gauge — Story & Test List

## Nassim's story

> **As a** tail-hedge trader funding convexity with short strangles,
> **I want** one chart that plots far-OTM wing cost (3m and 6m puts and calls) divided by the ATM straddle price over the last 2 years, with 25th/75th-percentile threshold lines and buy-dots marked,
> **so that** I can decide on any given morning whether tail protection is cheap enough to buy or too expensive to chase.

| INVEST | Yes/No | Why |
|---|---|---|
| **I**ndependent | ✅ | Standalone view; depends on nothing but the existing option-price feed |
| **N**egotiable | ✅ | Threshold (quartile vs 10th pct), wing distance (20% vs 15% OTM), and shading style are open until first demo |
| **V**aluable | ✅ | Converts a gut decision into a falsifiable rule: buy when ratio < bottom quartile — directly gates the wing purchase |
| **E**stimable | ✅ | One ratio function + one percentile line + one dot marker; a day of work |
| **S**mall | ✅ | One chart, no dashboard, no alerts, no config UI |
| **T**estable | ✅ | "Given 3m put $4.46 and straddle $69.83, ratio = 0.0639"; "given the 2-yr history, 25th-pct line = X"; "given ratio crossing below line on 2026-06-09, a dot renders on that date" |

**Acceptance:** the ratio is `wing_price / straddle_price` using mid-market closes; both series filtered to same-day quotes; the chart redraws on any day the data updates; the first automated test is the real Aug 7, 2026 data point (QQQ $723.03, Nov 20 expiry 105 DTE, ATM 725 straddle $69.83, 20% OTM 580 put $4.46 → ratio 0.0639).

## Kent's test list (F.I.R.S.T.)

Every test is **F**ast (in-memory numbers, no feed, no network), **I**ndependent (no shared state, no ordering), **R**epeatable (same inputs, same result, always), **S**elf-validating (boolean assertions, no eyeballing a chart), **T**imely (written *before* the code, one failing test at a time).

| # | Test | Behavior |
|---|---|---|
| **T1** | **Starter: single ratio.** `ratio(4.46, 69.83)` → 0.0639 (real Aug 7, 2026 data, Evident Data). | Wing price ÷ same-date ATM straddle. |
| **T2** | **Percentile thresholds.** Given the 2-year ratio series, `percentile(series, 25)` and `percentile(series, 75)` return the correct values on a small hand-built series, method pinned in the test. | 25th/75th percentile of the ratio history. |
| **T3** | **Daily series with same-date matching.** Given wing and straddle quote lists with some dates missing on one side, `daily_series(...)` returns one entry per date present in *both*, per maturity (3m, 6m), no invented data. | Clean, matched daily ratio series. |
| **T4** | **Buy-signal detection.** Given `[0.30, 0.29, 0.25, 0.24, 0.26]` and 25th-pct line 0.24, `signals(...)` marks only the date of the *crossing below* the line — not every day below, not the re-cross above. | The wing-purchase trigger rule. |
| **T5** | **Render output.** Given series + two threshold lines + signal dates, `render(...)` returns a chart object with exactly 2 line artists and 1 dot at the signal date — asserted from the axes, not a screenshot. | The thinnest plotting layer over proven logic. |

## Implementation order

| Order | Test | Reason |
|---|---|---|
| 1 | **T1 ratio** | **Starter Test** — green in minutes, answers "where does this belong?" (pure function). ✅ **DONE** — `fentu/pricingservices/tail_ratio.py`, one assertion, suite green. |
| 2 | **T2 percentile** | Second pure function, no I/O — **Obvious Implementation**. |
| 3 | **T3 daily series** | Data plumbing, still pure: list in, list out. **One Step Test** from known to unknown. |
| 4 | **T4 signals** | The business decision — crossing rule earns its regression guard forever. |
| 5 | **T5 render** | Last: the plotting library is the only untrusted dependency; T1–T4 are the green ratchet under it. |

Refactor between each; none of the tests may touch the network or database — a test that isn't run is risk piling up in silence.
