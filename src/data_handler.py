"""
Data Handler - Load and save retirement tracker data
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Data file path
DATA_FILE = Path(__file__).parent.parent / "data" / "irp_tracker_data.json"

DEFAULT_DATA = {
    "current_balance": 175_700_000,
    "target_goal": 400_000_000,
    "retirement_date": "2030-12-31",
    "monthly_contribution": 600_000,
    "deposits": [],
    "rsu_vestings": [
        {"tranche": 1, "date": "2027-03", "amount_usd": 7614, "vested": False},
        {"tranche": 2, "date": "2028-03", "amount_usd": 7614, "vested": False},
        {"tranche": 3, "date": "2029-03", "amount_usd": 7614, "vested": False},
        {"tranche": 4, "date": "2030-03", "amount_usd": 7614, "vested": False},
    ],
    "portfolio": {
        "growth_equities": 0.42,
        "defensive_equities": 0.18,
        "bonds": 0.11,
        "cash": 0.28
    },
    "created_at": None,
    "updated_at": None
}


def load_data() -> dict:
    """Load data from JSON file, create default if not exists"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return _create_default_data()
    else:
        return _create_default_data()


def save_data(data: dict) -> bool:
    """Save data to JSON file"""
    try:
        # Ensure data directory exists
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        data["updated_at"] = datetime.now().isoformat()
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


def _create_default_data() -> dict:
    """Create and save default data"""
    data = DEFAULT_DATA.copy()
    data["created_at"] = datetime.now().isoformat()
    data["updated_at"] = datetime.now().isoformat()
    save_data(data)
    return data


def add_deposit(amount: int, deposit_type: str = "base", date: str = None) -> bool:
    """Add a new deposit entry"""
    data = load_data()
    
    deposit = {
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "amount": amount,
        "type": deposit_type,  # "base", "bonus", "other"
        "recorded_at": datetime.now().isoformat()
    }
    
    data["deposits"].append(deposit)
    return save_data(data)


def update_balance(new_balance: int) -> bool:
    """Update current portfolio balance"""
    data = load_data()
    data["current_balance"] = new_balance
    return save_data(data)


def mark_rsu_vested(tranche: int) -> bool:
    """Mark an RSU tranche as vested"""
    data = load_data()
    
    for rsu in data["rsu_vestings"]:
        if rsu["tranche"] == tranche:
            rsu["vested"] = True
            break
    
    return save_data(data)


def get_deposit_history() -> list:
    """Get all deposit history"""
    data = load_data()
    return data.get("deposits", [])


def get_rsu_status() -> list:
    """Get RSU vesting status"""
    data = load_data()
    return data.get("rsu_vestings", [])
