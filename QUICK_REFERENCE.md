# QUICK REFERENCE — IRP Retirement Tracker

> Fast-access guide for running, using, and maintaining the IRP Tracker app.

---

## Start the App

```bash
cd c:\Users\tskdkim\Projects\IPR_Plan
.venv\Scripts\activate
streamlit run src/irp_web_app_enhanced.py
```

Opens at: **http://localhost:8501**

Stop the app: **Ctrl+C** in the terminal.

If port 8501 is busy:

```bash
streamlit run src/irp_web_app_enhanced.py --server.port 8502
```

---

## App Pages at a Glance

| Page | What It Does |
|------|-------------|
| **Dashboard** | Portfolio balance, progress toward 400M KRW goal, growth chart |
| **Track Deposits** | Record monthly 600K deposits and quarterly bonuses |
| **Market Dashboard** | Live market data (S&P 500, NASDAQ, KOSPI, VIX, USD/KRW, Gold, Oil, etc.) |
| **Rebalancing Alerts** | Drift detection (>5%), buy/sell share counts, T+2 settlement |
| **Plan Revision** | Compare Conservative / Moderate / Aggressive strategies |
| **Projections** | Year-by-year forecasts and scenario analysis to 2030 |
| **Reports** | Contributions summary, allocation pie chart, alerts |
| **Export for AI Review** | Generate portfolio snapshot markdown for Claude/ChatGPT/Gemini |
| **Import AI Review** | Upload AI response .md, compare allocations, apply changes |
| **RSU Tracking** | Keysight RSU vesting schedule (2027-2030) |

---

## Common Workflows

### Monthly Routine

1. Run the app
2. **Track Deposits** → add monthly entry (date, 600000 KRW base, bonus if any)
3. **Dashboard** → check progress and pace
4. **Market Dashboard** → review conditions and recommendations
5. Stop the app (Ctrl+C)

### Quarterly AI Review

1. **Export for AI Review** → copy the generated snapshot
2. Paste into [Claude.ai](https://claude.ai/new) (or ChatGPT / Gemini)
3. Save the AI response as a `.md` file
4. **Import AI Review** → upload the `.md` file
5. Review current vs. recommended allocation side-by-side
6. Click **Apply** to update targets (or **Reset** for Option B defaults)
7. **Rebalancing Alerts** → check for new trade recommendations
8. Execute trades if needed

### Rebalancing Execution (When Alerts Fire)

1. **Rebalancing Alerts** → review drift and share recommendations
2. Execute **sells first** (priority: HIGH drift items)
3. Wait for **T+2 settlement** (Korea business days, excludes holidays)
4. On settlement day, recalculate buy-side shares at current prices
5. Execute **buys**
6. Update the workflow tracker state as you progress

> Workflow states: `Not Started` → `Sells Executed` → `Awaiting Settlement` → `Buys Executed` → `Completed`

---

## ETF Portfolio (8 Assets)

| Short Name | KODEX ETF | Ticker | Type | Target % |
|-----------|-----------|--------|------|----------|
| AI Core Power | KODEX 미국AI전력핵심인프라 | 457930 | Equity | 28% |
| AI Tech TOP10 | KODEX 미국AI테크TOP10타겟커버드콜 | 483280 | Equity | 14% |
| Dividend Stocks | KODEX 미국배당다우존스 | 489250 | Equity | 10% |
| Consumer Staples | KODEX 미국S&P500필수소비재 | 453630 | Equity | 8% |
| Treasury Bonds | KODEX 미국30년국채액티브(H) | 484790 | Bond | 11% |
| Gold | KODEX 골드선물(H) | 132030 | Commodity | 7% |
| Japan TOPIX | KODEX 일본TOPIX100 | 101280 | Equity | 2% |
| Cash | — | — | Cash | 28% |

Allocation targets are editable via AI Review import or manual reset.

---

## Market Data Status Indicators

| Icon | Meaning |
|------|---------|
| 🟢 | **Live** — real-time data from yfinance / pykrx |
| 🟡 | **Fallback** — cached data (API temporarily unavailable) |
| 🔴 | **Mock** — offline placeholder data |

---

## Key Files

| File | Purpose |
|------|---------|
| `src/irp_web_app_enhanced.py` | Main Streamlit app (all pages) |
| `src/market_data.py` | Market data fetching (yfinance, cache, fallback) |
| `src/data_handler.py` | JSON data load/save, deposits, RSU |
| `src/utils.py` | Helpers: share conversion, settlement dates, AI snapshot |
| `data/etf_config.json` | ETF ticker codes and metadata |
| `data/irp_tracker_data.json` | All your portfolio data (auto-created) |
| `requirements.txt` | Python dependencies |

---

## Data Backup

```bash
copy data\irp_tracker_data.json data\irp_tracker_data_backup.json
```

Restore:

```bash
copy data\irp_tracker_data_backup.json data\irp_tracker_data.json
```

---

## Troubleshooting Cheat Sheet

| Problem | Fix |
|---------|-----|
| `command not found` / no `(venv)` prompt | `.venv\Scripts\activate` |
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| Port 8501 in use | Add `--server.port 8502` |
| `.venv` folder missing | `python -m venv .venv` then activate & install |
| Browser won't open | Copy URL from terminal, paste in browser |
| Data not saving | Don't close abruptly — always use Ctrl+C |
| ETF prices not loading | Check internet; app falls back to cached/mock data |

---

## Git Workflow

```bash
# Check status
git status

# Stage, commit, push
git add -A
git commit -m "your message"
git push
```

---

## Environment Setup (First Time Only)

```bash
cd c:\Users\tskdkim\Projects\IPR_Plan
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Requirements**: Python 3.11+, Windows, ~500MB disk space.

**Dependencies**: streamlit, pandas, plotly, numpy, requests, pykrx, yfinance, holidays

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Starting Balance | 175.7M KRW (March 2026) |
| Retirement Goal | 400M KRW |
| Retirement Date | December 31, 2030 |
| Monthly Deposit | 600K KRW + quarterly bonuses |
| RSU Total | $30,458 (4 tranches, 2027-2030) |
| Target CAGR | 10.2% |
| Success Probability | 88% |
| Rebalance Trigger | >5% drift from target allocation |
| Rebalancing Frequency | Every 90 days |

---

*Last Updated: March 12, 2026*
