"""
Utility functions for IRP Retirement Tracker
"""

import math
import re
from datetime import datetime, timedelta, date
from typing import Union
from zoneinfo import ZoneInfo
import holidays


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


# Korea timezone and holidays for settlement calculation
KR_TZ = ZoneInfo("Asia/Seoul")
KR_HOLIDAYS = holidays.KR()


def get_settlement_date(trade_date=None):
    """Calculate T+2 settlement date excluding weekends and Korean holidays.
    
    Args:
        trade_date: date or datetime object. Defaults to today (Korea time).
    
    Returns:
        dict with settlement_date, trade_date, business_days_away, and description.
    """
    if trade_date is None:
        trade_date = datetime.now(KR_TZ).date()
    elif isinstance(trade_date, datetime):
        trade_date = trade_date.date()

    business_days = 0
    current = trade_date
    while business_days < 2:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in KR_HOLIDAYS:
            business_days += 1

    # Check if settlement day itself is a holiday (shouldn't be, but safety check)
    settle_date = current

    # Build description
    cal_days = (settle_date - trade_date).days
    holiday_names = []
    check = trade_date
    while check <= settle_date:
        if check in KR_HOLIDAYS:
            holiday_names.append(f"{check.strftime('%m/%d')} {KR_HOLIDAYS.get(check)}")
        check += timedelta(days=1)

    desc_parts = [f"T+2 business days = {cal_days} calendar days"]
    if cal_days > 2:
        reasons = []
        # Count weekends
        d = trade_date
        weekends = 0
        while d <= settle_date:
            if d.weekday() >= 5:
                weekends += 1
            d += timedelta(days=1)
        if weekends:
            reasons.append(f"{weekends} weekend day(s)")
        if holiday_names:
            reasons.append(f"holiday(s): {', '.join(holiday_names)}")
        if reasons:
            desc_parts.append(f"skipped {' + '.join(reasons)}")

    return {
        "trade_date": trade_date,
        "settlement_date": settle_date,
        "business_days": 2,
        "calendar_days": cal_days,
        "description": " — ".join(desc_parts),
        "holidays_in_range": holiday_names,
    }


