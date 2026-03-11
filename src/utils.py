"""
Utility functions for IRP Retirement Tracker
"""

import math
from datetime import datetime
from typing import Union


def format_currency(amount: Union[int, float], currency: str = "KRW") -> str:
    """Format amount as currency string"""
    if currency == "KRW":
        if amount >= 100_000_000:  # 억 (100 million)
            return f"{amount / 100_000_000:.1f}억 원"
        elif amount >= 10_000:  # 만 (10 thousand)
            return f"{amount / 10_000:,.0f}만 원"
        else:
            return f"{amount:,.0f}원"
    elif currency == "USD":
        return f"${amount:,.2f}"
    return str(amount)


def calculate_progress(current: float, target: float) -> float:
    """Calculate progress percentage toward target"""
    if target <= 0:
        return 0.0
    return min((current / target) * 100, 100.0)


def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """Calculate Compound Annual Growth Rate"""
    if start_value <= 0 or years <= 0:
        return 0.0
    return ((end_value / start_value) ** (1 / years) - 1) * 100


def calculate_future_value(
    present_value: float,
    monthly_contribution: float,
    annual_rate: float,
    months: int
) -> float:
    """Calculate future value with monthly contributions"""
    monthly_rate = annual_rate / 12 / 100
    
    # Future value of lump sum
    fv_lump = present_value * ((1 + monthly_rate) ** months)
    
    # Future value of annuity (monthly contributions)
    if monthly_rate > 0:
        fv_annuity = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        fv_annuity = monthly_contribution * months
    
    return fv_lump + fv_annuity


def months_until_target(target_date: str) -> int:
    """Calculate months until target date"""
    target = datetime.strptime(target_date, "%Y-%m-%d")
    today = datetime.now()
    
    months = (target.year - today.year) * 12 + (target.month - today.month)
    return max(0, months)


def convert_usd_to_krw(usd_amount: float, exchange_rate: float = 1350) -> float:
    """Convert USD to KRW"""
    return usd_amount * exchange_rate


def calculate_after_tax_rsu(gross_usd: float, tax_rate: float = 0.22) -> float:
    """Calculate after-tax RSU value (default 22% tax)"""
    return gross_usd * (1 - tax_rate)


def get_allocation_drift(current: dict, target: dict) -> dict:
    """Calculate allocation drift from target"""
    drift = {}
    for key in target:
        current_val = current.get(key, 0)
        target_val = target[key]
        drift[key] = {
            "current": current_val,
            "target": target_val,
            "drift": (current_val - target_val) * 100,
            "needs_rebalance": abs(current_val - target_val) > 0.05
        }
    return drift


def krw_to_shares(amount_krw: float, price_per_share: float, action: str = "sell") -> int:
    """Convert KRW amount to number of whole shares.
    
    For 'sell': rounds down (floor) to avoid over-selling.
    For 'buy': rounds up (ceil) to ensure reaching target allocation.
    """
    if price_per_share <= 0:
        return 0
    exact = amount_krw / price_per_share
    if action == "sell":
        return math.floor(exact)
    else:
        return math.ceil(exact)


def format_date(date_str: str, format_out: str = "%Y년 %m월 %d일") -> str:
    """Format date string to Korean format"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime(format_out)
    except ValueError:
        return date_str
