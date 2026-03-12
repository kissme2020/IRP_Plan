# IRP Tracker Pro — Development Log

## Overview
Tracks implementation progress for the 5 Original Pages that were placeholders.  
Each page follows: **Plan → Code → Test → User Verify → Update MDs → Commit**

**Commit Strategy**: One commit per page (5 total commits)

---

## Implementation Status

| # | Page | Status | Date Started | Date Completed | Commit |
|---|------|--------|-------------|----------------|--------|
| 1 | Original Dashboard | ✅ Complete | 2026-03-12 | 2026-03-12 | — |
| 2 | Track Deposits | ✅ Complete | 2026-03-12 | 2026-03-12 | — |
| 3 | RSU Tracking | ⬜ Not Started | — | — | — |
| 4 | Projections | ⬜ Not Started | — | — | — |
| 5 | Reports | ⬜ Not Started | — | — | — |

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
_(To be planned)_

---

## Page 4: Projections
_(To be planned)_

---

## Page 5: Reports
_(To be planned)_
