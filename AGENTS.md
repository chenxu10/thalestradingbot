# AGENTS.md

## Purpose

Thales Trading Bot — a Python project expressing the tail-hedging / convexity
investing view from *Dao of Capital*. See `README.md` for the high-level intent.

## Related Repositories

- **`../Option-Combo-Simulation`** — sibling repo; a browser-based option combo
  simulator with optional Python WebSocket backends (live IBKR + SQLite
  historical replay) and an IV term-structure monitor. Consult it when working
  on option pricing, combo structure, delta hedging, or IBKR integration.
  Read its `AGENTS.md`, `ARCHITECTURE.md`, and `DEV_HANDOVER.md` first.

## Local Workflow

- A `pre-push` Git hook runs the full test suite AND the function-length
  power-law alpha gate before any push. To install it (or reinstall after
  cloning):
  ```bash
  cp .githooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push
  ```
  The hook lives in `.git/` (not tracked). A tracked copy is kept under
  `.githooks/` for portability.

### Function-length power-law alpha gate

`fentu/metaprogramming/function_length_powerlaw.py` walks the whole
codebase, extracts every function's line count, and fits a discrete power law
(Clauset-Shalizi-Newman 2009 / isitapowerlaw.com: MLE + KS `x_min` + bootstrap
p). Function lengths are fat-tailed; a **higher** `alpha` means a **lighter
tail** — fewer extreme-long functions, lower complexity, less exposure to
accidental tail events. We can't change *that* it's a power law, but
refactoring the longest functions raises `alpha`.

Every `git push` runs (in `--hook` mode, cached, no plot):

1. the full test suite (must pass), then
2. the alpha gate: recompute `alpha`, compare to the last approved push.
   - **Pass** if `alpha` increased, or the tree is unchanged since the last
     approved push (idempotent re-push / network-retry safe), or there is no
     prior baseline.
   - **Block** otherwise. The gate prints `alpha`, the delta vs the previous
     push, and the top-3 longest functions with the `alpha` projected if each
     were halved — the lever that raises `alpha`.
   - `FORCE_PUSH=1 git push` bypasses the alpha gate (tests still run) for
     emergencies (hotfix, deliberate architectural change).

State (last approved `alpha` + per-file parse cache + history) lives in
`.flen_cache/state.json` (gitignored). Re-runs only re-parse changed files.

Standalone analysis (full report, CCDF/frequency log-log plots, bootstrap
goodness-of-fit p, top-3 refactor targets):
```bash
uv run python -m fentu.metaprogramming.function_length_powerlaw --bootstrap 200
```
Plot -> `figures/function_length_powerlaw.png`.
