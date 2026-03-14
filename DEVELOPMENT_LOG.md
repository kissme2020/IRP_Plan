# IRP Tracker Pro — Development Log

## Overview
Tracks implementation progress for the IRP Tracker Pro app.
Each feature follows: **Plan → Code → Test → User Verify → Update MDs → Commit**

---

## Implementation Status

| # | Page | Status | Date Started | Date Completed | Commit |
|---|------|--------|-------------|----------------|--------|
| 1 | Original Dashboard | ✅ Complete | 2026-03-12 | 2026-03-12 | dba0ff3 |
| 2 | Track Deposits | ✅ Complete | 2026-03-12 | 2026-03-12 | 5d95228 |
| 3 | RSU Tracking | ✅ Complete | 2026-03-12 | 2026-03-12 | 46f55ef |
| 4 | Projections | ✅ Complete | 2026-03-12 | 2026-03-12 | d6d5153 |
| 5 | Reports | ✅ Complete | 2026-03-12 | 2026-03-12 | d6d5153 |

---

## Page 1: Original Dashboard

### Plan
- Balance overview with large KRW display
- Progress bar toward 400M goal with percentage
- Success probability gauge
- Balance growth chart over time (from deposit history)
- Key metrics: time remaining, required monthly savings, CAGR needed
- Goal visualization with milestones

### Backend Functions Available
- `calculate_current_balance()` — from holdings values
- `calculate_progress()` — percentage toward goal
- `calculate_time_remaining()` — years/months left
- `project_balance_to_retirement()` — future projection
- `get_success_probability()` — probability estimate
- `IRP_CONFIG` — target, retirement date, contributions

### Implementation Notes
- **Date:** 2026-03-12
- Added `page_original_dashboard()` function (~180 lines) before `main()`
- Updated `main()` routing: `elif page == "Original Dashboard": page_original_dashboard()`
- Updated placeholder message to exclude "Original Dashboard" from "coming soon" list
- **Sections implemented:**
  1. Key Metrics Row: Balance, Target Goal, Success Probability, Time Remaining
  2. Progress Gauge: Plotly gauge chart toward 400M, floor progress bar, breakdown
  3. Current vs Target Allocation: Side-by-side pie charts, drift table with status indicators
  4. Projected Growth: 3-scenario line chart (6%, 10.2%, 15%) with goal/floor reference lines
  5. Milestones: 200M → 400M milestone tracker with reached/pending status
  6. Key Financial Metrics: Projected retirement balance, required CAGR, monthly contribution, RSU total

---

## Page 2: Track Deposits

### Plan
- Summary metrics: total contributions, dividends, inflows, record count
- Add new deposit form: base (600K), bonus, other with date picker
- Deposit history table with tabs: All Inflows, Contributions, Dividends
- Delete capability per record
- Monthly bar chart (stacked contributions + dividends)
- Cumulative inflow line chart
- Deposit statistics: average, max, min, vs expected

### Backend Functions Used
- `add_transaction()` — reuses existing transaction system (type: contribution)
- `delete_transaction()` — existing delete by ID
- `get_transactions()` — filter by type
- Uses `transactions` list in irp_tracker_data.json (consistent with Rebalancing page)

### Implementation Notes
- **Date:** 2026-03-12
- Added `page_track_deposits()` function (~200 lines) + helper `_render_deposit_table()`
- Reuses existing transaction system rather than creating parallel deposit storage
- Contributions use `price_per_share` field for amount (matching existing data pattern)
- Updated `main()` routing

---

## Page 3: RSU Tracking

### Plan
- Summary metrics: total RSU value (USD & KRW), vested/unvested counts
- Vesting schedule table: tranche, date, USD, Gross KRW, Net KRW, status with countdown
- Mark as vested / undo vesting functionality
- Vesting timeline: bar chart by status + progress donut
- IRP impact: gap coverage %, gap after all RSU

### Backend Functions Used
- `_get_rsu_data()` — new helper, initializes 4 Keysight tranches if empty
- `save_data()` — persist vesting status changes
- `DEFAULT_RSU_SCHEDULE` — new constant with 4 tranches ($7,614 each)
- `IRP_CONFIG` for exchange rate (1,250) and after-tax % (70%)

### Implementation Notes
- **Date:** 2026-03-12
- Rewrote to **share-based data model**: `shares`, `grant_price_usd`, `vest_price_usd`, `vested_date`
- Added `_calc_rsu_value()` helper for consistent value calculations
- Added migration code in `_get_rsu_data()` to auto-convert old `amount_usd` format
- Added duplicate tranche # detection and auto-fix on load
- 5-tab management UI: Edit (shares+price), Vest (with actual price input & gain preview), Add (auto-numbering), Delete, Settings
- Fixed `calculate_total_deposits()` to work with share-based RSU data
- Updated `main()` routing

---

## Page 4: Projections

