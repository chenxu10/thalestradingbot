"""Far-OTM wing price as a fraction of the same-date ATM straddle price.

Self-checking asserts at module top level: xingjian executes this file on every
save, so these are the honest red/green gate for T1 (story/tail_cheapness_gauge.md).
"""


def wing_to_body_ratio(wing_price: float, straddle_price: float) -> float:
    """Ratio of far-OTM wing price to ATM straddle price, same date."""
    return wing_price / straddle_price


# T1 acceptance: real Aug 7, 2026 data (Evident Data) — QQQ $723.03, Nov 20
# expiry 105 DTE, ATM 725 straddle $69.83, 20% OTM 580 put $4.46.
assert round(wing_to_body_ratio(4.46, 69.83), 4) == 0.0639

# Property invariants that defeat a hardcoded or gamed answer:
assert wing_to_body_ratio(0.0, 69.83) == 0.0                    # no wing, no cost
assert wing_to_body_ratio(69.83, 69.83) == 1.0                  # wing at the money
