"""CANSLIM criterion M: market direction filter (O'Neil, Market Wizards 2006).

"Three out of four stocks will go in the same direction as a significant move
in the market averages" — criterion M therefore gates the whole portfolio, not
individual names. This module reads daily OHLCV for the S&P 500 index and
scores the current tape against O'Neil's two top-formation signals:

    1. the average made a new high on poor demand — the index sits below its
       50-day SMA, or the SMA has stopped rising;
    2. heavy-volume down days ("distribution days") — volume surges for several
       days with little or no upside price progress. O'Neil: after a few such
       days the market is under pressure.

PASS requires the close above a rising 50-day SMA AND at most
``--max-distribution-days`` heavy-volume down sessions in the trailing 25.

Usage:
    uv run python -m fentu.canslim.market_direction
    uv run python -m fentu.canslim.market_direction --index ^NDX
    uv run python -m fentu.canslim.market_direction --max-distribution-days 3
"""
import argparse
import sys
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import pandas as pd

DEFAULT_INDEX = "^GSPC"
DEFAULT_MAX_DISTRIBUTION_DAYS = 4
DEFAULT_MA_WINDOW = 50
DEFAULT_RISE_LOOKBACK = 5
DEFAULT_DIST_LOOKBACK = 25
DEFAULT_VOLUME_MULT = 1.25


@dataclass(frozen=True)
class MarketResult:
    index: str
    close: Optional[float]
    sma50: Optional[float]
    ma_rising: bool
    distribution_days: int
    passed: bool
    reason: str


def fetch_index_history(index: str = DEFAULT_INDEX) -> pd.DataFrame:
    """Daily OHLCV for the index (Open/High/Low/Close/Volume), the only I/O."""
    import yfinance as yf

    return yf.Ticker(index).history(period="6mo", auto_adjust=False)


def sma(closes: List[float], window: int) -> List[float]:
    """Rolling simple moving average; leading ``window - 1`` entries are NaN."""
    return pd.Series(closes).rolling(window).mean().tolist()


def _ma_rising(closes: List[float], window: int = DEFAULT_MA_WINDOW, rise_lookback: int = DEFAULT_RISE_LOOKBACK) -> bool:
    if len(closes) < window + rise_lookback:
        return False
    values = sma(closes, window)
    return values[-1] > values[-1 - rise_lookback]


def above_rising_ma(closes: List[float], window: int = DEFAULT_MA_WINDOW, rise_lookback: int = DEFAULT_RISE_LOOKBACK) -> bool:
    """Latest close above the SMA AND the SMA itself is rising (vulnerable rally test)."""
    if len(closes) < window + rise_lookback:
        return False
    values = sma(closes, window)
    return closes[-1] > values[-1] and values[-1] > values[-1 - rise_lookback]


def distribution_days(
    ohlcv: pd.DataFrame,
    lookback: int = DEFAULT_DIST_LOOKBACK,
    volume_mult: float = DEFAULT_VOLUME_MULT,
) -> int:
    """Heavy-volume down sessions in the trailing ``lookback``.

    O'Neil's distribution concept: close below the prior close on volume well
    above the recent average — volume surges with no upside price progress.
    """
    closes = [float(c) for c in ohlcv["Close"].tolist()]
    volumes = [float(v) for v in ohlcv["Volume"].tolist()]
    if len(closes) < 2:
        return 0
    avg_volume = sum(volumes[-lookback:]) / min(lookback, len(volumes))
    start = max(len(closes) - lookback, 1)
    return sum(
        1
        for i in range(start, len(closes))
        if closes[i] < closes[i - 1] and volumes[i] > volume_mult * avg_volume
    )


def market_verdict(
    closes: List[float],
    ohlcv: pd.DataFrame,
    max_distribution_days: int = DEFAULT_MAX_DISTRIBUTION_DAYS,
    ma_window: int = DEFAULT_MA_WINDOW,
    rise_lookback: int = DEFAULT_RISE_LOOKBACK,
    dist_lookback: int = DEFAULT_DIST_LOOKBACK,
    volume_mult: float = DEFAULT_VOLUME_MULT,
) -> Tuple[bool, str]:
    """Pure sub-signal composition: (passed, reason). First failing signal wins."""
    if not above_rising_ma(closes, ma_window, rise_lookback):
        last_sma = sma(closes, ma_window)[-1]
        if closes[-1] <= last_sma:
            return False, "below_50ma"
        return False, "ma_not_rising"
    if distribution_days(ohlcv, dist_lookback, volume_mult) > max_distribution_days:
        return False, "distribution_days_high"
    return True, ""


def _failure(index: str) -> MarketResult:
    return MarketResult(
        index=index,
        close=None,
        sma50=None,
        ma_rising=False,
        distribution_days=0,
        passed=False,
        reason="no_price_history",
    )


def _sma50(closes: List[float], window: int = DEFAULT_MA_WINDOW) -> Optional[float]:
    values = sma(closes, window)
    last = values[-1]
    return None if pd.isna(last) else float(last)


def market_direction(
    index: str = DEFAULT_INDEX,
    fetch: Callable[[str], pd.DataFrame] = fetch_index_history,
    max_distribution_days: int = DEFAULT_MAX_DISTRIBUTION_DAYS,
) -> MarketResult:
    """Verdict for one index tape: OHLCV -> MarketResult."""
    ohlcv = fetch(index)
    if ohlcv is None or ohlcv.empty or not {"Close", "Volume"}.issubset(ohlcv.columns):
        return _failure(index)
    closes = [float(c) for c in ohlcv["Close"].tolist()]
    passed, reason = market_verdict(closes, ohlcv, max_distribution_days)
    return MarketResult(
        index=index,
        close=closes[-1],
        sma50=_sma50(closes),
        ma_rising=_ma_rising(closes),
        distribution_days=distribution_days(ohlcv),
        passed=passed,
        reason=reason,
    )


def _format_value(value: Optional[float]) -> str:
    return "-" if value is None else f"{value:.2f}"


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="CANSLIM criterion M screen (market direction)")
    parser.add_argument("--index", default=DEFAULT_INDEX, help="index ticker (default ^GSPC)")
    parser.add_argument("--max-distribution-days", type=int, default=DEFAULT_MAX_DISTRIBUTION_DAYS, help="max heavy-volume down days (default 4)")
    args = parser.parse_args(argv)

    result = market_direction(args.index, fetch=fetch_index_history, max_distribution_days=args.max_distribution_days)
    verdict = "PASS" if result.passed else "FAIL"
    print(f"{verdict}  {result.index}  criterion M (market direction)")
    print(f"  reason            : {result.reason or 'market uptrend intact'}")
    print(f"  close             : {_format_value(result.close)}")
    print(f"  50-day SMA        : {_format_value(result.sma50)}")
    print(f"  ma rising         : {result.ma_rising}")
    print(f"  distribution days : {result.distribution_days} (max {args.max_distribution_days})")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
