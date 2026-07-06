"""Morning brief — one-line overnight HK summary for a US-east based trader.

Written test-first (Kent Beck, TDD By Example). Drives a tiny new feature:
`morning_brief()` reuses the existing `ReturnsRepository` network seam (the
ONLY object that touches yfinance) to fetch ^HSI OHLC and print a one-line
briefing. No new plotting, no scheduler, no new network path.

(^VHSI removed — delisted on yfinance feeds: HTTP 404 / no timezone found.)
"""
import pandas as pd
import numpy as np
import pytest
from unittest.mock import MagicMock

from fentu.explatoryservices.volcalculator import ReturnsRepository
from fentu.explatoryservices.morning_brief import morning_brief


HSI_TICKER = "^HSI"


def _ohlc(closes):
    """Build a tz-naive OHLC frame with a Close column (the only one used)."""
    idx = pd.bdate_range("2026-06-18", periods=len(closes))
    return pd.DataFrame({"Close": pd.Series(closes, index=idx, dtype=float)})


class TestMorningBrief:
    def test_reports_hsi_close_and_overnight_pct(self):
        # HSI: 22000 -> 23000 = +4.545% overnight
        hsi = _ohlc([22000.0, 23000.0])
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.return_value = hsi

        brief = morning_brief(repository=repo)

        assert brief == "HSI 23,000 (+4.55% o/n)"

    def test_negative_overnight_move(self):
        hsi = _ohlc([23000.0, 22000.0])  # -4.348%
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.return_value = hsi

        brief = morning_brief(repository=repo)

        assert brief == "HSI 22,000 (-4.35% o/n)"

    def test_uses_default_repository_when_none_injected(self):
        hsi = _ohlc([22000.0, 23000.0])
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "fentu.explatoryservices.morning_brief.ReturnsRepository._raw_ohlc",
                lambda self, t: hsi,
            )
            brief = morning_brief()
        assert brief == "HSI 23,000 (+4.55% o/n)"

    def test_handles_empty_hsi_gracefully(self):
        empty = pd.DataFrame({"Close": pd.Series([], dtype=float)})
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.return_value = empty

        brief = morning_brief(repository=repo)

        assert brief == "HSI unavailable"

    def test_handles_fetch_exception_without_crashing(self):
        """The brief must never crash on a network hiccup before coffee."""
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.side_effect = RuntimeError("network down")

        brief = morning_brief(repository=repo)

        assert brief == "HSI unavailable"