"""Tests for the function-length power-law analyzer.

Methodology mirrors Clauset-Shalizi-Newman (2009) / isitapowerlaw.com:
discrete MLE + KS x_min selection + parametric-bootstrap goodness-of-fit.
"""
import json
import textwrap

import numpy as np
import pytest

from fentu.metaprogramming import function_length_powerlaw as flp


# ---------------------------------------------------------------------------
# Fixtures: a tiny but realistic python codebase in a tmp dir.
# ---------------------------------------------------------------------------

A_PY = textwrap.dedent(
    """\
    def tiny(): pass


    def small():
        return 2


    class C:
        def method(self):
            return 3

        async def amethod(self):
            return 4
    """
)

B_PY = textwrap.dedent(
    """\
    def outer():
        def inner():
            return 0
        return 1
    """
)


@pytest.fixture
def codebase(tmp_path):
    (tmp_path / "a.py").write_text(A_PY)
    (tmp_path / "b.py").write_text(B_PY)
    return str(tmp_path)


# ---------------------------------------------------------------------------
# Extraction (AST)
# ---------------------------------------------------------------------------

def test_extract_finds_all_functions(codebase):
    recs = flp.extract_function_lengths(codebase)
    names = {r.name for r in recs}
    assert names == {"tiny", "small", "method", "amethod", "outer", "inner"}
    assert len(recs) == 6


def test_extract_line_counts(codebase):
    recs = {r.name: r for r in flp.extract_function_lengths(codebase)}
    assert recs["tiny"].line_count == 1
    assert recs["small"].line_count == 2
    assert recs["method"].line_count == 2
    assert recs["amethod"].line_count == 2
    assert recs["outer"].line_count == 4
    assert recs["inner"].line_count == 2


def test_extract_records_have_file_and_lineno(codebase):
    recs = flp.extract_function_lengths(codebase)
    for r in recs:
        assert r.file in ("a.py", "b.py")
        assert r.lineno >= 1
        assert r.end_lineno >= r.lineno


def test_extract_excludes_venv_and_cache(tmp_path):
    (tmp_path / "good.py").write_text("def f():\n    return 1\n")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "bad.py").write_text("def should_not_appear():\n    return 1\n")
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "bad2.py").write_text("def also_not():\n    return 1\n")
    recs = flp.extract_function_lengths(str(tmp_path))
    names = {r.name for r in recs}
    assert "f" in names
    assert "should_not_appear" not in names
    assert "also_not" not in names


# ---------------------------------------------------------------------------
# Frequency table (the user's requested data format)
# ---------------------------------------------------------------------------

def test_frequency_table_columns_and_sort(codebase):
    table = flp.build_frequency_table(flp.extract_function_lengths(codebase))
    # 3-tuple: (example_name, line_count, count); sorted by line_count asc.
    assert table == [("tiny", 1, 1), ("small", 2, 4), ("outer", 4, 1)]


def test_frequency_table_counts_sum_to_total(codebase):
    recs = flp.extract_function_lengths(codebase)
    table = flp.build_frequency_table(recs)
    assert sum(c for _, _, c in table) == len(recs)


# ---------------------------------------------------------------------------
# Power-law fit (Clauset-Shalizi-Newman 2009, discrete)
# ---------------------------------------------------------------------------

def test_mle_alpha_formula():
    tail = np.array([2, 3, 4, 5, 6])
    x_min = 2
    expected = 1.0 + len(tail) / np.sum(np.log(tail / (x_min - 0.5)))
    assert flp.mle_alpha(tail, x_min) == pytest.approx(expected)


def test_ks_distance_in_unit_interval():
    rng = np.random.default_rng(0)
    tail = (rng.pareto(3, 500) + 1).round().astype(int)
    tail = tail[tail >= 2]
    d = flp.ks_distance(tail, 2, 3.0)
    assert 0.0 <= d <= 1.0


def test_discrete_pl_sampler_has_right_support():
    rng = np.random.default_rng(1)
    s = flp._discrete_pl_samples(3.0, 5, 2000, rng)
    assert s.min() >= 5
    assert s.dtype.kind in "iu"


