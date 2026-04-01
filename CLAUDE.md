# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IRP Retirement Tracker — a Streamlit web app for managing a Korean IRP (Individual Retirement Pension) portfolio targeting 400M KRW by December 2030. Also tracks Keysight RSU vesting schedules.

## Commands

```bash
# Run the app
streamlit run src/irp_web_app_enhanced.py

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_claude_cli.py
python test_persona_parser.py
python test_portfolio_snapshots.py

# Quick smoke test (verify app launches without errors)
streamlit run src/irp_web_app_enhanced.py --server.headless true &
sleep 5 && curl -s http://localhost:8501/_stcore/health && kill %1

# Check for syntax errors before committing
python -m py_compile src/irp_web_app_enhanced.py
python -m py_compile src/utils.py
python -m py_compile src/market_data.py
python -m py_compile src/data_handler.py
```

## Architecture

**Stack:** Python 3.11+ / Streamlit / Plotly / yfinance / pykrx

### Source Layout

- `src/irp_web_app_enhanced.py` — Main app. All 9 Streamlit pages as `page_*()` functions with sidebar navigation.
- `src/utils.py` — Financial calculations (CAGR, FV, settlement dates), AI review parsing (standard + three-persona), Claude CLI integration (`run_claude_cli`, `_find_claude_exe`), portfolio snapshot generation.
- `src/market_data.py` — Live market data via yfinance with 10-minute Streamlit cache. Fallback chain: live API → cached values → mock data.
- `src/data_handler.py` — JSON load/save for the single data file.

### Data

- `data/irp_tracker_data.json` — Single source of truth. Holdings, transactions, deposits, RSU vesting, allocation targets/history, AI reviews. Auto-created with defaults on first run.
- `data/etf_config.json` — ETF metadata (8 assets: ticker codes, names, types).
- `data/IRP_AI_Review_*.md` — Saved AI review responses (timestamped).
- `data/backups/` — Auto and manual backups of the data file (gitignored).
- `portfolio_snapshots` array in JSON — Point-in-time portfolio value records (auto mid-month + on-demand).

### Portfolio Snapshot Flow

- **Auto:** Triggers on first Korean business day on or after the 15th each month (post-rebalancing). Skips weekends and Korean holidays. Uses `is_kr_business_day()` and `should_auto_snapshot()`.
- **Manual:** On-demand button on Dashboard with optional note.
- **Data captured:** shares, ETF prices, per-asset values, total value, allocation %, targets, trigger type, note.
- **Displayed:** Portfolio History line chart on Dashboard with goal/floor lines, auto vs manual markers. Per-asset stacked area chart shows individual asset values over time.

### AI Review Flow

1. **Export** — `generate_portfolio_snapshot()` or `generate_persona_export()` builds a markdown snapshot
2. **Execute** — Claude CLI (`claude -p`) via subprocess, or manual copy-paste fallback
3. **Parse** — `detect_review_format()` auto-detects, then `parse_ai_review_md()` or `parse_persona_review_md()` extracts structured data
4. **Apply** — User clicks "Save to Tracker" → `save_ai_review()` persists to JSON → surfaces on Dashboard/Reports/Projections via `get_latest_ai_review()`

Three-persona mode uses Cathie Wood, Peter Lynch, and Ray Dalio personas with synthesis.

## Key Patterns

