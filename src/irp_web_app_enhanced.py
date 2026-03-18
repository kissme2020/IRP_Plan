"""
ENHANCED IRP Retirement Tracker - Web App with Market Analysis & Recommendations
Complete Streamlit application with:
- Market trend monitoring (S&P 500, NASDAQ, AI sector)
- Automatic rebalancing alerts
- AI-powered recommendations
- Risk assessment
- Portfolio optimization suggestions

Run with: streamlit run irp_web_app_enhanced.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime, timedelta, date
import numpy as np
import requests
from functools import lru_cache
from utils import (
    krw_to_shares, generate_portfolio_snapshot, parse_ai_review_md,
    get_settlement_date, next_kr_business_day, KR_TZ,
    generate_persona_export, parse_persona_review_md,
    detect_review_format, persona_review_to_standard, normalize_asset_name,
    is_claude_cli_available, run_claude_cli, save_review_md,
    should_auto_snapshot, create_portfolio_snapshot,
)
from market_data import fetch_market_data, get_usd_krw, MARKET_INDICES

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & SETUP
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="IRP Tracker Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Your IRP parameters
IRP_CONFIG = {
    'initial_balance': 175_700_000,
    'target_goal': 400_000_000,
    'minimum_floor': 300_000_000,
    'target_cagr': 0.102,
    'start_date': datetime(2026, 3, 10),
    'retirement_date': datetime(2030, 12, 31),
    'base_monthly': 600_000,
    'expected_annual_bonus': 15_000_000,
    'rsu_value_usd': 30_458,
    'rsu_kwr_per_usd': 1_250,
    'rsu_after_tax_pct': 0.70,
}

# Target allocation (Option B - Moderate) — DEFAULT values
# At runtime, use get_allocation_target() which checks irp_tracker_data.json first
ALLOCATION_TARGET_DEFAULT = {
    'AI Core Power': 0.28,
    'AI Tech TOP10': 0.14,
    'Dividend Stocks': 0.10,
    'Consumer Staples': 0.08,
    'Treasury Bonds': 0.11,
    'Gold': 0.07,
    'Japan TOPIX': 0.02,
    'Cash': 0.28,
}
ALLOCATION_TARGET = ALLOCATION_TARGET_DEFAULT.copy()

# ETF Ticker Configuration (loaded from JSON file)
def load_etf_config():
    """Load ETF configuration from JSON file with fallback"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'etf_config.json')
    
    # Default fallback configuration
    default_config = {
        'AI Core Power': {'code': '457930', 'name': 'KODEX AI Core Power', 'name_kr': 'KODEX 미국AI전력핵심인프라', 'type': 'Equity', 'description': 'S&P 500 AI-focused companies'},
        'AI Tech TOP10': {'code': '483280', 'name': 'KODEX AI Tech TOP10 Target Covered Call', 'name_kr': 'KODEX 미국AI테크TOP10타겟커버드콜', 'type': 'Equity', 'description': 'Top 10 US tech AI companies with covered call'},
        'Dividend Stocks': {'code': '489250', 'name': 'KODEX US Dividend (Dow Jones)', 'name_kr': 'KODEX 미국배당다우존스', 'type': 'Equity', 'description': 'US dividend aristocrats'},
        'Consumer Staples': {'code': '453630', 'name': 'KODEX S&P 500 Consumer Staples', 'name_kr': 'KODEX 미국S&P500필수소비재', 'type': 'Equity', 'description': 'Defensive US consumer stocks'},
        'Treasury Bonds': {'code': '484790', 'name': 'KODEX US 30Y Treasury Active (H)', 'name_kr': 'KODEX 미국30년국채액티브(H)', 'type': 'Bond', 'description': 'Long-term US Treasury bonds, monthly dividend, hedged'},
        'Gold': {'code': '411060', 'name': 'ACE KRX Gold Spot', 'name_kr': 'ACE KRX금현물', 'type': 'Commodity', 'description': 'Gold commodity ETF'},
        'Japan TOPIX': {'code': '101280', 'name': 'KODEX Japan TOPIX100', 'name_kr': 'KODEX 일본TOPIX100', 'type': 'Equity', 'description': 'Top 100 Japanese companies'},
        'Cash': {'code': None, 'name': 'Cash', 'name_kr': '현금', 'type': 'Cash', 'description': 'Cash holdings'},
    }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.warning(f"⚠️ Could not load etf_config.json, using default configuration")
        return default_config

ETF_CONFIG = load_etf_config()

# ═══════════════════════════════════════════════════════════════════════════════
# KOREAN ETF PRICE FETCHING (using pykrx)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_etf_prices():
    """Fetch current prices for all ETFs from KRX using pykrx"""
    prices = {}
    errors = []
    
    try:
        from pykrx import stock
        from datetime import datetime, timedelta
        
        # Get today's date (or last trading day)
        today = datetime.now()
        date_str = today.strftime("%Y%m%d")
        
        # Try up to 5 days back to find a trading day
        for days_back in range(5):
            check_date = (today - timedelta(days=days_back)).strftime("%Y%m%d")
            
            for asset_name, config in ETF_CONFIG.items():
                if config['code'] is None:  # Skip Cash
                    continue
                    
                if asset_name in prices:  # Already fetched
                    continue
                
                try:
                    # Get closing price
                    df = stock.get_market_ohlcv(check_date, check_date, config['code'])
                    if not df.empty:
                        close_price = int(df.iloc[-1]['종가'])
                        prices[asset_name] = {
                            'price': close_price,
                            'date': check_date,
                            'status': 'success'
                        }
                except Exception as e:
                    errors.append(f"{asset_name}: {str(e)}")
            
            # Break if we got most prices
            if len(prices) >= len([c for c in ETF_CONFIG.values() if c['code']]) - 1:
                break
        
        # Set Cash price to 1 (1 KRW = 1 KRW)
        prices['Cash'] = {'price': 1, 'date': date_str, 'status': 'success'}
        
    except ImportError:
        # pykrx not installed, use fallback prices
        return get_fallback_prices()
    except Exception as e:
        errors.append(f"General error: {str(e)}")
        return get_fallback_prices()
    
    # Fill in any missing with fallback
    for asset_name in ETF_CONFIG:
        if asset_name not in prices:
            fallback = get_fallback_prices()
            prices[asset_name] = fallback.get(asset_name, {'price': 10000, 'date': '', 'status': 'fallback'})
    
    return prices

def get_fallback_prices():
    """Fallback prices if API fails (approximate values)"""
    return {
        'AI Core Power': {'price': 15000, 'date': '', 'status': 'fallback'},
        'AI Tech TOP10': {'price': 12000, 'date': '', 'status': 'fallback'},
        'Dividend Stocks': {'price': 11000, 'date': '', 'status': 'fallback'},
        'Consumer Staples': {'price': 10500, 'date': '', 'status': 'fallback'},
        'Treasury Bonds': {'price': 9500, 'date': '', 'status': 'fallback'},
        'Gold': {'price': 14000, 'date': '', 'status': 'fallback'},
        'Japan TOPIX': {'price': 16000, 'date': '', 'status': 'fallback'},
        'Cash': {'price': 1, 'date': '', 'status': 'success'},
    }

def calculate_holdings_value(shares, prices):
    """Calculate total holdings value from shares and prices"""
    total_value = 0
    holdings_detail = {}
    
    for asset_name, num_shares in shares.items():
        if asset_name in prices:
            price = prices[asset_name]['price']
            value = num_shares * price
            holdings_detail[asset_name] = {
                'shares': num_shares,
                'price': price,
                'value': value
            }
            total_value += value
    
    return total_value, holdings_detail

# ═══════════════════════════════════════════════════════════════════════════════
# MARKET DATA FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_market_data():
    """Fetch market data via hybrid approach (real API + cache + fallback).
    Delegates to market_data.fetch_market_data() which uses yfinance with
    Streamlit caching (10 min TTL) and mock fallback if API fails.
    """
    return fetch_market_data()

def get_market_trend_analysis(market_data):
    """Analyze market trends and provide assessment"""
    
    data = market_data['data']
    
    analysis = {
        'trend': 'NEUTRAL',
        'volatility': 'MODERATE',
        'sentiment': 'MIXED',
        'ai_sector': 'STRONG',
        'tech_sector': 'STRONG',
        'bond_outlook': 'FAVORABLE',
        'equity_outlook': 'POSITIVE',
        'confidence': 'MEDIUM',
    }
    
    # Analyze equity trends (US + Korea indices)
    equity_names = ['S&P 500', 'NASDAQ', 'Dow Jones', 'KOSPI', 'KOSDAQ']
    equity_changes = [data[n]['change_pct'] for n in equity_names if n in data]
    avg_change = np.mean(equity_changes) if equity_changes else 0
    
    if avg_change > 2:
        analysis['trend'] = 'BULLISH'
        analysis['sentiment'] = 'POSITIVE'
    elif avg_change < -2:
        analysis['trend'] = 'BEARISH'
        analysis['sentiment'] = 'NEGATIVE'
    else:
        analysis['trend'] = 'NEUTRAL'
        analysis['sentiment'] = 'MIXED'
    
    # Volatility from VIX
    vix = data.get('VIX', {}).get('price', 18)
    if vix > 30:
        analysis['volatility'] = 'HIGH'
    elif vix > 20:
        analysis['volatility'] = 'ELEVATED'
    else:
        analysis['volatility'] = 'LOW'
    
    # Tech sector analysis (NASDAQ as proxy)
    nasdaq_change = data.get('NASDAQ', {}).get('change_pct', 0)
    if nasdaq_change > 2:
        analysis['tech_sector'] = 'VERY STRONG'
        analysis['ai_sector'] = 'VERY STRONG'
        analysis['confidence'] = 'HIGH'
    elif nasdaq_change > 0:
        analysis['tech_sector'] = 'STRONG'
        analysis['ai_sector'] = 'STRONG'
    elif nasdaq_change < -2:
        analysis['tech_sector'] = 'WEAK'
        analysis['ai_sector'] = 'WEAK'
    else:
        analysis['tech_sector'] = 'MODERATE'
        analysis['ai_sector'] = 'MODERATE'
    
    # Bond outlook from US 10Y Yield
    yield_10y = data.get('US 10Y Yield', {}).get('price', 4.0)
    if yield_10y > 5.0:
        analysis['bond_outlook'] = 'UNFAVORABLE'
    elif yield_10y > 4.5:
        analysis['bond_outlook'] = 'CAUTIOUS'
    else:
        analysis['bond_outlook'] = 'FAVORABLE'
    
    return analysis

def get_rebalancing_recommendations(data, current_allocation):
    """Generate rebalancing recommendations"""
    
    recommendations = []
    
    # Check each position
    for asset, target_pct in ALLOCATION_TARGET.items():
        current_pct = current_allocation.get(asset, 0) / 100
        drift = abs(current_pct - target_pct)
        
        if drift > 0.05:  # More than 5% off target
            if current_pct > target_pct:
                recommendations.append({
                    'action': 'TRIM',
                    'asset': asset,
                    'current': current_pct * 100,
                    'target': target_pct * 100,
                    'drift': drift * 100,
                    'reason': f'Overweight by {drift*100:.1f}%',
                    'priority': 'HIGH' if drift > 0.10 else 'MEDIUM'
                })
            else:
                recommendations.append({
                    'action': 'ADD',
                    'asset': asset,
                    'current': current_pct * 100,
                    'target': target_pct * 100,
                    'drift': drift * 100,
                    'reason': f'Underweight by {drift*100:.1f}%',
                    'priority': 'HIGH' if drift > 0.10 else 'MEDIUM'
                })
    
    # Sort by priority and drift
    recommendations.sort(key=lambda x: (-len(x['priority']), -x['drift']))
    
    return recommendations

def get_ai_recommendations(data, progress, market_analysis):
    """Generate AI-powered recommendations based on market conditions"""
    
    recommendations = []
    current_balance = progress['current']
    
    # 1. Market sentiment recommendations
    if market_analysis['trend'] == 'BULLISH':
        if market_analysis['ai_sector'] == 'VERY STRONG':
            recommendations.append({
                'category': 'GROWTH',
                'recommendation': 'AI/Tech sector showing exceptional strength',
                'action': 'Maintain current 42% growth equity allocation',
                'confidence': 'HIGH',
                'timeframe': 'SHORT-TERM',
                'impact': 'POSITIVE'
            })
        
        if market_analysis['tech_sector'] == 'VERY STRONG':
            recommendations.append({
                'category': 'MARKET',
                'recommendation': 'Tech sector momentum is strong',
                'action': 'Consider slightly increasing allocation to KODEX AI Core Power',
                'confidence': 'HIGH',
                'timeframe': 'SHORT-TERM',
                'impact': 'POSITIVE'
            })
    
    elif market_analysis['trend'] == 'BEARISH':
        recommendations.append({
            'category': 'RISK',
            'recommendation': 'Market showing weakness - defensive positioning advised',
            'action': 'Increase allocation to Treasury Bonds from 11% to 15%',
            'confidence': 'HIGH',
            'timeframe': 'SHORT-TERM',
            'impact': 'PROTECTIVE'
        })
        
        recommendations.append({
            'category': 'STRATEGY',
            'recommendation': 'Market downturn presents buying opportunity',
            'action': 'Continue monthly deposits - dollar-cost averaging into dip',
            'confidence': 'HIGH',
            'timeframe': 'MEDIUM-TERM',
            'impact': 'POSITIVE'
        })
    
    # 2. Progress-based recommendations
    progress_pct = (current_balance / IRP_CONFIG['target_goal']) * 100
    
    if progress_pct >= 100:
        recommendations.append({
            'category': 'ACHIEVEMENT',
            'recommendation': '✓ GOAL ACHIEVED!',
            'action': 'Shift to 40% bonds, 20% dividend stocks (reduce risk)',
            'confidence': 'HIGH',
            'timeframe': 'IMMEDIATE',
            'impact': 'PROTECTIVE'
        })
    elif progress_pct >= 80:
        recommendations.append({
            'category': 'MOMENTUM',
            'recommendation': 'Approaching goal - begin de-risking gradually',
            'action': 'Shift 5-10% from growth to bonds over next 2 quarters',
            'confidence': 'HIGH',
            'timeframe': 'MEDIUM-TERM',
            'impact': 'PROTECTIVE'
        })
    elif progress_pct < 40:
        recommendations.append({
            'category': 'ACCELERATION',
            'recommendation': 'Behind schedule - maintain aggressive growth',
            'action': 'Keep 45% growth equities, increase monthly contributions if possible',
            'confidence': 'HIGH',
            'timeframe': 'LONG-TERM',
            'impact': 'GROWTH'
        })
    
    # 3. Timeline recommendations
    years_remaining, _, _ = calculate_time_remaining()
    
    if years_remaining < 2:
        recommendations.append({
            'category': 'TIMELINE',
            'recommendation': 'Less than 2 years to retirement - critical de-risking phase',
            'action': 'Shift to: 25% growth, 30% dividend, 30% bonds, 15% cash',
            'confidence': 'CRITICAL',
            'timeframe': 'IMMEDIATE',
            'impact': 'PROTECTIVE'
        })
    elif years_remaining < 3:
        recommendations.append({
            'category': 'TIMELINE',
            'recommendation': '2-3 years remaining - transition to balanced approach',
            'action': 'Begin gradual shift toward defensive allocation',
            'confidence': 'HIGH',
            'timeframe': 'ONGOING',
            'impact': 'BALANCED'
        })
    
    # 4. Allocation drift recommendations
    if progress.get('allocation_drift', []):
        for drift in progress['allocation_drift']:
            if drift['magnitude'] > 0.10:
                recommendations.append({
                    'category': 'REBALANCE',
                    'recommendation': f"{drift['asset']} is {drift['direction']} target by {drift['magnitude']*100:.1f}%",
                    'action': f"{'Trim' if drift['direction'] == 'above' else 'Add to'} {drift['asset']}",
                    'confidence': 'MEDIUM',
                    'timeframe': 'NEXT QUARTER',
                    'impact': 'BALANCED'
                })
    
    # 5. RSU recommendations
    recommendations.append({
        'category': 'RSU',
        'recommendation': '$30,458 RSU vesting over 4 years',
        'action': 'SELL RSU immediately upon vesting - deploy into diversified portfolio',
        'confidence': 'HIGH',
        'timeframe': '2027-2030',
        'impact': 'BOOST'
    })
    
    return recommendations

# ═══════════════════════════════════════════════════════════════════════════════
# DATA MANAGEMENT (Same as before)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_data_file():
    """Get or create data file"""
    from pathlib import Path
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "irp_tracker_data.json")

def load_data():
    """Load data from JSON file"""
    data_file = get_data_file()
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            data = json.load(f)
            # Ensure holdings structure exists (for backward compatibility)
            if 'holdings' not in data:
                data['holdings'] = get_default_holdings()
            if 'holdings_values' not in data:
                data['holdings_values'] = get_default_holdings_values()
            if 'holdings_updated' not in data:
                data['holdings_updated'] = None
            if 'rebalance_history' not in data:
                data['rebalance_history'] = []
            # New fields for transaction tracking and rebalancing settings
            if 'transactions' not in data:
                data['transactions'] = []
            if 'rebalancing_settings' not in data:
                data['rebalancing_settings'] = {
                    'frequency_days': 90,
                    'last_rebalance_date': None,
                    'alert_threshold_pct': 5.0
                }
            if 'portfolio_snapshots' not in data:
                data['portfolio_snapshots'] = []
            return data
    else:
        return {
            'created_date': datetime.now().isoformat(),
            'initial_balance': IRP_CONFIG['initial_balance'],
            'monthly_entries': [],
            'rsu_vesting': [],
            'rebalancing_history': [],
            'holdings': get_default_holdings(),
            'holdings_values': get_default_holdings_values(),
            'holdings_updated': None,
            'rebalance_history': [],
            'transactions': [],
            'rebalancing_settings': {
                'frequency_days': 90,
                'last_rebalance_date': None,
                'alert_threshold_pct': 5.0
            },
            'portfolio_snapshots': [],
        }

def get_default_holdings():
    """Get default holdings in SHARES (not values) based on initial balance and target allocation"""
    initial = IRP_CONFIG['initial_balance']
    
    # Estimated prices for initial calculation (will be updated with real prices)
    estimated_prices = {
        'AI Core Power': 15000,
        'AI Tech TOP10': 12000,
        'Dividend Stocks': 11000,
        'Consumer Staples': 10500,
        'Treasury Bonds': 9500,
        'Gold': 14000,
        'Japan TOPIX': 16000,
        'Cash': 1,  # Cash is 1:1
    }
    
    holdings = {}
    for asset, target_pct in ALLOCATION_TARGET.items():
        target_value = initial * target_pct
        est_price = estimated_prices.get(asset, 10000)
        # Calculate number of shares (round to nearest 10 for convenience)
        shares = int(target_value / est_price / 10) * 10
        holdings[asset] = shares
    
    return holdings

def get_default_holdings_values():
    """Get default holdings as VALUES (for backward compatibility)"""
    initial = IRP_CONFIG['initial_balance']
    return {
        'AI Core Power': int(initial * 0.28),
        'AI Tech TOP10': int(initial * 0.14),
        'Dividend Stocks': int(initial * 0.10),
        'Consumer Staples': int(initial * 0.08),
        'Treasury Bonds': int(initial * 0.11),
        'Gold': int(initial * 0.07),
        'Japan TOPIX': int(initial * 0.02),
        'Cash': int(initial * 0.20),  # Start with some cash buffer
    }

def save_holdings(holdings):
    """Save updated holdings (shares mode - calculated values)"""
    data = load_data()
    data['holdings'] = holdings
    data['holdings_updated'] = datetime.now().isoformat()
    save_data(data)
    return True

def save_holdings_values(holdings_values):
    """Save updated holdings values (values mode - direct KRW entry)"""
    data = load_data()
    data['holdings_values'] = holdings_values
    data['holdings_updated'] = datetime.now().isoformat()
    save_data(data)
    return True

def record_rebalance(trades_executed, notes=""):
    """Record a rebalancing action"""
    data = load_data()
    rebalance_record = {
        'date': datetime.now().isoformat(),
        'trades': trades_executed,
        'notes': notes,
        'portfolio_value_before': sum(data['holdings'].values()),
    }
    data['rebalance_history'].append(rebalance_record)
    save_data(data)
    return True

def get_holdings():
    """Get current holdings"""
    data = load_data()
    return data.get('holdings', get_default_holdings())

def save_data(data):
    """Save data to JSON file"""
    data_file = get_data_file()
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_allocation_target():
    """Load allocation target from data file, falling back to defaults."""
    global ALLOCATION_TARGET
    data = load_data()
    custom = data.get('allocation_target')
    if custom and isinstance(custom, dict):
        ALLOCATION_TARGET.update({k: v for k, v in custom.items() if k in ALLOCATION_TARGET})
    return ALLOCATION_TARGET


def save_allocation_target(new_target: dict, source: str = "manual", notes: str = ""):
    """Save new allocation target and record it in history."""
    global ALLOCATION_TARGET
    data = load_data()

    # Record history
    if 'allocation_history' not in data:
        data['allocation_history'] = []
    data['allocation_history'].append({
        'date': datetime.now().isoformat(),
        'source': source,
        'previous': dict(ALLOCATION_TARGET),
        'new': new_target,
        'notes': notes,
    })

    data['allocation_target'] = new_target
    save_data(data)
    ALLOCATION_TARGET.update(new_target)


def save_ai_review(review_data: dict, filename: str):
    """Save an AI review record in the data file."""
    data = load_data()
    if 'ai_reviews' not in data:
        data['ai_reviews'] = []
    record = {
        'date': datetime.now().isoformat(),
        'filename': filename,
        'allocation': review_data.get('allocation', {}),
        'cagr': review_data.get('cagr', {}),
        'recommendations': review_data.get('recommendations', []),
        'market_outlook': review_data.get('market_outlook', ''),
    }
    # Save persona discussions if present
    if review_data.get('persona_discussions'):
        record['persona_discussions'] = review_data['persona_discussions']
    data['ai_reviews'].append(record)
    save_data(data)


def get_latest_ai_review() -> dict | None:
    """Return the most recent AI review record, or None."""
    data = load_data()
    reviews = data.get('ai_reviews', [])
    return reviews[-1] if reviews else None


# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO SNAPSHOTS
# ═══════════════════════════════════════════════════════════════════════════════

