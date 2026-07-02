"""
Function-length power-law analyzer for the Thales Trading Bot.

Walks the whole codebase, extracts every function definition (``def`` /
``async def``, including methods and nested functions) with its line count,
and fits a **discrete power law** to the frequency distribution using the
Clauset-Shalizi-Newman (2009) procedure — the same methodology behind
`isitapowerlaw.com <http://isitapowerlaw.com>`_:

1. MLE of the exponent  ``alpha = 1 + n / sum( ln(x_i / (x_min - 0.5)) )``
2. ``x_min`` chosen by Kolmogorov-Smirnov minimization
3. goodness-of-fit p-value by parametric bootstrap (re-fitting ``x_min``)
4. standard error  ``sigma = (alpha - 1) / sqrt(n_tail)``

Why it matters (Taleb / *Statistical Consequences of Fat Tails*): function
lengths in a codebase are fat-tailed. A **steeper** distribution (higher
``alpha``) means a **lighter tail** — fewer extreme-long functions, lower
complexity, less exposure to accidental tail events. We cannot change *that*
the distribution is a power law, but refactoring (shortening/splitting the
longest functions) raises ``alpha``. The pre-push gate enforces that ``alpha``
never regresses.

CLI
---
* ``python -m fentu.metaprogramming.function_length_powerlaw``  — full report
  (data table + alpha + CCDF/frequency log-log plots + top-3 refactor targets).
* ``... --hook``  — fast gate mode for the pre-push hook (cached, no bootstrap,
  no plot); exits non-zero if ``alpha`` did not increase over the last approved
  push.  ``FORCE_PUSH=1`` bypasses the alpha gate (tests still run).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
from scipy.special import zeta

import matplotlib
matplotlib.use("Agg")  # non-interactive; safe in hooks / CI
import matplotlib.pyplot as plt


EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    "htmlcov", ".flen_cache", ".opencode", "build", "dist", ".eggs",
    ".mypy_cache", ".tox", ".cache",
}

EPS_ALPHA = 1e-6  # numerical guard for "alpha actually higher"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class FuncRec:
    name: str
    file: str          # repo-relative path
    lineno: int
    end_lineno: int
    line_count: int


# ---------------------------------------------------------------------------
# Extraction (AST)
# ---------------------------------------------------------------------------

def iter_python_files(root: str):
    """Yield repo-relative paths of ``*.py`` files, skipping venv/cache dirs."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.relpath(os.path.join(dirpath, fn), root)


def parse_file(path: str, root: str) -> list[FuncRec]:
    """Parse one .py file; return a FuncRec per FunctionDef/AsyncFunctionDef."""
    full = os.path.join(root, path)
    try:
        with open(full, "r", encoding="utf-8") as fh:
            src = fh.read()
    except (OSError, UnicodeDecodeError):
        return []
    import ast
    try:
        tree = ast.parse(src, filename=full)
    except SyntaxError:
        return []
    recs: list[FuncRec] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start, end = node.lineno, node.end_lineno
            recs.append(FuncRec(
                name=node.name,
                file=path,
                lineno=start,
                end_lineno=end,
                line_count=end - start + 1,
            ))
    return recs


def _content_hash(root: str, rel: str) -> str:
    full = os.path.join(root, rel)
    h = hashlib.sha256()
    try:
        with open(full, "rb") as fh:
            h.update(fh.read())
    except OSError:
        pass
    return h.hexdigest()


def extract_function_lengths(root: str, cache_path: Optional[str] = None) -> list[FuncRec]:
    """Extract all function records, reusing a parse cache for unchanged files."""
    state = load_state(cache_path) if cache_path else {}
    parse_cache = state.get("parse_cache", {})
    files = sorted(iter_python_files(root))
    recs: list[FuncRec] = []
    changed = False
    for rel in files:
        ch = _content_hash(root, rel)
        entry = parse_cache.get(rel)
        if entry and entry.get("content_hash") == ch:
            for r in entry["records"]:
                recs.append(FuncRec(*r))
        else:
            new = parse_file(rel, root)
            parse_cache[rel] = {"content_hash": ch,
                                "records": [[r.name, r.file, r.lineno,
                                             r.end_lineno, r.line_count] for r in new]}
            recs.extend(new)
            changed = True
    # prune cache entries for files that no longer exist
    stale = set(parse_cache) - set(files)
    for s in stale:
        parse_cache.pop(s, None)
    if stale:
        changed = True
    if cache_path and changed:
        state["parse_cache"] = parse_cache
        save_state(cache_path, state)
    return recs


