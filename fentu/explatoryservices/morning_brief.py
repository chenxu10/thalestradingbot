"""Morning brief — one-line overnight HK summary for a US-east based trader.

The smallest cost / highest value feature: reuse the existing `ReturnsRepository`
network seam (the ONLY object that touches yfinance) to fetch ^HSI OHLC, then
print one line: last HSI close + overnight % move.

No plotting, no scheduler, no new network path. The deep-dive (`see_change
daily ^HSI`) already exists; this answers the single sentence the trader asks
every US-east morning before any chart load.

(^VHSI removed — delisted on yfinance feeds: HTTP 404 / no timezone found.)
"""
from fentu.explatoryservices.volcalculator import ReturnsRepository

HSI_TICKER = "^HSI"


def morning_brief(repository=None):
    """One-line overnight HK summary: HSI close + % move o/n.

    `repository` is injectable for testing (defaults to a fresh
    `ReturnsRepository`, which does NO I/O until asked).
    """
    repo = repository if repository is not None else ReturnsRepository()
    move = _overnight_move(repo, HSI_TICKER)
    if move is None:
        return "HSI unavailable"
    last, _prior, pct = move
    sign = "+" if pct >= 0 else ""
    return f"HSI {last:,.0f} ({sign}{pct:.2f}% o/n)"


def _overnight_move(repo, ticker):
    """Last close, prior-trading-day close, and pct move for `ticker`.

    Returns (last_close, prior_close, pct) or None if data is empty / fetch
    blows up. The morning brief must never crash on a network hiccup before
    coffee.
    """
    ohlc = _safe_raw_ohlc(repo, ticker)
    if ohlc is None:
        return None
    close = ohlc.get("Close")
    if close is None or len(close) < 2:
        return None
    last = float(close.iloc[-1])
    prior = float(close.iloc[-2])
    pct = (last / prior - 1.0) * 100.0
    return last, prior, pct


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