# IRP Retirement Tracker

A professional web application for tracking your Korean IRP (Individual Retirement Pension) and Keysight RSU toward a 400M KRW retirement goal by December 2030.

## Features

- **Market Monitoring**: Live market data via yfinance (S&P 500, NASDAQ, Dow Jones, KOSPI, KOSDAQ, VIX, US 10Y Yield, USD/KRW, Gold, Crude Oil WTI, Silver, Copper, Natural Gas)
- **Rebalancing Alerts**: Automatic detection of portfolio drift with specific buy/sell recommendations
- **Time-Based Rebalancing**: Configurable rebalancing schedule (e.g., every 90 days) with alerts
- **Transaction Tracking**: Record buy/sell transactions with date, shares, and price
- **Gains/Losses Analysis**: Calculate unrealized gains/losses based on cost basis (FIFO method)
- **AI Recommendations**: Intelligent suggestions based on market conditions and your progress
- **Automatic Price Tracking**: Real-time ETF prices via pykrx API (Korea Exchange data)
- **Holdings Management**: ETFs as shares (auto-calculate value), Cash as KRW
- **Monthly Tracking**: Easy deposit entry and progress monitoring
- **RSU Management**: Track your Keysight RSU vesting (4 tranches: 2027-2030)
- **Projections**: Year-by-year balance projections to retirement
- **Export for AI Review**: Generate portfolio snapshots for Claude/ChatGPT/Gemini — Standard or Three-Persona format (Cathie Wood, Peter Lynch, Ray Dalio) with inter-persona discussion instructions
- **Import AI Review**: Auto-detect and parse Standard or Three-Persona .md files — persona tabs, discussion context, one-click apply
- **Data-Driven Allocation**: Allocation targets stored in JSON, editable via AI review or manual reset
- **Allocation History**: Track all allocation target changes over time with source and notes
- **Professional Dashboard**: Beautiful visualizations with Plotly

## Your Numbers

- **Current Balance**: 175.7M KRW (March 2026)
- **Target Goal**: 400M KRW
- **Retirement Date**: December 31, 2030
- **Monthly Contribution**: 600K KRW base + quarterly bonuses
- **Keysight RSU**: $30,458 (≈26-28M KRW after-tax)
- **Expected Return**: 10.2% CAGR
- **Success Probability**: 88% (Option B - Moderate strategy)

## Project Structure

```
c:/Users/tskdkim/Projects/IPR_Plan/
├── README.md                           # This file
├── QUICK_REFERENCE.md                  # Quick reference for running & using the app
├── .gitignore                          # Git ignore file
├── requirements.txt                    # Python dependencies
├── src/                                # Source code
│   ├── __init__.py                     # Package initializer
│   ├── irp_web_app_enhanced.py         # Main Streamlit app (Market, Rebalancing, etc.)
│   ├── market_data.py                  # Market data module (yfinance + cache + fallback)
│   ├── data_handler.py                 # Data loading/saving utilities
│   └── utils.py                        # Helper functions (incl. krw_to_shares)
├── data/                               # Data storage
│   └── irp_tracker_data.json           # Your retirement data (auto-created)
└── .venv/                              # Virtual environment
```

## Setup Instructions

### Requirements
- Python 3.11+
- Windows
- ~500MB disk space

### Installation