# ---------------------------------------------------------------------------
# Frequency table (user's requested data format)
# ---------------------------------------------------------------------------

def build_frequency_table(records: list[FuncRec]):
    """Rows of (example_function_name, line_count, num_functions), sorted by
    line_count ascending — the ``function name / line counts / # functions``
    format."""
    by_len: dict[int, list[str]] = {}
    for r in records:
        by_len.setdefault(r.line_count, []).append(r.name)
    return [(names[0], ln, len(names)) for ln, names in sorted(by_len.items())]


# ---------------------------------------------------------------------------
# Clauset-Shalizi-Newman (2009) discrete power-law fit
# ---------------------------------------------------------------------------

def mle_alpha(tail: np.ndarray, x_min: int) -> float:
    """Discrete MLE: alpha = 1 + n / sum( ln(x_i / (x_min - 0.5)) )."""
    tail = np.asarray(tail, dtype=float)
    n = len(tail)
    if n < 2:
        return np.nan
    s = float(np.sum(np.log(tail / (x_min - 0.5))))
    if s <= 0:
        return np.nan
    return 1.0 + n / s


def ks_distance(tail: np.ndarray, x_min: int, alpha: float) -> float:
    """KS distance between the empirical tail CDF and the exact discrete
    power-law CDF (normalised by the Hurwitz zeta)."""
    tail = np.sort(np.asarray(tail, dtype=int))
    n = len(tail)
    if n < 2:
        return 0.0
    if alpha is None or not np.isfinite(alpha) or alpha <= 1.0:
        return np.inf
    with np.errstate(all="ignore"):
        Z = float(zeta(alpha, x_min))
        if not np.isfinite(Z) or Z <= 0:
            return np.inf
        xs = np.unique(tail)
        emp = np.searchsorted(tail, xs, side="right") / n
        model = 1.0 - zeta(alpha, xs + 1) / Z
        d = np.max(np.abs(emp - model))
    return float(d) if np.isfinite(d) else np.inf


def select_xmin(data: np.ndarray):
    """KS-minimizing x_min selection. Returns (x_min, alpha, D, n_tail)."""
    data = np.asarray(data, dtype=int)
    data = data[data >= 1]
    if len(data) < 2:
        return None, None, None, 0
    best = (np.inf, None, None, 0)
    for xm in np.unique(data):
        tail = data[data >= xm]
        n = len(tail)
        if n < 2:
            continue
        a = mle_alpha(tail, int(xm))
        if not np.isfinite(a) or a <= 1.0:
            continue
        d = ks_distance(tail, int(xm), a)
        if d < best[0]:
            best = (d, int(xm), float(a), n)
    if best[1] is None:
        return None, None, None, 0
    return best[1], best[2], best[0], best[3]


def _discrete_pl_samples(alpha: float, x_min: int, n: int, rng) -> np.ndarray:
    """Exact inverse-CDF sampler for the discrete power law p(x)=x^-a/ζ(a,x_min)."""
    if alpha is None or not np.isfinite(alpha) or alpha <= 1.0 or n <= 0:
        return np.full(n, x_min, dtype=np.int64)
    Z = float(zeta(alpha, x_min))
    U = rng.random(n)
    target = U * Z  # we want smallest x>=x_min with ζ(alpha,x)/Z <= U
    lo = np.full(n, x_min, dtype=np.int64)
    hi = np.full(n, 10 ** 15, dtype=np.int64)
    for _ in range(80):  # log2(1e15) ~= 50; 80 is a safe margin
        mid = (lo + hi) // 2
        z = zeta(alpha, mid)
        cond = z > target  # CCDF still above U -> need larger x
        lo = np.where(cond, mid + 1, lo)
        hi = np.where(cond, hi, mid)
    return lo


def _bootstrap_pvalue(data, x_min, alpha, n_tail, B, rng) -> float:
    """Parametric bootstrap goodness-of-fit p-value (re-fits x_min each draw)."""
    D_obs = ks_distance(data[data >= x_min], x_min, alpha)
    count = 0
    for _ in range(B):
        synth = _discrete_pl_samples(alpha, x_min, n_tail, rng)
        _, _, D_s, _ = select_xmin(synth)
        if D_s is None:
            continue
        if D_s >= D_obs:
            count += 1
    return (count + 1) / (B + 1)


