"""
Market Data Module — Hybrid approach with yfinance + caching + fallback.

Fetches real market indices and USD/KRW exchange rate via yfinance.
Uses Streamlit's @st.cache_data for time-based caching (default 10 min).
Falls back to last-known cached values or mock data if API fails.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# INDEX CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MARKET_INDICES = {
    "S&P 500":       {"symbol": "^GSPC",  "category": "US Equity",  "description": "US Large Cap Benchmark"},
    "NASDAQ":        {"symbol": "^IXIC",  "category": "US Equity",  "description": "US Tech-Heavy Composite"},
    "Dow Jones":     {"symbol": "^DJI",   "category": "US Equity",  "description": "US Blue Chip 30"},
    "KOSPI":         {"symbol": "^KS11",  "category": "Korea",      "description": "Korea Composite Index"},
    "KOSDAQ":        {"symbol": "^KQ11",  "category": "Korea",      "description": "Korea Growth/Tech Index"},
    "US 10Y Yield":  {"symbol": "^TNX",   "category": "Bond",       "description": "US 10-Year Treasury Yield (%)"},
    "VIX":           {"symbol": "^VIX",   "category": "Volatility", "description": "CBOE Volatility Index (Fear Gauge)"},
    "USD/KRW":       {"symbol": "KRW=X",  "category": "Currency",   "description": "US Dollar to Korean Won"},
}

# Mock fallback data (used only when API completely fails)
_MOCK_FALLBACK = {
    "S&P 500":      {"price": 5850.0, "change_pct": 0.0, "prev_close": 5850.0},
    "NASDAQ":       {"price": 18650.0, "change_pct": 0.0, "prev_close": 18650.0},
    "Dow Jones":    {"price": 42000.0, "change_pct": 0.0, "prev_close": 42000.0},
    "KOSPI":        {"price": 2850.0, "change_pct": 0.0, "prev_close": 2850.0},
    "KOSDAQ":       {"price": 900.0, "change_pct": 0.0, "prev_close": 900.0},
    "US 10Y Yield": {"price": 4.25, "change_pct": 0.0, "prev_close": 4.25},
    "VIX":          {"price": 18.0, "change_pct": 0.0, "prev_close": 18.0},
    "USD/KRW":      {"price": 1350.0, "change_pct": 0.0, "prev_close": 1350.0},
}


# ═══════════════════════════════════════════════════════════════════════════════
# CORE FETCH FUNCTION (cached by Streamlit)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600, show_spinner="Fetching live market data...")
def fetch_market_data():
    """
    Fetch real market data from Yahoo Finance via yfinance.
    Cached for 10 minutes (ttl=600). Returns dict with index data + metadata.
    """
    symbols = [cfg["symbol"] for cfg in MARKET_INDICES.values()]
    result = {
        "timestamp": datetime.now(),
        "status": "live",
        "data": {},
    }

    try:
        # Batch download — single network call for all tickers
        df = yf.download(symbols, period="5d", group_by="ticker", threads=True, progress=False)

        for name, cfg in MARKET_INDICES.items():
            sym = cfg["symbol"]
            try:
                closes = df[sym]["Close"].dropna()
                if len(closes) >= 2:
                    last_price = float(closes.iloc[-1])
                    prev_price = float(closes.iloc[-2])
                    change_pct = ((last_price - prev_price) / prev_price) * 100
                    change_amt = last_price - prev_price
                elif len(closes) == 1:
                    last_price = float(closes.iloc[-1])
                    prev_price = last_price
                    change_pct = 0.0
                    change_amt = 0.0
                else:
                    raise ValueError(f"No data for {sym}")

                result["data"][name] = {
                    "price": last_price,
                    "prev_close": prev_price,
                    "change_pct": round(change_pct, 2),
                    "change_amt": round(change_amt, 2),
                    "category": cfg["category"],
                    "description": cfg["description"],
                    "source": "yahoo_finance",
                }
            except Exception as e:
                logger.warning(f"Failed to parse {name} ({sym}): {e}")
                fb = _MOCK_FALLBACK.get(name, {"price": 0, "change_pct": 0, "prev_close": 0})
                result["data"][name] = {
                    "price": fb["price"],
                    "prev_close": fb["prev_close"],
                    "change_pct": fb["change_pct"],
                    "change_amt": 0.0,
                    "category": cfg["category"],
                    "description": cfg["description"],
                    "source": "fallback",
                }

    except Exception as e:
        logger.error(f"yfinance batch download failed: {e}")
        result["status"] = "offline"
        for name, cfg in MARKET_INDICES.items():
            fb = _MOCK_FALLBACK[name]
            result["data"][name] = {
                "price": fb["price"],
                "prev_close": fb["prev_close"],
                "change_pct": fb["change_pct"],
                "change_amt": 0.0,
                "category": cfg["category"],
                "description": cfg["description"],
                "source": "mock",
            }

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE ACCESSORS
# ═══════════════════════════════════════════════════════════════════════════════

def get_usd_krw(market_data=None):
    """Return the current USD/KRW exchange rate from market data."""
    if market_data is None:
        market_data = fetch_market_data()
    return market_data["data"].get("USD/KRW", {}).get("price", 1350.0)


def get_index_price(name, market_data=None):
    """Return the current price of a named index."""
    if market_data is None:
        market_data = fetch_market_data()
    return market_data["data"].get(name, {}).get("price")
