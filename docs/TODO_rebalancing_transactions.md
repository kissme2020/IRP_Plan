# Rebalancing Workflow → Transaction History Integration

**Created:** 2026-03-17
**Status:** Planning
**Branch:** `feature/rebalancing-transactions`

---

## Goal

When the user clicks "I've executed the SELL/BUY orders" in the Rebalancing Workflow Tracker, automatically create batch transaction records in Transaction History with a **pending** status (price blank). The user fills in actual execution prices later (e.g., after 17:00 KST when broker confirms).

---

## Design Decisions

### Transaction ID Strategy

```
batch_id:  "RB-{YYYYMMDD}-{SEQ}"     e.g., "RB-20260317-001"
           ├── Shared across all transactions in one workflow step
           └── Links sells together, buys together

trans_id:  "{uuid8}"                   e.g., "a1b2c3d4"  (existing behavior)
           └── Per-asset, unique as before
```

- `batch_id` groups related transactions for display and bulk operations
- Each asset in the sell/buy list gets its own `trans_id` (unchanged)

### Extended Transaction Schema

```python
transaction = {
    'id': 'a1b2c3d4',                    # existing — unique per transaction
    'batch_id': 'RB-20260317-001',        # NEW — groups sell or buy batch
    'asset': 'AI Core Power',             # existing
    'type': 'sell',                        # existing — 'sell' or 'buy'
    'date': '2026-03-17',                  # existing — order date
    'shares': 15,                          # existing — planned (sell=fixed, buy=adjustable)
    'price_per_share': 0,                  # existing — 0 when pending
    'total_cost': 0,                       # existing — 0 when pending
    'status': 'pending',                   # NEW — 'pending' | 'completed'
    'notes': 'Rebalancing batch sell',     # existing
    'created_at': '2026-03-17T10:30:00',  # existing
}
```

### Hybrid UI for Price Confirmation

**"Confirm All"** button with per-row input fields:

| Asset | Shares | Exec. Price | Total | Status |
|-------|--------|-------------|-------|--------|
| AI Core Power [457930] | 15 (fixed) | `[input]` | auto-calc | Pending |
| Gold [411060] | 8 (fixed) | `[input]` | auto-calc | Pending |
| **[Confirm All Prices]** | | | | |

- **SELL**: Shares are **locked** (broker executes exact quantity)
- **BUY**: Shares are **editable** (price changes during T+2 may require adjustment)
- Single "Confirm All" button updates all rows at once → status becomes `completed`
- If user wants to confirm one-by-one (e.g., partial fills), individual row save is also available via a small per-row button

### Workflow Timeline (Practical Case)

```
Day 1 (Mon) — SELL
  09:00  User reviews rebalancing plan
  10:00  User places sell orders on broker
  10:01  Clicks "I've executed the SELL orders"
         → Creates PENDING sell transactions (price=0)
         → Workflow status: sells_executed
  17:00  Broker confirms execution prices
  17:05  User fills in actual prices in "Confirm Sell Prices" form
         → Transactions updated: pending → completed
         → Workflow status: sells_confirmed (NEW sub-status)

Day 2 (Tue) — SETTLEMENT
  (T+1, cash not yet available)
  UI shows: "⏳ Waiting for settlement — 1 day remaining"

Day 3 (Wed) — BUY
  09:00  Cash settled. UI shows: "✅ Cash available. Execute BUY orders."
         UI recalculates suggested buy shares using LIVE prices
  10:00  User places buy orders (may adjust share counts)
  10:01  Clicks "I've executed the BUY orders"
         → Creates PENDING buy transactions (shares=adjusted, price=0)
         → Workflow status: buys_executed
  17:00  Broker confirms execution prices
  17:05  User fills in actual prices in "Confirm Buy Prices" form
         → Transactions updated: pending → completed
         → Workflow status: buys_confirmed (NEW sub-status)
  17:10  User clicks "Complete Rebalancing"
         → ETF shares auto-updated from confirmed transactions (Cash excluded)
         → shares_applied flag set to prevent double-application
         → Workflow status: completed
```

---

## To-Do List

### Phase 1: Schema & Data Layer ✅
- [x] **1.1** Extend `add_transaction()` — add `batch_id` and `status` params (default `status='completed'`)
- [x] **1.2** Add `generate_batch_id()` function — format: `RB-{YYYYMMDD}-SEQ`
- [x] **1.3** Add `get_pending_transactions(batch_id=None)` — filter by status='pending'
- [x] **1.4** Add `update_transaction()` — generic field updater
- [x] **1.5** Add `confirm_batch_transactions(batch_id, price_map)` — bulk confirm
- [x] **1.6** Guard `calculate_cost_basis()` — skip pending transactions
- [x] **1.7** Add `_asset_name` and `_shares` hidden fields to trade dicts