def save_portfolio_snapshot(snapshot: dict):
    """Append a portfolio snapshot to the data file."""
    data = load_data()
    if 'portfolio_snapshots' not in data:
        data['portfolio_snapshots'] = []
    data['portfolio_snapshots'].append(snapshot)
    save_data(data)


def get_portfolio_snapshots() -> list[dict]:
    """Return all portfolio snapshots."""
    data = load_data()
    return data.get('portfolio_snapshots', [])


def check_and_run_auto_snapshot():
    """Check if an automatic mid-month snapshot should be taken, and take it."""
    data = load_data()
    snapshots = data.get('portfolio_snapshots', [])

    if not should_auto_snapshot(snapshots):
        return

    # Fetch current shares and prices
    shares = data.get('shares', get_default_holdings())
    prices = fetch_etf_prices()
    targets = dict(ALLOCATION_TARGET)

    snapshot = create_portfolio_snapshot(shares, prices, targets, trigger="auto")
    save_portfolio_snapshot(snapshot)
    st.toast("📸 Monthly portfolio snapshot saved automatically.", icon="✅")


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSACTION TRACKING (Purchase History)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_transaction_id():
    """Generate unique transaction ID"""
    import uuid
    return str(uuid.uuid4())[:8]

def generate_batch_id(prefix: str = "RB") -> str:
    """Generate batch ID in format RB-YYYYMMDD-SEQ."""
    data = load_data()
    today_str = datetime.now().strftime("%Y%m%d")
    existing = {t.get('batch_id', '') for t in data.get('transactions', [])}
    seq = 1
    while f"{prefix}-{today_str}-{seq:03d}" in existing:
        seq += 1
    return f"{prefix}-{today_str}-{seq:03d}"

def add_transaction(asset, trans_type, date_str, shares, price_per_share, notes="",
                    batch_id=None, status="completed"):
    """Add a transaction (buy, sell, contribution, or dividend)"""
    data = load_data()
    
    if 'transactions' not in data:
        data['transactions'] = []
    
    transaction = {
        'id': generate_transaction_id(),
        'asset': asset,
        'type': trans_type,  # 'buy', 'sell', 'contribution', 'dividend'
        'date': date_str,
        'shares': shares,
        'price_per_share': price_per_share,
        'total_cost': shares * price_per_share,
        'notes': notes,
        'batch_id': batch_id,
        'status': status,  # 'pending' or 'completed'
        'created_at': datetime.now().isoformat()
    }
    
    data['transactions'].append(transaction)
    save_data(data)
    return transaction

def delete_transaction(transaction_id):
    """Delete a transaction by ID"""
    data = load_data()
    if 'transactions' in data:
        data['transactions'] = [t for t in data['transactions'] if t['id'] != transaction_id]
        save_data(data)
        return True
    return False

def update_transaction(transaction_id: str, updates: dict) -> bool:
    """Update fields of an existing transaction by ID."""
    data = load_data()
    for t in data.get('transactions', []):
        if t['id'] == transaction_id:
            t.update(updates)
            if 'price_per_share' in updates or 'shares' in updates:
                t['total_cost'] = t['shares'] * t['price_per_share']
            save_data(data)
            return True
    return False

def get_pending_transactions(batch_id: str = None) -> list:
    """Get all pending transactions, optionally filtered by batch_id."""
    data = load_data()
    pending = [t for t in data.get('transactions', [])
               if t.get('status') == 'pending']
    if batch_id:
        pending = [t for t in pending if t.get('batch_id') == batch_id]
    return pending

def confirm_batch_transactions(batch_id: str, price_map: dict) -> int:
    """Confirm all pending transactions in a batch with actual prices.

    price_map: {transaction_id: {'price_per_share': float, 'shares': int (optional)}}
    Returns count of updated transactions.
    """
    data = load_data()
    count = 0
    for t in data.get('transactions', []):
        if t.get('batch_id') == batch_id and t.get('status') == 'pending':
            if t['id'] in price_map:
                info = price_map[t['id']]
                t['price_per_share'] = info['price_per_share']
                if 'shares' in info:
                    t['shares'] = info['shares']
                t['total_cost'] = t['shares'] * t['price_per_share']
                t['status'] = 'completed'
                t['confirmed_at'] = datetime.now().isoformat()
                count += 1
    save_data(data)
    return count

def get_transactions(asset=None):
    """Get all transactions, optionally filtered by asset"""
    data = load_data()
    transactions = data.get('transactions', [])
    
    if asset:
        transactions = [t for t in transactions if t['asset'] == asset]
    
    # Sort by date
    transactions.sort(key=lambda x: x['date'], reverse=True)
    return transactions

def calculate_cost_basis(asset):
    """Calculate average cost basis for an asset using FIFO method"""
    transactions = get_transactions(asset)
    
    total_shares = 0
    total_cost = 0
    
    for trans in transactions:
        if trans.get('status') == 'pending':
            continue
        if trans['type'] == 'buy':
            total_shares += trans['shares']
            total_cost += trans['total_cost']
        elif trans['type'] == 'sell':
            if total_shares > 0:
                # FIFO: reduce cost proportionally
                avg_cost = total_cost / total_shares if total_shares > 0 else 0
                total_shares -= trans['shares']
                total_cost -= trans['shares'] * avg_cost
    
    avg_cost_basis = total_cost / total_shares if total_shares > 0 else 0
    
    return {
        'total_shares': max(0, total_shares),
        'total_cost': max(0, total_cost),
        'avg_cost_basis': avg_cost_basis
    }

def calculate_gains_losses(current_prices):
    """Calculate unrealized gains/losses for all assets"""
    data = load_data()
    shares = data.get('shares', {})
    
    gains_losses = {}
    total_gain = 0
    total_cost = 0
    
    for asset in ALLOCATION_TARGET.keys():
        if asset == 'Cash':
            continue
            
        cost_info = calculate_cost_basis(asset)
        current_shares = shares.get(asset, 0)
        current_price = current_prices.get(asset, 0)
        
        current_value = current_shares * current_price
        
        # Use shares from transactions if available, otherwise from current holdings
        if cost_info['total_shares'] > 0:
            cost_basis = cost_info['total_cost']
            avg_cost = cost_info['avg_cost_basis']
        else:
            # No transactions recorded, assume current value is cost
            cost_basis = current_value
            avg_cost = current_price
        
        unrealized_gain = current_value - cost_basis
        gain_pct = (unrealized_gain / cost_basis * 100) if cost_basis > 0 else 0
        
        gains_losses[asset] = {
            'shares': current_shares,
            'avg_cost_basis': avg_cost,
            'total_cost': cost_basis,
            'current_price': current_price,
            'current_value': current_value,
            'unrealized_gain': unrealized_gain,
            'gain_pct': gain_pct
        }
        
        total_gain += unrealized_gain
        total_cost += cost_basis
    
    total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0
    
    return gains_losses, total_gain, total_gain_pct

# ═══════════════════════════════════════════════════════════════════════════════
# TIME-BASED REBALANCING ALERTS
# ═══════════════════════════════════════════════════════════════════════════════

def get_rebalancing_settings():
    """Get rebalancing settings"""
    data = load_data()
    settings = data.get('rebalancing_settings', {
        'frequency_days': 90,
        'last_rebalance_date': None,
        'alert_threshold_pct': 5.0  # Alert if allocation drifts more than 5%
    })
    return settings

def save_rebalancing_settings(settings):
    """Save rebalancing settings"""
    data = load_data()
    data['rebalancing_settings'] = settings
    save_data(data)

def check_time_based_rebalancing():
    """Check if it's time to rebalance based on schedule"""
    settings = get_rebalancing_settings()
    
    last_rebalance = settings.get('last_rebalance_date')
    frequency_days = settings.get('frequency_days', 90)
    
    if not last_rebalance:
        return {
            'should_rebalance': True,
            'days_since_last': None,
            'days_until_next': 0,
            'message': '⚠️ No rebalancing recorded. Consider setting your initial rebalance date.'
        }
    
    try:
        last_date = datetime.fromisoformat(last_rebalance)
        days_since = (datetime.now() - last_date).days
        days_until_next = max(0, frequency_days - days_since)
        
        should_rebalance = days_since >= frequency_days
        
        if should_rebalance:
            message = f"🚨 REBALANCING DUE! Last rebalanced {days_since} days ago (target: every {frequency_days} days)"
        elif days_until_next <= 7:
            message = f"⏰ Rebalancing due in {days_until_next} days"
        else:
            message = f"✅ Next rebalancing in {days_until_next} days"
        
        return {
            'should_rebalance': should_rebalance,
            'days_since_last': days_since,
            'days_until_next': days_until_next,
            'message': message
        }
    except:
        return {
            'should_rebalance': True,
            'days_since_last': None,
            'days_until_next': 0,
            'message': '⚠️ Could not parse last rebalance date.'
        }

def record_rebalance_date():
    """Record today as the last rebalance date"""
    settings = get_rebalancing_settings()
    settings['last_rebalance_date'] = datetime.now().isoformat()
    save_rebalancing_settings(settings)

# ═══════════════════════════════════════════════════════════════════════════════
# CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_total_deposits(data):
    """Calculate total deposits"""
    monthly_total = sum(e['total_deposit'] for e in data['monthly_entries'])
    # RSU: calculate net KRW from share-based data
    rsu_settings = data.get('rsu_settings', {})
    exchange_rate = rsu_settings.get('exchange_rate', IRP_CONFIG['rsu_kwr_per_usd'])
    tax_rate_saved = rsu_settings.get('tax_rate_pct', None)
    if tax_rate_saved is not None:
        after_tax_pct = (100 - tax_rate_saved) / 100
    else:
        after_tax_pct = IRP_CONFIG['rsu_after_tax_pct']

    rsu_total = 0
    for e in data.get('rsu_vesting', []):
        if 'net_kwr' in e:
            rsu_total += e['net_kwr']
        else:
            shares = e.get('shares', 0)
            price = e.get('vest_price_usd', None) if e.get('vested') else None
            if price is None:
                price = e.get('grant_price_usd', 0)
            rsu_total += shares * price * exchange_rate * after_tax_pct
    return monthly_total, rsu_total, monthly_total + rsu_total

def calculate_current_balance(data):
    """Calculate current portfolio balance"""
    balance = IRP_CONFIG['initial_balance']
    monthly, rsu, total = calculate_total_deposits(data)
    balance += total
    return balance

def calculate_progress(data):
    """Calculate progress metrics"""
    current = calculate_current_balance(data)
    progress_goal = (current / IRP_CONFIG['target_goal']) * 100
    progress_floor = (current / IRP_CONFIG['minimum_floor']) * 100
    
    return {
        'current': current,
        'target_goal': IRP_CONFIG['target_goal'],
        'floor': IRP_CONFIG['minimum_floor'],
        'progress_goal': progress_goal,
        'progress_floor': progress_floor,
        'remaining_to_goal': max(0, IRP_CONFIG['target_goal'] - current),
    }

def calculate_time_remaining():
    """Calculate time until retirement"""
    today = datetime.now()
    days = (IRP_CONFIG['retirement_date'] - today).days
    years = days / 365.25
    months = (days % 365) / 30.44
    return years, months, days

def project_balance_to_retirement(current_balance):
    """Project balance with compound growth"""
    years_remaining, _, _ = calculate_time_remaining()
    target_cagr = IRP_CONFIG['target_cagr']
    
    projected = current_balance * ((1 + target_cagr) ** years_remaining)
    return projected

def get_success_probability(current_balance):
    """Determine success probability based on current balance"""
    if current_balance >= IRP_CONFIG['target_goal']:
        return 100, "✓✓ EXCEEDED GOAL!"
    elif current_balance >= 350_000_000:
        return 88, "✓✓ VERY GOOD"
    elif current_balance >= IRP_CONFIG['minimum_floor']:
        return 95, "✓ ON TRACK"
    else:
        pct = (current_balance / IRP_CONFIG['minimum_floor']) * 100
        return pct, "⚠ MONITORING"

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: MARKET DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def page_market_dashboard():
    """Market trends and recommendations"""
    st.title("📊 Market Analysis & Recommendations")
    
    # Load market data
    market_data = get_market_data()
    market_analysis = get_market_trend_analysis(market_data)
    
    # Load IRP data
    data = load_data()
    progress = calculate_progress(data)
    
    # Load AI recommendations
    ai_recs = get_ai_recommendations(data, progress, market_analysis)
    
    # Market Overview
    st.subheader("Current Market Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Market Trend",
            market_analysis['trend'],
            market_analysis['sentiment']
        )
    
    with col2:
        st.metric(
            "AI Sector",
            market_analysis['ai_sector'],
            "High Growth" if market_analysis['ai_sector'] in ['STRONG', 'VERY STRONG'] else "Monitor"
        )
    
    with col3:
        st.metric(
            "Tech Sector",
            market_analysis['tech_sector'],
            "Positive" if market_analysis['tech_sector'] in ['STRONG', 'VERY STRONG'] else "Caution"
        )
    
    with col4:
        st.metric(
            "Bond Outlook",
            market_analysis['bond_outlook'],
            "Supportive" if market_analysis['bond_outlook'] == 'FAVORABLE' else "Monitor"
        )
    
    st.divider()
    
    # Market Indices — grouped by category
    st.subheader("Market Indices")
    
    # Data source indicator
    status = market_data.get('status', 'unknown')
    ts = market_data.get('timestamp')
    if status == 'live':
        st.caption(f"🟢 Live data via Yahoo Finance • Updated {ts.strftime('%Y-%m-%d %H:%M') if ts else 'N/A'} • Cached 10 min")
    elif status == 'offline':
        st.caption("🔴 Offline — showing fallback data. Check your internet connection.")
    
    # USD/KRW exchange rate — highlighted card
    usd_krw = market_data['data'].get('USD/KRW', {})
    if usd_krw:
        krw_col1, krw_col2, krw_col3 = st.columns([2, 1, 1])
        with krw_col1:
            st.metric(
                "💱 USD/KRW Exchange Rate",
                f"₩{usd_krw['price']:,.2f}",
                f"{usd_krw['change_pct']:+.2f}%"
            )
        with krw_col2:
            st.metric("Previous Close", f"₩{usd_krw.get('prev_close', 0):,.2f}")
        with krw_col3:
            st.metric("Change", f"₩{usd_krw.get('change_amt', 0):+,.2f}")
        st.divider()
    
    # Build table for all indices
    market_data_list = []
    for name, info in market_data['data'].items():
        price = info['price']
        # Format price based on category
        if info.get('category') == 'Currency':
            price_fmt = f"₩{price:,.2f}"
        elif info.get('category') == 'Bond':
            price_fmt = f"{price:.2f}%"
        elif info.get('category') == 'Commodities':
            price_fmt = f"${price:,.2f}"
        else:
            price_fmt = f"{price:,.2f}"
        
        change = info.get('change_pct', 0)
        source = info.get('source', '')
        source_icon = '🟢' if source == 'yahoo_finance' else '🟡' if source == 'fallback' else '🔴'
        
        market_data_list.append({
            'Category': info.get('category', ''),
            'Index': name,
            'Price': price_fmt,
            'Change %': f"{change:+.2f}%",
            'Trend': '📈' if change > 0 else '📉' if change < 0 else '➡️',
            'Source': source_icon,
        })
    
    df_markets = pd.DataFrame(market_data_list)
    st.dataframe(df_markets, width="stretch", hide_index=True)
    
    st.divider()
    
    # AI Recommendations
    st.subheader("🤖 AI-Powered Recommendations")
    
    if ai_recs:
        for idx, rec in enumerate(ai_recs, 1):
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    # Color code by impact
                    if rec['impact'] == 'POSITIVE':
                        icon = "✓"
                        color = "green"
                    elif rec['impact'] == 'PROTECTIVE':
                        icon = "🛡️"
                        color = "orange"
                    elif rec['impact'] == 'BOOST':
                        icon = "⬆️"
                        color = "blue"
                    else:
                        icon = "→"
                        color = "gray"
                    
                    st.write(f":{color}[**{icon} {rec['category']}**]")
                
                with col2:
                    st.write(f"**{rec['recommendation']}**")
                    st.write(f"*Action:* {rec['action']}")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.caption(f"Confidence: {rec['confidence']}")
                    with col_b:
                        st.caption(f"Timeframe: {rec['timeframe']}")
                    with col_c:
                        st.caption(f"Impact: {rec['impact']}")
            
            st.divider()
    else:
        st.info("No specific recommendations at this time. Keep monitoring market trends.")
    
    st.divider()
    
    # Risk Assessment
    st.subheader("Risk Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Current Risk Level")
        
        years, _, _ = calculate_time_remaining()
        
        if years < 1:
            risk_level = "LOW (Retirement in < 1 year)"
            risk_color = "green"
        elif years < 3:
            risk_level = "MEDIUM (Transition phase)"
            risk_color = "orange"
        else:
            risk_level = "HIGH (Growth phase - 3+ years)"
            risk_color = "red"
        
        st.write(f":{risk_color}[**{risk_level}**]")
        
        st.write("### Recommended Adjustments")
        
        if market_analysis['trend'] == 'BEARISH':
            st.write("⚠️ **Market correction detected**")
            st.write("- Consider increasing bonds to 15%")
            st.write("- Continue monthly deposits (dollar-cost average)")
            st.write("- Do NOT panic-sell")
        
        elif market_analysis['trend'] == 'BULLISH':
            st.write("✓ **Strong market conditions**")
            st.write("- Maintain current allocation")
            st.write("- Lock in gains via rebalancing")
            st.write("- Monitor for overweighting in winners")
    
    with col2:
        st.write("### Market Volatility")
        
        volatility_data = [
            {'Period': 'Last Week', 'Volatility': 'Medium', 'Change': '2-4%'},
            {'Period': 'Last Month', 'Volatility': 'Medium-High', 'Change': '5-8%'},
            {'Period': 'Last Quarter', 'Volatility': 'High', 'Change': '8-15%'},
        ]
        
        df_vol = pd.DataFrame(volatility_data)
        st.dataframe(df_vol, width="stretch", hide_index=True)
        
        st.write("### Recommended Action")
        
        if market_analysis['confidence'] == 'HIGH':
            st.write("✓ **Strong Conviction**")
            st.write("Follow recommendations with confidence")
        else:
            st.write("⚠️ **Mixed Signals**")
            st.write("Monitor before making large changes")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: REBALANCING ALERTS (New)
# ═══════════════════════════════════════════════════════════════════════════════