def format_date(date_str: str, format_out: str = "%Y년 %m월 %d일") -> str:
    """Format date string to Korean format"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime(format_out)
    except ValueError:
        return date_str


def generate_portfolio_snapshot(
    holdings: dict,
    prices: dict,
    allocation_target: dict,
    portfolio_value: float,
    progress: dict,
    years_remaining: float,
    transactions: list,
    gains_losses: dict,
    total_gain: float,
    total_gain_pct: float,
    etf_config: dict,
) -> str:
    """Generate a markdown snapshot of the portfolio for AI review.

    Returns a ready-to-paste markdown string.
    """
    today = datetime.now().strftime("%B %d, %Y")
    months_left = int(years_remaining * 12)

    lines = [
        f"# IRP Portfolio Snapshot — {today}",
        "",
        "## Goal",
        f"- Target: {progress['target_goal']/1e6:.0f}M KRW by Dec 2030 ({months_left} months remaining)",
        f"- Current portfolio value: {portfolio_value/1e6:.1f}M KRW ({progress['progress_goal']:.1f}% of goal)",
        f"- Remaining to goal: {progress['remaining_to_goal']/1e6:.1f}M KRW",
        "- Monthly contribution: 600K KRW + quarterly bonuses",
        "- RSU: 4 tranches (2027-2030), ~6.6M KRW each after-tax",
        "- Strategy: Option B (Moderate), 10.2% target CAGR",
        "",
        "## Current Holdings",
        "| Asset | Shares | Price (KRW) | Value (KRW) | Alloc % | Target % | Drift |",
        "|-------|--------|-------------|-------------|---------|----------|-------|",
    ]

    for asset in allocation_target:
        target_pct = allocation_target[asset] * 100
        price = prices.get(asset, {}).get('price', 0)
        value = holdings.get(asset, 0)
        alloc_pct = (value / portfolio_value * 100) if portfolio_value > 0 else 0
        drift = alloc_pct - target_pct

        if asset == 'Cash':
            lines.append(
                f"| {asset} | - | - | {value:,.0f} | {alloc_pct:.1f}% | {target_pct:.0f}% | {drift:+.1f}% |"
            )
        else:
            shares = int(value / price) if price > 0 else 0
            lines.append(
                f"| {asset} | {shares:,} | {price:,.0f} | {value:,.0f} | {alloc_pct:.1f}% | {target_pct:.0f}% | {drift:+.1f}% |"
            )

    lines.append(f"| **TOTAL** | | | **{portfolio_value:,.0f}** | **100%** | **100%** | |")

    # Drift alerts
    lines.append("")
    lines.append("## Drift Alerts (>5%)")
    alerts_found = False
    for asset in allocation_target:
        target_pct = allocation_target[asset] * 100
        value = holdings.get(asset, 0)
        alloc_pct = (value / portfolio_value * 100) if portfolio_value > 0 else 0
        drift = alloc_pct - target_pct
        if abs(drift) > 5:
            direction = "Overweight" if drift > 0 else "Underweight"
            priority = "HIGH" if abs(drift) > 10 else "MEDIUM"
            lines.append(f"- **{asset}**: {direction} by {abs(drift):.1f}% ({priority} priority)")
            alerts_found = True
    if not alerts_found:
        lines.append("- All assets within 5% of target. No immediate rebalancing needed.")

    # Cost basis / gains
    lines.append("")
    lines.append("## Unrealized Gains/Losses (FIFO)")
    lines.append("| Asset | Avg Cost | Current Price | Unrealized Gain | Gain % |")
    lines.append("|-------|----------|---------------|-----------------|--------|")
    for asset, gl in gains_losses.items():
        lines.append(
            f"| {asset} | {gl['avg_cost_basis']:,.0f} | {gl['current_price']:,.0f} "
            f"| {gl['unrealized_gain']:+,.0f} | {gl['gain_pct']:+.1f}% |"
        )
    lines.append(f"| **TOTAL** | | | **{total_gain:+,.0f}** | **{total_gain_pct:+.1f}%** |")

    # Recent transactions
    lines.append("")
    lines.append("## Recent Transactions (last 90 days)")
    cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    recent = [t for t in transactions if t.get('date', '') >= cutoff]
    if recent:
        for t in recent[:15]:
            lines.append(
                f"- {t['date']}: {t['type'].upper()} {t['shares']} shares {t['asset']} "
                f"@ {t['price_per_share']:,.0f} KRW"
            )
    else:
        lines.append("- No transactions in the last 90 days.")

    # ETF reference
    lines.append("")
    lines.append("## ETF Reference")
    lines.append("| Asset | Korean Name | Ticker | Type |")
    lines.append("|-------|-------------|--------|------|")
    for asset, cfg in etf_config.items():
        if cfg.get('code'):
            lines.append(f"| {asset} | {cfg.get('name_kr', '')} | {cfg['code']} | {cfg.get('type', '')} |")

    # Questions
    lines.append("")
    lines.append("## Questions for AI Review")
    lines.append("1. Given current market conditions, should I adjust my target allocation?")
    lines.append("2. Any assets I should trim or add to?")
    lines.append("3. Is the 10.2% CAGR assumption still realistic for the remaining period?")
    lines.append("4. Should I adjust my bond/cash/equity ratio given the current interest rate and macro environment?")
    lines.append("5. Are there any KODEX ETFs on Samsung Fund (samsungfund.com) I should consider swapping to?")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Response Format Instructions")
    lines.append("")
    lines.append("I will import your response as a .md file into my portfolio app.")
    lines.append("**You MUST follow this EXACT format** — my parser depends on it.")
    lines.append("")
    lines.append("### Rules")
    lines.append("1. Use the EXACT section headers shown below: `## Recommended Allocation`, `## CAGR Assessment`, `## Key Recommendations`, `## Market Outlook`")
    lines.append("2. Use the EXACT 8 asset names shown in the table (spelled exactly as written)")
    lines.append("3. All `Recommended %` values MUST be plain numbers (e.g., 28, 14, 10) and sum to exactly 100")
    lines.append("4. In the CAGR section, use plain text without bold/italic markers (no ** or _ wrapping)")
    lines.append("5. List recommendations as bullet points starting with `- HIGH:`, `- MEDIUM:`, or `- LOW:`")
    lines.append("6. You may add free-form analysis AFTER the Market Outlook section, but keep the 4 sections above in this exact order")
    lines.append("7. Do NOT wrap the response in a code fence — output it as plain markdown")
    lines.append("")
    lines.append("### Template (copy this structure exactly)")
    lines.append("")
    lines.append("# IRP AI Review — [Date]")
    lines.append("")
    lines.append("## Recommended Allocation")
    lines.append("")
    lines.append("| Asset | Current % | Recommended % | Action | Reason |")
    lines.append("|-------|-----------|---------------|--------|--------|")
    lines.append("| AI Core Power | [current] | [new] | Hold/Trim/Add | [reason] |")
    lines.append("| AI Tech TOP10 | [current] | [new] | Hold/Trim/Add | [reason] |")
    lines.append("| Dividend Stocks | [current] | [new] | Hold/Trim/Add | [reason] |")
    lines.append("| Consumer Staples | [current] | [new] | Hold/Trim/Add | [reason] |")
    lines.append("| Treasury Bonds | [current] | [new] | Hold/Trim/Add | [reason] |")
    lines.append("| Gold | [current] | [new] | Hold/Trim/Add | [reason] |")
    lines.append("| Japan TOPIX | [current] | [new] | Hold/Trim/Add | [reason] |")
    lines.append("| Cash | [current] | [new] | Hold/Trim/Add | [reason] |")
    lines.append("")
    lines.append("## CAGR Assessment")
    lines.append("")
    lines.append("- Current assumption: [current]%")
    lines.append("- Recommended: [new]%")
    lines.append("- Reason: [explanation]")
    lines.append("")
    lines.append("## Key Recommendations")
    lines.append("")
    lines.append("- HIGH: [most urgent action]")
    lines.append("- HIGH: [second urgent action]")
    lines.append("- MEDIUM: [important but not urgent]")
    lines.append("- LOW: [nice to have]")
    lines.append("")
    lines.append("## Market Outlook")
    lines.append("")
    lines.append("[Your analysis of current market conditions and impact on this portfolio]")
    lines.append("")

    return "\n".join(lines)


def parse_ai_review_md(content: str) -> dict:
    """Parse a structured AI review markdown file.

    Returns a dict with:
      - allocation: {asset_name: {current: float, recommended: float, action: str, reason: str}}
      - cagr: {current: float, recommended: float, reason: str}
      - recommendations: [str]
      - market_outlook: str
      - raw: str (full text)
    """
    result = {
        "allocation": {},
        "cagr": {"current": None, "recommended": None, "reason": ""},
        "recommendations": [],
        "market_outlook": "",
        "raw": content,
    }

    # ── Parse Recommended Allocation table ──
    alloc_pattern = re.compile(
        r"##\s*Recommended Allocation\s*\n"
        r"\|.*\|\s*\n"        # header row
        r"\|[-| ]+\|\s*\n"   # separator row
        r"((?:\|.*\|\s*\n?)+)",  # data rows
        re.IGNORECASE,
    )
    match = alloc_pattern.search(content)
    if match:
        rows_text = match.group(1).strip()
        for row in rows_text.split("\n"):
            cells = [c.strip() for c in row.split("|")]
            cells = [c for c in cells if c]  # remove empty from leading/trailing |
            if len(cells) >= 3:
                asset = cells[0].strip()
                try:
                    current_pct = float(re.sub(r"[^0-9.]", "", cells[1]))
                except (ValueError, IndexError):
                    current_pct = 0
                try:
                    recommended_pct = float(re.sub(r"[^0-9.]", "", cells[2]))
                except (ValueError, IndexError):
                    recommended_pct = 0
                action = cells[3].strip() if len(cells) > 3 else ""
                reason = cells[4].strip() if len(cells) > 4 else ""
                result["allocation"][asset] = {
                    "current": current_pct,
                    "recommended": recommended_pct,
                    "action": action,
                    "reason": reason,
                }

    # ── Parse CAGR Assessment ──
    cagr_section = re.search(
        r"##\s*CAGR Assessment\s*\n(.*?)(?=\n## [^#]|\Z)", content, re.DOTALL | re.IGNORECASE
    )
    if cagr_section:
        block = cagr_section.group(1)
        cur = re.search(r"\*{0,2}Current\s*assumption\*{0,2}\s*:?\s*\*{0,2}\s*([\d.]+)", block, re.IGNORECASE)
        rec = re.search(r"\*{0,2}Recommended\*{0,2}\s*:?\s*\*{0,2}\s*([\d.]+)", block, re.IGNORECASE)
        rea = re.search(r"\*{0,2}Reason\*{0,2}\s*:?\s*\*{0,2}\s*(.+)", block, re.IGNORECASE)
        if cur:
            result["cagr"]["current"] = float(cur.group(1))
        if rec:
            result["cagr"]["recommended"] = float(rec.group(1))
        if rea:
            result["cagr"]["reason"] = rea.group(1).strip()

    # ── Parse Key Recommendations ──
    rec_section = re.search(
        r"##\s*Key Recommendations\s*\n(.*?)(?=\n## [^#]|\Z)", content, re.DOTALL | re.IGNORECASE
    )
    if rec_section:
        current_priority = ""
        for line in rec_section.group(1).strip().split("\n"):
            line = line.strip()
            # Track priority sections (### HIGH Priority, ### MEDIUM Priority, etc.)
            priority_match = re.match(r"###\s*(HIGH|MEDIUM|LOW)\s*Priority", line, re.IGNORECASE)
            if priority_match:
                current_priority = priority_match.group(1).upper()
                continue
            # Format A: "- HIGH: description" (template format)
            bullet_priority = re.match(r"-\s*(HIGH|MEDIUM|LOW)\s*:\s*(.+)", line, re.IGNORECASE)
            if bullet_priority:
                prio = bullet_priority.group(1).upper()
                desc = bullet_priority.group(2).strip()
                result["recommendations"].append(f"[{prio}] {desc}")
                continue
            # Format B: numbered bold headers like **1. Rebalance AI Core Power...**
            numbered = re.match(r"\*{2}(\d+\.\s*.+?)\*{2}", line)
            if numbered:
                prefix = f"[{current_priority}] " if current_priority else ""
                result["recommendations"].append(prefix + numbered.group(1).strip())
                continue
            # Fallback: plain bullet points (only if nothing matched so far)
            if line.startswith("- ") and not result["recommendations"]:
                result["recommendations"].append(line.lstrip("- "))

    # ── Parse Market Outlook ──
    outlook_section = re.search(
        r"##\s*Market Outlook\s*\n(.*?)(?=\n## [^#]|\Z)", content, re.DOTALL | re.IGNORECASE
    )
    if outlook_section:
        result["market_outlook"] = outlook_section.group(1).strip()

    return result
