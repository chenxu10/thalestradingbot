# Four-Leg Expression — "Frequent Mild Upside, Rare Severe Downside"

View: upside is frequent but severity is limited; downside is rare but
severity is high → **long left-tail 4th moment, long down-skew (3rd moment),
cap the right tail you don't believe in.**

| # | Leg | Moneyness | DTE / bucket | Size | Moment role | What it expresses |
|---|---|---|---|---|---|---|
| 1 | **−1 put** (nearer OTM, K₁) | −8% | 3M (90d) | 1 | sells the *body* of the skew to fund the wing | "downside is rare" → collect the rich near-OTM put IV |
| 2 | **+2 puts** (deep OTM, K₂<K₁) | −22% | 3M (90d) | 2 | **long 4th moment (left tail)**, convex payoff below K₂ | "downside is *severe*" → uncapped +1 unit net put beyond K₂ |
| 3 | **−1 call** (OTM, K₃) | +6% | 3M (90d) | 1 | short the frequent grind-up premium (3rd-moment right-skew finance) | "upside is frequent" → you sell that body |
| 4 | **+1 call** (further OTM, K₄>K₃) | +15% | 3M (90d) | 1 | **caps the upside** since upside severity is limited | "upside severity is limited" → defined loss if thesis wrong |

## Exit rule

Roll the whole structure at the 3M mark if unchanged (don't let the
backspread's short K₁ put go ATM → "narrow the scale like a microscope,"
don't flip delta). If K₂ is approached, *add* to the deep puts (α just
dropped — stochasticize-α raises expected tail); never flatten the
convexity you built.