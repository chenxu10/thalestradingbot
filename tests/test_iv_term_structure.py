"""
Scope: pure, IBKR-free selection and bucketing logic that lives in
fentu.pricingservices. No network, no yfinance calls inside the tests.

Tests cover:
1. calculate_calendar_dte   (pure core)
2. pick_strike_window       (pure core)
3. build_expiry_detail_rows (pure core, glue step 3)
4. build_bucket_rows        (pure core, final computation)
5. yfinance_chain_to_detail_rows (adapter, step 5 -- consumes a yfinance-shaped
   chain dict; no yfinance import, no network)
6. plot_term_structure      (rendering, step 6 -- matplotlib, offline)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import date, datetime

import pytest

from fentu.pricingservices.iv_term_structure import (
    build_bucket_rows,
    build_expiry_detail_rows,
    calculate_calendar_dte,
    pick_strike_window,
)
from fentu.pricingservices.term_structure_plotting import plot_term_structure
from fentu.pricingservices.yfinance_adapter import yfinance_chain_to_detail_rows


class TestCalculateCalendarDte:
    @pytest.mark.parametrize("anchor, expiry, expected", [
        (date(2026, 4, 23), "20260521", 28),       
        (date(2026, 6, 27), "20260629", 2),        
    ])
    def test_basic_day_gap(self, anchor, expiry, expected):
        assert calculate_calendar_dte(anchor, expiry) == expected

    def test_zero_day_gap_same_day(self):
        assert calculate_calendar_dte(date(2026, 4, 23), "20260423") == 0

    def test_past_expiry_returns_negative(self):
        # Past expiries are out of scope for the curve but must still compute
        # truthfully so the maxDte filter can drop them, not silently return None.
        assert calculate_calendar_dte(date(2026, 4, 23), "20260420") == -3

class TestPickStrikeWindow:
    """Picks the ATM strike (nearest to spot) and a +/- radius window around it.

    This decides which option's IV represents each expiry, so wrong ATM -> wrong
    IV per tenor -> wrong curve. Operates only on a strike list + a price.
    """

    def test_finds_nearest_atm_with_radius_one_window(self):
        # Spot 107.5 is equidistant from 105 and 110 (both 2.5 away); lower wins.
        # ATM index 2 -> radius-1 window spans indices 1..3 = [100, 105, 110].
        result = pick_strike_window(
            [95, 100, 105, 110, 115], underlying_price=107.5, radius=1
        )
        assert result["atm_strike"] == 105
        assert result["window_strikes"] == [100, 105, 110]

    def test_radius_clamped_at_list_edges(self):
        # ATM is 95 (lowest); radius 3 should not underflow below the list.
        result = pick_strike_window(
            [95, 100, 105, 110, 115], underlying_price=94, radius=3
        )
        assert result["atm_strike"] == 95
        assert result["window_strikes"] == [95, 100, 105, 110]

    @pytest.mark.parametrize("strikes,spot", [
        ([], 100),                    # empty strike list
        (["bad", "also-bad"], 100),   # no numeric strikes
        ([100, 105], None),           # invalid underlying price
    ])
    def test_invalid_input_returns_none_atm(self, strikes, spot):
        result = pick_strike_window(strikes, underlying_price=spot, radius=1)
        assert result["atm_strike"] is None
        assert result["window_strikes"] == []


class TestBuildExpiryDetailRows:
    """Glue step 3: read call/put IV at the ATM strike, average -> atmIv per expiry.

    Consumes per-expiry selection rows (each pointing at an ATM call and put via
    a generic quote key) plus a quote lookup, and emits the detail rows that
    build_bucket_rows will later fold into tenor buckets. Data-source-agnostic:
    the "sub_id" key is whatever the caller uses to identify a quote (yfinance
    row id, IBKR sub id, a stub key in tests) -- this module never touches a
    broker.
    """

    def test_averages_call_and_put_iv_and_sorts_by_dte(self):
        # Happy path: two expiries out of order; both sides present.
        # Pins the full row shape, the (call+put)/2 averaging, and dte sort.
        expiry_rows = [
            {
                "expiry": "20260618", "dte": 56, "atm_strike": 105,
                "atm_call_sub_id": "c2", "atm_put_sub_id": "p2",
            },
            {
                "expiry": "20260521", "dte": 28, "atm_strike": 105,
                "atm_call_sub_id": "c1", "atm_put_sub_id": "p1",
            },
        ]
        quotes_by_sub_id = {
            "c1": {"iv": 0.23, "mark": 3.20},
            "p1": {"iv": 0.25, "mark": 4.10},
            "c2": {"iv": 0.21, "mark": 5.00},
            "p2": {"iv": 0.22, "mark": 5.50},
        }

        rows = build_expiry_detail_rows(expiry_rows, quotes_by_sub_id)

        assert [r["dte"] for r in rows] == [28, 56]
        r1 = rows[0]
        assert r1["expiry"] == "20260521"
        assert r1["atm_strike"] == 105
        assert r1["call_iv"] == 0.23
        assert r1["put_iv"] == 0.25
        assert r1["atm_iv"] == 0.24
        assert r1["has_complete_pair"] is True
        assert r1["call_mark"] == 3.20
        assert r1["put_mark"] == 4.10

    @pytest.mark.parametrize("quotes,expected_call,expected_put", [
        # Missing put quote: call survives, atm_iv None.
        ({"c1": {"iv": 0.23, "mark": 3.20}}, 0.23, None),
        # Missing call quote: put survives, atm_iv None.
        ({"p1": {"iv": 0.25, "mark": 4.10}}, None, 0.25),
        # Non-positive IV rejected on both sides -> both None.
        ({"c1": {"iv": 0.0, "mark": 3.20}, "p1": {"iv": -0.1, "mark": 4.10}}, None, None),
        # Non-numeric IV on one side -> that side None, other survives.
        ({"c1": {"iv": "bad", "mark": 3.20}, "p1": {"iv": 0.25, "mark": 4.10}}, None, 0.25),
        # String IV coerced to float on both sides -> averaged normally.
        ({"c1": {"iv": "0.23", "mark": "3.20"}, "p1": {"iv": "0.25", "mark": "4.10"}}, 0.23, 0.25),
        # Yahoo sentinel: stale/no-trade ATM call returns IV=1e-5 (0.001%) --
        # physically impossible for an equity index (floor ~5%) and would poison
        # the (call+put)/2 average. Must be rejected as None; put survives.
        ({"c1": {"iv": 1e-5, "mark": 0.0}, "p1": {"iv": 0.35, "mark": 4.10}}, None, 0.35),
    ])
    def test_incomplete_or_invalid_quote_yields_none_atm_iv(
        self, quotes, expected_call, expected_put
    ):
        expiry_rows = [{
            "expiry": "20260521", "dte": 28, "atm_strike": 105,
            "atm_call_sub_id": "c1", "atm_put_sub_id": "p1",
        }]

        rows = build_expiry_detail_rows(expiry_rows, quotes)

        r = rows[0]
        assert r["call_iv"] == expected_call
        assert r["put_iv"] == expected_put
        complete = expected_call is not None and expected_put is not None
        assert r["atm_iv"] == (round((expected_call + expected_put) / 2, 6) if complete else None)
        assert r["has_complete_pair"] is complete

    def test_empty_inputs_return_empty_list(self):
        assert build_expiry_detail_rows([], {}) == []
        assert build_expiry_detail_rows(None, None) == []


def _detail_row(dte, atm_iv, expiry=None, has_complete_pair=True):
    """Helper: build a detail row with a self-documenting atm_iv encoding.

    atm_iv = 0.2 + dte * 0.001, so dte 2 -> 0.202, dte 60 -> 0.260, etc.
    Makes bucket-matching assertions readable without magic numbers. Pass
    atm_iv=None to model an incomplete-pair row (call_iv/put_iv also None).
    """
    if atm_iv is None:
        call_iv = put_iv = None
    else:
        call_iv = atm_iv - 0.01
        put_iv = atm_iv + 0.01
    return {
        "expiry": expiry or f"2026{dte:04d}",
        "dte": dte,
        "atm_strike": 105.0,
        "call_iv": call_iv,
        "put_iv": put_iv,
        "atm_iv": atm_iv,
        "has_complete_pair": has_complete_pair,
        "call_mark": 3.0,
        "put_mark": 4.0,
        "atm_call_sub_id": f"c{dte}",
        "atm_put_sub_id": f"p{dte}",
    }


class TestBuildBucketRows:
    """Final computation step: fold per-expiry detail rows into tenor buckets.

    Each bucket (1D/3D/1W/3W/1M/3M/6M by default) is matched to the detail row
    whose dte is nearest the bucket's targetDays. The output is the normalized
    term-structure curve -- the decision-relevant artifact that the plot renders
    and that Thales will compare against realized vol.
    """

    def test_default_buckets_match_nearest_dte(self):
        # Detail rows at dtes 2, 8, 22, 60, 95, 200 with atm_iv = 0.2 + dte*0.001.
        detail_rows = [
            _detail_row(2, 0.202),
            _detail_row(8, 0.208),
            _detail_row(22, 0.222),
            _detail_row(60, 0.260),
            _detail_row(95, 0.295),
            _detail_row(200, 0.400),
        ]

        buckets = build_bucket_rows(detail_rows)

        # bucket: (label, targetDays) -> expected matched dte
        expected_matches = {
            "1D": 2,    # target 1:  nearest is 2 (dist 1)
            "3D": 2,    # target 3:  nearest is 2 (dist 1) vs 8 (dist 5) -> 2
            "1W": 8,    # target 7:  nearest is 8 (dist 1)
            "3W": 22,   # target 21: nearest is 22 (dist 1)
            "1M": 22,   # target 30: nearest is 22 (dist 8) vs 60 (dist 30) -> 22
            "3M": 95,   # target 90: nearest is 95 (dist 5) vs 60 (dist 30) -> 95
            "6M": 200,  # target 180: nearest is 200 (dist 20) vs 95 (dist 85) -> 200
        }

        assert [b["label"] for b in buckets] == [
            "1D", "3D", "1W", "3W", "1M", "3M", "6M"
        ]

        for bucket in buckets:
            expected_dte = expected_matches[bucket["label"]]
            assert bucket["matched_dte"] == expected_dte, (
                f"{bucket['label']}: matched_dte {bucket['matched_dte']} "
                f"!= expected {expected_dte}"
            )
            assert bucket["atm_iv"] == round(0.2 + expected_dte * 0.001, 6), (
                f"{bucket['label']}: atm_iv {bucket['atm_iv']} mismatch"
            )
            assert bucket["has_complete_pair"] is True

    def test_bucket_row_shape_has_all_fields(self):
        detail_rows = [_detail_row(7, 0.207)]
        buckets = build_bucket_rows(detail_rows)

        assert len(buckets) == 1 or len(buckets) == 7  # defaults give 7 buckets
        row = buckets[0]
        assert set(row.keys()) == {
            "label", "target_days", "matched_expiry", "matched_dte",
            "atm_strike", "call_iv", "put_iv", "atm_iv", "has_complete_pair",
        }

    def test_empty_detail_rows_yield_all_none_buckets(self):
        buckets = build_bucket_rows([])

        assert len(buckets) == 7
        for bucket in buckets:
            assert bucket["matched_expiry"] is None
            assert bucket["matched_dte"] is None
            assert bucket["atm_iv"] is None
            assert bucket["has_complete_pair"] is False

    def test_matched_row_with_none_atm_iv_propagates_none(self):
        # A detail row exists and is nearest, but its atm_iv is None (incomplete
        # pair). The bucket must reflect that, not fabricate an IV.
        detail_rows = [
            _detail_row(7, None, has_complete_pair=False),
            _detail_row(30, 0.230),
        ]

        buckets = build_bucket_rows(detail_rows)

        week_bucket = next(b for b in buckets if b["label"] == "1W")
        assert week_bucket["matched_dte"] == 7
        assert week_bucket["atm_iv"] is None
        assert week_bucket["has_complete_pair"] is False

    def test_tie_breaks_to_lower_dte_then_earlier_expiry(self):
        # Two rows equidistant from targetDays=10: dte 8 (dist 2) and dte 12 (dist 2).
        # Tiebreak: lower dte wins. If dte also ties, earlier expiry string wins.
        detail_rows = [
            _detail_row(8, 0.208, expiry="20260501"),
            _detail_row(12, 0.212, expiry="20260505"),
        ]
        custom_buckets = [{"label": "TIE", "targetDays": 10}]

        buckets = build_bucket_rows(detail_rows, custom_buckets)

        assert buckets[0]["matched_dte"] == 8
        assert buckets[0]["atm_iv"] == 0.208

    def test_tie_breaks_to_earlier_expiry_when_dte_equal(self):
        detail_rows = [
            _detail_row(10, 0.210, expiry="20260510"),
            _detail_row(10, 0.210, expiry="20260505"),  # earlier expiry
        ]
        custom_buckets = [{"label": "TIE", "targetDays": 10}]

        buckets = build_bucket_rows(detail_rows, custom_buckets)

        assert buckets[0]["matched_expiry"] == "20260505"

    def test_custom_bucket_definitions_override_defaults(self):
        detail_rows = [_detail_row(45, 0.245)]
        custom = [
            {"label": "45D", "targetDays": 45},
            {"label": "1Y", "targetDays": 365},
        ]

        buckets = build_bucket_rows(detail_rows, custom)

        assert [b["label"] for b in buckets] == ["45D", "1Y"]
        assert buckets[0]["matched_dte"] == 45
        assert buckets[0]["atm_iv"] == 0.245
        # 1Y bucket: only row is at dte 45 (dist 320) -- still nearest, so matched.
        assert buckets[1]["matched_dte"] == 45
        assert buckets[1]["atm_iv"] == 0.245

    def test_custom_bucket_far_from_any_row_still_matches_nearest(self):
        # No maxDte-style cutoff here; nearest is unconditional. Filtering of
        # too-far matches is the caller's job, not build_bucket_rows'.
        detail_rows = [_detail_row(5, 0.205)]
        custom = [{"label": "1Y", "targetDays": 365}]

        buckets = build_bucket_rows(detail_rows, custom)

        assert buckets[0]["matched_dte"] == 5
        assert buckets[0]["atm_iv"] == 0.205

    def test_ignores_rows_with_missing_or_non_integer_dte(self):
        detail_rows = [
            {"expiry": "20260521", "dte": "bad", "atm_iv": 0.30},
            _detail_row(7, 0.207),
            {"expiry": "20260618", "atm_iv": 0.25},  # no dte field
        ]

        buckets = build_bucket_rows(detail_rows)

        week_bucket = next(b for b in buckets if b["label"] == "1W")
        assert week_bucket["matched_dte"] == 7

    def test_ignores_rows_with_blank_expiry(self):
        detail_rows = [
            {"expiry": "", "dte": 7, "atm_iv": 0.30},
            _detail_row(7, 0.207, expiry="20260507"),
        ]

        buckets = build_bucket_rows(detail_rows)

        week_bucket = next(b for b in buckets if b["label"] == "1W")
        assert week_bucket["matched_expiry"] == "20260507"

    def test_empty_bucket_definitions_falls_back_to_defaults(self):
        detail_rows = [_detail_row(7, 0.207)]

        buckets = build_bucket_rows(detail_rows, None)

        assert len(buckets) == 7
        assert [b["label"] for b in buckets] == [
            "1D", "3D", "1W", "3W", "1M", "3M", "6M"
        ]

    def test_malformed_bucket_definition_uses_safe_defaults(self):
        detail_rows = [_detail_row(7, 0.207)]
        # Missing targetDays, non-string label -- should not crash.
        custom = [{"label": "", "targetDays": None}, {"targetDays": 7}]

        buckets = build_bucket_rows(detail_rows, custom)

        assert len(buckets) == 2
        # Coerced: blank label -> "Bucket", None targetDays -> 0.
        assert buckets[0]["label"] == "Bucket"
        assert buckets[0]["target_days"] == 0
        assert buckets[1]["label"] == "Bucket"


def _fake_chain(expiries_data, underlying_price=400):
    """Build a yfinance-shaped chain dict from compact specs.

    expiries_data: list of (expiry, atm_strike, call_iv, put_iv).
    Each expiry gets 5 strikes centered on atm_strike; the ATM call/put carry
    the given IVs, off-ATM strikes get a flat 0.30 so they don't contaminate.
    """
    chains = {}
    for expiry, atm_strike, call_iv, put_iv in expiries_data:
        exp_compact = expiry.replace("-", "")
        strikes = [atm_strike - 10, atm_strike - 5, atm_strike, atm_strike + 5, atm_strike + 10]
        calls, puts = [], []
        for s in strikes:
            is_atm = s == atm_strike
            calls.append({
                "contractSymbol": f"{exp_compact}C{int(s * 1000):08d}",
                "strike": s,
                "iv": call_iv if is_atm else 0.30,
                "lastPrice": 3.0 if is_atm else 1.0,
            })
            puts.append({
                "contractSymbol": f"{exp_compact}P{int(s * 1000):08d}",
                "strike": s,
                "iv": put_iv if is_atm else 0.30,
                "lastPrice": 4.0 if is_atm else 1.0,
            })
        chains[expiry] = {"calls": calls, "puts": puts}
    return {
        "expiries": [e for e, *_ in expiries_data],
        "chains": chains,
    }


class TestYfinanceChainToDetailRows:
    """Step 5 adapter: yfinance-shaped option chain -> detail rows.

    Consumes a dict mirroring yfinance's ticker.options + ticker.option_chain()
    shape (list-of-dict records, or pandas DataFrames) and emits the detail rows
    that build_bucket_rows folds into the curve. No yfinance import, no network.
    """

    def test_two_expiries_produce_correct_detail_rows(self):
        chain = _fake_chain([
            ("2026-05-21", 400, 0.23, 0.25),
            ("2026-06-18", 400, 0.21, 0.22),
        ])

        rows = yfinance_chain_to_detail_rows(
            chain, underlying_price=400, anchor_date=date(2026, 4, 23)
        )

        assert len(rows) == 2
        assert rows[0]["expiry"] == "20260521"
        assert rows[0]["dte"] == 28
        assert rows[0]["atm_strike"] == 400
        assert rows[0]["call_iv"] == 0.23
        assert rows[0]["put_iv"] == 0.25
        assert rows[0]["atm_iv"] == 0.24
        assert rows[0]["has_complete_pair"] is True
        assert rows[1]["dte"] == 56
        assert rows[1]["atm_iv"] == round((0.21 + 0.22) / 2, 6)

    def test_past_expiry_is_filtered_out(self):
        chain = _fake_chain([
            ("2026-04-20", 400, 0.23, 0.25),  # 3 days before anchor -> dte -3
            ("2026-05-21", 400, 0.21, 0.22),
        ])

        rows = yfinance_chain_to_detail_rows(
            chain, underlying_price=400, anchor_date=date(2026, 4, 23)
        )

        assert [r["expiry"] for r in rows] == ["20260521"]

    def test_expiry_beyond_max_dte_is_filtered(self):
        chain = _fake_chain([
            ("2026-05-21", 400, 0.23, 0.25),
            ("2027-04-23", 400, 0.20, 0.21),  # dte 365 > max_dte 200
        ])

        rows = yfinance_chain_to_detail_rows(
            chain, underlying_price=400, anchor_date=date(2026, 4, 23), max_dte=200
        )

        assert [r["expiry"] for r in rows] == ["20260521"]

    def test_unsorted_strikes_still_pick_atm(self):
        # Build a chain with scrambled strike order in the records.
        chain = _fake_chain([("2026-05-21", 400, 0.23, 0.25)])
        calls = chain["chains"]["2026-05-21"]["calls"]
        chain["chains"]["2026-05-21"]["calls"] = list(reversed(calls))

        rows = yfinance_chain_to_detail_rows(
            chain, underlying_price=402, anchor_date=date(2026, 4, 23)
        )

        # Spot 402 is nearest to 400 (dist 2) vs 405 (dist 3) -> ATM 400.
        assert rows[0]["atm_strike"] == 400
        assert rows[0]["atm_iv"] == 0.24

    def test_missing_call_at_atm_yields_incomplete_pair(self):
        # Remove the ATM call so only the put is found at the ATM strike.
        chain = _fake_chain([("2026-05-21", 400, 0.23, 0.25)])
        calls = chain["chains"]["2026-05-21"]["calls"]
        chain["chains"]["2026-05-21"]["calls"] = [c for c in calls if c["strike"] != 400]

        rows = yfinance_chain_to_detail_rows(
            chain, underlying_price=400, anchor_date=date(2026, 4, 23)
        )

        r = rows[0]
        assert r["call_iv"] is None
        assert r["put_iv"] == 0.25
        assert r["atm_iv"] is None
        assert r["has_complete_pair"] is False

    def test_pandas_dataframe_input_works(self):
        pd = pytest.importorskip("pandas")
        chain = _fake_chain([("2026-05-21", 400, 0.23, 0.25)])
        for expiry, sides in chain["chains"].items():
            chain["chains"][expiry] = {
                "calls": pd.DataFrame(sides["calls"]),
                "puts": pd.DataFrame(sides["puts"]),
            }

        rows = yfinance_chain_to_detail_rows(
            chain, underlying_price=400, anchor_date=date(2026, 4, 23)
        )

        assert len(rows) == 1
        assert rows[0]["atm_iv"] == 0.24

    def test_empty_chain_returns_empty_list(self):
        chain = {"expiries": [], "chains": {}}
        rows = yfinance_chain_to_detail_rows(
            chain, underlying_price=400, anchor_date=date(2026, 4, 23)
        )
        assert rows == []

    def test_invalid_anchor_returns_empty(self):
        chain = _fake_chain([("2026-05-21", 400, 0.23, 0.25)])
        rows = yfinance_chain_to_detail_rows(
            chain, underlying_price=400, anchor_date=None
        )
        assert rows == []

    def test_real_yfinance_shape_implied_volatility_column_and_namedtuple_chain(self):
        # Pins the actual yfinance option_chain() return shape: a namedtuple-like
        # object with .calls/.puts attributes (not a dict) and an
        # 'impliedVolatility' column (not 'iv'). The adapter must read both.
        pd = pytest.importorskip("pandas")
        from collections import namedtuple
        Chain = namedtuple("Chain", ["calls", "puts"])

        calls = pd.DataFrame([
            {"contractSymbol": "20260521C0400000", "strike": 400, "impliedVolatility": 0.23, "lastPrice": 3.0},
            {"contractSymbol": "20260521C0405000", "strike": 405, "impliedVolatility": 0.30, "lastPrice": 1.0},
        ])
        puts = pd.DataFrame([
            {"contractSymbol": "20260521P0400000", "strike": 400, "impliedVolatility": 0.25, "lastPrice": 4.0},
            {"contractSymbol": "20260521P0405000", "strike": 405, "impliedVolatility": 0.30, "lastPrice": 1.0},
        ])
        chain_data = {
            "expiries": ["2026-05-21"],
            "chains": {"2026-05-21": Chain(calls=calls, puts=puts)},
        }

        rows = yfinance_chain_to_detail_rows(
            chain_data, underlying_price=400, anchor_date=date(2026, 4, 23)
        )

        assert len(rows) == 1
        r = rows[0]
        assert r["atm_strike"] == 400
        assert r["call_iv"] == 0.23
        assert r["put_iv"] == 0.25
        assert r["atm_iv"] == 0.24
        assert r["has_complete_pair"] is True


class TestPlotTermStructure:
    """Step 6 rendering: bucket rows -> matplotlib Axes.

    Plots tenor labels on x, atm_iv on y, skipping buckets whose atm_iv is None.
    Fully offline (Agg backend). Inspects the drawn line's data and tick labels.
    """

    def _buckets(self, ivs):
        """ivs: list of (label, atm_iv) -- builds minimal bucket rows."""
        return [
            {
                "label": label, "target_days": 1, "matched_expiry": "20260101",
                "matched_dte": 1, "atm_strike": 100, "call_iv": None,
                "put_iv": None, "atm_iv": iv, "has_complete_pair": iv is not None,
            }
            for label, iv in ivs
        ]

    def test_renders_line_with_tenor_labels_and_atm_iv(self):
        buckets = self._buckets([("1D", 0.202), ("3D", None), ("1W", 0.208), ("1M", 0.222)])

        fig, ax = plt.subplots()
        result = plot_term_structure(buckets, ax=ax, show=False)

        assert result is ax
        line = ax.lines[0]
        # None bucket (3D) is skipped -> 3 plotted points at x 0,1,2.
        assert list(line.get_xdata()) == [0, 1, 2]
        assert list(line.get_ydata()) == [0.202, 0.208, 0.222]
        fig.canvas.draw()
        labels = [t.get_text() for t in ax.get_xticklabels()]
        assert labels == ["1D", "1W", "1M"]

    def test_sets_title_and_axis_labels_when_provided(self):
        buckets = self._buckets([("1D", 0.20)])

        fig, ax = plt.subplots()
        plot_term_structure(buckets, ax=ax, show=False, title="QQQ IV Term Structure")

        assert ax.get_title() == "QQQ IV Term Structure"
        assert ax.get_ylabel() == "ATM IV"

    def test_default_title_when_none_provided(self):
        buckets = self._buckets([("1D", 0.20)])

        fig, ax = plt.subplots()
        plot_term_structure(buckets, ax=ax, show=False)

        assert ax.get_title() == "IV Term Structure"

    def test_all_none_buckets_plots_no_line(self):
        buckets = self._buckets([("1D", None), ("1W", None)])

        fig, ax = plt.subplots()
        plot_term_structure(buckets, ax=ax, show=False)

        assert len(ax.lines) == 0

    def test_empty_buckets_plots_no_line(self):
        fig, ax = plt.subplots()
        plot_term_structure([], ax=ax, show=False)
        assert len(ax.lines) == 0

    def test_creates_own_axes_when_none_passed(self):
        buckets = self._buckets([("1D", 0.20)])

        ax = plot_term_structure(buckets, ax=None, show=False)
        line = ax.lines[0]
        assert list(line.get_ydata()) == [0.20]
        plt.close(ax.figure)


class TestPlotTermStructurePanelWiring:
    """Step 7 glue: VolatilityFacade._plot_term_structure_panel drives the
    full pipeline (fetch -> adapter -> buckets -> plot) on a matplotlib Axes
    and is network-failure-safe.

    Network is stubbed by monkeypatching fetch_yfinance_chain so no real
    yfinance call is made; this pins the wiring contract, not yfinance itself.
    """

    def _stub_fetcher(self, monkeypatch, chain_data, underlying_price):
        import fentu.pricingservices.yfinance_fetcher as fetcher
        monkeypatch.setattr(
            fetcher, "fetch_yfinance_chain",
            lambda sym, max_expiries=None: (chain_data, underlying_price),
        )

    def test_panel_renders_curve_from_fetched_chain(self, monkeypatch):
        from collections import namedtuple
        pd = pytest.importorskip("pandas")
        from fentu.explatoryservices.volcalculator import VolatilityFacade

        Chain = namedtuple("Chain", ["calls", "puts"])
        # Future expiry relative to today so it survives the dte >= 0 filter.
        calls = pd.DataFrame([
            {"contractSymbol": "20260717C0400000", "strike": 400, "impliedVolatility": 0.23, "lastPrice": 3.0},
            {"contractSymbol": "20260717C0405000", "strike": 405, "impliedVolatility": 0.30, "lastPrice": 1.0},
        ])
        puts = pd.DataFrame([
            {"contractSymbol": "20260717P0400000", "strike": 400, "impliedVolatility": 0.25, "lastPrice": 4.0},
            {"contractSymbol": "20260717P0405000", "strike": 405, "impliedVolatility": 0.30, "lastPrice": 1.0},
        ])
        chain_data = {"expiries": ["2026-07-17"], "chains": {"2026-07-17": Chain(calls=calls, puts=puts)}}
        self._stub_fetcher(monkeypatch, chain_data, 400.0)

        fig, ax = plt.subplots()
        facade = VolatilityFacade.__new__(VolatilityFacade)
        facade._plot_term_structure_panel(ax, "QQQ")

        assert ax.get_title() == "QQQ IV Term Structure"
        assert len(ax.lines) == 1
        fig.canvas.draw()
        labels = [t.get_text() for t in ax.get_xticklabels()]
        assert labels == ["1D", "3D", "1W", "3W", "1M", "3M", "6M"]

    def test_panel_shows_note_when_no_expiries(self, monkeypatch):
        from fentu.explatoryservices.volcalculator import VolatilityFacade
        self._stub_fetcher(monkeypatch, {"expiries": [], "chains": {}}, 400.0)

        fig, ax = plt.subplots()
        facade = VolatilityFacade.__new__(VolatilityFacade)
        facade._plot_term_structure_panel(ax, "QQQ")

        assert ax.get_title() == "IV Term Structure"
        assert len(ax.lines) == 0
        assert any("unavailable" in t.get_text() for t in ax.texts)

    def test_panel_graceful_on_fetch_exception(self, monkeypatch):
        from fentu.explatoryservices.volcalculator import VolatilityFacade
        import fentu.pricingservices.yfinance_fetcher as fetcher

        def boom(sym, max_expiries=None):
            raise RuntimeError("network down")
        monkeypatch.setattr(fetcher, "fetch_yfinance_chain", boom)

        fig, ax = plt.subplots()
        facade = VolatilityFacade.__new__(VolatilityFacade)
        facade._plot_term_structure_panel(ax, "QQQ")

        assert ax.get_title() == "IV Term Structure"
        assert len(ax.lines) == 0
        texts = [t.get_text() for t in ax.texts]
        assert any("unavailable" in t and "RuntimeError" in t for t in texts)
