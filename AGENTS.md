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

- A `pre-push` Git hook runs the full test suite before any push. To install it
  (or reinstall after cloning):
  ```bash
  cp .githooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push
  ```
  The hook lives in `.git/` (not tracked). A tracked copy is kept under
  `.githooks/` for portability.
