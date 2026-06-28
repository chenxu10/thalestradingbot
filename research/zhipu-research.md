# Zhipu Upstream Supplier Research — Hypothesis Set

## Compute / accelerators (dominant cost leg — κ-suspect)

| Entity | Ticker | Role | Confidence | Convexity axis |
|---|---|---|---|---|
| NVIDIA | NVDA | H800/H20 (China-permitted) GPUs | High (export-control regime forces it) | Exposed to embargo tail — gap delta at the trigger |
| Huawei Ascend | private (subs 002152.SZ) | Domestic fallback accelerator (910B/910C) | High (stated substitution policy) | Regime-change payoff; watch skew instability |
| Cambricon | 688256.SH | Domestic GPU aspirant | Medium | Pure-tail bet; revenue power-law, mostly loss-making |

## Cloud / training infrastructure

| Entity | Ticker | Role | Confidence |
|---|---|---|---|
| Alibaba Cloud | BABA / 9988.HK | Likely compute-tenant + investor-adjacent | Medium |
| Tencent Cloud | TCEHY / 0700.HK | Reported partner | Medium |
| Baidu Cloud | BIDU / 9888.HK | Possible | Low |
| Huawei Cloud | private (subs 002152.SZ) | Ascend stack bundling | Medium |

## Foundry / silicon upstream (the real choke point — tax on every model)

| Entity | Ticker | Role | Confidence |
|---|---|---|---|
| TSMC | TSM / 2330.TW | Fabricates NVIDIA + Ascend | High — single point of failure |
| SMIC | 00981.HK / 688981.SH | Domestic foundry, limited 7nm+ capability | High for fragility, low for substitution |
| Samsung Foundry | 005930.KS | Secondary advanced-node source | Medium |

## Memory / HBM (under-appreciated bottleneck tail)

| Entity | Ticker | Role | Confidence |
|---|---|---|---|
| SK Hynix | 000660.KS | Dominant HBM supplier | High |
| Micron | MU | HBM3E qualified at NVIDIA | High |

## Packaging / advanced interconnect

| Entity | Ticker | Role | Confidence |
|---|---|---|---|
| ASE / SPIL | ASX / 3711.TW | CoWoS packaging throughput | Medium-High |
| Amkor | AMKR | Advanced packaging | Medium |

## Power / cooling (magnitudes ignored by most screens)

| Entity | Ticker | Role | Confidence |
|---|---|---|---|
| Vertiv | VRT | Datacenter power/cooling | Medium — serves all AI, not Zhipu-specific |
| Eaton | ETN | Datacenter power/cooling | Medium |
| Schneider Electric | SU.PA | Datacenter power/cooling | Medium |

## Software / framework (thin tail, low convexity)

| Entity | Ticker | Role | Confidence |
|---|---|---|---|
| Microsoft / Azure | MSFT | Possibly via partnership | Low |
| Open-source (PyTorch, DeepSpeed) | — | Free | High — irrelevant for pricing |

---

## How to use this list (per the Taleb critique)

1. **Don't pick "Zhipu's suppliers" — pick the SDF of the choke point.**
   TSMC + SK Hynix + ASE are the smallest decomposable fragment: every model,
   Chinese or not, pays them. That's where the convexity sits, not in any one
   named customer relationship.

2. **Apply power-law relative pricing.** Anchor on TSMC ADR (liquid), estimate
   α on its returns via Hill MLE, then imply the price of the less-liquid
   domestic peers (SMIC, Cambricon) — don't take their P/B at face value.

3. **Stochasticize α downward.** If export-control regimes can tighten, the
   tail exponent falls for the beneficiaries (TSMC/Ascend/HBM) — model α at
   its minimum plausible value, never its mean.

4. **Wittgenstein's ruler on Chinese small-caps** (SMIC A-shares, Cambricon):
   their multiples may look absurd because the numerator (earnings) is the
   broken ruler under the embargo regime, not because they're mispriced. Don't
   screen them out.

5. **If a name is cheap-on-P/B + high-ROIE + screenable by you**, assume it's
   driftwood — there are gap orders at the trigger. Look instead at the names
   *adjacent* to the screenable ones (ASE packaging, Hynix HBM, Vertiv power)
   where the tail repricing hasn't been arbitraged.