1. **Navigate to project folder**
   ```bash
   cd c:/Users/tskdkim/Projects/IPR_Plan
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   ```bash
   .venv\Scripts\activate
   ```

4. **Install packages**
   ```bash
   pip install -r requirements.txt
   ```

   Or manually:
   ```bash
   pip install streamlit pandas plotly numpy requests pykrx yfinance
   ```

5. **Verify installation**
   ```bash
   python --version
   ```
   
   Should show: `Python 3.11.x`

## Running the App

Start the app with:
```bash
streamlit run src/irp_web_app_enhanced.py
```

The app will open in your browser at:
```
http://localhost:8501
```

If browser doesn't open automatically, manually navigate to that URL.

To stop the app, press `Ctrl+C` in the terminal.

## How to Use the App

### Dashboard
- View current portfolio balance (starting 175.7M KRW)
- Check progress toward 400M KRW goal
- See success probability
- View balance growth chart over time
- **Latest AI Review summary**: CAGR metric, key recommendations, market outlook, persona discussions

### Track Deposits
- Add monthly 600K IRP deposits
- Record quarterly bonuses (variable amounts)
- Track portfolio values
- View deposit history and trends
- See monthly statistics

### RSU Tracking
- Record Keysight RSU vesting tranches (2027-2030)
- Each tranche: ~$7,614 USD (~6.6M KRW after-tax)
- Track cumulative progress
- Monitor vesting timeline
- All 4 tranches contribute to your goal

### Market Dashboard
- **Live market data** via Yahoo Finance (yfinance) with 10-minute cache:
  - S&P 500 (US large cap benchmark)
  - NASDAQ (US tech-heavy composite)
  - Dow Jones (US blue chip 30)
  - KOSPI (Korea composite index)
  - KOSDAQ (Korea growth/tech index)
  - US 10Y Treasury Yield (bond reference)
  - VIX (CBOE volatility / fear gauge)
  - **USD/KRW exchange rate** (highlighted metric card)
  - Gold Futures (USD/oz)
  - Crude Oil WTI Futures (USD/bbl)
  - Silver Futures (USD/oz)
  - Copper Futures (USD/lb)
  - Natural Gas Futures (USD/MMBtu)
- Hybrid approach: real API → cached 10 min → fallback mock if offline
- Source indicators: 🟢 Live / 🟡 Fallback / 🔴 Mock
- Market trend analysis uses live VIX for volatility, 10Y yield for bond outlook
- AI-powered recommendations based on current conditions

### Rebalancing Alerts
- Automatic drift detection (>5% from target)
- Specific buy/sell recommendations with **number of shares** to trade
- Rebalancing calculator with exact amounts (KRW + shares)
- **T+2 Settlement Timeline**: Shows trade day and settlement date (Korea business days)
  - Excludes weekends and Korean public holidays (설날, 추석, etc.)
  - Uses `Asia/Seoul` timezone
  - Settlement date auto-calculated via `holidays` Python package
- **Rebalancing Workflow Tracker**: Step-by-step state machine
  - `Not Started` → `Sells Executed` → `Awaiting Settlement` → `Buys Executed` → `Completed`
  - Progress bar with visual status
  - Warns against buying before cash settles
  - Reminds to recalculate buy-side shares at current prices on settlement day
- Execution order guidance (sell first, wait for settlement, then buy)
- Priority ranking (HIGH/MEDIUM)

### Plan Revision
- Evaluate your current strategy
- Compare 3 options:
  - Conservative (30% growth): 340-360M outcome
  - Moderate (42% growth): 375-400M outcome ← Your choice
  - Aggressive (55% growth): 410-470M outcome
- Get personalized recommendations based on progress
- Assess current risk level

### Projections
- Year-by-year balance forecasts to 2030
- Scenario analysis with different return rates (6%, 10%, 15%, 18%)
- Expected Return pre-filled with latest AI-recommended CAGR (falls back to 10.2%)
- Impact of different monthly deposit amounts
- Impact of annual return rate changes
- Milestone tracking

### Reports
- Contribution summary (base + bonuses)
- Monthly breakdown of deposits
- Recommended allocation pie chart (Option B allocation)
- Alerts and recommendations based on progress
- Current portfolio status
- **AI Review History**: Last 5 reviews with allocation, CAGR, recommendations, outlook, persona discussions

### Export for AI Review
- Generates a ready-to-paste markdown snapshot of your entire portfolio
- Includes holdings, drift analysis, gains/losses, transaction history, and ETF reference
- **Two export modes**: Standard (single reviewer) or Three-Persona (Cathie Wood, Peter Lynch, Ray Dalio)
- Three-Persona mode includes mandates per persona and `### Discussion` subsection instructions for inter-persona debate
- Contains **Response Format Instructions** that tell any AI to reply in our exact parseable format
- **Claude CLI integration**: one-click "Run AI Review Now" button — generates snapshot, calls `claude -p`, parses response, and displays results with Apply button (no copy-paste needed)
- Model selection (Sonnet for speed, Opus for depth), configurable timeout and budget cap
- Fallback: manual copy text → paste into Claude.ai / ChatGPT / Gemini → save response as .md