def test_fit_recovers_synthetic_alpha():
    rng = np.random.default_rng(42)
    data = flp._discrete_pl_samples(3.0, 2, 8000, rng)
    fit = flp.fit_power_law(data, n_bootstrap=0)
    assert fit["alpha"] == pytest.approx(3.0, abs=0.3)
    assert fit["x_min"] >= 1
    assert fit["n_tail"] >= 100
    assert fit["alpha_std"] > 0
    assert fit["p"] is None  # bootstrap skipped


def test_fit_returns_required_keys():
    rng = np.random.default_rng(7)
    data = flp._discrete_pl_samples(2.5, 3, 2000, rng)
    fit = flp.fit_power_law(data, n_bootstrap=0)
    for k in ("alpha", "alpha_std", "x_min", "n_tail", "n_total", "ks", "p"):
        assert k in fit


def test_fit_pvalue_when_bootstrap_requested():
    rng = np.random.default_rng(7)
    data = flp._discrete_pl_samples(3.0, 2, 2000, rng)
    fit = flp.fit_power_law(data, n_bootstrap=50, seed=7)
    assert fit["p"] is not None
    assert 0.0 <= fit["p"] <= 1.0


def test_fit_handles_degenerate_small_input():
    # A single observation: every candidate x_min yields n_tail<2 -> no fit.
    fit = flp.fit_power_law(np.array([1]), n_bootstrap=0)
    assert fit["alpha"] is None
    assert fit["n_total"] == 1


def test_fit_handles_empty_input():
    fit = flp.fit_power_law(np.array([], dtype=int), n_bootstrap=0)
    assert fit["alpha"] is None
    assert fit["n_total"] == 0


# ---------------------------------------------------------------------------
# Recommender (top-k functions worth refactoring to raise alpha)
# ---------------------------------------------------------------------------

def test_recommend_returns_top_k_by_length(codebase):
    recs = flp.extract_function_lengths(codebase)
    fit = flp.fit_power_law(np.array([r.line_count for r in recs]), n_bootstrap=0)
    recs_out = flp.recommend_refactors(recs, fit, k=3)
    assert len(recs_out) <= 3
    # Longest function is 'outer' (4 lines) -> ranked first.
    assert recs_out[0]["name"] == "outer"
    assert recs_out[0]["line_count"] == 4
    for r in recs_out:
        assert {"name", "file", "lineno", "line_count", "projected_alpha", "delta"} <= set(r)


def test_recommend_empty_when_no_functions():
    fit = flp.fit_power_law(np.array([], dtype=int), n_bootstrap=0)
    assert flp.recommend_refactors([], fit, k=3) == []


# ---------------------------------------------------------------------------
# Tree signature + cache IO
# ---------------------------------------------------------------------------

def test_tree_signature_content_based(codebase, tmp_path):
    sig1 = flp.tree_signature(codebase)
    # Rewrite identical content (mtime changes) -> signature must be stable.
    (tmp_path / "a.py").write_text(A_PY)
    sig2 = flp.tree_signature(codebase)
    assert sig1 == sig2
    # Change content -> signature changes.
    (tmp_path / "a.py").write_text("def brand_new():\n    return 99\n")
    sig3 = flp.tree_signature(codebase)
    assert sig3 != sig1


def test_state_roundtrip(tmp_path):
    state = {
        "last_approved": {"signature": "abc", "alpha": 2.9, "alpha_std": 0.1},
        "history": [{"signature": "abc", "alpha": 2.9}],
        "parse_cache": {"a.py": {"content_hash": "h", "records": [["f", 1, 1, 1]]}},
    }
    p = tmp_path / "state.json"
    flp.save_state(str(p), state)
    loaded = flp.load_state(str(p))
    assert loaded["last_approved"]["alpha"] == 2.9
    assert loaded["parse_cache"]["a.py"]["records"] == [["f", 1, 1, 1]]


def test_parse_cache_speeds_up_second_extract(codebase, tmp_path):
    cache = tmp_path / "state.json"
    recs1 = flp.extract_function_lengths(codebase, cache_path=str(cache))
    # Second call reuses cache; same result, and cache file now populated.
    recs2 = flp.extract_function_lengths(codebase, cache_path=str(cache))
    assert len(recs1) == len(recs2)
    state = flp.load_state(str(cache))
    assert "a.py" in state["parse_cache"]


# ---------------------------------------------------------------------------
# Gate decision logic (pure) + gate_check integration (monkeypatched)
# ---------------------------------------------------------------------------