def fit_power_law(lengths, n_bootstrap: int = 0, seed: int = 0) -> dict:
    """Full CSN fit. Returns a dict with alpha, alpha_std, x_min, n_tail,
    n_total, ks, p (p is None unless n_bootstrap > 0)."""
    data = np.asarray(lengths, dtype=int)
    if data.size:
        data = data[np.isfinite(data.astype(float))] if data.dtype.kind == "f" else data
        data = data[data >= 1]
    n_total = len(data)
    xm, alpha, D, n_tail = select_xmin(data)
    out = {"alpha": alpha, "alpha_std": None, "x_min": xm,
           "n_tail": n_tail, "n_total": n_total, "ks": D, "p": None}
    if alpha is None or not np.isfinite(alpha):
        return out
    out["alpha_std"] = (alpha - 1.0) / np.sqrt(n_tail)
    if n_bootstrap and n_bootstrap > 0 and n_tail >= 10:
        rng = np.random.default_rng(seed)
        out["p"] = _bootstrap_pvalue(data, xm, alpha, n_tail, n_bootstrap, rng)
    return out


# ---------------------------------------------------------------------------
# Refactor recommendations (top-k longest functions; projected alpha if
# shortened 25% — the lever that raises alpha / lightens the tail)
# ---------------------------------------------------------------------------

def recommend_refactors(records: list[FuncRec], fit: dict, k: int = 3) -> list[dict]:
    cur = fit.get("alpha")
    if not records or cur is None or not np.isfinite(cur):
        return []
    data = np.array([r.line_count for r in records], dtype=int)
    ranked = sorted(range(len(records)), key=lambda i: records[i].line_count, reverse=True)
    out = []
    for i in ranked[:k]:
        r = records[i]
        # Project: halve this function's length (a substantial, realistic refactor).
        new_len = max(1, int(round(r.line_count * 0.5)))
        sim = data.copy()
        sim[i] = new_len
        proj = fit_power_law(sim, n_bootstrap=0).get("alpha")
        delta = (proj - cur) if (proj is not None and np.isfinite(proj)) else float("nan")
        out.append({
            "name": r.name,
            "file": r.file,
            "lineno": r.lineno,
            "line_count": r.line_count,
            "projected_alpha": proj,
            "delta": delta,
        })
    return out


# ---------------------------------------------------------------------------
# Tree signature + cache IO
# ---------------------------------------------------------------------------

def tree_signature(root: str) -> str:
    """Content-multiset hash of all .py files: stable across checkouts, mtimes,
    AND file moves/renames (alpha depends only on content, not on paths)."""
    hashes = sorted(_content_hash(root, rel) for rel in iter_python_files(root))
    h = hashlib.sha256()
    for ch in hashes:
        h.update(ch.encode())
        h.update(b"\x00")
    return h.hexdigest()


def load_state(path: Optional[str]) -> dict:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
    os.replace(tmp, path)


def _git_head(root: str) -> str:
    try:
        out = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown"


# ---------------------------------------------------------------------------
# Gate decision (pure) + gate_check (IO)
# ---------------------------------------------------------------------------

def decide_gate(last_approved, current_fit: dict, signature: str, force: bool = False):
    """Decide whether a push may proceed. Returns (allowed, reason)."""
    if force:
        return True, "FORCE_PUSH set: alpha gate bypassed"
    if last_approved is None:
        return True, "no prior baseline; recording baseline alpha"
    if last_approved.get("signature") == signature:
        return True, "tree unchanged since last approved push (idempotent)"
    cur = current_fit.get("alpha")
    prev = last_approved.get("alpha")
    if cur is None or prev is None or not np.isfinite(cur) or not np.isfinite(prev):
        return True, "alpha unavailable; gate skipped"
    if cur > prev + EPS_ALPHA:
        return True, f"alpha increased: {cur:.4f} > {prev:.4f}"
    return False, (f"alpha NOT higher: {cur:.4f} <= {prev:.4f} — "
                   f"shorten/split long functions to raise alpha (lighter tail)")


