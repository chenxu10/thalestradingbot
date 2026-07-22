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

1. the full test suite (must pass — a failure blocks the push), then
2. the alpha gate (**advisory only, never blocks**): recompute `alpha`,
   compare to the last approved push, and print a console report.
   - The report shows `alpha`, the delta vs the previous push, and a table of
     the top-3 longest functions (line count, # functions at that length,
     name, location) — the lever that raises `alpha`.
   - `alpha` regressed? The push still proceeds; the report is the reminder
     to refactor.

State (last approved `alpha` + per-file parse cache + history) lives in
`.flen_cache/state.json` (gitignored). Re-runs only re-parse changed files.

Standalone analysis (full report, CCDF/frequency log-log plots, bootstrap
goodness-of-fit p, top-3 refactor targets):
```bash
uv run python -m fentu.metaprogramming.function_length_powerlaw --bootstrap 200
```
Plot -> `figures/function_length_powerlaw.png`.
