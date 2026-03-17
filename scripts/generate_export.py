"""Standalone script to generate persona export markdown for comparison testing."""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from datetime import datetime
from utils import generate_persona_export


def calculate_time_remaining():
    """Calculate time until Dec 2030."""
    target = datetime(2030, 12, 31)
    days = (target - datetime.now()).days
    years = days / 365.25
    months = (days % 365) / 30.44
    return years, months, days

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def main(output_path: str) -> None:
    """Generate persona export and save to output_path."""
    with open(DATA_DIR / "irp_tracker_data.json", encoding="utf-8") as f:
        data = json.load(f)
    with open(DATA_DIR / "etf_config.json", encoding="utf-8") as f:
        etf_config = json.load(f)

    # Allocation target from data
    allocation_target = data.get("allocation_target", {})

    # Shares & holdings
    shares = data.get("shares", {})

    # Use mock prices (no live API needed for comparison)
    # Just use last known prices from transactions or fallback
    prices = {}
    for asset in allocation_target:
        if asset == "Cash":
            prices[asset] = {"price": 1}
        else:
            # Use a fallback price of 10000 if not available
            prices[asset] = {"price": 10000}

    # Try to get better prices from recent transactions
    for t in reversed(data.get("transactions", [])):
        asset = t.get("asset", "")
        if asset in prices and asset != "Cash":
            prices[asset] = {"price": t.get("price_per_share", 10000)}

    # Calculate holdings
    holdings = {}
    for asset in allocation_target:
        num_shares = shares.get(asset, 0)
        holdings[asset] = num_shares if asset == "Cash" else num_shares * prices.get(asset, {}).get("price", 0)

    portfolio_value = sum(holdings.values())

    # Progress
    target_goal = data.get("target_amount", 400_000_000)
    progress = {
        "target_goal": target_goal,
        "progress_goal": (portfolio_value / target_goal * 100) if target_goal > 0 else 0,
        "remaining_to_goal": target_goal - portfolio_value,
    }

    years_remaining, _, _ = calculate_time_remaining()

    # Gains/losses (simplified from transaction history)
    gains_losses = {}
    total_cost = 0
    total_current = 0
    for asset in allocation_target:
        if asset == "Cash":
            continue
        # Calculate average cost from transactions
        buy_shares = 0
        buy_cost = 0
        for t in data.get("transactions", []):
            if t.get("asset") == asset and t.get("type") == "buy":
                buy_shares += t.get("shares", 0)
                buy_cost += t.get("shares", 0) * t.get("price_per_share", 0)
        avg_cost = (buy_cost / buy_shares) if buy_shares > 0 else 0
        current_price = prices.get(asset, {}).get("price", 0)
        current_value = holdings.get(asset, 0)
        cost_basis = avg_cost * shares.get(asset, 0)
        unrealized = current_value - cost_basis

        gains_losses[asset] = {
            "avg_cost_basis": avg_cost,
            "current_price": current_price,
            "unrealized_gain": unrealized,
            "gain_pct": (unrealized / cost_basis * 100) if cost_basis > 0 else 0,
        }
        total_cost += cost_basis
        total_current += current_value

    total_gain = total_current - total_cost
    total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0

    transactions = data.get("transactions", [])

    result = generate_persona_export(
        holdings=holdings,
        prices=prices,
        allocation_target=allocation_target,
        portfolio_value=portfolio_value,
        progress=progress,
        years_remaining=years_remaining,
        transactions=transactions,
        gains_losses=gains_losses,
        total_gain=total_gain,
        total_gain_pct=total_gain_pct,
        etf_config=etf_config,
    )

    Path(output_path).write_text(result, encoding="utf-8")
    print(f"Saved to {output_path} ({len(result)} chars, {result.count(chr(10))} lines)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "export_output.md"
    main(out)