### Phase 2: SELL Workflow Integration ✅
- [x] **2.1** Modify SELL button handler — create pending sell transactions, store `sell_batch_id`
- [x] **2.2** Add "Confirm Sell Prices" form — per-row price input + "Confirm All" button
- [x] **2.3** Add `sells_confirmed` sub-status with settlement countdown
- [x] **2.4** Expand workflow progress bar to 6 steps

### Phase 3: BUY Workflow Integration ✅
- [x] **3.1** Modify BUY button handler — create pending buy transactions from `planned_buys`
- [x] **3.2** Add "Confirm Buy Prices" form — editable shares + price inputs
- [x] **3.3** Add `buys_confirmed` sub-status + "Complete Rebalancing" button
- [x] **3.4** Wire "Complete Rebalancing" to auto-update `data['shares']` for ETFs from confirmed sell/buy transactions (Cash excluded — managed via Track Deposits). Retroactive "Apply Transactions to Holdings Now" button for workflows completed before this fix. `shares_applied` flag prevents double-application.

### Phase 4: Transaction History Display Updates ✅
- [x] **4.1** Update Transaction History table — Status badge (⏳/✅), Batch column, "—" for pending prices
- [x] **4.2** Update workflow summary (wf_col2) — show batch IDs and confirmation timestamps
- [x] **4.3** Handle workflow reset — delete pending transactions from batch IDs
- [ ] **4.4** Add batch grouping header rows in Transaction History (future enhancement)
- [ ] **4.5** Add filter option for pending transactions (future enhancement)

### Phase 5: Backup & Restore ✅
- [x] **5.0** Auto-backup on every `save_data()` — timestamped files in `data/backups/`, last 10 kept
- [x] **5.1** Manual backup with custom label via sidebar UI
- [x] **5.2** Restore from backup — validates JSON, creates safety `pre_restore` backup first
- [x] **5.3** `.gitignore` updated to exclude `data/backups/`

### Phase 6: Data Consolidation & Structural Cleanup ✅
- [x] **6.1** Remove zombie fields: `data['holdings']`, `data['holdings_values']` — `load_data()` now pops these and ensures `data['shares']` exists
- [x] **6.2** Remove dead functions: `save_holdings()`, `save_holdings_values()`, `get_holdings()`, `get_default_holdings_values()`
- [x] **6.3** Remove Section 4 (manual holdings form) — redundant now that "Complete Rebalancing" auto-updates shares
- [x] **6.4** Fix `record_rebalance()` — compute portfolio value from `shares × prices` instead of stale `data['holdings']`
- [x] **6.5** Consolidate fallback prices — shared `ESTIMATED_ETF_PRICES` constant used by both `get_fallback_prices()` and `get_default_holdings()`
- [x] **6.6** Fix balance calculation across all pages — new `calculate_portfolio_value()` function, `calculate_current_balance()` and `calculate_progress()` now use shares × live prices. Dashboard, Reports, Projections, Plan Revision all consistent.
- [x] **6.7** Add per-asset value history chart — stacked area chart `_render_per_asset_history_chart()` on Dashboard from `portfolio_snapshots`

### Phase 7: Edge Cases & Polish (Future)
- [ ] **7.1** Handle partial confirmation — individual row save buttons alongside "Confirm All"
- [ ] **7.2** Update `generate_portfolio_snapshot()` — include pending transaction info if mid-workflow
- [ ] **7.3** Test backward compatibility — existing transactions without new fields

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/irp_web_app_enhanced.py` | `add_transaction()`, `generate_batch_id()`, new query functions, SELL/BUY button handlers, Confirm UI sections, Transaction History display, workflow status expansion |
| `src/data_handler.py` | Migration logic for new fields in existing data |
| `src/utils.py` | Update `generate_portfolio_snapshot()` if pending transactions should appear in exports |

---

## Notes

- All prices in KRW. No currency conversion needed for ETFs (all KRX-listed).
- `cost_basis` calculation (`calculate_cost_basis`) already uses transaction history — pending transactions (price=0) must be excluded from cost basis until confirmed.
- Korean ETF market hours: 09:00–15:30 KST. Execution prices available ~16:30–17:00.
