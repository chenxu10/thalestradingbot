"""CANSLIM criterion C screen: pull quarterly EPS from yfinance and apply it.

Usage:
    uv run python -m fentu.canslim.screen 3696.HK
    uv run python -m fentu.canslim.screen 3696.HK --min-growth 0.25
    uv run python -m fentu.canslim.screen ONC    # BeOne Medicines (ex-BeiGene), Nasdaq
"""
import argparse
import sys
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

import pandas as pd

from fentu.canslim.current_eps import CurrentEpsCriterion

DILUTED_EPS_ROW = "Diluted EPS"
SAME_QUARTER_TOLERANCE_DAYS = 100


@dataclass(frozen=True)
class ScreenResult:
    ticker: str
    current_eps: Optional[float]
    prior_year_eps: Optional[float]
    current_period: Optional[str]
    prior_period: Optional[str]
    growth: Optional[float]
    passed: bool
    reason: str


def fetch_quarterly_eps(ticker: str) -> pd.DataFrame:
    import yfinance as yf

    return yf.Ticker(ticker).quarterly_income_stmt


def align_same_quarter_last_year(stmt: pd.DataFrame, tolerance_days: int = SAME_QUARTER_TOLERANCE_DAYS):
    """Most recent period end and the period nearest one year earlier, or None if unmatched."""
    periods = sorted(stmt.columns)
    current = periods[-1]
    target = current - timedelta(days=365)
    candidates = [c for c in periods[:-1] if abs((c - target).days) <= tolerance_days]
    if not candidates:
        return current, None
    prior = min(candidates, key=lambda c: abs((c - target).days))
    return current, prior


def screen_current_eps(ticker: str, min_growth: float = 0.20) -> ScreenResult:
    stmt = fetch_quarterly_eps(ticker)
    if stmt is None or stmt.empty or DILUTED_EPS_ROW not in stmt.index:
        return ScreenResult(ticker, None, None, None, None, None, False, "no_quarterly_data")
    eps_series = stmt.loc[DILUTED_EPS_ROW]
    current_period, prior_period = align_same_quarter_last_year(stmt)
    if prior_period is None:
        return ScreenResult(ticker, None, None, str(current_period.date()), None, None, False, "no_prior_year_quarter")
    current_eps = float(eps_series[current_period])
    prior_year_eps = float(eps_series[prior_period])
    if pd.isna(current_eps) or pd.isna(prior_year_eps):
        return ScreenResult(ticker, None, None, str(current_period.date()), str(prior_period.date()), None, False, "missing_eps")
    result = CurrentEpsCriterion(min_growth).score(current_eps, prior_year_eps)
    reason = result.reason if result.reason is not None else ("" if result.passed else "below_threshold")
    return ScreenResult(
        ticker,
        current_eps,
        prior_year_eps,
        str(current_period.date()),
        str(prior_period.date()),
        result.growth,
        result.passed,
        reason,
    )


def _format_growth(growth: Optional[float]) -> str:
    if growth is None:
        return "-"
    return f"{growth * 100:.1f}%"


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="CANSLIM criterion C screen (current quarterly EPS)")
    parser.add_argument("ticker", help="yfinance ticker, e.g. 3696.HK")
    parser.add_argument("--min-growth", type=float, default=0.20, help="YoY growth threshold (default 0.20)")
    args = parser.parse_args(argv)

    result = screen_current_eps(args.ticker, args.min_growth)
    verdict = "PASS" if result.passed else "FAIL"
    print(f"{verdict}  {result.ticker}  criterion C (min growth {args.min_growth * 100:.0f}%)")
    print(f"  reason : {result.reason or 'meets threshold'}")
    print(f"  quarter: {result.current_period or '-'}  EPS {result.current_eps if result.current_eps is not None else '-'}")
    print(f"  prior  : {result.prior_period or '-'}  EPS {result.prior_year_eps if result.prior_year_eps is not None else '-'}")
    print(f"  growth : {_format_growth(result.growth)}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())