def gate_check(root: str, cache_path: str, force: bool = False):
    """Run the fast alpha gate. Returns (allowed, reason, info)."""
    force = force or bool(os.environ.get("FORCE_PUSH"))
    recs = extract_function_lengths(root, cache_path=cache_path)
    lengths = np.array([r.line_count for r in recs], dtype=int) if recs else np.array([], dtype=int)
    fit = fit_power_law(lengths, n_bootstrap=0)
    sig = tree_signature(root)
    state = load_state(cache_path)
    last = state.get("last_approved")
    alpha = fit.get("alpha")

    if alpha is None or not np.isfinite(alpha) or fit["n_tail"] < 10:
        _print_report(fit, recs, last, delta=None, verdict="SKIP", top_k=3)
        return True, "insufficient function data to estimate alpha; gate skipped", \
            {"fit": fit, "recs": recs, "signature": sig}

    ok, reason = decide_gate(last, fit, sig, force=force)
    is_idempotent = last is not None and last.get("signature") == sig and not force
    if ok and not is_idempotent:
        # record a new approval (baseline, improved alpha, or forced).
        entry = {
            "signature": sig, "alpha": alpha, "alpha_std": fit["alpha_std"],
            "x_min": fit["x_min"], "n_tail": fit["n_tail"], "n_total": fit["n_total"],
            "timestamp": time.time(), "commit": _git_head(root), "force": force,
        }
        state["last_approved"] = entry
        state.setdefault("history", []).append({**entry, "status": "approved"})
        save_state(cache_path, state)
    # idempotent re-push: no state change, no history entry, no write.

    delta = (alpha - last["alpha"]) if (last and last.get("alpha") is not None) else None
    _print_report(fit, recs, last, delta=delta, verdict="PASS" if ok else "FAIL", top_k=3)
    return ok, reason, {"fit": fit, "recs": recs, "signature": sig}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_report(fit, recs, last, delta, verdict, top_k=3):
    alpha = fit.get("alpha")
    alpha_s = f"{alpha:.4f}" if (alpha is not None and np.isfinite(alpha)) else "n/a"
    prev = last.get("alpha") if last else None
    prev_s = f"{prev:.4f}" if (prev is not None and np.isfinite(prev)) else "none"
    delta_s = f"{delta:+.4f}" if delta is not None and np.isfinite(delta) else "n/a"
    print("\n" + "=" * 64)
    print(f"FUNCTION-LENGTH POWER-LAW GATE  [{verdict}]")
    print("-" * 64)
    print(f"  total functions : {fit['n_total']}")
    print(f"  tail (x>=x_min) : {fit['n_tail']}   x_min={fit['x_min']}")
    print(f"  alpha (current) : {alpha_s}   +/- {fit['alpha_std']:.4f}"
          if fit['alpha_std'] else f"  alpha (current) : {alpha_s}")
    print(f"  alpha (previous): {prev_s}   delta={delta_s}")
    if fit.get("p") is not None:
        pl = "plausible" if fit["p"] > 0.1 else "rejected"
        print(f"  power-law p     : {fit['p']:.3f}  ({pl}; >0.1 = plausible)")
    print("-" * 64)
    recs_top = recommend_refactors(recs, fit, k=top_k)
    if recs_top:
        print(f"  Top {top_k} functions worth refactoring (shorten to raise alpha):")
        for r in recs_top:
            pa = f"{r['projected_alpha']:.4f}" if r['projected_alpha'] is not None and np.isfinite(r['projected_alpha']) else "n/a"
            da = f"{r['delta']:+.4f}" if r['delta'] is not None and np.isfinite(r['delta']) else "n/a"
            print(f"    {r['file']}:{r['lineno']}  {r['name']}  "
                  f"({r['line_count']} lines) -> alpha if halved: {pa} ({da})")
    print("=" * 64)


def print_data_table(records: list[FuncRec]):
    table = build_frequency_table(records)
    print("\nFUNCTION-LENGTH FREQUENCY DISTRIBUTION")
    print(f"{'EXAMPLE_FUNCTION':32} | {'LINE_COUNT':>10} | {'NUM_FUNCTIONS':>13}")
    print("-" * 62)
    for name, ln, cnt in table:
        print(f"{name:32} | {ln:>10} | {cnt:>13}")
    print("-" * 62)
    print(f"{'TOTAL':32} | {'':>10} | {len(records):>13}")


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------