### Import AI Review
- Upload the AI's .md response file (for manual workflow)
- **Auto-detects** Standard or Three-Persona format
- Parser extracts: allocation table, CAGR assessment, key recommendations (HIGH/MEDIUM/LOW), market outlook, persona discussions
- Three-Persona imports show **per-persona tabs** with individual allocations, CAGR, recommendations, and discussion context
- Side-by-side comparison of current vs recommended allocation (uses SYNTHESIS for persona format)
- Fine-tune values before applying
- One-click **Apply** to update allocation targets, or **Reset** to Option B defaults
- View allocation change history

## Strategy Details

### Target Allocation (Option B - Moderate)

Default allocation targets (can be updated via AI Review import):

- **Growth Equities (42%)**
  - KODEX AI Core Power (28%)
  - KODEX AI Tech TOP10 (14%)
  
- **Defensive Equities (18%)**
  - KODEX Dividend Stocks (10%)
  - KODEX Consumer Staples (8%)
  
- **Bonds (11%)**
  - KODEX US 30Y Treasury Active (H)
  
- **Cash (28%)**
  - Flexible buffer for bonuses and opportunities

### 5-Year Timeline

- **March 2026**: Start with 175.7M KRW
- **2027**: RSU Tranche 1 vests (~6.6M KRW, March)
- **2028**: RSU Tranche 2 vests (~6.6M KRW, March)
- **2029**: RSU Tranche 3 vests (~6.6M KRW, March)
- **2030**: RSU Tranche 4 vests (~6.6M KRW, March)
- **December 2030**: Retirement target (~400M+ KRW)

### Expected Outcomes

- **Conservative Case**: 375M KRW (88% probability)
- **Expected Case**: 400M KRW
- **Optimistic Case**: 425M+ KRW
- **Monthly Annuity Income**: 3.0-3.2M KRW
- **Living Need**: 3.0M KRW/month

## Data Storage

Your retirement data is automatically saved in:
```
c:/Users/tskdkim/Projects/IPR_Plan/data/irp_tracker_data.json
```

This file contains:
- All monthly deposits
- RSU vesting records
- Progress tracking
- App settings
- Custom allocation targets (updated via AI Review import)
- Allocation change history (date, source, previous/new values)
- AI review records

**Important: Back up this file regularly!**

To backup:
```bash
# Copy to another location
copy data\irp_tracker_data.json [backup_location]
```

To restore:
```bash
# Copy backup back to data folder
copy [backup_location]\irp_tracker_data.json data\
```

## ETF Configuration

ETF configuration is stored in `data/etf_config.json` for easy maintenance. The app tracks the following Korean ETFs:

| ETF Name (English) | Korean Name | Ticker Code | Category |
|-------------------|-------------|-------------|----------|
| AI Core Power | KODEX 미국AI전력핵심인프라 | 457930 | Growth |
| AI Tech TOP10 | KODEX 미국AI테크TOP10타겟커버드콜 | 483280 | Growth |
| Dividend Stocks | KODEX 미국배당다우존스 | 489250 | Defensive |
| Consumer Staples | KODEX 미국S&P500필수소비재 | 453630 | Defensive |
| Treasury Bonds | KODEX 미국30년국채액티브(H) | 484790 | Bonds |
| Gold | ACE KRX금현물 | 411060 | Safe Haven |
| Japan TOPIX | KODEX 일본TOPIX100 | 101280 | International |