- **Currency:** All amounts in KRW. `format_currency()` for display. RSU values converted via `convert_usd_to_krw()`.
- **Settlement:** 2-day rebalancing cycle. Day 1: sell, broker confirms price ~17:00. Day 2 (next business day): cash deposited, execute buy orders, broker confirms buy price ~17:00. Weekends/Korean holidays skipped via `holidays` library. User selects actual sell/buy execution dates via date pickers (within 5 Korean business day window). Historical prices from pykrx used for validation instead of live prices.
- **Portfolio Value:** Single source of truth: `calculate_portfolio_value(data)` returns `(total, holdings_dict)` from `data['shares']` × live ETF prices. Used by Dashboard, Reports, Projections, Plan Revision. Fallback prices defined in `ESTIMATED_ETF_PRICES` constant (shared by `get_fallback_prices()` and `get_default_holdings()`). The old `data['holdings']` and `data['holdings_values']` fields are removed on load.
- **Rebalancing:** Drift threshold >5% triggers alerts with specific share counts (floor for sell, ceil for buy). Workflow tracker allows user to select actual sell/buy execution dates (within 5 Korean business days). Buy step shows settlement info but does not block — user confirms cash availability. Price validation uses historical prices from the selected execution date via `fetch_etf_price_on_date()`. Workflow expires with a warning after 5 business days. Stores `effective_sell_date`, `effective_buy_date`, `settlement_date`, and `workflow_started` per cycle. On "Complete Rebalancing", confirmed sell/buy transactions auto-update `data['shares']` for ETFs (subtract sold, add bought). Cash is excluded — managed separately via Track Deposits. A `shares_applied` flag prevents double-application.
- **Backup:** Every `save_data()` call auto-creates a timestamped backup in `data/backups/` (last 10 kept). Manual backups with custom labels via sidebar. Restore validates JSON and creates a safety `pre_restore` backup before overwriting.
- **Encoding:** Subprocess calls to Claude CLI must use `encoding="utf-8"` (Korean text on Windows).
- **Claude CLI detection:** `_find_claude_exe()` checks `shutil.which` then known install paths (`~/.local/bin/`, `AppData/Roaming/npm/`) since Streamlit may not inherit the full user PATH.

## Coding Standards

- **Language:** Code and comments in English. UI labels and user-facing strings in Korean (한국어).
- **Type hints:** Use type hints for all function signatures.
- **Docstrings:** Every public function needs a one-line docstring minimum.
- **Error handling:** Always wrap external API calls (yfinance, pykrx, subprocess) in try/except with meaningful fallbacks — never let the Streamlit app crash.
- **Streamlit state:** Use `st.session_state` for cross-page data. Never use global variables.
- **Imports:** Standard library → third-party → local modules. No unused imports.
- **No hardcoded paths:** Use `pathlib.Path` or `os.path` for file paths. The app must work on both Windows and Linux.

## Git Workflow

- **Branch naming:** `feature/description`, `fix/description`, `refactor/description`
- **Commit messages:** Use conventional format — `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
  - Example: `feat: add RSU dividend tracking to dashboard`
  - Example: `fix: handle missing market data for delisted ETFs`
- **Before committing:** Always run `python -m py_compile` on changed files to catch syntax errors.
- **Never commit:** `data/irp_tracker_data.json` with real portfolio data, `.env` files, `__pycache__/`
- **Main branch:** `main` — always keep deployable.

## Common Pitfalls (Do NOT)

- **Do NOT** modify `data/irp_tracker_data.json` structure without updating `load_data()`/`save_data()` logic and adding migration handling for existing data files.
- **Do NOT** remove the fallback chain in `market_data.py` (live → cache → mock). The app must work offline.
- **Do NOT** use `subprocess.run()` without `encoding="utf-8"` — Korean characters will break on Windows.
- **Do NOT** add new Streamlit pages as separate files. All pages are `page_*()` functions in the main app file.
- **Do NOT** use `st.cache_data` for mutable data (portfolio state). Use `st.session_state` instead.
- **Do NOT** commit with failing tests. Run tests first.

## Environment

- **OS:** Windows 11 (company-managed, no admin rights)
- **IDE:** VS Code with GitHub Copilot agent
- **Terminal:** PowerShell / Git Bash
- **Python:** 3.11+ via venv (`.venv/` in project root)
- **Claude Code path:** `C:\Users\tskdkim\.local\bin\claude.exe`
- **Activate venv:** `source .venv/Scripts/activate` (Git Bash) or `.venv\Scripts\Activate.ps1` (PowerShell)

## When Resuming Work

If a session was interrupted or you're starting fresh, follow this sequence:
1. Read this CLAUDE.md file (automatic)
2. Check `git status` and `git log --oneline -5` to understand recent changes
3. Check if there are any uncommitted changes that need to be completed
4. Ask the user what they'd like to work on next