def plot_distribution(lengths, fit: dict, out_path: str):
    """Two-panel log-log figure: frequency distribution + CCDF with the fitted
    power law and the alpha +/- 1.96*sigma 'typical range' band."""
    data = np.asarray(lengths, dtype=int)
    data = data[data >= 1]
    alpha = fit.get("alpha")
    xm = fit.get("x_min")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # --- Panel 1: frequency distribution (log-log) ---
    vals, counts = np.unique(data, return_counts=True)
    ax1.loglog(vals, counts, "o", color="steelblue", alpha=0.6, label="data")
    if alpha is not None and np.isfinite(alpha) and xm:
        Z = float(zeta(alpha, xm))
        xs = np.arange(xm, max(vals.max(), xm) + 1)
        expected = fit["n_total"] * xs.astype(float) ** (-alpha) / Z
        ax1.loglog(xs, expected, "r-", lw=2, label=f"fit x^-a, a={alpha:.2f}")
    ax1.set_xlabel("function line count (log)")
    ax1.set_ylabel("# functions (log)")
    ax1.set_title("Frequency distribution (log-log)")
    ax1.legend()
    ax1.grid(True, which="both", alpha=0.3)

    # --- Panel 2: CCDF (log-log) ---
    xs_u = np.unique(data)
    n = len(data)
    ccdf_emp = np.array([np.sum(data >= x) / n for x in xs_u])
    ax2.loglog(xs_u, ccdf_emp, "o", color="steelblue", alpha=0.6, label="empirical CCDF")
    if alpha is not None and np.isfinite(alpha) and xm:
        Z = float(zeta(alpha, xm))
        xs = np.arange(xm, max(vals.max(), xm) * 2)
        ax2.loglog(xs, zeta(alpha, xs) / Z, "r-", lw=2,
                   label=f"fit  a={alpha:.2f} +/- {fit.get('alpha_std') or 0:.2f}")
        sigma = fit.get("alpha_std") or 0.0
        if sigma > 0:
            for a, style, lbl in [(alpha + 1.96 * sigma, "--", f"+1.96s (a={alpha+1.96*sigma:.2f})"),
                                  (alpha - 1.96 * sigma, "--", f"-1.96s (a={alpha-1.96*sigma:.2f})")]:
                if a > 1.0:
                    ax2.loglog(xs, zeta(a, xs) / float(zeta(a, xm)), "k:", alpha=0.5)
        txt = (f"a = {alpha:.2f} +/- {1.96*sigma:.2f} (95% range)\n"
               f"x_min = {xm}, n_tail = {fit['n_tail']}\n"
               f"p = {fit['p']:.3f}" if fit.get('p') is not None else
               f"a = {alpha:.2f} +/- {1.96*sigma:.2f} (95% range)\n"
               f"x_min = {xm}, n_tail = {fit['n_tail']}")
        ax2.text(0.05, 0.05, txt, transform=ax2.transAxes, fontsize=9,
                 va="bottom", bbox=dict(boxstyle="round", fc="wheat", alpha=0.7))
    ax2.set_xlabel("function line count (log)")
    ax2.set_ylabel("P(X >= x) (log)")
    ax2.set_title("CCDF (log-log) + power-law fit")
    ax2.legend()
    ax2.grid(True, which="both", alpha=0.3)

    fig.suptitle(f"Function-length power law: alpha={alpha:.2f}" if alpha else "Function lengths",
                 fontsize=13)
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------

def default_cache_path(root: str) -> str:
    return os.path.join(root, ".flen_cache", "state.json")


def run_analysis(root: str, cache_path: Optional[str] = None,
                 bootstrap: int = 0, plot: bool = True,
                 plot_path: Optional[str] = None) -> dict:
    cache_path = cache_path or default_cache_path(root)
    recs = extract_function_lengths(root, cache_path=cache_path)
    lengths = np.array([r.line_count for r in recs], dtype=int) if recs else np.array([], dtype=int)
    fit = fit_power_law(lengths, n_bootstrap=bootstrap, seed=0)
    print_data_table(recs)
    _print_report(fit, recs, last=None, delta=None, verdict="ANALYSIS", top_k=3)
    if plot:
        out = plot_path or os.path.join(root, "figures", "function_length_powerlaw.png")
        try:
            plot_distribution(lengths, fit, out)
            print(f"\nPlot saved -> {out}")
        except Exception as exc:  # plotting must never block analysis
            print(f"\n(plot skipped: {exc})")
    return {"fit": fit, "records": recs}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hook", action="store_true",
                    help="fast pre-push gate mode (cached, no bootstrap/plot)")
    ap.add_argument("--root", default=os.getcwd(), help="repo root (default: cwd)")
    ap.add_argument("--cache", default=None, help="cache state.json path")
    ap.add_argument("--bootstrap", type=int, default=0,
                    help="parametric bootstrap iterations for goodness-of-fit p")
    ap.add_argument("--no-plot", action="store_true", help="skip plotting")
    ap.add_argument("--force", action="store_true",
                    help="bypass the alpha gate (also: FORCE_PUSH=1 env)")
    args = ap.parse_args(argv)

    cache = args.cache or default_cache_path(args.root)

    if args.hook:
        ok, reason, _ = gate_check(args.root, cache, force=args.force)
        if not ok:
            print(f"\nPush BLOCKED: {reason}")
            print("Set FORCE_PUSH=1 to bypass (tests still run).")
        return 0 if ok else 1

    run_analysis(args.root, cache, bootstrap=args.bootstrap, plot=not args.no_plot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