To add or modify ETFs, edit `data/etf_config.json`:
```json
{
    "ETF Name": {
        "code": "123456",
        "name": "Full ETF Name (English)",
        "name_kr": "한국어 ETF 이름",
        "type": "Equity|Bond|Commodity|Cash",
        "description": "Description"
    }
}
```

### Price Tracking

Prices are automatically fetched from the Korea Exchange (KRX) using the `pykrx` library. If a ticker fails to fetch, the app uses fallback prices.

### Holdings Input

Enter your holdings for accurate portfolio value calculation:

| Asset Type | Input | Calculation |
|------------|-------|-------------|
| **ETFs** | Number of shares | Value = Shares × Live Price (from KRX API) |
| **Cash** | KRW amount | Value = KRW amount (1:1) |

This approach is more accurate because:
- Share counts don't change (you own what you own)
- Prices update automatically from Korea Exchange
- Portfolio value = Σ (shares × current price)

### Transaction Tracking

Record your transactions to track portfolio activity and calculate gains/losses:

| Field | Description | Required |
|-------|-------------|----------|
| Asset | Which ETF (e.g., AI Core Power) | ✅ Yes |
| Date | Transaction date | ✅ Yes |
| Type | 🟢 Buy, 🔴 Sell, 💰 Employer Contribution, or 📊 ETF Dividend | ✅ Yes |
| Shares | Number of shares (Buy/Sell only) | ✅ For Buy/Sell |
| Price per Share | Price in KRW (Buy/Sell only) | ✅ For Buy/Sell |
| Amount | KRW amount (Contribution/Dividend only) | ✅ For Cash types |
| Notes | Optional memo | ❌ No |

**Transaction Types:**
- **Buy/Sell**: Standard ETF trades with shares and price
- **Employer Contribution**: Cash deposits from employer (amount in KRW)
- **ETF Dividend**: Dividend income received from ETFs (amount in KRW)

### Gains/Losses Calculation

The app calculates unrealized gains/losses using the **FIFO (First In, First Out)** method:
- Tracks your average cost basis per asset
- Compares with current market prices
- Shows both absolute gain (KRW) and percentage return

### Time-Based Rebalancing

Configure automatic rebalancing alerts:
- **Frequency**: How often to rebalance (default: 90 days)
- **Alert Threshold**: Warn when allocation drifts > X% (default: 5%)
- **Last Rebalance**: Track when you last rebalanced

## Monthly Workflow

### Each Month:

1. **Run the app**
   ```bash
   streamlit run src/irp_web_app_enhanced.py
   ```

2. **Click "Track Deposits"**

3. **Add your monthly entry**
   - Date: Today or date you received deposit
   - Base deposit: 600000 (KRW)
   - Bonus: 0 (unless you received one)
   - Portfolio value: (optional)

4. **Click "Dashboard"**
   - Check your progress
   - See if you're on pace

5. **Check "Market Dashboard"**
   - See market conditions
   - Read recommendations
   - Any portfolio adjustments needed?

6. **When done, stop the app**
   ```bash
   Press Ctrl+C in terminal
   ```

### Quarterly (Every 3 months):

**Option A — Claude CLI (recommended, 3 steps):**
1. Go to **Export for AI Review** → choose Standard or Three-Persona → click **"Run AI Review Now"**
2. Review the parsed results → click **Apply** to update targets
3. Check **Rebalancing Alerts** for new trade recommendations → execute trades → backup data