### Plan
- Adjustable parameters: monthly contribution, annual bonus, expected return %, RSU toggle
- Year-by-year projection table (2026–2030) with all income sources
- Multi-scenario growth chart (Conservative/Custom/Optimistic)
- Contribution source breakdown pie chart
- Required return calculator with estimated goal date

### Backend Functions Used
- `calculate_progress()` — current balance and gap
- `calculate_time_remaining()` — years/months to retirement
- `calculate_future_value()` from utils.py — compound growth
- `IRP_CONFIG` — base monthly, bonus, target CAGR
- RSU data from `data['rsu_vesting']` — unvested tranches by year

### Implementation Notes
- **Date:** 2026-03-12
- Added `page_projections()` function (~200 lines)
- Year-by-year loop builds balance with monthly compounding, bonus, and RSU lump sums
- Binary search algorithm for required annual return to reach goal
- Months-to-goal calculator estimates when 400M target is hit
- Updated `main()` routing

---

## Page 5: Reports

### Plan
- Portfolio summary metrics (balance, goal, progress, time remaining)
- Allocation report: actual vs target with deviation table and status indicators
- Side-by-side pie charts (current vs target allocation)
- Contribution history summary with monthly bar chart
- RSU summary (shares, vested/unvested, total value)
- Plan parameters reference table

### Backend Functions Used
- `calculate_progress()` — portfolio metrics
- `ALLOCATION_TARGET` — target allocation percentages
- `data['holdings_values']` — KRW values (not share counts)
- `data['transactions']` — contribution and dividend history
- `data['rsu_vesting']` — RSU summary data

### Implementation Notes
- **Date:** 2026-03-12
- Added `page_reports()` function (~200 lines)
- Uses `holdings_values` (not `holdings`) for proper KRW-based allocation percentages
- Falls back to `get_default_holdings_values()` if no values data exists
- Updated `main()` routing
- **All 10 sidebar pages now fully implemented**

---

## Bug Fixes

### Arrow Serialization Error — Mixed Types in 'Shares' Column
- **Date:** 2026-03-13
- **Error:** `pyarrow.lib.ArrowInvalid: Could not convert '-' with type str: tried to convert to int64 — Conversion failed for column Shares with type object`
- **Root Cause:** The `Shares` column in DataFrames passed to `st.dataframe()` contained mixed types — `'-'` (string) for cash transactions (contributions/dividends) alongside raw integers for buy/sell transactions. PyArrow cannot serialize columns with mixed int/str types.
- **Files Changed:** `src/irp_web_app_enhanced.py`
- **Fix:** Cast all `Shares` values to `str()` before building DataFrames:
  - **Line ~1375** (Transaction History table): `str(t['shares'])` instead of raw `t['shares']`
  - **Line ~1519** (Gains/Losses table): `str(data_item['shares'])` instead of raw `data_item['shares']`
- **Impact:** Resolved repeated Arrow serialization warnings in Streamlit console

### Raw Materials / Commodity Indices Added to Market Dashboard
- **Date:** 2026-03-13
- **Change:** Added 5 commodity indices to `MARKET_INDICES` in `src/market_data.py`
  - Gold (`GC=F`) — Gold Futures (USD/oz)
  - Crude Oil WTI (`CL=F`) — WTI Crude Oil Futures (USD/bbl)
  - Silver (`SI=F`) — Silver Futures (USD/oz)
  - Copper (`HG=F`) — Copper Futures (USD/lb)
  - Natural Gas (`NG=F`) — Natural Gas Futures (USD/MMBtu)
- **Files Changed:** `src/market_data.py`, `src/irp_web_app_enhanced.py`
- **Details:**
  - New `"Commodities"` category in `MARKET_INDICES` and `_MOCK_FALLBACK`
  - Added `$` USD price formatting for Commodities category in the web app
  - Total tracked indices: 8 → 13

---

## Feature: Three-Persona AI Review with Discussion Context

### Persona Export / Import (Commit: f44316a)
- **Date:** 2026-03-13
- **Branch:** `feature/persona-ai-review`
- **Files Changed:** `src/utils.py`, `src/irp_web_app_enhanced.py`, `data/sample_persona_review.md`, `test_persona_parser.py`
- **Changes:**
  - **`src/utils.py`**: Added `generate_persona_export()` — three-persona export template with Cathie Wood, Peter Lynch, Ray Dalio mandates. Added `parse_persona_review_md()`, `_parse_persona_section()`, `detect_review_format()`, `persona_review_to_standard()`, `normalize_asset_name()` with fuzzy `_ASSET_ALIASES` map
  - **`src/irp_web_app_enhanced.py`**: Export page gains Standard/Three-Persona toggle. Import page auto-detects format, shows persona tabs via `_show_persona_tabs()`. Fixed orphaned `col2` reset button.
  - Created `data/sample_persona_review.md` and `test_persona_parser.py`
  - All 8 assets match, sums to 100%, parser tests pass