def page_rebalancing_alerts():
    """Rebalancing alerts and recommendations"""
    st.title("⚠️ Rebalancing Alerts & Recommendations")
    
    data = load_data()
    progress = calculate_progress(data)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 0: UPDATE YOUR HOLDINGS
    # ═══════════════════════════════════════════════════════════════════════════
    st.header("✏️ Section 0: Update Your Holdings")
    
    holdings_updated = data.get('holdings_updated')
    if holdings_updated:
        st.info(f"📅 Last updated: {holdings_updated[:10]}")
    else:
        st.warning("⚠️ Holdings have never been updated. Using default values.")
    
    st.caption("**ETFs**: Enter number of shares → Value calculated from live prices | **Cash**: Enter KRW amount directly")
    
    # Get current shares data
    shares = data.get('shares', get_default_holdings())
    
    with st.expander("📝 Click to Update Your Holdings", expanded=False):
        st.write("Enter your current holdings:")
        
        updated_shares = {}
        cols = st.columns(2)
        
        for idx, asset in enumerate(ALLOCATION_TARGET.keys()):
            current_shares = shares.get(asset, 0)
            etf_info = ETF_CONFIG.get(asset, {})
            code = etf_info.get('code', 'N/A')
            name_kr = etf_info.get('name_kr', '')
            
            with cols[idx % 2]:
                if asset == 'Cash':
                    updated_shares[asset] = st.number_input(
                        f"💵 {asset} ({name_kr})",
                        value=current_shares,
                        step=100_000,
                        min_value=0,
                        key=f"shares_{asset}",
                        help="Enter your cash balance in KRW"
                    )
                else:
                    updated_shares[asset] = st.number_input(
                        f"📊 {asset} ({name_kr})",
                        value=current_shares,
                        step=1,
                        min_value=0,
                        key=f"shares_{asset}",
                        help=f"[{code}] {etf_info.get('name', '')} - Enter number of shares"
                    )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Holdings", width="stretch", type="primary"):
                data['shares'] = updated_shares
                data['holdings_updated'] = datetime.now().isoformat()
                save_data(data)
                st.cache_data.clear()  # Clear price cache to refetch
                st.success("✅ Holdings saved successfully!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh Prices", width="stretch"):
                st.cache_data.clear()
                st.rerun()
    
    # Fetch current prices from API
    st.subheader("📡 Live Price Data & Portfolio Value")
    
    with st.spinner("Fetching prices from KRX..."):
        prices = fetch_etf_prices()
    
    # Display price status
    price_status_data = []
    for asset, config in ETF_CONFIG.items():
        if config['code']:
            price_info = prices.get(asset, {})
            name_kr = config.get('name_kr', '')
            price_status_data.append({
                'Asset': f"{asset} ({name_kr})",
                'Code': config['code'],
                'Price (KRW)': f"{price_info.get('price', 0):,}",
                'Date': price_info.get('date', 'N/A'),
                'Status': '✅' if price_info.get('status') == 'success' else '⚠️ Fallback'
            })
    
    df_prices = pd.DataFrame(price_status_data)
    st.dataframe(df_prices, width="stretch", hide_index=True)
    
    # Calculate holdings values from shares * prices
    holdings = {}
    holdings_detail = {}
    for asset in ALLOCATION_TARGET.keys():
        num_shares = shares.get(asset, 0)
        price = prices.get(asset, {}).get('price', 0)
        
        if asset == 'Cash':
            value = num_shares  # Cash is already in KRW
        else:
            value = num_shares * price
        
        holdings[asset] = value
        holdings_detail[asset] = {
            'shares': num_shares,
            'price': price,
            'value': value
        }
    
    portfolio_value = sum(holdings.values())
    
    # Show calculated portfolio summary
    st.subheader("💰 Calculated Portfolio Value")
    summary_data = []
    for asset, detail in holdings_detail.items():
        etf_info = ETF_CONFIG.get(asset, {})
        name_kr = etf_info.get('name_kr', '')
        if asset == 'Cash':
            summary_data.append({
                'Asset': f"💵 {asset} ({name_kr})",
                'Shares/Amount': f"₩{detail['shares']:,}",
                'Price': '-',
                'Value (KRW)': f"₩{detail['value']:,.0f}"
            })
        else:
            summary_data.append({
                'Asset': f"📊 {asset} ({name_kr})",
                'Shares/Amount': f"{detail['shares']:,} shares",
                'Price': f"₩{detail['price']:,}",
                'Value (KRW)': f"₩{detail['value']:,.0f}"
            })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, width="stretch", hide_index=True)
    
    st.metric("📊 Total Portfolio Value", f"₩{portfolio_value:,.0f} ({portfolio_value/1_000_000:.1f}M KRW)")
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 0.5: TRANSACTION HISTORY (Purchase/Sale Tracking)
    # ═══════════════════════════════════════════════════════════════════════════
    st.header("💳 Section 0.5: Transaction History")
    st.caption("Track buy/sell transactions, employer contributions, and ETF dividends")
    
    # Add new transaction
    with st.expander("➕ Add New Transaction", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        TRANS_TYPE_LABELS = {
            'buy': '🟢 Buy',
            'sell': '🔴 Sell',
            'contribution': '💰 Employer Contribution',
            'dividend': '📊 ETF Dividend',
        }
        
        with col2:
            trans_type = st.selectbox(
                "Transaction Type",
                options=['buy', 'sell', 'contribution', 'dividend'],
                format_func=lambda x: TRANS_TYPE_LABELS[x],
                key="trans_type"
            )
        
        is_cash_type = trans_type in ('contribution', 'dividend')
        
        with col1:
            if is_cash_type and trans_type == 'contribution':
                trans_asset = 'Cash'
                st.text_input("Asset", value="Cash (IRP Account)", disabled=True, key="trans_asset_display")
            elif is_cash_type and trans_type == 'dividend':
                trans_asset = st.selectbox(
                    "Source Asset",
                    options=[a for a in ALLOCATION_TARGET.keys() if a != 'Cash'],
                    key="trans_asset_div"
                )
            else:
                trans_asset = st.selectbox(
                    "Asset",
                    options=[a for a in ALLOCATION_TARGET.keys() if a != 'Cash'],
                    key="trans_asset"
                )
        
        with col3:
            trans_date = st.date_input(
                "Transaction Date",
                value=datetime.now(),
                key="trans_date"
            )
        
        if is_cash_type:
            col4, col5 = st.columns([2, 1])
            with col4:
                trans_amount = st.number_input(
                    "Amount (KRW)",
                    min_value=1,
                    value=600000 if trans_type == 'contribution' else 10000,
                    step=10000,
                    key="trans_amount"
                )
            with col5:
                st.metric("Total Amount", f"₩{trans_amount:,.0f}")
            trans_shares = 0
            trans_price = trans_amount
        else:
            col4, col5, col6 = st.columns(3)
            with col4:
                trans_shares = st.number_input(
                    "Number of Shares",
                    min_value=1,
                    value=10,
                    step=1,
                    key="trans_shares"
                )
            with col5:
                trans_price = st.number_input(
                    "Price per Share (KRW)",
                    min_value=1,
                    value=10000,
                    step=100,
                    key="trans_price"
                )
            with col6:
                trans_total = trans_shares * trans_price
                st.metric("Total Amount", f"₩{trans_total:,.0f}")
        
        trans_notes = st.text_input("Notes (optional)", key="trans_notes")
        
        if st.button("💾 Save Transaction", type="primary", key="save_trans"):
            add_transaction(
                asset=trans_asset,
                trans_type=trans_type,
                date_str=trans_date.strftime("%Y-%m-%d"),
                shares=trans_shares,
                price_per_share=trans_price,
                notes=trans_notes
            )
            if is_cash_type:
                label = "Employer Contribution" if trans_type == 'contribution' else f"ETF Dividend from {trans_asset}"
                st.success(f"✅ Recorded: {label} — ₩{trans_price:,.0f}")
            else:
                st.success(f"✅ Transaction recorded: {trans_type.upper()} {trans_shares} shares of {trans_asset}")
            st.rerun()
    
    # Show transaction history
    all_transactions = get_transactions()
    
    if all_transactions:
        with st.expander(f"📜 View Transaction History ({len(all_transactions)} transactions)", expanded=False):
            # Filter by asset
            filter_asset = st.selectbox(
                "Filter by Asset",
                options=['All'] + list(ALLOCATION_TARGET.keys()),
                key="filter_trans_asset"
            )
            
            filtered_trans = all_transactions if filter_asset == 'All' else get_transactions(filter_asset)
            
            if filtered_trans:
                trans_table = []
                type_labels = {
                    'buy': '🟢 Buy',
                    'sell': '🔴 Sell',
                    'contribution': '💰 Contribution',
                    'dividend': '📊 Dividend',
                }
                status_labels = {
                    'pending': '⏳ Pending',
                    'completed': '✅ Completed',
                }
                for t in filtered_trans:
                    is_cash = t['type'] in ('contribution', 'dividend')
                    is_pending = t.get('status') == 'pending'
                    trans_table.append({
                        'ID': t['id'],
                        'Batch': t.get('batch_id', '—') or '—',
                        'Date': t['date'],
                        'Asset': t['asset'],
                        'Type': type_labels.get(t['type'], t['type']),
                        'Status': status_labels.get(t.get('status', 'completed'), '✅ Completed'),
                        'Shares': '-' if is_cash else str(t['shares']),
                        'Price': '—' if (is_cash or is_pending) else f"₩{t['price_per_share']:,.0f}",
                        'Total': '—' if is_pending else f"₩{t['total_cost']:,.0f}",
                        'Notes': t.get('notes', '')
                    })
                
                df_trans = pd.DataFrame(trans_table)
                st.dataframe(df_trans, width="stretch", hide_index=True)
                
                # Option to delete transaction
                st.caption("To delete a transaction, enter its ID:")
                col1, col2 = st.columns([3, 1])
                with col1:
                    delete_id = st.text_input("Transaction ID to delete", key="delete_trans_id")
                with col2:
                    if st.button("🗑️ Delete", key="delete_trans_btn"):
                        if delete_id:
                            if delete_transaction(delete_id):
                                st.success(f"Deleted transaction {delete_id}")
                                st.rerun()
                            else:
                                st.error("Transaction not found")
            else:
                st.info(f"No transactions found for {filter_asset}")
    else:
        st.info("💡 No transactions recorded yet. Click 'Add New Transaction' to start tracking your purchases.")
    
    st.divider()
    
    # Calculate current allocation percentages from holdings
    current_allocation = {}
    for asset, value in holdings.items():
        if portfolio_value > 0:
            current_allocation[asset] = (value / portfolio_value) * 100
        else:
            current_allocation[asset] = 0
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: CURRENT PORTFOLIO STATUS
    # ═══════════════════════════════════════════════════════════════════════════
    st.header("📊 Section 1: Current Portfolio Status")
    
    st.metric("Total Portfolio Value", f"{portfolio_value:,.0f} KRW ({portfolio_value/1_000_000:.1f}M)")
    
    # Create a table showing current allocation
    current_status_data = []
    for asset, current_pct in current_allocation.items():
        target_pct = ALLOCATION_TARGET.get(asset, 0) * 100
        drift = current_pct - target_pct
        current_value = holdings[asset]
        
        # Determine status
        if abs(drift) > 5:
            status = "⚠️ NEEDS REBALANCING" if abs(drift) > 10 else "⚡ MONITOR"
        else:
            status = "✅ OK"
        
        row_data = {
            'Asset': asset,
            'Current Value': f"{current_value:,.0f}",
            'Current %': f"{current_pct:.1f}%",
            'Target %': f"{target_pct:.1f}%",
            'Drift': f"{drift:+.1f}%",
            'Status': status
        }
        
        # Add shares info if in shares mode
        if holdings_detail and asset in holdings_detail:
            detail = holdings_detail[asset]
            row_data['Shares'] = f"{detail['shares']:,}"
            row_data['Price'] = f"{detail['price']:,}"
        
        current_status_data.append(row_data)
    
    df_status = pd.DataFrame(current_status_data)
    st.dataframe(df_status, width="stretch", hide_index=True)
    
    # Visual comparison chart
    st.subheader("Current vs Target Allocation")
    
    chart_data = []
    for asset in current_allocation:
        chart_data.append({
            'Asset': asset,
            'Type': 'Current',
            'Percentage': current_allocation[asset]
        })
        chart_data.append({
            'Asset': asset,
            'Type': 'Target',
            'Percentage': ALLOCATION_TARGET.get(asset, 0) * 100
        })
    
    df_chart = pd.DataFrame(chart_data)
    fig = px.bar(df_chart, x='Asset', y='Percentage', color='Type', barmode='group',
                 title='Current vs Target Allocation (%)',
                 color_discrete_map={'Current': '#1f77b4', 'Target': '#2ca02c'})
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, width="stretch")
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1.5: GAINS/LOSSES ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════
    st.header("📈 Section 1.5: Gains/Losses Analysis")
    
    # Only show gains/losses if we have transaction history
    all_transactions = get_transactions()
    
    if all_transactions:
        # We have transaction history, calculate gains/losses
        # Use prices already fetched above (or use estimated as fallback)
        current_prices = {}
        for asset in ALLOCATION_TARGET.keys():
            if asset == 'Cash':
                current_prices[asset] = 1
            else:
                price_info = prices.get(asset, {})
                current_prices[asset] = price_info.get('price', 0)
        
        gains_data, total_gain, total_gain_pct = calculate_gains_losses(current_prices)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            total_cost = sum(g['total_cost'] for g in gains_data.values())
            st.metric("Total Cost Basis", f"₩{total_cost:,.0f}")
        with col2:
            total_current = sum(g['current_value'] for g in gains_data.values())
            st.metric("Total Current Value", f"₩{total_current:,.0f}")
        with col3:
            gain_color = "normal" if total_gain >= 0 else "inverse"
            st.metric("Total Unrealized Gain/Loss", 
                     f"₩{total_gain:,.0f}",
                     delta=f"{total_gain_pct:+.1f}%",
                     delta_color=gain_color)
        
        # Detailed gains table
        with st.expander("📊 Detailed Gains/Losses by Asset", expanded=False):
            gains_table = []
            for asset, data_item in gains_data.items():
                gains_table.append({
                    'Asset': asset,
                    'Shares': str(data_item['shares']),
                    'Avg Cost': f"₩{data_item['avg_cost_basis']:,.0f}",
                    'Current Price': f"₩{data_item['current_price']:,.0f}",
                    'Total Cost': f"₩{data_item['total_cost']:,.0f}",
                    'Current Value': f"₩{data_item['current_value']:,.0f}",
                    'Gain/Loss': f"₩{data_item['unrealized_gain']:,.0f}",
                    'Return %': f"{data_item['gain_pct']:+.1f}%"
                })
            
            df_gains = pd.DataFrame(gains_table)
            st.dataframe(df_gains, width="stretch", hide_index=True)
    else:
        st.info("💡 No transaction history recorded yet. Add your purchase history to see gains/losses analysis.")
        st.caption("Go to 'Transaction History' section below to record buy/sell transactions, contributions, and dividends.")
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: ALERTS - ASSETS NEEDING REBALANCING
    # ═══════════════════════════════════════════════════════════════════════════
    st.header("🚨 Section 2: Rebalancing Alerts")
    
    # Time-based rebalancing check
    st.subheader("⏰ Time-Based Rebalancing")
    time_check = check_time_based_rebalancing()
    
    if time_check['should_rebalance']:
        st.error(time_check['message'])
    elif time_check['days_until_next'] <= 7:
        st.warning(time_check['message'])
    else:
        st.success(time_check['message'])
    
    # Rebalancing frequency settings
    with st.expander("⚙️ Rebalancing Schedule Settings"):
        settings = get_rebalancing_settings()
        
        col1, col2 = st.columns(2)
        with col1:
            new_frequency = st.number_input(
                "Rebalancing Frequency (days)",
                min_value=7,
                max_value=365,
                value=settings.get('frequency_days', 90),
                step=7,
                help="How often you want to rebalance your portfolio"
            )
        
        with col2:
            new_threshold = st.number_input(
                "Alert Threshold (%)",
                min_value=1.0,
                max_value=20.0,
                value=settings.get('alert_threshold_pct', 5.0),
                step=0.5,
                help="Alert when allocation drifts more than this %"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("💾 Save Settings", key="save_rebal_settings"):
                new_settings = {
                    'frequency_days': new_frequency,
                    'alert_threshold_pct': new_threshold,
                    'last_rebalance_date': settings.get('last_rebalance_date')
                }
                save_rebalancing_settings(new_settings)
                st.success("Settings saved!")
                st.rerun()
        
        with col4:
            if st.button("📅 Mark Rebalanced Today", key="mark_rebalanced"):
                record_rebalance_date()
                st.success("✅ Rebalance date recorded!")
                st.rerun()
    
    st.divider()
    
    # Drift-based alerts
    st.subheader("📊 Allocation Drift Alerts")
    
    recommendations = get_rebalancing_recommendations(data, current_allocation)
    
    if recommendations:
        st.warning(f"⚠️ Found {len(recommendations)} asset(s) with drift > 5% that need rebalancing")
        
        for rec in recommendations:
            with st.expander(f"{'📈' if rec['action'] == 'ADD' else '📉'} {rec['asset']} - {rec['priority']} Priority", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Allocation", f"{rec['current']:.1f}%")
                
                with col2:
                    st.metric("Target Allocation", f"{rec['target']:.1f}%")
                
                with col3:
                    drift_delta = rec['current'] - rec['target']
                    st.metric("Drift", f"{abs(rec['drift']):.1f}%", 
                             delta=f"{drift_delta:+.1f}%",
                             delta_color="inverse" if rec['action'] == 'ADD' else "normal")
                
                st.write(f"**Action Needed:** {rec['action']} - {rec['reason']}")
    else:
        st.success("✅ All assets are within 5% of target allocation. No rebalancing needed!")
    
    st.divider()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: RECOMMENDED REBALANCING TRADES
    # ═══════════════════════════════════════════════════════════════════════════
    st.header("💰 Section 3: Recommended Rebalancing Trades")
    
    # Settlement date info (T+2 Korea business days)
    now_kr = datetime.now(KR_TZ)
    # If after 15:00, effective trade date is next business day
    if now_kr.hour >= 15:
        effective_trade_date = next_kr_business_day(now_kr.date())
        after_cutoff = True
    else:
        effective_trade_date = now_kr.date()
        after_cutoff = False
    settlement = get_settlement_date(effective_trade_date)
    trade_date_str = settlement['trade_date'].strftime('%Y-%m-%d (%a)')
    settle_date_str = settlement['settlement_date'].strftime('%Y-%m-%d (%a)')

    st.info(f"""
    📅 **매도 → 입금 타임라인 (Sell → Cash Deposit)**

    | Step | Date / Time | Action |
    |------|-------------|--------|
    | **1. 매도 주문** | {trade_date_str} before 15:00 | Execute SELL orders on Samsung Fund |
    | **2. 체결가 확인** | {trade_date_str} ~17:00 | Broker confirms execution price |
    | **3. 입금 (T+2)** | {settle_date_str} | Cash deposited → Execute BUY orders |

    {settlement['description']}
    """)
    if after_cutoff:
        st.warning(f"⚠️ 현재 15:00 이후 — 매도 주문 시 체결일은 다음 영업일 ({trade_date_str}) 입니다.")
    if settlement.get('holidays_in_range'):
        st.caption(f"🇰🇷 Korean holidays in range: {', '.join(settlement['holidays_in_range'])}")
    
    st.write("Based on your current portfolio, here are the specific trades to execute:")
    
    # Calculate trades using real holdings
    trades_buy = []
    trades_sell = []
    total_buy = 0
    total_sell = 0
    
    for asset, current_value in holdings.items():
        target_pct = ALLOCATION_TARGET.get(asset, 0)
        target_value = portfolio_value * target_pct
        difference = target_value - current_value
        
        if abs(difference) > 500_000:  # Only if > 500K difference
            asset_price = prices.get(asset, {}).get('price', 0)
            etf_code = ETF_CONFIG.get(asset, {}).get('code', '')
            asset_label = f"{asset} [{etf_code}]" if etf_code else asset
            if difference > 0:
                shares_to_trade = str(krw_to_shares(abs(difference), asset_price, action="buy")) if asset != 'Cash' else '-'
                trades_buy.append({
                    'Asset': asset_label,
                    'Current Value': f"{current_value:,.0f}",
                    'Target Value': f"{target_value:,.0f}",
                    'Amount (KRW)': f"{abs(difference):,.0f}",
                    'Shares to BUY': shares_to_trade,
                    '_asset_name': asset,
                    '_shares': int(shares_to_trade) if shares_to_trade != '-' else 0,
                    '_amount': abs(difference)
                })
                total_buy += abs(difference)
            else:
                shares_to_trade = str(krw_to_shares(abs(difference), asset_price, action="sell")) if asset != 'Cash' else '-'
                trades_sell.append({
                    'Asset': asset_label,
                    'Current Value': f"{current_value:,.0f}",
                    'Target Value': f"{target_value:,.0f}",
                    'Amount (KRW)': f"{abs(difference):,.0f}",
                    'Shares to SELL': shares_to_trade,
                    '_asset_name': asset,
                    '_shares': int(shares_to_trade) if shares_to_trade != '-' else 0,
                    '_amount': abs(difference)
                })
                total_sell += abs(difference)
    
    # Show SELL trades first
    if trades_sell:
        st.subheader("📉 Step 1: SELL These Assets (Do First)")
        df_sell = pd.DataFrame([{k: v for k, v in t.items() if not k.startswith('_')} for t in trades_sell])
        if 'Shares to SELL' in df_sell.columns:
            df_sell['Shares to SELL'] = df_sell['Shares to SELL'].astype(str)
        st.dataframe(df_sell, width="stretch", hide_index=True)
        st.metric("Total to Sell", f"{total_sell:,.0f} KRW")
    else:
        st.info("No assets need to be sold.")
    
    st.write("")
    
    # Show BUY trades second
    if trades_buy:
        st.subheader("📈 Step 2: BUY These Assets (Do Second)")
        df_buy = pd.DataFrame([{k: v for k, v in t.items() if not k.startswith('_')} for t in trades_buy])
        if 'Shares to BUY' in df_buy.columns:
            df_buy['Shares to BUY'] = df_buy['Shares to BUY'].astype(str)
        st.dataframe(df_buy, width="stretch", hide_index=True)
        st.metric("Total to Buy", f"{total_buy:,.0f} KRW")
    else:
        st.info("No assets need to be bought.")
    
    # Summary
    if trades_sell or trades_buy:
        st.divider()
        st.subheader("📋 Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total to Sell", f"{total_sell:,.0f} KRW", delta=f"-{total_sell/1_000_000:.1f}M")
        with col2:
            st.metric("Total to Buy", f"{total_buy:,.0f} KRW", delta=f"+{total_buy/1_000_000:.1f}M")
        with col3:
            net = total_buy - total_sell
            st.metric("Net Cash Needed", f"{net:,.0f} KRW", 
                     delta=f"{net/1_000_000:+.1f}M" if net != 0 else "0")
        
        st.info(f"""
        **실행 순서 (Execution Order):**
        1. 📉 **{trade_date_str} (15:00 전)** — SELL overweight assets
        2. 💲 **{trade_date_str} ~17:00** — Confirm sell execution prices from broker
        3. ⏳ **Wait for cash deposit** — 2 business days ({settle_date_str})
        4. 📈 **{settle_date_str}** — BUY underweight assets (recalculate shares at current prices!)
        5. ✅ **After buys** — Record rebalancing below

        ⚠️ **Important**: Recalculate buy-side share counts on {settle_date_str} using live prices,
        as prices may have changed during the deposit waiting period.
        """)
        
        # ═══════════════════════════════════════════════════════════════════════
        # REBALANCING WORKFLOW TRACKER
        # ═══════════════════════════════════════════════════════════════════════
        st.divider()
        st.subheader("📍 Rebalancing Workflow Tracker")
        
        # Load workflow state from data
        workflow = data.get('rebalancing_workflow', {})
        wf_status = workflow.get('status', 'not_started')
        
        # Progress bar
        status_steps = ['not_started', 'sells_executed', 'sells_confirmed',
                        'buys_executed', 'buys_confirmed', 'completed']
        step_labels = ['Not Started', 'Sells Executed', 'Sells Confirmed',
                        'Buys Executed', 'Buys Confirmed', 'Completed']
        step_idx = status_steps.index(wf_status) if wf_status in status_steps else 0
        st.progress(step_idx / (len(status_steps) - 1), text=f"Step {step_idx}/{len(status_steps)-1}: {step_labels[step_idx]}")
        
        # Show current state and actions
        wf_col1, wf_col2 = st.columns(2)
        
        with wf_col1:
            if wf_status == 'not_started':
                st.write("🔵 **Status**: Ready to start rebalancing")
                if st.button("📉 I've executed the SELL orders", key="wf_sell_done", type="primary"):
                    sell_now = datetime.now(KR_TZ)
                    batch_id = generate_batch_id("RB")
                    today_str = sell_now.strftime("%Y-%m-%d")
                    # Determine effective trade date: if after 15:00, sell executes next business day
                    if sell_now.hour >= 15:
                        effective_sell_date = next_kr_business_day(sell_now.date())
                    else:
                        effective_sell_date = sell_now.date()
                    sell_settlement = get_settlement_date(effective_sell_date)
                    sell_tx_ids = []
                    for t in trades_sell:
                        asset_name = t['_asset_name']
                        shares = t['_shares']
                        if asset_name == 'Cash' or shares == 0:
                            continue
                        tx = add_transaction(
                            asset=asset_name,
                            trans_type='sell',
                            date_str=today_str,
                            shares=shares,
                            price_per_share=0,
                            notes="Rebalancing sell (pending confirmation)",
                            batch_id=batch_id,
                            status='pending'
                        )
                        sell_tx_ids.append(tx['id'])
                    data = load_data()
                    data['rebalancing_workflow'] = {
                        'status': 'sells_executed',
                        'sell_date': sell_now.isoformat(),
                        'sell_time': sell_now.strftime('%H:%M'),
                        'effective_sell_date': effective_sell_date.isoformat(),
                        'settlement_date': sell_settlement['settlement_date'].isoformat(),
                        'sells_total': total_sell,
                        'sell_batch_id': batch_id,
                        'sell_tx_ids': sell_tx_ids,
                        'planned_buys': [{'asset': t['_asset_name'], 'amount': t['_amount'],
                                          'shares': t['_shares']} for t in trades_buy
                                         if t['_asset_name'] != 'Cash' and t['_shares'] > 0],
                    }
                    save_data(data)
                    if sell_now.hour >= 15:
                        st.warning(f"⚠️ 15:00 이후 매도 주문 — 실제 체결일은 다음 영업일 ({effective_sell_date}) 입니다.")
                    st.rerun()

            elif wf_status == 'sells_executed':
                sell_batch = workflow.get('sell_batch_id', '')
                pending_sells = get_pending_transactions(sell_batch) if sell_batch else []

                if pending_sells:
                    st.write("⏳ **Status**: Sell orders placed — enter broker execution prices")
                    st.caption(f"Batch: `{sell_batch}`")
                    with st.form("confirm_sell_prices"):
                        st.write("📋 Enter the **actual sale price per share** from your broker report:")
                        # Header row
                        hcol1, hcol2, hcol3, hcol4 = st.columns([3, 2, 2, 2])
                        with hcol1:
                            st.markdown("**Asset**")
                        with hcol2:
                            st.markdown("**Shares Sold**")
                        with hcol3:
                            st.markdown("**Price per Share**")
                        with hcol4:
                            st.markdown("**Ref. Market Price**")
                        st.divider()
                        sell_inputs = {}
                        preview_data = []
                        for tx in pending_sells:
                            etf_code = ETF_CONFIG.get(tx['asset'], {}).get('code', '')
                            label = f"{tx['asset']} [{etf_code}]" if etf_code else tx['asset']
                            market_price = prices.get(tx['asset'], {}).get('price', 0)
                            rcol1, rcol2, rcol3, rcol4 = st.columns([3, 2, 2, 2])
                            with rcol1:
                                st.write(label)
                            with rcol2:
                                shares_val = st.number_input(
                                    f"shares_{tx['asset']}",
                                    min_value=0,
                                    value=tx['shares'],
                                    step=1,
                                    key=f"sell_shares_{tx['id']}",
                                    label_visibility="collapsed",
                                    help="Adjust if actual shares sold differs from planned"
                                )
                            with rcol3:
                                price_val = st.number_input(
                                    f"price_{tx['asset']}",
                                    min_value=0,
                                    value=0,
                                    step=100,
                                    key=f"sell_price_{tx['id']}",
                                    label_visibility="collapsed",
                                    help="Enter broker execution price"
                                )
                            with rcol4:
                                st.write(f"₩{market_price:,.0f}")
                            sell_inputs[tx['id']] = {'shares': shares_val, 'price_per_share': price_val}
                            preview_data.append({'asset': tx['asset'], 'shares': shares_val,
                                                 'market_price': market_price, 'tx_id': tx['id']})

                        if st.form_submit_button("✅ Confirm All Sell Prices", type="primary"):
                            all_filled = all(v['price_per_share'] > 0 for v in sell_inputs.values())
                            if not all_filled:
                                st.error("모든 가격을 입력해주세요 (All prices must be > 0)")
                            else:
                                # Validate prices are within reasonable range of market
                                warnings = []
                                for pv in preview_data:
                                    entered = sell_inputs[pv['tx_id']]['price_per_share']
                                    mkt = pv['market_price']
                                    if mkt > 0 and (entered < mkt * 0.5 or entered > mkt * 1.5):
                                        warnings.append(f"{pv['asset']}: ₩{entered:,} (market: ₩{mkt:,.0f})")
                                if warnings:
                                    st.warning("⚠️ Price(s) differ significantly from market:\n" +
                                               "\n".join(f"- {w}" for w in warnings) +
                                               "\n\nSubmit again to confirm if correct.")
                                    st.session_state['sell_price_warning_shown'] = True
                                elif not st.session_state.get('sell_price_warning_shown', False):
                                    confirm_batch_transactions(sell_batch, sell_inputs)
                                    data = load_data()
                                    data['rebalancing_workflow']['status'] = 'sells_confirmed'
                                    data['rebalancing_workflow']['sells_confirmed_at'] = datetime.now().isoformat()
                                    save_data(data)
                                    st.session_state.pop('sell_price_warning_shown', None)
                                    st.rerun()
                                else:
                                    # Warning was shown before, user submitted again — accept
                                    confirm_batch_transactions(sell_batch, sell_inputs)
                                    data = load_data()
                                    data['rebalancing_workflow']['status'] = 'sells_confirmed'
                                    data['rebalancing_workflow']['sells_confirmed_at'] = datetime.now().isoformat()
                                    save_data(data)
                                    st.session_state.pop('sell_price_warning_shown', None)
                                    st.rerun()
                else:
                    data = load_data()
                    data['rebalancing_workflow']['status'] = 'sells_confirmed'
                    save_data(data)
                    st.rerun()

            elif wf_status == 'sells_confirmed':
                sell_date = workflow.get('sell_date', '')[:10]
                target_settle = workflow.get('settlement_date', '')[:10]
                today_kr = datetime.now(KR_TZ).date()
                settle_dt = date.fromisoformat(target_settle) if target_settle else today_kr
                days_left = (settle_dt - today_kr).days

                # Allow editing confirmed sell prices
                sell_batch = workflow.get('sell_batch_id', '')
                if sell_batch:
                    confirmed_sells = [t for t in get_transactions()
                                       if t.get('batch_id') == sell_batch and t.get('status') == 'completed']
                    if confirmed_sells:
                        with st.expander("✏️ Edit Sell Transactions (correction)", expanded=False):
                            with st.form("edit_sell_prices"):
                                st.write("📋 Correct **shares sold** and/or **price per share** from your broker report:")
                                # Header row
                                hcol1, hcol2, hcol3, hcol4 = st.columns([3, 2, 2, 2])
                                with hcol1:
                                    st.markdown("**Asset**")
                                with hcol2:
                                    st.markdown("**Shares Sold**")
                                with hcol3:
                                    st.markdown("**Price per Share**")
                                with hcol4:
                                    st.markdown("**Ref. Market Price**")
                                st.divider()
                                edit_inputs = {}
                                for tx in confirmed_sells:
                                    etf_code = ETF_CONFIG.get(tx['asset'], {}).get('code', '')
                                    label = f"{tx['asset']} [{etf_code}]" if etf_code else tx['asset']
                                    market_price = prices.get(tx['asset'], {}).get('price', 0)
                                    stored_price = int(tx['price_per_share'])
                                    rcol1, rcol2, rcol3, rcol4 = st.columns([3, 2, 2, 2])
                                    with rcol1:
                                        st.write(label)
                                    with rcol2:
                                        shares_val = st.number_input(
                                            f"shares_{tx['asset']}",
                                            min_value=0,
                                            value=tx['shares'],
                                            step=1,
                                            key=f"edit_sell_shares_{tx['id']}",
                                            label_visibility="collapsed",
                                            help="Adjust if actual shares differs"
                                        )
                                    with rcol3:
                                        price_val = st.number_input(
                                            f"price_{tx['asset']}",
                                            min_value=1,
                                            value=stored_price if stored_price > 0 else 0,
                                            step=100,
                                            key=f"edit_sell_price_{tx['id']}",
                                            label_visibility="collapsed",
                                            help="Enter broker execution price"
                                        )
                                    with rcol4:
                                        st.write(f"₩{market_price:,.0f}")
                                    edit_inputs[tx['id']] = {'shares': shares_val, 'price_per_share': price_val}
                                if st.form_submit_button("💾 Update Sell Transactions"):
                                    for tid, vals in edit_inputs.items():
                                        update_transaction(tid, {
                                            'shares': vals['shares'],
                                            'price_per_share': vals['price_per_share']
                                        })
                                    st.success("✅ Sell transactions updated!")
                                    st.rerun()

                sell_time = workflow.get('sell_time', '')
                effective_date = workflow.get('effective_sell_date', sell_date)
                sell_label = f"**{sell_date} at {sell_time} KST**" if sell_time else f"**{sell_date}**"
                if effective_date != sell_date:
                    sell_label += f" (체결일: {effective_date})"

                if days_left > 0:
                    st.write("⏳ **Status**: Sells confirmed. Waiting for cash deposit")
                    st.write(f"Sold on: {sell_label}")
                    st.write(f"Cash deposits: **{target_settle}** ({days_left} business day(s) remaining)")
                    st.warning("💡 Do NOT execute buy orders yet — cash has not been deposited.")
                else:
                    st.write(f"✅ **Status**: Cash deposited! Ready to buy.")
                    st.write(f"Sold on: {sell_label} → Deposited: **{target_settle}**")
                    st.success("💰 Cash is available. Execute BUY orders now with current prices.")
                    if st.button("📈 I've executed the BUY orders", key="wf_buy_done", type="primary"):
                        buy_batch_id = generate_batch_id("RB")
                        buy_today = datetime.now(KR_TZ).strftime("%Y-%m-%d")
                        buy_tx_ids = []
                        for planned in workflow.get('planned_buys', []):
                            asset_name = planned['asset']
                            shares = planned.get('shares', 0)
                            if asset_name == 'Cash' or shares == 0:
                                continue
                            tx = add_transaction(
                                asset=asset_name,
                                trans_type='buy',
                                date_str=buy_today,
                                shares=shares,
                                price_per_share=0,
                                notes="Rebalancing buy (pending confirmation)",
                                batch_id=buy_batch_id,
                                status='pending'
                            )
                            buy_tx_ids.append(tx['id'])
                        data = load_data()
                        data['rebalancing_workflow']['status'] = 'buys_executed'
                        data['rebalancing_workflow']['buy_date'] = datetime.now().isoformat()
                        data['rebalancing_workflow']['buy_batch_id'] = buy_batch_id
                        data['rebalancing_workflow']['buy_tx_ids'] = buy_tx_ids
                        save_data(data)
                        st.rerun()

            elif wf_status == 'buys_executed':
                buy_batch = workflow.get('buy_batch_id', '')
                pending_buys = get_pending_transactions(buy_batch) if buy_batch else []

                if pending_buys:
                    st.write("⏳ **Status**: Buy orders placed — enter broker execution prices")
                    st.caption(f"Batch: `{buy_batch}`")
                    with st.form("confirm_buy_prices"):
                        st.write("📋 Enter the **actual buy price per share** from your broker report (adjust shares if needed):")
                        # Header row
                        hcol1, hcol2, hcol3, hcol4 = st.columns([3, 2, 2, 2])
                        with hcol1:
                            st.markdown("**Asset**")
                        with hcol2:
                            st.markdown("**Shares Bought**")
                        with hcol3:
                            st.markdown("**Price per Share**")
                        with hcol4:
                            st.markdown("**Ref. Market Price**")
                        st.divider()
                        buy_inputs = {}
                        buy_preview = []
                        for tx in pending_buys:
                            etf_code = ETF_CONFIG.get(tx['asset'], {}).get('code', '')
                            label = f"{tx['asset']} [{etf_code}]" if etf_code else tx['asset']
                            market_price = prices.get(tx['asset'], {}).get('price', 0)
                            rcol1, rcol2, rcol3, rcol4 = st.columns([3, 2, 2, 2])
                            with rcol1:
                                st.write(label)
                            with rcol2:
                                shares_val = st.number_input(
                                    f"shares_{tx['asset']}",
                                    min_value=0,
                                    value=tx['shares'],
                                    step=1,
                                    key=f"buy_shares_{tx['id']}",
                                    label_visibility="collapsed"
                                )
                            with rcol3:
                                price_val = st.number_input(
                                    f"price_{tx['asset']}",
                                    min_value=0,
                                    value=0,
                                    step=100,
                                    key=f"buy_price_{tx['id']}",
                                    label_visibility="collapsed",
                                    help="Enter broker execution price"
                                )
                            with rcol4:
                                st.write(f"₩{market_price:,.0f}")
                            buy_inputs[tx['id']] = {'shares': shares_val, 'price_per_share': price_val}
                            buy_preview.append({'asset': tx['asset'], 'shares': shares_val,
                                                'market_price': market_price, 'tx_id': tx['id']})
                        if st.form_submit_button("✅ Confirm All Buy Prices", type="primary"):
                            all_filled = all(v['price_per_share'] > 0 for v in buy_inputs.values())
                            if not all_filled:
                                st.error("모든 가격을 입력해주세요 (All prices must be > 0)")
                            else:
                                # Validate prices are within reasonable range of market
                                warnings = []
                                for pv in buy_preview:
                                    entered = buy_inputs[pv['tx_id']]['price_per_share']
                                    mkt = pv['market_price']
                                    if mkt > 0 and (entered < mkt * 0.5 or entered > mkt * 1.5):
                                        warnings.append(f"{pv['asset']}: ₩{entered:,} (market: ₩{mkt:,.0f})")
                                if warnings:
                                    st.warning("⚠️ Price(s) differ significantly from market:\n" +
                                               "\n".join(f"- {w}" for w in warnings) +
                                               "\n\nSubmit again to confirm if correct.")
                                    st.session_state['buy_price_warning_shown'] = True
                                elif not st.session_state.get('buy_price_warning_shown', False):
                                    confirm_batch_transactions(buy_batch, buy_inputs)
                                    data = load_data()
                                    data['rebalancing_workflow']['status'] = 'buys_confirmed'
                                    data['rebalancing_workflow']['buys_confirmed_at'] = datetime.now().isoformat()
                                    save_data(data)
                                    st.session_state.pop('buy_price_warning_shown', None)
                                    st.rerun()
                                else:
                                    confirm_batch_transactions(buy_batch, buy_inputs)
                                    data = load_data()
                                    data['rebalancing_workflow']['status'] = 'buys_confirmed'
                                    data['rebalancing_workflow']['buys_confirmed_at'] = datetime.now().isoformat()
                                    save_data(data)
                                    st.session_state.pop('buy_price_warning_shown', None)
                                    st.rerun()
                else:
                    data = load_data()
                    data['rebalancing_workflow']['status'] = 'buys_confirmed'
                    save_data(data)
                    st.rerun()

            elif wf_status == 'buys_confirmed':
                st.write("✅ **Status**: All orders confirmed!")
                st.write("Update your holdings below to complete the rebalancing.")
                if st.button("🏁 Complete Rebalancing", key="wf_complete", type="primary"):
                    data = load_data()
                    data['rebalancing_workflow']['status'] = 'completed'
                    data['rebalancing_workflow']['completed_at'] = datetime.now().isoformat()
                    save_data(data)
                    st.rerun()

            elif wf_status == 'completed':
                st.write("🎉 **Status**: Rebalancing completed!")
                st.write("You can reset the workflow to start a new cycle.")

        with wf_col2:
            if wf_status != 'not_started':
                st.write("**Workflow Summary:**")
                if workflow.get('sell_date'):
                    sell_disp = workflow['sell_date'][:10]
                    sell_time_disp = workflow.get('sell_time', '')
                    eff_date_disp = workflow.get('effective_sell_date', sell_disp)
                    time_str = f" {sell_time_disp}" if sell_time_disp else ""
                    st.write(f"📉 Sells: {sell_disp}{time_str} KST")
                    if eff_date_disp != sell_disp:
                        st.caption(f"체결일: {eff_date_disp} (15:00 이후 매도)")
                if workflow.get('sell_batch_id'):
                    st.caption(f"Sell Batch: `{workflow['sell_batch_id']}`")
                if workflow.get('sells_confirmed_at'):
                    st.write(f"✅ Sells Confirmed: {workflow['sells_confirmed_at'][:10]}")
                if workflow.get('settlement_date'):
                    st.write(f"💰 Cash Deposit: {workflow['settlement_date'][:10]}")
                if workflow.get('buy_date'):
                    st.write(f"📈 Buys: {workflow['buy_date'][:10]}")
                if workflow.get('buy_batch_id'):
                    st.caption(f"Buy Batch: `{workflow['buy_batch_id']}`")
                if workflow.get('buys_confirmed_at'):
                    st.write(f"✅ Buys Confirmed: {workflow['buys_confirmed_at'][:10]}")
                if workflow.get('sells_total'):
                    st.write(f"💵 Amount: ₩{workflow['sells_total']:,.0f}")

                st.write("")
                if st.button("🔄 Reset Workflow", key="wf_reset", help="Reset if you want to start over"):
                    data = load_data()
                    sell_batch = workflow.get('sell_batch_id')
                    buy_batch = workflow.get('buy_batch_id')
                    batch_ids = {b for b in (sell_batch, buy_batch) if b}
                    if batch_ids:
                        data['transactions'] = [
                            t for t in data.get('transactions', [])
                            if not (t.get('status') == 'pending' and t.get('batch_id') in batch_ids)
                        ]
                    data['rebalancing_workflow'] = {'status': 'not_started'}
                    save_data(data)
                    st.rerun()
        
        # ═══════════════════════════════════════════════════════════════════════
        # SECTION 4: RECORD REBALANCING
        # ═══════════════════════════════════════════════════════════════════════
        st.divider()
        st.header("✅ Section 4: Record Your Rebalancing")
        
        st.write("After executing the trades, update your holdings to reflect the new values:")
        
        with st.expander("📝 I've completed the rebalancing - Update my holdings", expanded=False):
            st.write("Enter the new values after rebalancing:")
            
            new_holdings = {}
            cols = st.columns(2)
            
            for idx, (asset, current_value) in enumerate(holdings.items()):
                # Calculate suggested new value (target)
                target_pct = ALLOCATION_TARGET.get(asset, 0)
                suggested_value = int(portfolio_value * target_pct)
                
                with cols[idx % 2]:
                    new_holdings[asset] = st.number_input(
                        f"{asset} (Suggested: {suggested_value:,})",
                        value=suggested_value,
                        step=100_000,
                        min_value=0,
                        key=f"new_holding_{asset}"
                    )
            
            notes = st.text_input("Notes (optional)", placeholder="e.g., Quarterly rebalancing March 2026")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save New Holdings & Record Rebalance", width="stretch", type="primary"):
                    # Record the trades
                    all_trades = []
                    for t in trades_sell:
                        all_trades.append({'action': 'SELL', 'asset': t['Asset'], 'amount': t['_amount']})
                    for t in trades_buy:
                        all_trades.append({'action': 'BUY', 'asset': t['Asset'], 'amount': t['_amount']})
                    
                    record_rebalance(all_trades, notes)
                    save_holdings(new_holdings)
                    st.success("✅ Holdings updated and rebalancing recorded!")
                    st.rerun()
            
            with col2:
                new_total = sum(new_holdings.values())
                st.metric("New Total", f"{new_total:,.0f} KRW")
    else:
        st.success("✅ Portfolio is well-balanced! No trades needed at this time.")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5: REBALANCING HISTORY
    # ═══════════════════════════════════════════════════════════════════════════
    st.divider()
    st.header("📜 Section 5: Rebalancing History")
    
    rebalance_history = data.get('rebalance_history', [])
    
    if rebalance_history:
        for idx, record in enumerate(reversed(rebalance_history[-5:])):  # Show last 5
            with st.expander(f"📅 {record['date'][:10]} - {record.get('notes', 'No notes')}", expanded=False):
                st.write(f"**Portfolio Value:** {record.get('portfolio_value_before', 0):,.0f} KRW")
                st.write("**Trades Executed:**")
                for trade in record.get('trades', []):
                    icon = "📈" if trade['action'] == 'BUY' else "📉"
                    st.write(f"  {icon} {trade['action']} {trade['asset']}: {trade['amount']:,.0f} KRW")
    else:
        st.info("No rebalancing history yet. Your first rebalancing will be recorded here.")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: PLAN REVISION (New)
# ═══════════════════════════════════════════════════════════════════════════════

def page_plan_revision():
    """Plan revision based on market and progress"""
    st.title("📋 Plan Revision & Strategy Adjustment")
    
    data = load_data()
    progress = calculate_progress(data)
    market_data = get_market_data()
    market_analysis = get_market_trend_analysis(market_data)
    
    st.subheader("Strategy Review")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Current Strategy (Option B - Moderate)")
        st.write("**Allocation:**")
        st.write("- Growth Equities: 42%")
        st.write("- Defensive Equities: 18%")
        st.write("- Bonds: 11%")
        st.write("- Cash: 28%")
        st.write("")
        st.write("**Expected Return:** 10.2% CAGR")
    
    with col2:
        st.write("### Recommendation Status")
        
        years, _, _ = calculate_time_remaining()
        
        if years > 3:
            st.write("✓ **Maintain Current Strategy**")
            st.write("- You have 3+ years for growth")
            st.write("- Current 42% growth is appropriate")
            st.write("- Continue monthly deposits")
        elif years > 2:
            st.write("→ **Begin Gradual Transition**")
            st.write("- Shift 5% to bonds over next 6 months")
            st.write("- Maintain 37% growth equities")
            st.write("- Increase dividend allocation")
        else:
            st.write("🛡️ **De-Risk Aggressively**")
            st.write("- Shift to 30% growth, 40% bonds")
            st.write("- Focus on capital preservation")
            st.write("- Increase monthly contributions to bonds")
    
    st.divider()
    
    st.subheader("Scenario Analysis: Should You Revise?")
    
    tabs = st.tabs(["Keep Strategy", "Shift Conservative", "Go Aggressive"])
    
    with tabs[0]:
        st.write("### Option 1: Keep Current Strategy (42% Growth)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Pros:**")
            st.write("✓ Proven 10.2% CAGR achievable")
            st.write("✓ Matches your risk tolerance")
            st.write("✓ Well-diversified across sectors")
            st.write("✓ Automatic de-risking via deposits")
        
        with col2:
            st.write("**Cons:**")
            st.write("✗ Vulnerable to AI sector crash")
            st.write("✗ Higher volatility possible")
            st.write("✗ May need to adjust if market crashes")
        
        st.write("")
        st.write("**Expected 5-Year Outcome:** 375-400M KRW")
        st.write("**Success Probability:** 75-88%")
        st.write("")
        st.write("**Recommendation: ✓ KEEP THIS STRATEGY**")
        st.write("This is the optimal balance for your 5-year timeline.")
    
    with tabs[1]:
        st.write("### Option 2: Shift to Conservative (30% Growth)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Pros:**")
            st.write("✓ Much lower volatility")
            st.write("✓ Better sleep at night")
            st.write("✓ Protected against crashes")
            st.write("✓ Stable income focus")
        
        with col2:
            st.write("**Cons:**")
            st.write("✗ Expected return only 7-8%")
            st.write("✗ May miss your 400M goal")
            st.write("✗ Less growth potential")
            st.write("✗ Need to rely on RSU gains")
        
        st.write("")
        st.write("**Expected 5-Year Outcome:** 340-360M KRW")
        st.write("**Success Probability:** 70-80%")
        st.write("")
        st.write("**When to Consider:** Only if market crashes >30% and you can't hold")
    
    with tabs[2]:
        st.write("### Option 3: Go Aggressive (55% Growth)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Pros:**")
            st.write("✓ Expected return: 13%+ CAGR")
            st.write("✓ Almost guaranteed 400M+ goal")
            st.write("✓ Potential 450M-500M+ outcome")
            st.write("✓ Maximum wealth building")
        
        with col2:
            st.write("**Cons:**")
            st.write("✗ High volatility (±25% swings)")
            st.write("✗ Risk of 30-40% corrections")
            st.write("✗ Difficult to hold in downturns")
            st.write("✗ Concentration risk in AI sector")
        
        st.write("")
        st.write("**Expected 5-Year Outcome:** 410-470M KRW")
        st.write("**Success Probability:** 68-72% (LOWER!)")
        st.write("")
        st.write("**Recommendation: ❌ NOT RECOMMENDED**")
        st.write("Risk of failure increases even though upside is higher.")
    
    st.divider()
    
    # Final recommendation
    st.subheader("Final Recommendation")
    
    if progress['progress_goal'] >= 80:
        st.warning("✓ You're 80%+ toward goal - BEGIN DE-RISKING")
        st.write("""
        Since you're already at 80%+ of your 400M goal:
        
        **Immediate Actions:**
        1. Shift 10% from growth to bonds this quarter
        2. Increase dividend allocation to 15%
        3. Target: 35% growth, 25% dividend, 20% bonds, 20% cash
        4. Lock in gains through systematic rebalancing
        
        **Why:** You've already achieved most of your goal. 
        Losing 20-30% now is more painful than missing 5-10% upside.
        """)
    
    elif progress['progress_goal'] >= 60:
        st.info("→ You're on track - MAINTAIN CURRENT STRATEGY")
        st.write("""
        You're between 60-80% of your goal:
        
        **Keep Doing:**
        1. Stay with 42% growth, 18% defensive, 11% bonds
        2. Continue monthly 600K deposits
        3. Record RSU vesting as it happens
        4. Quarterly rebalancing
        
        **Why:** You have 3+ years to compound growth.
        Your current 10.2% CAGR target is achievable.
        """)
    
    else:
        st.success("⬆️ You're behind pace - STAY AGGRESSIVE")
        st.write("""
        You're below 60% of goal - need more growth:
        
        **Keep Current Strategy:**
        1. Maintain 42% growth allocation
        2. Could even increase to 50% if comfortable
        3. Maximum emphasis on monthly deposits
        4. RSU deployment is critical
        
        **Why:** You need aggressive growth to catch up.
        Time is more valuable than safety right now.
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: EXPORT FOR AI REVIEW
# ═══════════════════════════════════════════════════════════════════════════════

def page_export_snapshot():
    """Generate portfolio snapshot for AI review"""
    st.title("📋 Export for AI Review")

    st.markdown("""
    Generate a **ready-to-paste markdown snapshot** of your portfolio for Claude Web or other AI tools.
    Use this for **quarterly strategic reviews** aligned with your 90-day rebalancing cycle.
    """)

    # ── Review Mode Toggle ──
    review_mode = st.radio(
        "Review Mode",
        ["Standard Review", "Three-Persona Review"],
        index=1,
        horizontal=True,
        help="Standard: single AI reviewer. Persona: Cathie Wood (growth) + Peter Lynch (valuation) + Ray Dalio (crash protection)",
    )
    use_persona = review_mode == "Three-Persona Review"

    if use_persona:
        st.info(
            "**Three-Persona Mode** — The AI will respond as Cathie Wood, Peter Lynch, and Ray Dalio, "
            "each analyzing your portfolio from their perspective, then synthesize a final recommendation."
        )

    data = load_data()
    progress = calculate_progress(data)
    shares = data.get('shares', get_default_holdings())
    years_remaining, _, _ = calculate_time_remaining()

    with st.spinner("Fetching live prices from KRX..."):
        prices = fetch_etf_prices()

    # Calculate holdings values
    holdings = {}
    for asset in ALLOCATION_TARGET:
        num_shares = shares.get(asset, 0)
        price = prices.get(asset, {}).get('price', 0)
        holdings[asset] = num_shares if asset == 'Cash' else num_shares * price

    portfolio_value = sum(holdings.values())

    # Build current_prices dict for gains/losses
    current_prices = {}
    for asset in ALLOCATION_TARGET:
        if asset == 'Cash':
            current_prices[asset] = 1
        else:
            current_prices[asset] = prices.get(asset, {}).get('price', 0)

    gains_losses, total_gain, total_gain_pct = calculate_gains_losses(current_prices)
    transactions = get_transactions()

    gen_kwargs = dict(
        holdings=holdings,
        prices=prices,
        allocation_target=ALLOCATION_TARGET,
        portfolio_value=portfolio_value,
        progress=progress,
        years_remaining=years_remaining,
        transactions=transactions,
        gains_losses=gains_losses,
        total_gain=total_gain,
        total_gain_pct=total_gain_pct,
        etf_config=ETF_CONFIG,
    )

    if use_persona:
        snapshot = generate_persona_export(**gen_kwargs)
    else:
        snapshot = generate_portfolio_snapshot(**gen_kwargs)

    # ── Claude CLI: one-click AI review ──
    cli_available = is_claude_cli_available()

    st.subheader("🚀 Run AI Review via Claude CLI")

    if cli_available:
        st.success("Claude CLI detected — you can run the review directly from here.")

        cli_col1, cli_col2, cli_col3 = st.columns([2, 1, 1])
        with cli_col1:
            cli_model = st.selectbox(
                "Model",
                ["sonnet", "opus"],
                index=0,
                help="Sonnet: fast & cheap (~30s). Opus: deeper analysis (~90s).",
                key="cli_model",
            )
        with cli_col2:
            cli_timeout = st.number_input(
                "Timeout (seconds)",
                min_value=60,
                max_value=600,
                value=300,
                step=30,
                key="cli_timeout",
            )
        with cli_col3:
            cli_budget = st.number_input(
                "Max budget (USD)",
                min_value=0.0,
                max_value=5.0,
                value=1.0,
                step=0.25,
                format="%.2f",
                key="cli_budget",
            )

        if st.button("Run AI Review Now", type="primary", use_container_width=True, key="run_cli_review"):
            review_mode_tag = "persona" if use_persona else "standard"
            with st.spinner(f"Running Claude CLI ({cli_model})... this may take 30-120 seconds"):
                cli_result = run_claude_cli(
                    snapshot,
                    model=cli_model,
                    timeout_seconds=int(cli_timeout),
                    max_budget_usd=cli_budget if cli_budget > 0 else None,
                )

            if cli_result["success"]:
                response_text = cli_result["response"]
                saved_path = save_review_md(response_text, review_mode=review_mode_tag)

                st.success(
                    f"Review completed in {cli_result['elapsed_seconds']:.0f}s "
                    f"(model: {cli_result['model']}). Saved to `{saved_path.name}`."
                )

                # Parse and display inline
                fmt = detect_review_format(response_text)
                if fmt == "persona":
                    persona_result = parse_persona_review_md(response_text)
                    review = persona_review_to_standard(persona_result)
                    _show_persona_tabs(persona_result)
                else:
                    review = parse_ai_review_md(response_text)
                    persona_result = None

                # Show parsed allocation
                _show_cli_review_results(review, persona_result, saved_path.name)
            else:
                st.error(f"Claude CLI failed: {cli_result['error']}")
                st.info("You can still use the manual copy-paste workflow below.")
    else:
        st.warning(
            "Claude CLI not found. Install it (`npm install -g @anthropic-ai/claude-code`) "
            "or use the manual copy-paste workflow below."
        )

    st.divider()

    # ── Manual workflow (fallback) ──
    with st.expander("📑 Manual Copy-Paste Workflow", expanded=not cli_available):
        # Preview
        st.subheader("📄 Snapshot Preview")
        st.markdown(snapshot)

        st.subheader("📑 Copy This Text")
        st.text_area(
            "Select all and copy (Ctrl+A, Ctrl+C):",
            value=snapshot,
            height=500,
            key=f"snapshot_text_{'persona' if use_persona else 'standard'}",
        )

        if use_persona:
            st.info("""
            **How to use (Three-Persona):**
            1. Copy the text above
            2. Open [Claude Web](https://claude.ai) (or another AI)
            3. Paste the snapshot — the AI will respond as three personas + a synthesis
            4. Save the full AI response as a `.md` file
            5. Import it using the **Import AI Review** page (persona format auto-detected)
            """)
        else:
            st.info("""
            **How to use:**
            1. Copy the text above
            2. Open [Claude Web](https://claude.ai) (or another AI)
            3. Paste the snapshot and ask for a quarterly review
            4. Review the AI's recommendations before making changes
            5. Save the AI response as a .md file
            6. Import it using the **Import AI Review** page
            """)


def _show_cli_review_results(review: dict, persona_result: dict | None, filename: str):
    """Display parsed CLI review results with Apply/Reset buttons inline on the Export page."""
    st.divider()
    st.subheader("📊 Recommended Allocation Changes" + (" (from SYNTHESIS)" if persona_result else ""))

    if not review.get("allocation"):
        st.warning("Could not parse allocation from the response. Check the raw output below.")
        with st.expander("Raw AI response"):
            st.code(review.get("raw", "")[:5000])
        return

    valid_assets = {}
    comparison_rows = []
    for asset_name, info in review["allocation"].items():
        matched_key = normalize_asset_name(asset_name)
        if not matched_key or matched_key not in ALLOCATION_TARGET:
            continue

        current_target = ALLOCATION_TARGET[matched_key] * 100
        recommended = info["recommended"]
        change = recommended - current_target
        valid_assets[matched_key] = recommended

        comparison_rows.append({
            "Asset": matched_key,
            "Current Target %": f"{current_target:.0f}%",
            "Recommended %": f"{recommended:.0f}%",
            "Change": f"{change:+.0f}%",
            "Action": info.get("action", ""),
            "Reason": info.get("reason", ""),
        })

    if comparison_rows:
        df = pd.DataFrame(comparison_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        total_pct = sum(valid_assets.values())
        if abs(total_pct - 100) > 1:
            st.warning(f"Recommended allocations sum to {total_pct:.0f}% (should be 100%). Adjust before applying.")
        else:
            st.success(f"Allocations sum to {total_pct:.0f}%")

    # CAGR
    if review.get("cagr", {}).get("recommended"):
        st.subheader("📈 CAGR Assessment")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Current CAGR", f"{review['cagr']['current']}%")
        with c2:
            delta = review['cagr']['recommended'] - (review['cagr']['current'] or 0)
            st.metric("Recommended CAGR", f"{review['cagr']['recommended']}%", delta=f"{delta:+.1f}%")
        if review['cagr'].get('reason'):
            st.caption(f"Reason: {review['cagr']['reason']}")

    # Recommendations
    if review.get("recommendations"):
        st.subheader("🎯 Key Recommendations")
        for rec in review["recommendations"]:
            rec_upper = rec.upper()
            if rec_upper.startswith("[HIGH]") or rec_upper.startswith("HIGH"):
                st.error(f"🔴 {rec}")
            elif rec_upper.startswith("[MEDIUM]") or rec_upper.startswith("MEDIUM"):
                st.warning(f"🟡 {rec}")
            else:
                st.info(f"🔵 {rec}")

    # Market Outlook
    if review.get("market_outlook"):
        st.subheader("🌍 Market Outlook")
        st.markdown(review["market_outlook"])

    # Apply / Reset
    if valid_assets:
        st.divider()
        st.subheader("✅ Apply Changes")

        with st.expander("🔧 Fine-tune before applying (optional)"):
            adjusted = {}
            cols = st.columns(2)
            for idx, (asset, pct) in enumerate(valid_assets.items()):
                with cols[idx % 2]:
                    adjusted[asset] = st.number_input(
                        f"{asset} %",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(pct),
                        step=1.0,
                        key=f"cli_adjust_{asset}",
                    )
            adj_total = sum(adjusted.values())
            if abs(adj_total - 100) > 1:
                st.warning(f"Total: {adj_total:.0f}% — must be ~100%")
            else:
                st.success(f"Total: {adj_total:.0f}%")
                valid_assets = adjusted

        col1, col2 = st.columns(2)
        with col1:
            source_label = "persona_cli_review" if persona_result else "cli_review"
            if st.button("🚀 Apply Recommended Allocation", type="primary", use_container_width=True, key="cli_apply"):
                new_target = {asset: pct / 100.0 for asset, pct in valid_assets.items()}
                notes = f"From CLI review: {filename}"
                if persona_result:
                    personas_found = list(persona_result.get('personas', {}).keys())
                    notes += f" | Personas: {', '.join(personas_found)}"
                if review.get("recommendations"):
                    notes += " | " + "; ".join(review["recommendations"][:3])
                save_allocation_target(new_target, source=source_label, notes=notes)
                save_ai_review(review, filename)
                st.success("Allocation targets updated! Go to **Rebalancing Alerts** to see new trade recommendations.")
                st.balloons()
        with col2:
            if st.button("🔄 Reset to Default (Option B)", use_container_width=True, key="cli_reset"):
                save_allocation_target(
                    dict(ALLOCATION_TARGET_DEFAULT),
                    source="reset",
                    notes="Reset to Option B defaults",
                )
                st.success("Reset to default Option B allocation.")
                st.rerun()

    # Raw response
    with st.expander("📄 Full AI Response"):
        st.markdown(review.get("raw", ""))


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: IMPORT AI REVIEW
# ═══════════════════════════════════════════════════════════════════════════════

def page_import_ai_review():
    """Import and apply AI review recommendations"""
    st.title("📥 Import AI Review")

    st.markdown("""
    Upload the **.md file** you received from Claude Web (or another AI).
    The app auto-detects **Standard** or **Three-Persona** format and parses accordingly.
    """)

    uploaded = st.file_uploader(
        "Upload AI Review (.md file)",
        type=["md", "txt", "markdown"],
        key="ai_review_upload",
    )

    if uploaded is None:
        st.info("👆 Upload an AI review markdown file to get started.")

        # Show review history
        data = load_data()
        history = data.get('allocation_history', [])
        if history:
            st.divider()
            st.subheader("📜 Allocation Change History")
            for entry in reversed(history[-10:]):
                date_str = entry['date'][:10]
                source = entry.get('source', 'unknown')
                with st.expander(f"{date_str} — via {source}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Previous**")
                        for asset, pct in entry.get('previous', {}).items():
                            st.write(f"  {asset}: {pct*100:.0f}%")
                    with col2:
                        st.write("**New**")
                        for asset, pct in entry.get('new', {}).items():
                            st.write(f"  {asset}: {pct*100:.0f}%")
                    if entry.get('notes'):
                        st.caption(entry['notes'])
        return

    # ── Parse the uploaded file ──
    content = uploaded.read().decode("utf-8")
    fmt = detect_review_format(content)

    if fmt == "persona":
        st.success("🎭 **Three-Persona format detected** — showing per-persona analysis + synthesis")
        persona_result = parse_persona_review_md(content)
        # Convert synthesis to standard format for the apply flow
        review = persona_review_to_standard(persona_result)
        _show_persona_tabs(persona_result)
    else:
        st.info("📄 Standard review format detected")
        review = parse_ai_review_md(content)
        persona_result = None

    # ── Show parsed results (synthesis / standard) ──
    st.divider()
    st.subheader("📊 Recommended Allocation Changes" + (" (from SYNTHESIS)" if persona_result else ""))

    # Build comparison table from review
    if review["allocation"]:
        comparison_rows = []
        valid_assets = {}
        for asset_name, info in review["allocation"].items():
            matched_key = normalize_asset_name(asset_name)
            if not matched_key or matched_key not in ALLOCATION_TARGET:
                continue

            current_target = ALLOCATION_TARGET[matched_key] * 100
            recommended = info["recommended"]
            change = recommended - current_target
            valid_assets[matched_key] = recommended

            comparison_rows.append({
                "Asset": matched_key,
                "Current Target %": f"{current_target:.0f}%",
                "Recommended %": f"{recommended:.0f}%",
                "Change": f"{change:+.0f}%",
                "Action": info.get("action", ""),
                "Reason": info.get("reason", ""),
            })

        if comparison_rows:
            df = pd.DataFrame(comparison_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            total_pct = sum(valid_assets.values())
            if abs(total_pct - 100) > 1:
                st.warning(f"⚠️ Recommended allocations sum to {total_pct:.0f}% (should be 100%). Adjust before applying.")
            else:
                st.success(f"✅ Allocations sum to {total_pct:.0f}%")
        else:
            st.warning("Could not match any asset names from the review. Check the file format.")
    else:
        st.warning("⚠️ No 'Recommended Allocation' table found. Make sure the file follows the template.")
        with st.expander("Show raw file content"):
            st.code(content[:3000])
        return

    # 2) CAGR Assessment
    if review["cagr"].get("recommended"):
        st.subheader("📈 CAGR Assessment")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current CAGR", f"{review['cagr']['current']}%")
        with col2:
            delta = review['cagr']['recommended'] - (review['cagr']['current'] or 0)
            st.metric("Recommended CAGR", f"{review['cagr']['recommended']}%",
                      delta=f"{delta:+.1f}%")
        if review['cagr']['reason']:
            st.caption(f"Reason: {review['cagr']['reason']}")

    # 3) Key Recommendations
    if review["recommendations"]:
        st.subheader("🎯 Key Recommendations")
        for rec in review["recommendations"]:
            # Handle both "[HIGH] text" and "HIGH: text" patterns
            rec_upper = rec.upper()
            if rec_upper.startswith("[HIGH]") or rec_upper.startswith("HIGH"):
                st.error(f"🔴 {rec}")
            elif rec_upper.startswith("[MEDIUM]") or rec_upper.startswith("MEDIUM"):
                st.warning(f"🟡 {rec}")
            else:
                st.info(f"🔵 {rec}")

    # 4) Market Outlook
    if review.get("market_outlook"):
        st.subheader("🌍 Market Outlook")
        st.markdown(review["market_outlook"])

    # ── Apply button ──
    if valid_assets:
        st.divider()
        st.subheader("✅ Apply Changes")

        st.write("Review the comparison above. Click below to update your allocation targets.")

        # Allow manual adjustment before applying
        with st.expander("🔧 Fine-tune before applying (optional)"):
            adjusted = {}
            cols = st.columns(2)
            for idx, (asset, pct) in enumerate(valid_assets.items()):
                with cols[idx % 2]:
                    adjusted[asset] = st.number_input(
                        f"{asset} %",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(pct),
                        step=1.0,
                        key=f"adjust_{asset}",
                    )

            adj_total = sum(adjusted.values())
            if abs(adj_total - 100) > 1:
                st.warning(f"Total: {adj_total:.0f}% — must be ~100%")
            else:
                st.success(f"Total: {adj_total:.0f}%")
                valid_assets = adjusted

        col1, col2 = st.columns(2)
        with col1:
            source_label = "persona_ai_review" if persona_result else "ai_review"
            if st.button("🚀 Apply Recommended Allocation", type="primary", use_container_width=True):
                new_target = {asset: pct / 100.0 for asset, pct in valid_assets.items()}
                notes = f"From AI review: {uploaded.name}"
                if persona_result:
                    personas_found = list(persona_result.get('personas', {}).keys())
                    notes += f" | Personas: {', '.join(personas_found)}"
                if review["recommendations"]:
                    notes += " | " + "; ".join(review["recommendations"][:3])
                save_allocation_target(new_target, source=source_label, notes=notes)
                save_ai_review(review, uploaded.name)
                st.success("✅ Allocation targets updated! Go to **Rebalancing Alerts** to see new trade recommendations.")
                st.balloons()
        with col2:
            if st.button("🔄 Reset to Default (Option B)", use_container_width=True):
                save_allocation_target(
                    dict(ALLOCATION_TARGET_DEFAULT),
                    source="reset",
                    notes="Reset to Option B defaults",
                )
                st.success("✅ Reset to default Option B allocation.")
                st.rerun()


def _show_persona_tabs(persona_result: dict):
    """Display per-persona analysis in tabs when a persona-format review is imported."""
    personas = persona_result.get("personas", {})
    if not personas:
        return

    persona_names = list(personas.keys())
    tab_labels = [f"🎭 {name}" for name in persona_names]

    tabs = st.tabs(tab_labels)
    for tab, name in zip(tabs, persona_names):
        pdata = personas[name]
        with tab:
            st.markdown(f"### {name}'s Analysis")

            # Allocation table
            if pdata.get("allocation"):
                alloc_rows = []
                for asset, info in pdata["allocation"].items():
                    current_target = ALLOCATION_TARGET.get(asset, 0) * 100
                    alloc_rows.append({
                        "Asset": asset,
                        "Current %": f"{current_target:.0f}%",
                        f"{name}'s %": f"{info['recommended']:.0f}%",
                        "Action": info.get("action", ""),
                        "Reason": info.get("reason", "")[:80],
                    })
                if alloc_rows:
                    st.dataframe(pd.DataFrame(alloc_rows), use_container_width=True, hide_index=True)

            # CAGR
            cagr = pdata.get("cagr", {})
            if cagr.get("growth") or cagr.get("blended"):
                cols = st.columns(3)
                with cols[0]:
                    if cagr.get("growth"):
                        st.metric("Growth CAGR", f"{cagr['growth']}%")
                with cols[1]:
                    if cagr.get("blended"):
                        st.metric("Blended CAGR", f"{cagr['blended']}%")
                with cols[2]:
                    if cagr.get("reason"):
                        st.caption(f"Reason: {cagr['reason']}")

            # Recommendations
            if pdata.get("recommendations"):
                st.markdown("**Key Recommendations:**")
                for rec in pdata["recommendations"]:
                    rec_upper = rec.upper()
                    if "[HIGH]" in rec_upper:
                        st.error(f"🔴 {rec}")
                    elif "[MEDIUM]" in rec_upper:
                        st.warning(f"🟡 {rec}")
                    else:
                        st.info(f"🔵 {rec}")

            # Discussion
            discussion = pdata.get("discussion", "")
            if discussion:
                with st.expander("💬 Discussion with other personas"):
                    st.markdown(discussion)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6: ORIGINAL DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def page_original_dashboard():
    """Original Dashboard — Portfolio overview, progress, and goal tracking"""
    st.title("📊 Dashboard")

    data = load_data()
    progress = calculate_progress(data)
    years_remaining, months_remaining, days_remaining = calculate_time_remaining()

    # ── Key Metrics Row ──────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "💰 Current Balance",
            f"{progress['current']/1_000_000:.1f}M KRW",
            help="Total portfolio value from holdings"
        )
    with col2:
        st.metric(
            "🎯 Target Goal",
            f"{progress['target_goal']/1_000_000:.0f}M KRW",
            delta=f"{progress['remaining_to_goal']/1_000_000:.1f}M remaining",
            delta_color="inverse"
        )
    with col3:
        prob, prob_label = get_success_probability(progress['current'])
        st.metric(
            "📈 Success Probability",
            f"{prob:.0f}%",
            delta=prob_label,
            delta_color="normal" if prob >= 80 else "inverse"
        )
    with col4:
        st.metric(
            "⏳ Time Remaining",
            f"{years_remaining:.1f} years",
            delta=f"{days_remaining} days",
            delta_color="off"
        )

    st.divider()

    # ── Progress Toward Goal ─────────────────────────────────────────────────
    st.subheader("🏁 Progress Toward Goal")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        # Progress bar using plotly gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=progress['progress_goal'],
            number={'suffix': '%', 'font': {'size': 48}},
            delta={'reference': 100, 'relative': False, 'suffix': '%'},
            gauge={
                'axis': {'range': [0, 100], 'ticksuffix': '%'},
                'bar': {'color': '#2196F3'},
                'steps': [
                    {'range': [0, 50], 'color': '#ffebee'},
                    {'range': [50, 75], 'color': '#fff3e0'},
                    {'range': [75, 100], 'color': '#e8f5e9'},
                ],
                'threshold': {
                    'line': {'color': '#4CAF50', 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            },
            title={'text': 'Progress to 400M KRW Goal'}
        ))
        fig_gauge.update_layout(height=300, margin=dict(t=60, b=20, l=40, r=40))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_right:
        # Minimum floor progress
        st.markdown("#### Floor Target (300M)")
        floor_pct = progress['progress_floor']
        st.progress(min(floor_pct / 100, 1.0), text=f"{floor_pct:.1f}%")

        st.markdown("#### Balance Breakdown")
        st.write(f"**Current:** ₩{progress['current']:,.0f}")
        st.write(f"**Goal:** ₩{progress['target_goal']:,.0f}")
        st.write(f"**Floor:** ₩{progress['floor']:,.0f}")
        st.write(f"**Gap to Goal:** ₩{progress['remaining_to_goal']:,.0f}")

    st.divider()

    # ── Portfolio Allocation (current) ───────────────────────────────────────
    st.subheader("🥧 Current Allocation vs Target")

    # Get current holdings values
    shares = data.get('shares', get_default_holdings())
    prices = fetch_etf_prices()

    holdings = {}
    for asset in ALLOCATION_TARGET.keys():
        num_shares = shares.get(asset, 0)
        price = prices.get(asset, {}).get('price', 0)
        if asset == 'Cash':
            holdings[asset] = num_shares
        else:
            holdings[asset] = num_shares * price

    portfolio_value = sum(holdings.values())

    if portfolio_value > 0:
        col_pie1, col_pie2 = st.columns(2)

        with col_pie1:
            current_pcts = {k: (v / portfolio_value) * 100 for k, v in holdings.items() if v > 0}
            fig_current = px.pie(
                names=list(current_pcts.keys()),
                values=list(current_pcts.values()),
                title="Current Allocation",
                hole=0.4
            )
            fig_current.update_layout(height=350, margin=dict(t=40, b=20))
            st.plotly_chart(fig_current, use_container_width=True)

        with col_pie2:
            target_pcts = {k: v * 100 for k, v in ALLOCATION_TARGET.items() if v > 0}
            fig_target = px.pie(
                names=list(target_pcts.keys()),
                values=list(target_pcts.values()),
                title="Target Allocation",
                hole=0.4
            )
            fig_target.update_layout(height=350, margin=dict(t=40, b=20))
            st.plotly_chart(fig_target, use_container_width=True)

        # Drift table
        drift_data = []
        for asset in ALLOCATION_TARGET.keys():
            current_pct = (holdings.get(asset, 0) / portfolio_value) * 100
            target_pct = ALLOCATION_TARGET[asset] * 100
            drift = current_pct - target_pct
            status = "✅" if abs(drift) <= 5 else "⚠️" if abs(drift) <= 10 else "🔴"
            drift_data.append({
                'Asset': asset,
                'Current %': f"{current_pct:.1f}%",
                'Target %': f"{target_pct:.1f}%",
                'Drift': f"{drift:+.1f}%",
                'Status': status
            })
        st.dataframe(pd.DataFrame(drift_data), use_container_width=True, hide_index=True)
    else:
        st.info("No holdings data available. Update your holdings in the Rebalancing Alerts page.")

    st.divider()

    # ── Projected Growth ─────────────────────────────────────────────────────
    st.subheader("📈 Projected Growth to Retirement")

    current_balance = progress['current'] if portfolio_value == 0 else portfolio_value
    monthly_contrib = IRP_CONFIG['base_monthly']
    target_cagr = IRP_CONFIG['target_cagr']
    months_left = int(years_remaining * 12)

    # Build month-by-month projection for multiple scenarios
    scenarios = {
        'Conservative (6%)': 6.0,
        'Target (10.2%)': target_cagr * 100,
        'Optimistic (15%)': 15.0,
    }

    projection_rows = []
    for month in range(0, months_left + 1, 3):  # quarterly points
        row = {'Month': month, 'Date': (datetime.now() + timedelta(days=month * 30.44)).strftime('%Y-%m')}
        for label, annual_rate in scenarios.items():
            from utils import calculate_future_value
            fv = calculate_future_value(current_balance, monthly_contrib, annual_rate, month)
            row[label] = fv
        projection_rows.append(row)

    df_proj = pd.DataFrame(projection_rows)

    fig_proj = go.Figure()
    colors = {'Conservative (6%)': '#FF9800', f'Target (10.2%)': '#2196F3', 'Optimistic (15%)': '#4CAF50'}
    for label in scenarios:
        fig_proj.add_trace(go.Scatter(
            x=df_proj['Date'], y=df_proj[label],
            mode='lines', name=label,
            line=dict(color=colors.get(label, '#999'), width=2)
        ))

    # Goal & floor lines
    fig_proj.add_hline(y=IRP_CONFIG['target_goal'], line_dash='dash', line_color='green',
                       annotation_text='Goal: 400M')
    fig_proj.add_hline(y=IRP_CONFIG['minimum_floor'], line_dash='dot', line_color='orange',
                       annotation_text='Floor: 300M')

    fig_proj.update_layout(
        title='Portfolio Growth Scenarios (with 600K/month contributions)',
        xaxis_title='Date', yaxis_title='Balance (KRW)',
        height=420, legend=dict(orientation='h', yanchor='bottom', y=1.02),
        yaxis=dict(tickformat=',.0f')
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    st.divider()

    # ── Milestones ───────────────────────────────────────────────────────────
    st.subheader("🏆 Milestones")

    milestones = [
        {'Milestone': '200M KRW', 'Value': 200_000_000},
        {'Milestone': '250M KRW', 'Value': 250_000_000},
        {'Milestone': '300M KRW (Floor)', 'Value': 300_000_000},
        {'Milestone': '350M KRW', 'Value': 350_000_000},
        {'Milestone': '400M KRW (Goal)', 'Value': 400_000_000},
    ]

    milestone_data = []
    for m in milestones:
        reached = current_balance >= m['Value']
        milestone_data.append({
            'Milestone': m['Milestone'],
            'Target': f"₩{m['Value']:,.0f}",
            'Status': '✅ Reached' if reached else '⬜ Pending',
            'Gap': f"₩{max(0, m['Value'] - current_balance):,.0f}" if not reached else '—'
        })

    st.dataframe(pd.DataFrame(milestone_data), use_container_width=True, hide_index=True)

    # ── Key Financial Metrics ────────────────────────────────────────────────
    st.subheader("📋 Key Financial Metrics")

    col_m1, col_m2, col_m3 = st.columns(3)

    projected_at_retirement = project_balance_to_retirement(current_balance)

    with col_m1:
        st.metric("Projected at Retirement", f"{projected_at_retirement/1_000_000:.1f}M KRW")
        required_monthly = (IRP_CONFIG['target_goal'] - current_balance) / max(months_left, 1)
        st.metric("Required Monthly Savings", f"{required_monthly/1_000_000:.2f}M KRW",
                  help="Monthly amount needed (without growth) to reach goal")

    with col_m2:
        from utils import calculate_cagr
        if years_remaining > 0:
            required_cagr = calculate_cagr(current_balance, IRP_CONFIG['target_goal'], years_remaining)
        else:
            required_cagr = 0
        st.metric("Required CAGR to Goal", f"{required_cagr:.1f}%")
        st.metric("Target CAGR", f"{IRP_CONFIG['target_cagr']*100:.1f}%")

    with col_m3:
        st.metric("Monthly Contribution", f"₩{IRP_CONFIG['base_monthly']:,.0f}")
        st.metric("Annual Bonus (Expected)", f"₩{IRP_CONFIG['expected_annual_bonus']:,.0f}")
        rsu_total_krw = IRP_CONFIG['rsu_value_usd'] * IRP_CONFIG['rsu_kwr_per_usd'] * IRP_CONFIG['rsu_after_tax_pct']
        st.metric("RSU Total (After Tax)", f"₩{rsu_total_krw:,.0f}")

    # ── Latest AI Review Summary ─────────────────────────────────────────────
    latest_review = get_latest_ai_review()
    if latest_review:
        st.divider()
        st.subheader("🤖 Latest AI Review")
        review_date = latest_review['date'][:10]
        review_file = latest_review.get('filename', 'Unknown')
        st.caption(f"From **{review_file}** on {review_date}")

        # CAGR
        cagr_info = latest_review.get('cagr', {})
        if cagr_info.get('recommended') or cagr_info.get('current'):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.metric("AI-Recommended CAGR", f"{cagr_info.get('recommended', '—')}%")
            with col_r2:
                reason = cagr_info.get('reason', '')
                if reason:
                    st.caption(f"Reason: {reason[:200]}")

        # Key Recommendations
        recs = latest_review.get('recommendations', [])
        if recs:
            with st.expander(f"🎯 Key Recommendations ({len(recs)} items)", expanded=False):
                for rec in recs:
                    rec_upper = rec.upper()
                    if '[HIGH]' in rec_upper or rec_upper.startswith('HIGH'):
                        st.error(f"🔴 {rec}")
                    elif '[MEDIUM]' in rec_upper or rec_upper.startswith('MEDIUM'):
                        st.warning(f"🟡 {rec}")
                    else:
                        st.info(f"🔵 {rec}")

        # Market Outlook
        outlook = latest_review.get('market_outlook', '')
        if outlook:
            with st.expander("🌍 Market Outlook", expanded=False):
                st.markdown(outlook)

        # Persona Discussions
        discussions = latest_review.get('persona_discussions', {})
        if discussions:
            with st.expander("🎭 Persona Discussions", expanded=False):
                for persona_name, discussion_text in discussions.items():
                    st.markdown(f"**{persona_name}**")
                    st.markdown(discussion_text[:500] + ('...' if len(discussion_text) > 500 else ''))
                    st.markdown('---')

    # ── Portfolio Snapshots ───────────────────────────────────────────────────
    st.divider()
    st.subheader("📸 Portfolio Snapshots")

    snapshots = get_portfolio_snapshots()

    # On-demand snapshot button
    snap_col1, snap_col2 = st.columns([3, 1])
    with snap_col1:
        snap_note = st.text_input(
            "Note (optional)",
            placeholder="e.g., Post-rebalancing, Pre-AI review",
            key="snapshot_note",
        )
    with snap_col2:
        st.write("")  # spacing
        if st.button("📸 Take Snapshot Now", type="primary", key="take_snapshot"):
            snap_shares = data.get('shares', get_default_holdings())
            snap_prices = fetch_etf_prices()
            snap_targets = dict(ALLOCATION_TARGET)
            snapshot = create_portfolio_snapshot(
                snap_shares, snap_prices, snap_targets,
                trigger="manual", note=snap_note,
            )
            save_portfolio_snapshot(snapshot)
            st.success(
                f"Snapshot saved — Total: ₩{snapshot['total_value']:,.0f} "
                f"({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            )
            st.rerun()

    # Portfolio History chart
    if snapshots:
        _render_portfolio_history_chart(snapshots)

        # Snapshot history table
        with st.expander(f"📋 Snapshot History ({len(snapshots)} records)", expanded=False):
            snap_rows = []
            for s in reversed(snapshots):
                snap_rows.append({
                    'Date': s['date'][:16].replace('T', ' '),
                    'Total Value': f"₩{s['total_value']:,.0f}",
                    'Trigger': '🔄 Auto' if s['trigger'] == 'auto' else '👤 Manual',
                    'Note': s.get('note', ''),
                })
            st.dataframe(pd.DataFrame(snap_rows), use_container_width=True, hide_index=True)
    else:
        st.info(
            "No snapshots yet. Click **Take Snapshot Now** to capture your first one. "
            "Auto-snapshots run on the first Korean business day on or after the 15th of each month."
        )


def _render_portfolio_history_chart(snapshots: list[dict]):
    """Render a Portfolio History line chart with goal line."""
    dates = [s['date'][:10] for s in snapshots]
    totals = [s['total_value'] for s in snapshots]
    triggers = [s.get('trigger', 'manual') for s in snapshots]
    hover_texts = []
    for s in snapshots:
        parts = [f"Total: ₩{s['total_value']:,.0f}"]
        for asset, val in s.get('values', {}).items():
            if val > 0:
                parts.append(f"  {asset}: ₩{val:,.0f}")
        if s.get('note'):
            parts.append(f"Note: {s['note']}")
        hover_texts.append("<br>".join(parts))

    fig = go.Figure()

    # Main line
    fig.add_trace(go.Scatter(
        x=dates, y=totals,
        mode='lines+markers',
        name='Portfolio Value',
        line=dict(color='#2196F3', width=3),
        hovertext=hover_texts,
        hoverinfo='text',
    ))

    # Color markers by trigger type
    auto_dates = [d for d, t in zip(dates, triggers) if t == 'auto']
    auto_vals = [v for v, t in zip(totals, triggers) if t == 'auto']
    manual_dates = [d for d, t in zip(dates, triggers) if t != 'auto']
    manual_vals = [v for v, t in zip(totals, triggers) if t != 'auto']

    if auto_dates:
        fig.add_trace(go.Scatter(
            x=auto_dates, y=auto_vals,
            mode='markers', name='Auto (mid-month)',
            marker=dict(color='#4CAF50', size=10, symbol='circle'),
            hoverinfo='skip',
        ))
    if manual_dates:
        fig.add_trace(go.Scatter(
            x=manual_dates, y=manual_vals,
            mode='markers', name='Manual (on-demand)',
            marker=dict(color='#FF9800', size=10, symbol='diamond'),
            hoverinfo='skip',
        ))

    # Goal & floor lines
    fig.add_hline(y=400_000_000, line_dash='dash', line_color='green',
                  annotation_text='Goal: 400M')
    fig.add_hline(y=300_000_000, line_dash='dot', line_color='orange',
                  annotation_text='Floor: 300M')

    fig.update_layout(
        title='Portfolio Value Over Time',
        xaxis_title='Date', yaxis_title='Portfolio Value (KRW)',
        height=420,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        yaxis=dict(tickformat=',.0f'),
    )
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 7: TRACK DEPOSITS
# ═══════════════════════════════════════════════════════════════════════════════

def page_track_deposits():
    """Track Deposits — Monthly contributions, bonuses, and deposit history"""
    st.title("💰 Track Deposits")

    data = load_data()
    transactions = data.get('transactions', [])

    # Filter deposit-related transactions (contributions & dividends)
    deposits = [t for t in transactions if t['type'] in ('contribution', 'dividend')]
    deposits.sort(key=lambda x: x['date'], reverse=True)

    contributions = [t for t in transactions if t['type'] == 'contribution']
    dividends = [t for t in transactions if t['type'] == 'dividend']

    # ── Summary Metrics ──────────────────────────────────────────────────────
    total_contributions = sum(t.get('price_per_share', 0) for t in contributions)
    total_dividends = sum(t.get('price_per_share', 0) for t in dividends)
    total_inflows = total_contributions + total_dividends

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📥 Total Contributions", f"₩{total_contributions:,.0f}")
    with col2:
        st.metric("📊 Total Dividends", f"₩{total_dividends:,.0f}")
    with col3:
        st.metric("💵 Total Inflows", f"₩{total_inflows:,.0f}")
    with col4:
        deposit_count = len(deposits)
        st.metric("📋 Total Records", f"{deposit_count}")

    st.divider()

    # ── Add New Deposit ──────────────────────────────────────────────────────
    st.subheader("➕ Record New Deposit")

    with st.expander("Click to add a new deposit", expanded=False):
        col_a, col_b, col_c = st.columns(3)

        DEPOSIT_TYPES = {
            'base': '📅 Monthly Base (600K)',
            'bonus': '🎁 Quarterly/Annual Bonus',
            'other': '📦 Other Deposit',
        }

        with col_a:
            deposit_type = st.selectbox(
                "Deposit Type",
                options=['base', 'bonus', 'other'],
                format_func=lambda x: DEPOSIT_TYPES[x],
                key="dep_type"
            )

        with col_b:
            default_amount = 600_000 if deposit_type == 'base' else (15_000_000 if deposit_type == 'bonus' else 100_000)
            deposit_amount = st.number_input(
                "Amount (KRW)",
                min_value=1,
                value=default_amount,
                step=100_000,
                key="dep_amount"
            )

        with col_c:
            deposit_date = st.date_input(
                "Deposit Date",
                value=datetime.now(),
                key="dep_date"
            )

        deposit_notes = st.text_input("Notes (optional)", key="dep_notes",
                                       placeholder=f"e.g., {deposit_type} deposit for {deposit_date.strftime('%Y-%m') if hasattr(deposit_date, 'strftime') else ''}")

        if st.button("💾 Record Deposit", type="primary"):
            note_text = deposit_notes or f"{DEPOSIT_TYPES[deposit_type]} deposit"
            new_trans = add_transaction(
                asset='Cash',
                trans_type='contribution',
                date_str=deposit_date.strftime('%Y-%m-%d'),
                shares=0,
                price_per_share=deposit_amount,
                notes=note_text
            )
            st.success(f"✅ Recorded ₩{deposit_amount:,.0f} deposit on {deposit_date}")
            st.rerun()

    st.divider()

    # ── Deposit History Table ────────────────────────────────────────────────
    st.subheader("📋 Deposit History")

    if deposits:
        tab_all, tab_contrib, tab_div = st.tabs(["All Inflows", "Contributions", "Dividends"])

        with tab_all:
            _render_deposit_table(deposits, "all")

        with tab_contrib:
            if contributions:
                _render_deposit_table(sorted(contributions, key=lambda x: x['date'], reverse=True), "contributions")
            else:
                st.info("No contributions recorded yet.")

        with tab_div:
            if dividends:
                _render_deposit_table(sorted(dividends, key=lambda x: x['date'], reverse=True), "dividends")
            else:
                st.info("No dividends recorded yet.")

        st.divider()

        # ── Monthly Trend Chart ──────────────────────────────────────────────
        st.subheader("📈 Monthly Inflow Trends")

        # Aggregate by month
        monthly_data = {}
        for t in deposits:
            month_key = t['date'][:7]  # YYYY-MM
            amount = t.get('price_per_share', 0)
            if month_key not in monthly_data:
                monthly_data[month_key] = {'Contributions': 0, 'Dividends': 0}
            if t['type'] == 'contribution':
                monthly_data[month_key]['Contributions'] += amount
            elif t['type'] == 'dividend':
                monthly_data[month_key]['Dividends'] += amount

        if monthly_data:
            months_sorted = sorted(monthly_data.keys())
            chart_rows = []
            cumulative = 0
            for m in months_sorted:
                contrib = monthly_data[m]['Contributions']
                div = monthly_data[m]['Dividends']
                cumulative += contrib + div
                chart_rows.append({
                    'Month': m,
                    'Contributions': contrib,
                    'Dividends': div,
                    'Total': contrib + div,
                    'Cumulative': cumulative,
                })

            df_chart = pd.DataFrame(chart_rows)

            # Bar chart: monthly breakdown
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=df_chart['Month'], y=df_chart['Contributions'],
                name='Contributions', marker_color='#2196F3'
            ))
            fig_bar.add_trace(go.Bar(
                x=df_chart['Month'], y=df_chart['Dividends'],
                name='Dividends', marker_color='#4CAF50'
            ))
            fig_bar.update_layout(
                title='Monthly Inflows by Type',
                xaxis_title='Month', yaxis_title='Amount (KRW)',
                barmode='stack', height=350,
                yaxis=dict(tickformat=',.0f')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Line chart: cumulative inflows
            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                x=df_chart['Month'], y=df_chart['Cumulative'],
                mode='lines+markers', name='Cumulative Inflows',
                line=dict(color='#FF9800', width=2),
                fill='tozeroy', fillcolor='rgba(255,152,0,0.1)'
            ))
            fig_cum.update_layout(
                title='Cumulative Inflows Over Time',
                xaxis_title='Month', yaxis_title='Cumulative (KRW)',
                height=300, yaxis=dict(tickformat=',.0f')
            )
            st.plotly_chart(fig_cum, use_container_width=True)

        st.divider()

        # ── Monthly Statistics ───────────────────────────────────────────────
        st.subheader("📊 Deposit Statistics")

        if contributions:
            contrib_amounts = [t.get('price_per_share', 0) for t in contributions]
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                st.metric("Avg Contribution", f"₩{sum(contrib_amounts)/len(contrib_amounts):,.0f}")
            with col_s2:
                st.metric("Max Contribution", f"₩{max(contrib_amounts):,.0f}")
            with col_s3:
                st.metric("Min Contribution", f"₩{min(contrib_amounts):,.0f}")
            with col_s4:
                # Expected vs actual
                months_active = len(set(t['date'][:7] for t in contributions))
                expected = months_active * IRP_CONFIG['base_monthly']
                pct = (total_contributions / expected * 100) if expected > 0 else 0
                st.metric("vs Expected", f"{pct:.0f}%",
                          delta=f"₩{total_contributions - expected:+,.0f}",
                          delta_color="normal" if total_contributions >= expected else "inverse")
    else:
        st.info("No deposits recorded yet. Use the form above or record contributions in the Rebalancing Alerts → Transaction History section.")

        st.markdown("""
        **Tip:** The recommended workflow is:
        1. Record your monthly 600K IRP deposit here
        2. Record quarterly bonuses when received
        3. Track dividends as they arrive in your account
        """)


def _render_deposit_table(items, table_key):
    """Helper to render a deposit/dividend table with delete capability"""
    TYPE_ICONS = {
        'contribution': '💰',
        'dividend': '📊',
    }
    table_data = []
    for t in items:
        icon = TYPE_ICONS.get(t['type'], '📦')
        table_data.append({
            'Date': t['date'],
            'Type': f"{icon} {t['type'].title()}",
            'Asset': t.get('asset', 'Cash'),
            'Amount (KRW)': f"₩{t.get('price_per_share', 0):,.0f}",
            'Notes': t.get('notes', ''),
            'ID': t['id'],
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df.drop(columns=['ID']), use_container_width=True, hide_index=True)

    # Delete functionality
    with st.expander(f"🗑️ Delete a record", expanded=False):
        if table_data:
            delete_options = {f"{t['Date']} | {t['Type']} | {t['Amount (KRW)']}": t['ID'] for t in table_data}
            selected = st.selectbox("Select record to delete", options=list(delete_options.keys()), key=f"del_{table_key}")
            if st.button("🗑️ Delete Selected", key=f"del_btn_{table_key}"):
                delete_transaction(delete_options[selected])
                st.success("✅ Record deleted.")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 8: RSU TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

# Default RSU schedule — 4 Keysight tranches (share-based)
# Total grant: ~194 shares at ~$157 grant price ≈ $30,458
DEFAULT_RSU_SCHEDULE = [
    {'tranche': 1, 'date': '2027-03', 'shares': 49, 'grant_price_usd': 157.0, 'vest_price_usd': None, 'vested': False, 'vested_date': None, 'notes': ''},
    {'tranche': 2, 'date': '2028-03', 'shares': 49, 'grant_price_usd': 157.0, 'vest_price_usd': None, 'vested': False, 'vested_date': None, 'notes': ''},
    {'tranche': 3, 'date': '2029-03', 'shares': 48, 'grant_price_usd': 157.0, 'vest_price_usd': None, 'vested': False, 'vested_date': None, 'notes': ''},
    {'tranche': 4, 'date': '2030-03', 'shares': 48, 'grant_price_usd': 157.0, 'vest_price_usd': None, 'vested': False, 'vested_date': None, 'notes': ''},
]


def _get_rsu_data(data):
    """Get RSU vesting data, initializing defaults if empty.
    Migrates old amount-only format to share-based format."""
    rsu_list = data.get('rsu_vesting', [])
    if not rsu_list:
        rsu_list = [dict(r) for r in DEFAULT_RSU_SCHEDULE]
        data['rsu_vesting'] = rsu_list
        save_data(data)
        return rsu_list

    # Migrate old format (amount_usd only) → share-based
    migrated = False
    for r in rsu_list:
        if 'shares' not in r:
            old_amount = r.get('amount_usd', 7614)
            est_price = 157.0
            r['shares'] = round(old_amount / est_price)
            r['grant_price_usd'] = est_price
            r['vest_price_usd'] = None
            r.setdefault('vested_date', None)
            migrated = True

    # Fix duplicate tranche numbers
    seen = set()
    for r in rsu_list:
        if r['tranche'] in seen:
            new_num = 1
            all_nums = {x['tranche'] for x in rsu_list}
            while new_num in all_nums or new_num in seen:
                new_num += 1
            r['tranche'] = new_num
            migrated = True
        seen.add(r['tranche'])

    if migrated:
        data['rsu_vesting'] = rsu_list
        save_data(data)

    return rsu_list


def _calc_rsu_value(r, exchange_rate, after_tax_pct):
    """Calculate values for a single RSU tranche."""
    shares = r.get('shares', 0)
    grant_price = r.get('grant_price_usd', 0)
    vest_price = r.get('vest_price_usd', None)

    effective_price = vest_price if (r['vested'] and vest_price) else grant_price
    gross_usd = shares * effective_price
    gross_krw = gross_usd * exchange_rate
    net_krw = gross_krw * after_tax_pct

    if r['vested'] and vest_price and grant_price > 0:
        gain_usd = (vest_price - grant_price) * shares
        gain_pct = ((vest_price / grant_price) - 1) * 100
    else:
        gain_usd = 0
        gain_pct = 0

    return {
        'shares': shares,
        'grant_price': grant_price,
        'vest_price': vest_price,
        'effective_price': effective_price,
        'gross_usd': gross_usd,
        'gross_krw': gross_krw,
        'net_krw': net_krw,
        'gain_usd': gain_usd,
        'gain_pct': gain_pct,
    }


def page_rsu_tracking():
    """RSU Tracking — Keysight RSU vesting schedule with share-based tracking"""
    st.title("📈 RSU Tracking")

    data = load_data()
    rsu_list = _get_rsu_data(data)

    # Exchange rate & tax config — load saved settings if available
    rsu_settings = data.get('rsu_settings', {})
    exchange_rate = rsu_settings.get('exchange_rate', IRP_CONFIG['rsu_kwr_per_usd'])
    tax_rate_saved = rsu_settings.get('tax_rate_pct', None)
    if tax_rate_saved is not None:
        after_tax_pct = (100 - tax_rate_saved) / 100
    else:
        after_tax_pct = IRP_CONFIG['rsu_after_tax_pct']
    tax_rate_pct = (1 - after_tax_pct) * 100

    # ── Summary Metrics ──────────────────────────────────────────────────────
    total_shares = sum(r.get('shares', 0) for r in rsu_list)
    vested_shares = sum(r.get('shares', 0) for r in rsu_list if r['vested'])
    unvested_shares = total_shares - vested_shares
    vested_count = sum(1 for r in rsu_list if r['vested'])

    total_vals = [_calc_rsu_value(r, exchange_rate, after_tax_pct) for r in rsu_list]
    total_gross_usd = sum(v['gross_usd'] for v in total_vals)
    vested_gross_usd = sum(v['gross_usd'] for v, r in zip(total_vals, rsu_list) if r['vested'])
    unvested_gross_usd = total_gross_usd - vested_gross_usd
    total_net_krw = sum(v['net_krw'] for v in total_vals)
    unvested_net_krw = sum(v['net_krw'] for v, r in zip(total_vals, rsu_list) if not r['vested'])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Shares", f"{total_shares:,}",
                  help=f"Estimated gross: ${total_gross_usd:,.0f}")
    with col2:
        st.metric("✅ Vested", f"{vested_shares:,} shares",
                  delta=f"{vested_count}/{len(rsu_list)} tranches")
    with col3:
        st.metric("⏳ Unvested", f"{unvested_shares:,} shares",
                  delta=f"{len(rsu_list) - vested_count} remaining", delta_color="off")
    with col4:
        st.metric("💰 After-Tax Total (KRW)", f"₩{total_net_krw:,.0f}",
                  help=f"Tax: {tax_rate_pct:.0f}% | Rate: ₩{exchange_rate:,}/USD")

    st.divider()

    # ── Vesting Schedule Table ───────────────────────────────────────────────
    st.subheader("📅 Vesting Schedule")
    st.caption(f"Exchange Rate: ₩{exchange_rate:,}/USD | Tax Rate: {tax_rate_pct:.0f}% | After-Tax: {after_tax_pct*100:.0f}%")

    schedule_data = []
    today = datetime.now()

    for r, val in zip(rsu_list, total_vals):
        vest_year, vest_month = int(r['date'][:4]), int(r['date'][5:7])
        vest_date = datetime(vest_year, vest_month, 1)
        days_until = (vest_date - today).days

        if r['vested']:
            time_status = '✅ Vested'
        elif days_until <= 0:
            time_status = '🟡 Ready to vest'
        elif days_until <= 90:
            time_status = f'🔶 {days_until}d away'
        else:
            months_away = days_until // 30
            time_status = f'⏳ {months_away}mo away'

        price_display = f"${val['vest_price']:,.2f}" if val['vest_price'] else f"${val['grant_price']:,.2f} (est)"
        gain_display = f"{val['gain_pct']:+.1f}%" if r['vested'] and val['vest_price'] else '—'

        schedule_data.append({
            'Tranche': f"#{r['tranche']}",
            'Vest Date': r['date'],
            'Shares': f"{val['shares']:,}",
            'Grant Price': f"${val['grant_price']:,.2f}",
            'Vest Price': price_display,
            'Gross (USD)': f"${val['gross_usd']:,.0f}",
            'Net (KRW)': f"₩{val['net_krw']:,.0f}",
            'Gain': gain_display,
            'Status': time_status,
        })

    st.dataframe(pd.DataFrame(schedule_data), use_container_width=True, hide_index=True)

    st.divider()

    # ── Manage RSU Tranches ──────────────────────────────────────────────────
    st.subheader("✏️ Manage RSU Tranches")

    tab_edit, tab_vest, tab_add, tab_delete, tab_settings = st.tabs([
        "📝 Edit Tranche", "✅ Vesting Status", "➕ Add Tranche", "🗑️ Delete Tranche", "⚙️ Settings"
    ])

    # --- Tab 1: Edit Tranche Details ---
    with tab_edit:
        if rsu_list:
            edit_options = {f"#{r['tranche']} — {r['date']} ({r.get('shares',0)} shares)": idx for idx, r in enumerate(rsu_list)}
            selected_edit = st.selectbox("Select tranche to edit", options=list(edit_options.keys()), key="rsu_edit_select")
            edit_idx = edit_options[selected_edit]
            editing = rsu_list[edit_idx]

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                new_date = st.text_input("Vest Date (YYYY-MM)", value=editing['date'], key="rsu_edit_date")
                new_shares = st.number_input("Number of Shares", value=editing.get('shares', 0),
                                              min_value=0, step=1, key="rsu_edit_shares")
            with col_e2:
                new_grant_price = st.number_input("Grant Price (USD)", value=float(editing.get('grant_price_usd', 0)),
                                                   min_value=0.0, step=1.0, format="%.2f", key="rsu_edit_grant_price")
                new_notes = st.text_input("Notes", value=editing.get('notes', ''), key="rsu_edit_notes")

            est_value = new_shares * new_grant_price
            st.caption(f"Estimated value at grant price: **${est_value:,.0f}** → ₩{est_value * exchange_rate * after_tax_pct:,.0f} (after tax)")

            if st.button("💾 Save Changes", key="rsu_save_edit", type="primary"):
                rsu_list[edit_idx]['date'] = new_date
                rsu_list[edit_idx]['shares'] = new_shares
                rsu_list[edit_idx]['grant_price_usd'] = new_grant_price
                rsu_list[edit_idx]['notes'] = new_notes
                data['rsu_vesting'] = rsu_list
                save_data(data)
                st.success(f"✅ Tranche #{editing['tranche']} updated!")
                st.rerun()
        else:
            st.info("No tranches to edit. Add one first.")

    # --- Tab 2: Vesting Status ---
    with tab_vest:
        unvested = [r for r in rsu_list if not r['vested']]
        vested = [r for r in rsu_list if r['vested']]

        if unvested:
            st.markdown("**Mark a tranche as vested** — enter the actual stock price at vesting:")
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                tranche_options = {f"#{r['tranche']} — {r['date']} ({r.get('shares',0)} shares @ ${r.get('grant_price_usd',0):,.2f})": r['tranche'] for r in unvested}
                selected_tranche = st.selectbox("Select tranche", options=list(tranche_options.keys()), key="rsu_vest_select")
            with col_v2:
                sel_num = tranche_options[selected_tranche]
                sel_r = next(r for r in rsu_list if r['tranche'] == sel_num)
                vest_price_input = st.number_input(
                    "Actual Vest Price (USD per share)",
                    value=float(sel_r.get('grant_price_usd', 157.0)),
                    min_value=0.01, step=1.0, format="%.2f",
                    key="rsu_vest_price",
                    help="The Keysight stock price on the vesting date"
                )

            preview_gross = sel_r.get('shares', 0) * vest_price_input
            preview_net_krw = preview_gross * exchange_rate * after_tax_pct
            preview_gain = ((vest_price_input / sel_r.get('grant_price_usd', 1)) - 1) * 100
            st.caption(
                f"Preview: {sel_r.get('shares',0)} shares × ${vest_price_input:,.2f} = "
                f"**${preview_gross:,.0f}** → ₩{preview_net_krw:,.0f} after tax | "
                f"Gain: {preview_gain:+.1f}% vs grant"
            )

            vest_notes = st.text_input("Notes (optional)", key="rsu_vest_notes",
                                      placeholder="e.g., Sold immediately, deployed to bonds")

            if st.button("✅ Mark as Vested", type="primary"):
                vest_date_str = datetime.now().strftime('%Y-%m-%d')
                shares = sel_r.get('shares', 0)
                gross_usd = shares * vest_price_input
                net_krw = gross_usd * exchange_rate * after_tax_pct
                note_text = (
                    f"RSU Tranche #{sel_num}: {shares} shares @ ${vest_price_input:,.2f} "
                    f"= ${gross_usd:,.0f} → ₩{net_krw:,.0f} after tax"
                )
                if vest_notes:
                    note_text += f" | {vest_notes}"
                # Record as contribution in Transaction History
                tx = add_transaction(
                    asset='Cash',
                    trans_type='contribution',
                    date_str=vest_date_str,
                    shares=0,
                    price_per_share=int(net_krw),
                    notes=note_text
                )
                for r in rsu_list:
                    if r['tranche'] == sel_num:
                        r['vested'] = True
                        r['vest_price_usd'] = vest_price_input
                        r['vested_date'] = vest_date_str
                        r['transaction_id'] = tx['id']
                        if vest_notes:
                            r['notes'] = vest_notes
                        break
                data['rsu_vesting'] = rsu_list
                save_data(data)
                st.success(f"✅ Tranche #{sel_num} vested at ${vest_price_input:,.2f}/share → ₩{net_krw:,.0f} recorded in Transaction History")
                st.rerun()
        else:
            st.success("🎉 All RSU tranches have been vested!")

        if vested:
            st.markdown("---")
            st.markdown("**Undo Vesting:**")
            undo_options = {f"#{r['tranche']} — {r['date']} ({r.get('shares',0)} shares, vested @ ${r.get('vest_price_usd',0):,.2f})": r['tranche'] for r in vested}
            selected_undo = st.selectbox("Select tranche to undo", options=list(undo_options.keys()), key="rsu_undo_select")
            if st.button("↩️ Mark as Unvested"):
                tranche_num = undo_options[selected_undo]
                tx_id = None
                for r in rsu_list:
                    if r['tranche'] == tranche_num:
                        tx_id = r.pop('transaction_id', None)
                        r['vested'] = False
                        r['vest_price_usd'] = None
                        r.pop('vested_date', None)
                        break
                if tx_id:
                    delete_transaction(tx_id)
                data['rsu_vesting'] = rsu_list
                save_data(data)
                msg = f"↩️ Tranche #{tranche_num} marked as unvested."
                if tx_id:
                    msg += " Transaction removed from history."
                st.success(msg)
                st.rerun()

    # --- Tab 3: Add New Tranche ---
    with tab_add:
        st.markdown("Add a new RSU grant tranche (e.g., new annual grant).")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            new_tranche_date = st.text_input("Vest Date (YYYY-MM)", value=f"{datetime.now().year + 1}-03", key="rsu_add_date")
            new_tranche_shares = st.number_input("Number of Shares", value=49, min_value=1, step=1, key="rsu_add_shares")
        with col_a2:
            new_tranche_grant = st.number_input("Grant Price (USD)", value=157.0, min_value=0.01, step=1.0, format="%.2f", key="rsu_add_grant")
            new_tranche_notes = st.text_input("Notes (optional)", key="rsu_add_notes", placeholder="e.g., 2026 annual grant")

        # Auto-generate unique Tranche #
        existing_nums = {r['tranche'] for r in rsu_list}
        auto_tranche = 1
        while auto_tranche in existing_nums:
            auto_tranche += 1

        est_val = new_tranche_shares * new_tranche_grant
        st.caption(
            f"Will be assigned **Tranche #{auto_tranche}** | "
            f"Estimated value: {new_tranche_shares} × ${new_tranche_grant:,.2f} = **${est_val:,.0f}** → ₩{est_val * exchange_rate * after_tax_pct:,.0f} after tax"
        )

        if st.button("➕ Add Tranche", type="primary", key="rsu_add_btn"):
            new_entry = {
                'tranche': auto_tranche,
                'date': new_tranche_date,
                'shares': new_tranche_shares,
                'grant_price_usd': new_tranche_grant,
                'vest_price_usd': None,
                'vested': False,
                'vested_date': None,
                'notes': new_tranche_notes,
            }
            rsu_list.append(new_entry)
            rsu_list.sort(key=lambda x: (x['date'], x['tranche']))
            data['rsu_vesting'] = rsu_list
            save_data(data)
            st.success(f"✅ Tranche #{auto_tranche} added ({new_tranche_shares} shares @ ${new_tranche_grant:,.2f})!")
            st.rerun()

    # --- Tab 4: Delete Tranche ---
    with tab_delete:
        if rsu_list:
            del_options = {f"#{r['tranche']} — {r['date']} ({r.get('shares',0)} sh) {'✅' if r['vested'] else '⏳'}": idx for idx, r in enumerate(rsu_list)}
            selected_del = st.selectbox("Select tranche to delete", options=list(del_options.keys()), key="rsu_del_select")
            st.warning("⚠️ This action cannot be undone.")
            if st.button("🗑️ Delete Tranche", key="rsu_del_btn"):
                del_idx = del_options[selected_del]
                removed = rsu_list.pop(del_idx)
                data['rsu_vesting'] = rsu_list
                save_data(data)
                st.success(f"✅ Tranche #{removed['tranche']} deleted.")
                st.rerun()
        else:
            st.info("No tranches to delete.")

    # --- Tab 5: Settings ---
    with tab_settings:
        st.markdown("Adjust exchange rate and tax assumptions for KRW calculations.")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            new_exchange_rate = st.number_input(
                "USD/KRW Exchange Rate",
                value=exchange_rate,
                min_value=800, max_value=2000, step=10,
                key="rsu_exchange_rate",
                help="Current rate used for USD → KRW conversion"
            )
        with col_s2:
            new_tax_pct = st.number_input(
                "Tax Rate (%)",
                value=int(tax_rate_pct),
                min_value=0, max_value=50, step=1,
                key="rsu_tax_rate",
                help="Withholding + income tax on RSU vesting"
            )

        if st.button("💾 Save Settings", key="rsu_save_settings"):
            IRP_CONFIG['rsu_kwr_per_usd'] = new_exchange_rate
            IRP_CONFIG['rsu_after_tax_pct'] = (100 - new_tax_pct) / 100
            # Persist to data file
            data['rsu_settings'] = {
                'exchange_rate': new_exchange_rate,
                'tax_rate_pct': new_tax_pct,
            }
            save_data(data)
            st.success(f"✅ Settings saved: ₩{new_exchange_rate:,}/USD, {new_tax_pct}% tax")
            st.rerun()

    st.divider()

    # ── Vesting Timeline ────────────────────────────────────────────────────
    st.subheader("📊 Vesting Timeline")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # Bar chart: shares per tranche with vested/unvested color
        timeline_rows = []
        sorted_rsu = sorted(rsu_list, key=lambda x: x['date'])
        sorted_vals = [_calc_rsu_value(r, exchange_rate, after_tax_pct) for r in sorted_rsu]
        for r, val in zip(sorted_rsu, sorted_vals):
            timeline_rows.append({
                'Date': r['date'],
                'Shares': val['shares'],
                'Value (USD)': val['gross_usd'],
                'Status': 'Vested' if r['vested'] else 'Unvested',
            })

        df_timeline = pd.DataFrame(timeline_rows)
        colors_map = {'Vested': '#4CAF50', 'Unvested': '#90CAF9'}
        fig_bar = go.Figure()
        for status in ['Vested', 'Unvested']:
            mask = df_timeline['Status'] == status
            if mask.any():
                fig_bar.add_trace(go.Bar(
                    x=df_timeline.loc[mask, 'Date'],
                    y=df_timeline.loc[mask, 'Shares'],
                    name=status,
                    marker_color=colors_map[status],
                    text=df_timeline.loc[mask, 'Shares'],
                    textposition='auto'
                ))
        fig_bar.update_layout(
            title='Shares per Tranche',
            xaxis_title='Vesting Date', yaxis_title='Shares',
            height=320, barmode='stack',
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        # Progress donut
        fig_pie = go.Figure(go.Pie(
            labels=['Vested', 'Unvested'],
            values=[vested_shares, unvested_shares],
            marker=dict(colors=['#4CAF50', '#90CAF9']),
            hole=0.5,
            textinfo='label+percent+value',
            texttemplate='%{label}<br>%{value} shares<br>%{percent}'
        ))
        fig_pie.update_layout(title='Vesting Progress', height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # ── IRP Impact Summary ──────────────────────────────────────────────────
    st.subheader("🎯 Impact on IRP Goal")

    progress = calculate_progress(data)
    gap = progress['remaining_to_goal']

    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        st.metric("Current Gap to Goal", f"₩{gap:,.0f}")
    with col_i2:
        coverage_pct = (unvested_net_krw / gap * 100) if gap > 0 else 100
        st.metric("RSU Coverage of Gap", f"{coverage_pct:.1f}%",
                  help=f"Unvested RSU (₩{unvested_net_krw:,.0f}) as % of remaining gap")
    with col_i3:
        gap_after_rsu = max(0, gap - unvested_net_krw)
        st.metric("Gap After All RSU", f"₩{gap_after_rsu:,.0f}",
                  delta=f"₩{-unvested_net_krw:,.0f} from RSU", delta_color="normal")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 9: PROJECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def page_projections():
    """Projections — Year-by-year forecast, scenario analysis, what-if simulator"""
    st.title("🔮 Projections")

    data = load_data()
    progress = calculate_progress(data)
    current_balance = progress['current']
    years_remaining, _, days_remaining = calculate_time_remaining()
    months_left = max(1, int(years_remaining * 12))

    # ── User Controls ────────────────────────────────────────────────────────
    st.subheader("⚙️ Projection Parameters")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        monthly_contrib = st.number_input(
            "Monthly Contribution (KRW)",
            value=IRP_CONFIG['base_monthly'],
            min_value=0, step=100_000, format="%d",
            key="proj_monthly"
        )
    with col_p2:
        annual_bonus = st.number_input(
            "Annual Bonus (KRW)",
            value=IRP_CONFIG['expected_annual_bonus'],
            min_value=0, step=1_000_000, format="%d",
            key="proj_bonus"
        )
    with col_p3:
        # Use AI-recommended CAGR if available, otherwise fall back to config
        _latest = get_latest_ai_review()
        _default_cagr = IRP_CONFIG['target_cagr'] * 100
        if _latest and _latest.get('cagr', {}).get('recommended'):
            _default_cagr = float(_latest['cagr']['recommended'])
        custom_rate = st.number_input(
            "Expected Return (%)",
            value=_default_cagr,
            min_value=0.0, max_value=30.0, step=0.5, format="%.1f",
            key="proj_rate",
            help="Pre-filled with latest AI-recommended CAGR" if _latest else None,
        )
    with col_p4:
        rsu_include = st.checkbox("Include RSU (after-tax)", value=True, key="proj_rsu")

    # RSU lump sums by year
    rsu_by_year = {}
    if rsu_include:
        rsu_settings = data.get('rsu_settings', {})
        ex_rate = rsu_settings.get('exchange_rate', IRP_CONFIG['rsu_kwr_per_usd'])
        tax_saved = rsu_settings.get('tax_rate_pct', None)
        atax = (100 - tax_saved) / 100 if tax_saved is not None else IRP_CONFIG['rsu_after_tax_pct']
        for r in data.get('rsu_vesting', []):
            if not r.get('vested', False):
                yr = int(r['date'][:4])
                shares = r.get('shares', 0)
                price = r.get('grant_price_usd', 0)
                net_krw = shares * price * ex_rate * atax
                rsu_by_year[yr] = rsu_by_year.get(yr, 0) + net_krw

    st.divider()

    # ── Year-by-Year Projection Table ────────────────────────────────────────
    st.subheader("📅 Year-by-Year Projection")

    from utils import calculate_future_value

    rows = []
    balance = current_balance
    today = datetime.now()

    for year in range(today.year, 2031):
        if year == today.year:
            months_this_year = 12 - today.month
        else:
            months_this_year = min(12, int((datetime(2030, 12, 31) - datetime(year, 1, 1)).days / 30.44))
            months_this_year = max(0, min(12, months_this_year))

        # Monthly contributions
        contrib = monthly_contrib * months_this_year
        # Annual bonus (added once per year, except partial first year)
        bonus = annual_bonus if year > today.year else int(annual_bonus * months_this_year / 12)
        # RSU vesting
        rsu_amt = rsu_by_year.get(year, 0)
        # Investment growth (compound monthly)
        monthly_rate = custom_rate / 12 / 100
        growth_start = balance
        for _ in range(months_this_year):
            balance = balance * (1 + monthly_rate) + monthly_contrib
        # Add bonus & RSU at year end
        balance += bonus + rsu_amt
        investment_return = balance - growth_start - contrib - bonus - rsu_amt

        rows.append({
            'Year': year,
            'Start Balance': growth_start,
            'Contributions': contrib,
            'Bonus': bonus,
            'RSU (After-Tax)': rsu_amt,
            'Investment Return': investment_return,
            'End Balance': balance,
            'vs Goal': balance - IRP_CONFIG['target_goal'],
        })

    df_year = pd.DataFrame(rows)

    # Format for display
    display_rows = []
    for _, r in df_year.iterrows():
        display_rows.append({
            'Year': int(r['Year']),
            'Start': f"₩{r['Start Balance']:,.0f}",
            'Contributions': f"₩{r['Contributions']:,.0f}",
            'Bonus': f"₩{r['Bonus']:,.0f}",
            'RSU': f"₩{r['RSU (After-Tax)']:,.0f}" if r['RSU (After-Tax)'] > 0 else '—',
            'Return': f"₩{r['Investment Return']:,.0f}",
            'End Balance': f"₩{r['End Balance']:,.0f}",
            'vs Goal': f"₩{r['vs Goal']:,.0f}",
        })
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

    final_balance = balance
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.metric("Projected Final (2030)", f"₩{final_balance:,.0f}")
    with col_r2:
        delta = final_balance - IRP_CONFIG['target_goal']
        st.metric("vs Goal (400M)", f"₩{delta:,.0f}",
                  delta="Surplus" if delta >= 0 else "Shortfall",
                  delta_color="normal" if delta >= 0 else "inverse")
    with col_r3:
        if current_balance > 0:
            implied_cagr = ((final_balance / current_balance) ** (1 / max(0.1, years_remaining)) - 1) * 100
            st.metric("Implied CAGR", f"{implied_cagr:.1f}%")

    st.divider()

    # ── Multi-Scenario Chart ─────────────────────────────────────────────────
    st.subheader("📊 Scenario Comparison")

    scenarios = {
        'Conservative (6%)': 6.0,
        f'Custom ({custom_rate:.1f}%)': custom_rate,
        'Optimistic (15%)': 15.0,
    }

    projection_rows = []
    for month in range(0, months_left + 1, 1):
        date_label = (today + timedelta(days=month * 30.44)).strftime('%Y-%m')
        row = {'Month': month, 'Date': date_label}
        for label, rate in scenarios.items():
            bal = current_balance
            m_rate = rate / 12 / 100
            for m in range(month):
                # Add RSU lump sums at appropriate month
                rsu_this = 0
                month_date = today + timedelta(days=m * 30.44)
                if rsu_include and month_date.month == 3:  # approximate RSU at March
                    rsu_this = rsu_by_year.get(month_date.year, 0) / 12
                bal = bal * (1 + m_rate) + monthly_contrib + rsu_this
            row[label] = bal
        projection_rows.append(row)

    df_proj = pd.DataFrame(projection_rows)

    fig = go.Figure()
    colors = ['#FF9800', '#2196F3', '#4CAF50']
    for i, label in enumerate(scenarios):
        fig.add_trace(go.Scatter(
            x=df_proj['Date'], y=df_proj[label],
            mode='lines', name=label,
            line=dict(color=colors[i], width=2)
        ))

    fig.add_hline(y=IRP_CONFIG['target_goal'], line_dash='dash', line_color='green',
                  annotation_text='Goal: 400M')
    fig.add_hline(y=IRP_CONFIG['minimum_floor'], line_dash='dot', line_color='orange',
                  annotation_text='Floor: 300M')

    fig.update_layout(
        title='Portfolio Growth Scenarios',
        xaxis_title='Date', yaxis_title='Balance (KRW)',
        height=450, legend=dict(orientation='h', yanchor='bottom', y=1.02),
        yaxis=dict(tickformat=',.0f')
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Contribution Breakdown ───────────────────────────────────────────────
    st.subheader("💰 Contribution Sources Breakdown")

    total_contrib = sum(r['Contributions'] for _, r in df_year.iterrows())
    total_bonus = sum(r['Bonus'] for _, r in df_year.iterrows())
    total_rsu = sum(r['RSU (After-Tax)'] for _, r in df_year.iterrows())
    total_return = sum(r['Investment Return'] for _, r in df_year.iterrows())

    sources = {
        'Monthly Contributions': total_contrib,
        'Annual Bonus': total_bonus,
        'RSU (After-Tax)': total_rsu,
        'Investment Returns': total_return,
    }
    # Filter out zero values
    sources = {k: v for k, v in sources.items() if v > 0}

    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        fig_pie = go.Figure(go.Pie(
            labels=list(sources.keys()),
            values=list(sources.values()),
            hole=0.45,
            textinfo='label+percent',
            marker=dict(colors=['#2196F3', '#FF9800', '#9C27B0', '#4CAF50'])
        ))
        fig_pie.update_layout(title='Growth Sources (to 2030)', height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_c2:
        for label, val in sources.items():
            pct = val / sum(sources.values()) * 100
            st.metric(label, f"₩{val:,.0f}", delta=f"{pct:.1f}%", delta_color="off")

    st.divider()

    # ── Required Return Calculator ───────────────────────────────────────────
    st.subheader("🎯 Required Return to Reach Goal")

    # Binary search for required annual return
    target = IRP_CONFIG['target_goal']
    low, high = 0.0, 50.0
    for _ in range(50):
        mid = (low + high) / 2
        bal = current_balance
        m_rate = mid / 12 / 100
        for mo in range(months_left):
            bal = bal * (1 + m_rate) + monthly_contrib
        # Add all bonuses and RSU
        bal += annual_bonus * years_remaining + sum(rsu_by_year.values())
        if bal < target:
            low = mid
        else:
            high = mid
    required_return = (low + high) / 2

    col_rr1, col_rr2, col_rr3 = st.columns(3)
    with col_rr1:
        st.metric("Required Annual Return", f"{required_return:.1f}%",
                  help="Minimum CAGR needed to reach 400M by 2030")
    with col_rr2:
        buffer = custom_rate - required_return
        st.metric("Buffer vs Your Rate", f"{buffer:+.1f}%",
                  delta="Comfortable" if buffer > 2 else ("Tight" if buffer > 0 else "At risk"),
                  delta_color="normal" if buffer > 0 else "inverse")
    with col_rr3:
        # Months to goal at custom rate
        bal = current_balance
        m_rate = custom_rate / 12 / 100
        months_to_goal = None
        for m in range(1, 120):
            bal = bal * (1 + m_rate) + monthly_contrib
            if m % 12 == 0:
                bal += annual_bonus + rsu_by_year.get(today.year + m // 12, 0)
            if bal >= target:
                months_to_goal = m
                break
        if months_to_goal:
            goal_date = (today + timedelta(days=months_to_goal * 30.44)).strftime('%Y-%m')
            st.metric("Est. Goal Date", goal_date,
                      delta=f"{months_to_goal} months", delta_color="off")
        else:
            st.metric("Est. Goal Date", "Beyond 10 years")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 10: REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

def page_reports():
    """Reports — Portfolio summary, allocation analysis, contribution history"""
    st.title("📋 Reports")

    data = load_data()
    progress = calculate_progress(data)
    current_balance = progress['current']
    years_remaining, _, _ = calculate_time_remaining()

    # ── Portfolio Summary ────────────────────────────────────────────────────
    st.subheader("📊 Portfolio Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Balance", f"₩{current_balance:,.0f}")
    with col2:
        st.metric("Target Goal", f"₩{IRP_CONFIG['target_goal']:,.0f}")
    with col3:
        st.metric("Progress", f"{progress['progress_goal']:.1f}%")
    with col4:
        st.metric("Time Remaining", f"{years_remaining:.1f} years")

    st.divider()

    # ── Allocation Report ────────────────────────────────────────────────────
    st.subheader("🎯 Current Allocation vs Target")

    holdings = data.get('holdings_values', data.get('holdings', {}))
    if not holdings or all(v == 0 for v in holdings.values()):
        holdings = get_default_holdings_values()
    total_portfolio = sum(holdings.values()) if holdings else 0
    target_alloc = ALLOCATION_TARGET

    if total_portfolio > 0:
        alloc_rows = []
        for etf, amount in sorted(holdings.items(), key=lambda x: x[1], reverse=True):
            actual_pct = (amount / total_portfolio) * 100
            target_pct = target_alloc.get(etf, 0) * 100
            diff = actual_pct - target_pct
            alloc_rows.append({
                'ETF': etf,
                'Value (KRW)': f"₩{amount:,.0f}",
                'Actual %': f"{actual_pct:.1f}%",
                'Target %': f"{target_pct:.1f}%",
                'Deviation': f"{diff:+.1f}%",
                'Status': '✅' if abs(diff) <= 3 else ('⚠️' if abs(diff) <= 5 else '🔴'),
            })
        st.dataframe(pd.DataFrame(alloc_rows), use_container_width=True, hide_index=True)

        # Allocation pie charts side by side
        col_pie1, col_pie2 = st.columns(2)
        with col_pie1:
            fig_actual = go.Figure(go.Pie(
                labels=list(holdings.keys()),
                values=list(holdings.values()),
                hole=0.4, textinfo='label+percent'
            ))
            fig_actual.update_layout(title='Current Allocation', height=350)
            st.plotly_chart(fig_actual, use_container_width=True)

        with col_pie2:
            target_vals = {k: v * total_portfolio for k, v in target_alloc.items()}
            fig_target = go.Figure(go.Pie(
                labels=list(target_vals.keys()),
                values=list(target_vals.values()),
                hole=0.4, textinfo='label+percent'
            ))
            fig_target.update_layout(title='Target Allocation', height=350)
            st.plotly_chart(fig_target, use_container_width=True)
    else:
        st.info("No holdings data available.")

    st.divider()

    # ── Contribution History Summary ─────────────────────────────────────────
    st.subheader("💰 Contribution Summary")

    transactions = data.get('transactions', [])
    contributions = [t for t in transactions if t.get('type') == 'contribution']
    dividends = [t for t in transactions if t.get('type') == 'dividend']

    col_h1, col_h2, col_h3, col_h4 = st.columns(4)
    total_contribs = sum(t.get('price_per_share', t.get('amount', 0)) for t in contributions)
    total_divs = sum(t.get('price_per_share', t.get('amount', 0)) for t in dividends)
    with col_h1:
        st.metric("Total Contributions", f"₩{total_contribs:,.0f}")
    with col_h2:
        st.metric("# of Deposits", f"{len(contributions)}")
    with col_h3:
        st.metric("Total Dividends", f"₩{total_divs:,.0f}")
    with col_h4:
        avg = total_contribs / len(contributions) if contributions else 0
        st.metric("Avg Deposit", f"₩{avg:,.0f}")

    # Monthly contribution bar chart
    if contributions:
        monthly_sums = {}
        for t in contributions:
            month_key = t.get('date', '')[:7]
            amount = t.get('price_per_share', t.get('amount', 0))
            monthly_sums[month_key] = monthly_sums.get(month_key, 0) + amount

        months_sorted = sorted(monthly_sums.keys())
        fig_contrib = go.Figure(go.Bar(
            x=months_sorted,
            y=[monthly_sums[m] for m in months_sorted],
            marker_color='#2196F3',
            text=[f"₩{monthly_sums[m]:,.0f}" for m in months_sorted],
            textposition='auto'
        ))
        fig_contrib.update_layout(
            title='Monthly Contributions',
            xaxis_title='Month', yaxis_title='Amount (KRW)',
            height=300, yaxis=dict(tickformat=',.0f')
        )
        st.plotly_chart(fig_contrib, use_container_width=True)

    st.divider()

    # ── RSU Summary ──────────────────────────────────────────────────────────
    st.subheader("📈 RSU Summary")

    rsu_list = data.get('rsu_vesting', [])
    rsu_settings = data.get('rsu_settings', {})
    ex_rate = rsu_settings.get('exchange_rate', IRP_CONFIG['rsu_kwr_per_usd'])
    tax_saved = rsu_settings.get('tax_rate_pct', None)
    atax = (100 - tax_saved) / 100 if tax_saved is not None else IRP_CONFIG['rsu_after_tax_pct']

    if rsu_list:
        total_shares = sum(r.get('shares', 0) for r in rsu_list)
        vested_shares = sum(r.get('shares', 0) for r in rsu_list if r.get('vested'))
        unvested_shares = total_shares - vested_shares
        total_value = sum(
            r.get('shares', 0) * (r.get('vest_price_usd') or r.get('grant_price_usd', 0)) * ex_rate * atax
            for r in rsu_list
        )

        col_rsu1, col_rsu2, col_rsu3, col_rsu4 = st.columns(4)
        with col_rsu1:
            st.metric("Total Shares", f"{total_shares:,}")
        with col_rsu2:
            st.metric("Vested", f"{vested_shares:,}")
        with col_rsu3:
            st.metric("Unvested", f"{unvested_shares:,}")
        with col_rsu4:
            st.metric("Total Value (Net KRW)", f"₩{total_value:,.0f}")
    else:
        st.info("No RSU data available.")

    st.divider()

    # ── Key Parameters ───────────────────────────────────────────────────────
    st.subheader("📝 Plan Parameters")

    params = {
        'Initial Balance': f"₩{IRP_CONFIG['initial_balance']:,.0f}",
        'Target Goal': f"₩{IRP_CONFIG['target_goal']:,.0f}",
        'Minimum Floor': f"₩{IRP_CONFIG['minimum_floor']:,.0f}",
        'Target CAGR': f"{IRP_CONFIG['target_cagr'] * 100:.1f}%",
        'Monthly Contribution': f"₩{IRP_CONFIG['base_monthly']:,.0f}",
        'Annual Bonus': f"₩{IRP_CONFIG['expected_annual_bonus']:,.0f}",
        'Start Date': IRP_CONFIG['start_date'].strftime('%Y-%m-%d'),
        'Retirement Date': IRP_CONFIG['retirement_date'].strftime('%Y-%m-%d'),
    }
    df_params = pd.DataFrame(list(params.items()), columns=['Parameter', 'Value'])
    st.dataframe(df_params, use_container_width=True, hide_index=True)

    st.divider()

    # ── AI Review History ────────────────────────────────────────────────────
    st.subheader("🤖 AI Review History")
    ai_reviews = data.get('ai_reviews', [])
    if ai_reviews:
        for review in reversed(ai_reviews[-5:]):
            review_date = review['date'][:10]
            filename = review.get('filename', 'Unknown')
            cagr_info = review.get('cagr', {})
            cagr_str = f"CAGR: {cagr_info.get('recommended', '?')}%" if cagr_info.get('recommended') else ''
            recs = review.get('recommendations', [])
            num_recs = len(recs)

            with st.expander(f"{review_date} — {filename} {f'| {cagr_str}' if cagr_str else ''} | {num_recs} recommendations"):
                # Allocation changes
                alloc = review.get('allocation', {})
                if alloc:
                    alloc_rows = []
                    for asset, info in alloc.items():
                        if isinstance(info, dict):
                            alloc_rows.append({
                                'Asset': asset,
                                'Recommended %': f"{info.get('recommended', '?')}%",
                                'Action': info.get('action', ''),
                                'Reason': info.get('reason', '')[:80],
                            })
                    if alloc_rows:
                        st.dataframe(pd.DataFrame(alloc_rows), use_container_width=True, hide_index=True)

                # CAGR
                if cagr_info.get('reason'):
                    st.caption(f"CAGR Reason: {cagr_info['reason'][:200]}")

                # Recommendations
                if recs:
                    st.markdown("**Key Recommendations:**")
                    for rec in recs:
                        rec_upper = rec.upper()
                        if '[HIGH]' in rec_upper or rec_upper.startswith('HIGH'):
                            st.error(f"🔴 {rec}")
                        elif '[MEDIUM]' in rec_upper or rec_upper.startswith('MEDIUM'):
                            st.warning(f"🟡 {rec}")
                        else:
                            st.info(f"🔵 {rec}")

                # Market Outlook
                outlook = review.get('market_outlook', '')
                if outlook:
                    st.markdown("**Market Outlook:**")
                    st.markdown(outlook)

                # Persona Discussions
                discussions = review.get('persona_discussions', {})
                if discussions:
                    st.markdown("**Persona Discussions:**")
                    for pname, ptext in discussions.items():
                        st.markdown(f"*{pname}:*")
                        st.markdown(ptext[:600] + ('...' if len(ptext) > 600 else ''))
    else:
        st.info("No AI reviews imported yet. Use the **Import AI Review** page to add one.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP (All Original Pages + 3 New Pages)
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main application"""
    
    # Load custom allocation targets (if any)
    load_allocation_target()

    # Auto-snapshot: mid-month on first Korean business day >= 15th
    check_and_run_auto_snapshot()

    # Sidebar navigation
    st.sidebar.title("IRP Tracker Pro")
    
    pages = [
        "Market Dashboard",
        "Rebalancing Alerts",
        "Plan Revision",
        "Export for AI Review",
        "Import AI Review",
        "Original Dashboard",
        "Track Deposits",
        "RSU Tracking",
        "Projections",
        "Reports"
    ]
    
    page = st.sidebar.radio(
        "Navigation",
        pages,
        label_visibility="collapsed"
    )
    
    st.sidebar.divider()
    
    # Sidebar info
    st.sidebar.markdown("### Strategy Summary")
    st.sidebar.write("**Target:** 400M KRW")
    st.sidebar.write("**Retirement:** Dec 31, 2030")
    st.sidebar.write("**Strategy:** Option B (Moderate)")
    
    data = load_data()
    progress = calculate_progress(data)
    
    st.sidebar.markdown("### Current Status")
    st.sidebar.metric("Balance", f"{progress['current']/1_000_000:.1f}M KRW")
    st.sidebar.metric("Progress", f"{progress['progress_goal']:.1f}%")
    
    years, _, _ = calculate_time_remaining()
    st.sidebar.metric("Time Left", f"{years:.1f} years")
    
    # Render selected page
    if page == "Market Dashboard":
        page_market_dashboard()
    elif page == "Rebalancing Alerts":
        page_rebalancing_alerts()
    elif page == "Plan Revision":
        page_plan_revision()
    elif page == "Export for AI Review":
        page_export_snapshot()
    elif page == "Import AI Review":
        page_import_ai_review()
    elif page == "Original Dashboard":
        page_original_dashboard()
    elif page == "Track Deposits":
        page_track_deposits()
    elif page == "RSU Tracking":
        page_rsu_tracking()
    elif page == "Projections":
        page_projections()
    elif page == "Reports":
        page_reports()
    else:
        st.write("# Page Not Found")
        st.info("This page is not available.")

if __name__ == "__main__":
    main()