def test_decide_gate_baseline():
    ok, reason = flp.decide_gate(None, {"alpha": 2.5}, "sig1", force=False)
    assert ok and "baseline" in reason.lower()


def test_decide_gate_idempotent_same_signature():
    last = {"signature": "sig1", "alpha": 2.5}
    ok, _ = flp.decide_gate(last, {"alpha": 2.5}, "sig1", force=False)
    assert ok


def test_decide_gate_allows_when_alpha_higher():
    last = {"signature": "sig1", "alpha": 2.5}
    ok, _ = flp.decide_gate(last, {"alpha": 2.9}, "sig2", force=False)
    assert ok


def test_decide_gate_blocks_when_alpha_not_higher():
    last = {"signature": "sig1", "alpha": 2.9}
    ok, _ = flp.decide_gate(last, {"alpha": 2.5}, "sig2", force=False)
    assert not ok
    ok, _ = flp.decide_gate(last, {"alpha": 2.9}, "sig2", force=False)
    assert not ok  # equal alpha with changed tree -> not "actually higher"


def test_decide_gate_force_overrides():
    last = {"signature": "sig1", "alpha": 2.9}
    ok, reason = flp.decide_gate(last, {"alpha": 1.0}, "sig2", force=True)
    assert ok and "force" in reason.lower()


def _recs_from_lengths(lengths, name_prefix="f"):
    return [
        flp.FuncRec(name=f"{name_prefix}{i}", file="x.py", lineno=1,
                    end_lineno=int(v), line_count=int(v))
        for i, v in enumerate(lengths)
    ]


def test_gate_check_integration(monkeypatch, tmp_path):
    rng = np.random.default_rng(123)
    low_alpha = flp._discrete_pl_samples(2.2, 2, 3000, rng)   # heavier tail
    high_alpha = flp._discrete_pl_samples(4.0, 2, 3000, rng)  # lighter tail

    fit_low = flp.fit_power_law(low_alpha, n_bootstrap=0)
    fit_high = flp.fit_power_law(high_alpha, n_bootstrap=0)
    assert fit_high["alpha"] > fit_low["alpha"]  # sanity

    cache = str(tmp_path / "state.json")
    calls = {"sig": None}

    def fake_extract(root, cache_path=None):
        return _recs_from_lengths(calls["data"])

    def fake_sig(root):
        return calls["sig"]

    monkeypatch.setattr(flp, "extract_function_lengths", fake_extract)
    monkeypatch.setattr(flp, "tree_signature", fake_sig)

    # 1) baseline -> allowed
    calls["data"], calls["sig"] = low_alpha, "L1"
    ok, _, _ = flp.gate_check(".", cache, force=False)
    assert ok

    # 2) identical state -> idempotent allow
    ok, _, _ = flp.gate_check(".", cache, force=False)
    assert ok

    # 3) changed tree, same (low) alpha -> blocked
    calls["sig"] = "L2"
    ok, _, _ = flp.gate_check(".", cache, force=False)
    assert not ok

    # 4) changed tree, higher alpha -> allowed
    calls["data"], calls["sig"] = high_alpha, "H1"
    ok, _, _ = flp.gate_check(".", cache, force=False)
    assert ok

    # 5) lower alpha, force -> allowed
    calls["data"], calls["sig"] = low_alpha, "L3"
    ok, _, _ = flp.gate_check(".", cache, force=True)
    assert ok


def test_gate_check_allows_when_too_few_functions(monkeypatch, tmp_path):
    monkeypatch.setattr(flp, "extract_function_lengths",
                        lambda root, cache_path=None: [])
    monkeypatch.setattr(flp, "tree_signature", lambda root: "s")
    ok, reason, _ = flp.gate_check(".", str(tmp_path / "s.json"), force=False)
    assert ok
    assert "insufficient" in reason.lower() or "few" in reason.lower()


# ---------------------------------------------------------------------------
# Plot smoke test
# ---------------------------------------------------------------------------

def test_plot_distribution_creates_file(tmp_path):
    rng = np.random.default_rng(0)
    data = flp._discrete_pl_samples(2.8, 2, 2000, rng)
    fit = flp.fit_power_law(data, n_bootstrap=0)
    out = tmp_path / "plot.png"
    flp.plot_distribution(data, fit, str(out))
    assert out.exists() and out.stat().st_size > 0
