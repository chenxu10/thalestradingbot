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


def _closes_from_returns(returns_pct, start=28000.0):
    """Build a close series from daily returns expressed in percent.

    ``returns_pct[i]`` is the % change from close ``i`` to close ``i+1``.
    Returned closes have length ``len(returns_pct) + 1`` and start at ``start``.
    """
    closes = [start]
    for r in returns_pct:
        closes.append(closes[-1] * (1.0 + r / 100.0))
    return closes


def _ohlc_with_calibration(prior_returns_pct, overnight_pct, start=28000.0):
    """OHLC whose last return is the overnight move and prior 60 are calibration.

    Returns ``(frame, last_close)`` so tests can format the displayed close in
    the expected string without recomputing it by hand (close is a display
    field; the MAD-multiple, pct, and flag are the independently hand-derived
    assertions).
    """
    all_returns = list(prior_returns_pct) + [overnight_pct]
    closes = _closes_from_returns(all_returns, start)
    return _ohlc(closes), closes[-1]


def _alternating_mad_window(mad, n=60):
    """``n`` returns alternating ``+mad``/``-mad`` % ⇒ MAD == ``mad`` (mean 0)."""
    return [mad if i % 2 == 0 else -mad for i in range(n)]


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


class TestMorningBriefMadChute:
    """Taleb's one feature: a MAD-scaled overnight gap, split by sign, with a
    CHUTE flag. MAD calibrated over the prior 60 trading days (the calm), NOT
    including the overnight move being measured — the event never calibrates its
    own denominator.

    Calibration window here: 60 alternating +/-0.50% returns ⇒ mean 0,
    MAD == 0.50%. An overnight move of X% therefore reads as (X / 0.50) MAD.
    """

    MAD = 0.50  # half a percent; the calibration window's mean absolute dev

    def test_signed_mad_multiple_escalator_on_mild_up_move(self):
        # overnight +0.40% ⇒ +0.8 MAD (matches Taleb's escalator example)
        hsi, last = _ohlc_with_calibration(
            _alternating_mad_window(self.MAD), overnight_pct=0.40
        )
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.return_value = hsi

        brief = morning_brief(repository=repo)

        assert brief == (
            f"HSI {last:,.0f} (+0.40% o/n, +0.8 MAD over 60d — escalator)"
        )

    def test_chute_flag_when_down_move_exceeds_2_5_mad(self):
        # overnight -1.30% ⇒ -2.6 MAD ⇒ CHUTE (down-move past the 2.5 gate)
        hsi, last = _ohlc_with_calibration(
            _alternating_mad_window(self.MAD), overnight_pct=-1.30
        )
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.return_value = hsi

        brief = morning_brief(repository=repo)

        assert brief == (
            f"HSI {last:,.0f} (-1.30% o/n, -2.6 MAD over 60d — CHUTE)"
        )

    def test_down_move_below_threshold_is_escalator_not_chute(self):
        # overnight -1.00% ⇒ -2.0 MAD ⇒ escalator (down, but calm still holds;
        # this is the sign-asymmetry test: a -2.0 move is NOT a -2.0 magnitude)
        hsi, last = _ohlc_with_calibration(
            _alternating_mad_window(self.MAD), overnight_pct=-1.00
        )
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.return_value = hsi

        brief = morning_brief(repository=repo)

        assert brief == (
            f"HSI {last:,.0f} (-1.00% o/n, -2.0 MAD over 60d — escalator)"
        )

    def test_large_up_move_is_escalator_not_chute(self):
        # overnight +1.30% ⇒ +2.6 MAD ⇒ escalator (a +3.4-MAD up-move is a
        # euphoria print, never a chute — sign is the entire signal)
        hsi, last = _ohlc_with_calibration(
            _alternating_mad_window(self.MAD), overnight_pct=1.30
        )
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.return_value = hsi

        brief = morning_brief(repository=repo)

        assert brief == (
            f"HSI {last:,.0f} (+1.30% o/n, +2.6 MAD over 60d — escalator)"
        )

    def test_overnight_move_does_not_calibrate_its_own_denominator(self):
        # If the overnight move leaked into the MAD window, a -10% overnight
        # on a 0.5% window would hardly budge the MAD of 60 values and still
        # read ~-20 MAD. We assert the window excludes the overnight move by
        # checking the multiple equals pct / 0.50 exactly.
        hsi, last = _ohlc_with_calibration(
            _alternating_mad_window(self.MAD), overnight_pct=-10.00
        )
        repo = MagicMock(spec=ReturnsRepository)
        repo._raw_ohlc.return_value = hsi

        brief = morning_brief(repository=repo)

        # -10.00 / 0.50 == -20.0 MAD exactly ⇒ the overnight did not dilute its
        # own denominator. (If it had, the multiple would be ~-19.7.)
        assert brief == (
            f"HSI {last:,.0f} (-10.00% o/n, -20.0 MAD over 60d — CHUTE)"
        )