### AI Review on Dashboard / Reports / Projections + Persona Discussions (Commit: 254523c)
- **Date:** 2026-03-13
- **Branch:** `feature/persona-ai-review`
- **Files Changed:** `src/utils.py`, `src/irp_web_app_enhanced.py`, `data/sample_persona_review.md`, `test_persona_parser.py`
- **Changes:**
  - **`save_ai_review()`**: Now persists `market_outlook` and `persona_discussions` fields
  - **`get_latest_ai_review()`**: New helper returns most recent AI review record
  - **Dashboard**: Added "Latest AI Review" section — CAGR metric, expandable recommendations, market outlook, persona discussions
  - **Reports**: Added "AI Review History" — last 5 reviews with expandable allocation, CAGR, recommendations, outlook, discussions
  - **Projections**: Pre-fills Expected Return with AI-recommended CAGR (falls back to config 10.2%)
  - **Export template**: Added `### Discussion` subsection instructions — each persona responds to/critiques others
  - **Parser**: `_parse_persona_section()` extracts `### Discussion` content
  - **`persona_review_to_standard()`**: Bundles per-persona + synthesis discussions into `persona_discussions` dict
  - **`_show_persona_tabs()`**: Displays discussion in expandable "💬 Discussion with other personas" section
  - Updated `data/sample_persona_review.md` with Discussion sections for all 3 personas + synthesis
  - All parser tests pass including discussion extraction (4 discussion entries)

### Claude CLI Integration for One-Click AI Review
- **Date:** 2026-03-14
- **Files Changed:** `src/utils.py`, `src/irp_web_app_enhanced.py`, `test_claude_cli.py`, `README.md`, `QUICK_REFERENCE.md`, `DEVELOPMENT_LOG.md`
- **Changes:**
  - **`utils.py`**: Added `is_claude_cli_available()`, `run_claude_cli()`, `save_review_md()` — subprocess wrapper for `claude -p` with model selection, timeout, budget cap, and error handling
  - **`irp_web_app_enhanced.py`**: Updated `page_export_snapshot()` — added "Run AI Review Now" button with model/timeout/budget controls; inline result display via `_show_cli_review_results()` with Apply/Reset; existing manual workflow moved to collapsible fallback section
  - **`test_claude_cli.py`**: 32 unit tests covering CLI detection, success/failure/timeout paths, save_review_md, end-to-end parse, budget flag passthrough
  - **Quarterly workflow reduced from 8 manual steps to 3** (generate → review → apply)
  - Documentation updated: README.md (feature description, quarterly workflow Option A/B, version history), QUICK_REFERENCE.md (page table, workflow steps)

### Portfolio Snapshots — On-Demand + Auto Mid-Month
- **Date:** 2026-03-14
- **Files Changed:** `src/utils.py`, `src/irp_web_app_enhanced.py`, `test_portfolio_snapshots.py`, `CLAUDE.md`, `QUICK_REFERENCE.md`, `DEVELOPMENT_LOG.md`
- **Changes:**
  - **`utils.py`**: Added `is_kr_business_day()`, `should_auto_snapshot()`, `create_portfolio_snapshot()` — reuses existing `KR_TZ`, `KR_HOLIDAYS` for Korean business day logic. Auto-snapshot triggers on first business day ≥ 15th if no snapshot exists for that month. Skips weekends and Korean holidays (including substitute holidays).
  - **`irp_web_app_enhanced.py`**: Added `save_portfolio_snapshot()`, `get_portfolio_snapshots()`, `check_and_run_auto_snapshot()`, `_render_portfolio_history_chart()`. Dashboard gains "Portfolio Snapshots" section: on-demand button with optional note, Portfolio History line chart (auto=green circles, manual=orange diamonds) with 400M goal and 300M floor lines, snapshot history table. Auto-check runs in `main()` on every app launch. Backward-compatible migration for `portfolio_snapshots` key in `load_data()`.
  - **`test_portfolio_snapshots.py`**: 28 unit tests covering `is_kr_business_day` (weekends, holidays, business days), `should_auto_snapshot` (before 15th, on 15th, existing snapshot, weekend 15th, substitute holiday, first biz day, cross-month), `create_portfolio_snapshot` (values, totals, allocation, triggers, empty portfolio).
  - **Snapshot data:** date, trigger (auto/manual), shares, prices, values, total_value, allocation_pct, allocation_targets, note
  - **Design rationale:** Company deposit arrives end-of-month → ETF rebalancing takes ~2 weeks → mid-month snapshot captures settled post-rebalance state
  - **Verification:** Scheduled for 2026-03-16 (Monday) — first Korean business day ≥ 15th for March 2026. The 15th (Sunday) will be skipped; auto-snapshot should trigger on the 16th.
