"""Morning brief — one-line overnight HK summary for a US-east based trader.

The smallest cost / highest value feature: reuse the existing `ReturnsRepository`
network seam (the ONLY object that touches yfinance) to fetch ^HSI OHLC, then
print one line: last HSI close + overnight % move.

No plotting, no scheduler, no new network path. The deep-dive (`see_change
daily ^HSI`) already exists; this answers the single sentence the trader asks
every US-east morning before any chart load.

The overnight percent move is *not* a body statistic: it is reported as a
signed MAD-multiple against the recent 60-day calm, plus a `CHUTE` flag when the
down-move is past the gate. HSI is equities, EM-adjacent — "up the escalator,
down the chute.' Rallies are calm; sell-offs bring the skew that pays the tail
hedger. STD is forbidden (a body metric on a fat-tailed variable; STD/MAD
~1.6+ in HSI); MAD is the scale, the sign is kept, and a down-move past 2.5 MAD
prints `CHUTE`. See `featurerequest/morning_brief_mad_chute.md`.


CLI
---
* ``python -m fentu.explatoryservices.morning_brief``  — print the one-line
  overnight HSI summary (last close + % move o/n), or ``HSI unavailable`` on a
  network hiccup.
"""
from fentu.explatoryservices.volcalculator import ReturnsRepository

HSI_TICKER = "^HSI"
MAD_WINDOW = 60
CHUTE_THRESHOLD = 2.5


def morning_brief(repository=None):
    """One-line overnight HK summary: HSI close + signed MAD-multiple + flag.

    The overnight % move is scaled by the mean absolute deviation of the prior
    ``MAD_WINDOW`` daily returns (the recent calm; the overnight move never
    calibrates its own denominator) and kept signed. A down-move past
    ``CHUTE_THRESHOLD`` MAD prints ``CHUTE``; anything else is ``escalator``.

    `repository` is injectable for testing (defaults to a fresh
    `ReturnsRepository`, which does NO I/O until asked).
    """
    repo = repository if repository is not None else ReturnsRepository()
    reading = _overnight_reading(repo, HSI_TICKER)
    if reading is None:
        return "HSI unavailable"
    last, pct, mad_multiple = reading
    pct_sign = "+" if pct >= 0 else ""
    mad_line = _mad_suffix(mad_multiple)
    return f"HSI {last:,.0f} ({pct_sign}{pct:.2f}% o/n{mad_line})"


def _mad_suffix(mad_multiple):
    """Render the signed MAD-multiple and the chute/escalator flag.

    ``None`` (calibration window empty / MAD zero) ⇒ no suffix: we still report
    the close + percent move rather than going dark on a short yfinance feed.
    """
    if mad_multiple is None:
        return ""
    mad_sign = "+" if mad_multiple >= 0 else ""
    flag = "CHUTE" if mad_multiple < -CHUTE_THRESHOLD else "escalator"
    return (
        f", {mad_sign}{mad_multiple:.1f} MAD over {MAD_WINDOW}d — {flag}"
    )


def _overnight_reading(repo, ticker):
    """Last close, overnight % move, and signed MAD-multiple for `ticker`.

    Returns ``(last_close, pct, mad_multiple)`` or ``None`` if data is empty /
    fetch blows up. ``mad_multiple`` is ``None`` when the prior-history window
    is empty (no MAD to compute). The morning brief must never crash on a
    network hiccup before coffee.
    """
    ohlc = _safe_raw_ohlc(repo, ticker)
    if ohlc is None:
        return None
    close = ohlc.get("Close")
    if close is None or len(close) < 2:
        return None
    last = float(close.iloc[-1])
    prior = float(close.iloc[-2])
    pct = _pct_move(last, prior)
    mad_multiple = _signed_mad_multiple(close, pct)
    return last, pct, mad_multiple


def _pct_move(last, prior):
    """Percent move from ``prior`` close to ``last`` close."""
    return (last / prior - 1.0) * 100.0


def _signed_mad_multiple(close, overnight_pct):
    """Signed overnight-move MAD-multiple vs the prior ``MAD_WINDOW`` calm.

    Returns ``None`` when the prior window is empty or MAD is zero. The
    overnight move (the last return) is excluded from the calibration window so
    the event never dilutes its own denominator. MAD, not STD: it exists
    whenever the mean exists, and is not inflated by the fourth moment HSI does
    not have.
    """
    returns = close.pct_change().iloc[1:-1] * 100.0  # prior returns only
    window = returns.dropna().iloc[-MAD_WINDOW:]
    if window.empty:
        return None
    mad = window.sub(window.mean()).abs().mean()
    if not mad or mad != mad:  # 0.0 or NaN
        return None
    return float(overnight_pct / mad)


def _safe_raw_ohlc(repo, ticker):
    """Fetch OHLC, returning None on any exception or odd shape.

    `ReturnsRepository._raw_ohlc` assumes yfinance returns a tz-aware
    DatetimeIndex; tickers that 404 yield a plain Index and crash the
    pre-existing helper. The brief stays green.
    """
    try:
        return repo._raw_ohlc(ticker)
    except Exception:
        return None


def main():
    print(morning_brief())


if __name__ == "__main__":
    main()