**Option B — Manual copy-paste (fallback, 9 steps):**
1. Go to **Export for AI Review** → expand "Manual Copy-Paste Workflow" → copy the snapshot
2. Paste into [Claude.ai](https://claude.ai/new) (or ChatGPT/Gemini)
3. Save the AI response as a `.md` file
4. Go to **Import AI Review** → upload the file
5. Review recommended allocation changes
6. Click **Apply** to update targets
7. Check **Rebalancing Alerts** for new trade recommendations
8. Execute any portfolio adjustments
9. Update data backup

### Annually (December):

1. Full year review
2. Compare actual vs. target progress
3. Assess if strategy adjustments needed
4. Plan next year's approach

## Troubleshooting

### App Won't Start

**Error**: Command not found
```bash
# Make sure virtual environment is active
# Look for (venv) at start of terminal line
```

**Fix**:
```bash
.venv\Scripts\activate
```

### ModuleNotFoundError

**Error**: No module named 'streamlit'
```bash
# Package not installed
```

**Fix**:
```bash
# Make sure (venv) is active first
pip install streamlit pandas plotly numpy requests
```

### Port Already in Use

**Error**: Port 8501 already in use

**Fix**:
```bash
# Use a different port
streamlit run src/irp_web_app_enhanced.py --server.port 8502

# Then visit: http://localhost:8502
```

### Virtual Environment Issues

**If (.venv) isn't showing**:
```bash
.venv\Scripts\activate
```

**If .venv folder is missing**:
```bash
# Recreate it
python -m venv .venv

# Then activate
.venv\Scripts\activate

# Then reinstall packages
pip install -r requirements.txt
```

### Browser Won't Open Automatically

1. Check terminal for the URL
2. Copy the "Local URL" line
3. Manually open in browser
4. Paste URL in address bar

### Data Not Saving

1. Don't close app abruptly (use Ctrl+C)
2. Check that data/irp_tracker_data.json exists
3. Verify file permissions allow writing
4. Try running app again

## Important Notes

### Strategy Discipline

✓ Continue monthly deposits even during market corrections
✓ Market crashes are buying opportunities (dollar-cost averaging)
✓ Hold firm through 10-30% corrections (normal in markets)
✓ Use app recommendations to guide decisions

### Market Volatility

- **10-15% correction**: Keep deposits flowing, rebalance if drift >5%
- **20-30% correction**: Hold firmly, increase deposits if possible
- **>30% crash**: Legendary buying opportunity, maintain discipline

### Risk Management

- Your allocation automatically shifts more conservative over time
- Monthly deposits provide dollar-cost averaging (buying at all prices)
- Quarterly rebalancing locks in gains
- RSU vesting provides external capital injection

### Success Factors

✓ Consistency (monthly deposits are critical)
✓ Discipline (don't panic sell)
✓ Monitoring (quarterly reviews)
✓ Patience (5-year timeline)
✓ Automation (app does calculations for you)

## Author

**Created by**: tskdkim  
**Date**: March 2026  
**Project**: IRP Retirement Tracker  
**Purpose**: Track IRP retirement savings with intelligent market monitoring  
**License**: Personal use

## Support & Help

For help or questions:

1. **Quick Reference**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common commands and workflows
2. **Error messages**: Read carefully - they tell you what's wrong
3. **Documentation**: Check SETUP guides provided
3. **Streamlit docs**: https://docs.streamlit.io/
4. **Python docs**: https://docs.python.org/3.11/
5. **Search**: Google the error message (likely someone solved it)

## Next Steps

1. ✓ Save this README.md to your project folder
2. ✓ Create .gitignore file
3. ✓ Create virtual environment
4. ✓ Install packages
5. → Run the app: `streamlit run src/irp_web_app_enhanced.py`
6. → Add your first monthly deposit
7. → Start tracking your retirement journey!

## Version History

- **v1.0** (March 2026): Initial setup and deployment
- **v1.1** (March 2026): Added QUICK_REFERENCE.md
- **v1.2** (March 2026): Claude CLI integration for one-click AI review
- **Status**: Active monitoring (March 2026 - December 2030)
- **Last Update**: March 14, 2026

---

**Target**: 400M KRW by December 2030  
**Status**: On track for success! 🚀  
**Motto**: "Discipline today, retirement tomorrow"

---

For the complete setup guide, refer to the comprehensive documentation provided during project setup.

Good luck with your retirement planning! 💰
