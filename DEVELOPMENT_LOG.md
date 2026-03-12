# IRP Tracker Pro — Development Log

## Overview
Tracks implementation progress for the 5 Original Pages that were placeholders.  
Each page follows: **Plan → Code → Test → User Verify → Update MDs → Commit**

**Commit Strategy**: One commit per page (5 total commits)

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
