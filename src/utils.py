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


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONA-BASED AI REVIEW: EXPORT & IMPORT
# ═══════════════════════════════════════════════════════════════════════════════

# Canonical asset names used throughout the app
CANONICAL_ASSETS = [
    "AI Core Power", "AI Tech TOP10", "Dividend Stocks", "Consumer Staples",
    "Treasury Bonds", "Gold", "Japan TOPIX", "Cash",
]

# Fuzzy aliases that AI personas might use instead of canonical names
_ASSET_ALIASES = {
    "ai core power": "AI Core Power",
    "ai core": "AI Core Power",
    "kodex 미국ai전력핵심인프라": "AI Core Power",
    "ai tech top10": "AI Tech TOP10",
    "ai tech": "AI Tech TOP10",
    "kodex 미국ai테크top10타겟커버드콜": "AI Tech TOP10",
    "dividend stocks": "Dividend Stocks",
    "dividend stock": "Dividend Stocks",
    "dividend aristocrats": "Dividend Stocks",
    "dividend quality": "Dividend Stocks",
    "kodex 미국배당다우존스": "Dividend Stocks",
    "consumer staples": "Consumer Staples",
    "defensive staples": "Consumer Staples",
    "staples": "Consumer Staples",
    "kodex 미국s&p500필수소비재": "Consumer Staples",
    "treasury bonds": "Treasury Bonds",
    "us treasury bonds": "Treasury Bonds",
    "bonds": "Treasury Bonds",
    "kodex 미국30년국채액티브(h)": "Treasury Bonds",
    "gold": "Gold",
    "gold / gold etf": "Gold",
    "kodex 골드선물(h)": "Gold",
    "japan topix": "Japan TOPIX",
    "japan robotics / ai": "Japan TOPIX",
    "kodex 일본topix100": "Japan TOPIX",
    "cash": "Cash",
    "short-term cash / money market": "Cash",
    "cash / money market": "Cash",
}


def normalize_asset_name(raw_name: str) -> str | None:
    """Match a raw asset name (possibly from AI output) to a canonical name.

    Returns the canonical name, or None if no match is found.
    """
    cleaned = raw_name.strip()

    # Exact match (case-insensitive)
    for canon in CANONICAL_ASSETS:
        if cleaned.lower() == canon.lower():
            return canon

    # Alias lookup
    alias_hit = _ASSET_ALIASES.get(cleaned.lower())
    if alias_hit:
        return alias_hit

    # Substring containment (e.g., "AI Core Power (50% of growth)" → AI Core Power)
    for canon in CANONICAL_ASSETS:
        if canon.lower() in cleaned.lower():
            return canon

    return None


def generate_persona_export(
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
    """Generate a markdown snapshot for AI review using three investment personas.

    Builds on the standard snapshot but adds persona-specific mandates and
    a strict response format that the persona parser can reliably extract.
    """
    today = datetime.now().strftime("%B %d, %Y")
    months_left = int(years_remaining * 12)

    lines = [
        f"# IRP Portfolio Snapshot — {today}",
        f"# Three-Persona Strategic Review",
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

    # ── Three-Persona Mandates ──
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Three-Persona Review Mandates")
    lines.append("")
    lines.append("I want you to analyze this portfolio through three expert personas.")
    lines.append("Each persona has a specific mandate (question to answer).")
    lines.append("")
    lines.append("### PERSONA 1: Cathie Wood — Growth Maximization")
    lines.append('**Mandate:** "Which are the most powerful growth ETFs to fill 70% of my portfolio with, in order to double my capital within five years?"')
    lines.append("- Evaluate which of the 8 assets should form the growth sleeve")
    lines.append("- Provide CAGR targets for the growth sleeve")
    lines.append("- Be specific about allocation percentages and entry strategy")
    lines.append("")
    lines.append("### PERSONA 2: Peter Lynch — Bubble Reality Check")
    lines.append('**Mandate:** "Are the assets Wood selected not a bubble? Isn\'t there a \'reasonable\' alternative backed by actual earnings?"')
    lines.append("- Apply PEG ratio and earnings-yield tests to Cathie's picks")
    lines.append("- Identify which are fairly valued vs. overpriced")
    lines.append("- Suggest earnings-backed alternatives where needed")
    lines.append("")
    lines.append("### PERSONA 3: Ray Dalio — Crash-Proof Safe Sleeve")
    lines.append('**Mandate:** "How should the remaining 30% be structured in safe assets so that even if the stock market crashes by -30%, my total net worth doesn\'t deviate from the path toward 400 million?"')
    lines.append("- Design the 30% safe sleeve with specific allocations")
    lines.append("- Model crash scenarios (-30% equity drawdown)")
    lines.append("- Show how rebalancing during crashes recovers the path")
    lines.append("")

    # ── Strict response format ──
    lines.append("---")
    lines.append("")
    lines.append("## Response Format Instructions")
    lines.append("")
    lines.append("I will import your response as a .md file into my portfolio app.")
    lines.append("**You MUST follow this EXACT format** — my parser depends on it.")
    lines.append("")
    lines.append("### Rules")
    lines.append("1. Structure your analysis in EXACTLY these sections, in this order:")
    lines.append("   - `## PERSONA 1: Cathie Wood` (growth analysis)")
    lines.append("   - `## PERSONA 2: Peter Lynch` (valuation check)")
    lines.append("   - `## PERSONA 3: Ray Dalio` (safe sleeve design)")
    lines.append("   - `## SYNTHESIS` (integrated final recommendation)")
    lines.append("2. Each PERSONA section MUST contain a subsection `### Recommended Allocation` with this EXACT table format:")
    lines.append("")
    lines.append("   | Asset | % of Total | Action | Reason |")
    lines.append("   |-------|-----------|--------|--------|")
    lines.append("   | AI Core Power | [number] | Hold/Trim/Add | [reason] |")
    lines.append("   | ... (all 8 assets) | ... | ... | ... |")
    lines.append("")
    lines.append("3. Each PERSONA section MUST contain a subsection `### CAGR Assessment` with:")
    lines.append("   - Growth CAGR: [number]%")
    lines.append("   - Blended CAGR: [number]%")
    lines.append("   - Reason: [text]")
    lines.append("")
    lines.append("4. Each PERSONA section MUST contain a subsection `### Key Recommendations` with bullets:")
    lines.append("   - HIGH: [description]")
    lines.append("   - MEDIUM: [description]")
    lines.append("   - LOW: [description]")
    lines.append("")
    lines.append("5. The `## SYNTHESIS` section MUST contain:")
    lines.append("   - `### Recommended Allocation` — the FINAL integrated table (same format as persona tables)")
    lines.append("   - `### CAGR Assessment` — blended view")
    lines.append("   - `### Key Recommendations` — prioritized action items")
    lines.append("   - `### Market Outlook` — macro view")
    lines.append("   - `### Implementation Plan` — phased execution steps")
    lines.append("")
    lines.append("6. Use EXACTLY these 8 asset names (spelled exactly): AI Core Power, AI Tech TOP10, Dividend Stocks, Consumer Staples, Treasury Bonds, Gold, Japan TOPIX, Cash")
    lines.append("7. All `% of Total` values in each table MUST be plain numbers that sum to exactly 100")
    lines.append("8. You may add rich analysis text WITHIN each persona section, but keep the subsection headers exact")
    lines.append("9. Do NOT wrap the response in a code fence — output as plain markdown")
    lines.append("")
    lines.append("### Template (each persona section follows this pattern)")
    lines.append("")
    lines.append("```")
    lines.append("## PERSONA 1: Cathie Wood")
    lines.append("")
    lines.append("[Analysis text...]")
    lines.append("")
    lines.append("### Recommended Allocation")
    lines.append("")
    lines.append("| Asset | % of Total | Action | Reason |")
    lines.append("|-------|-----------|--------|--------|")
    lines.append("| AI Core Power | 35 | Add | [reason] |")
    lines.append("| AI Tech TOP10 | 15 | Hold | [reason] |")
    lines.append("| Dividend Stocks | 7 | Trim | [reason] |")
    lines.append("| Consumer Staples | 3 | Hold | [reason] |")
    lines.append("| Treasury Bonds | 12 | Add | [reason] |")
    lines.append("| Gold | 5 | Hold | [reason] |")
    lines.append("| Japan TOPIX | 0 | Eliminate | [reason] |")
    lines.append("| Cash | 23 | Deploy | [reason] |")
    lines.append("")
    lines.append("### CAGR Assessment")
    lines.append("")
    lines.append("- Growth CAGR: 17.1%")
    lines.append("- Blended CAGR: 11.5%")
    lines.append("- Reason: [explanation]")
    lines.append("")
    lines.append("### Key Recommendations")
    lines.append("")
    lines.append("- HIGH: [action]")
    lines.append("- MEDIUM: [action]")
    lines.append("- LOW: [action]")
    lines.append("```")
    lines.append("")
    lines.append("The `## SYNTHESIS` section uses the same subsection format but adds `### Market Outlook` and `### Implementation Plan`.")
    lines.append("")

    return "\n".join(lines)


def parse_persona_review_md(content: str) -> dict:
    """Parse a three-persona AI review markdown file.

    Returns:
        {
            "format": "persona",
            "personas": {
                "Cathie Wood": {"allocation": {...}, "cagr": {...}, "recommendations": [...], "raw": str},
                "Peter Lynch": {"allocation": {...}, "cagr": {...}, "recommendations": [...], "raw": str},
                "Ray Dalio":   {"allocation": {...}, "cagr": {...}, "recommendations": [...], "raw": str},
            },
            "synthesis": {
                "allocation": {...},
                "cagr": {...},
                "recommendations": [...],
                "market_outlook": str,
                "implementation_plan": str,
            },
            "raw": str,
        }
    """
    result = {
        "format": "persona",
        "personas": {},
        "synthesis": {
            "allocation": {},
            "cagr": {"growth": None, "blended": None, "reason": ""},
            "recommendations": [],
            "market_outlook": "",
            "implementation_plan": "",
        },
        "raw": content,
    }

    # ── Split into persona sections ──
    # Match: ## PERSONA N: Name  or  ## SYNTHESIS
    section_pattern = re.compile(
        r"^##\s+(?:PERSONA\s+\d+\s*:\s*(.+?)|(SYNTHESIS))\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    section_starts = list(section_pattern.finditer(content))

    if not section_starts:
        # Not a persona-format file; return empty
        return result

    for i, m in enumerate(section_starts):
        start = m.start()
        end = section_starts[i + 1].start() if i + 1 < len(section_starts) else len(content)
        section_text = content[start:end]

        persona_name = m.group(1)  # e.g., "Cathie Wood" or None
        is_synthesis = m.group(2) is not None

        if is_synthesis:
            parsed = _parse_persona_section(section_text)
            result["synthesis"]["allocation"] = parsed["allocation"]
            result["synthesis"]["cagr"] = parsed["cagr"]
            result["synthesis"]["recommendations"] = parsed["recommendations"]
            # Market Outlook
            outlook = re.search(
                r"###\s*Market Outlook\s*\n(.*?)(?=\n### |\n## |\Z)",
                section_text, re.DOTALL | re.IGNORECASE,
            )
            if outlook:
                result["synthesis"]["market_outlook"] = outlook.group(1).strip()
            # Implementation Plan
            impl = re.search(
                r"###\s*Implementation Plan\s*\n(.*?)(?=\n### |\n## |\Z)",
                section_text, re.DOTALL | re.IGNORECASE,
            )
            if impl:
                result["synthesis"]["implementation_plan"] = impl.group(1).strip()
        elif persona_name:
            # Clean up persona name (e.g., strip "—" suffixes like "Cathie Wood — Growth Maximization")
            clean_name = re.split(r"\s*[—–-]\s*", persona_name.strip())[0].strip()
            parsed = _parse_persona_section(section_text)
            parsed["raw"] = section_text
            result["personas"][clean_name] = parsed

    return result


def _parse_persona_section(section_text: str) -> dict:
    """Parse allocation, CAGR, and recommendations from a persona (or synthesis) section."""
    parsed = {
        "allocation": {},
        "cagr": {"growth": None, "blended": None, "reason": ""},
        "recommendations": [],
    }

    # ── Allocation table ──
    # Look for ### Recommended Allocation (or ## Recommended Allocation for backward compat)
    alloc_pattern = re.compile(
        r"#{2,3}\s*Recommended Allocation\s*\n"
        r"\|.*\|\s*\n"
        r"\|[-| ]+\|\s*\n"
        r"((?:\|.*\|\s*\n?)+)",
        re.IGNORECASE,
    )
    match = alloc_pattern.search(section_text)
    if match:
        rows_text = match.group(1).strip()
        for row in rows_text.split("\n"):
            cells = [c.strip() for c in row.split("|")]
            cells = [c for c in cells if c]
            if len(cells) < 2:
                continue

            raw_asset = cells[0].strip()
            # Skip total/subtotal rows
            if raw_asset.lower().startswith(("**total", "total", "**growth", "**safe")):
                continue

            canonical = normalize_asset_name(raw_asset)
            if not canonical:
                continue

            # Try to find percentage: look for first numeric value
            pct = 0.0
            for cell in cells[1:]:
                try:
                    val = float(re.sub(r"[^0-9.]", "", cell))
                    if 0 <= val <= 100:
                        pct = val
                        break
                except (ValueError, IndexError):
                    continue

            # Action and reason from remaining cells
            action = ""
            reason = ""
            if len(cells) >= 3:
                # The action cell is typically after the percentage
                for cell_idx in range(2, len(cells)):
                    cell_val = cells[cell_idx].strip()
                    # Skip cells that look like numbers/percentages
                    if re.match(r"^[\d.%\s+\-]*$", cell_val):
                        continue
                    if not action:
                        action = cell_val
                    elif not reason:
                        reason = cell_val
                        break

            parsed["allocation"][canonical] = {
                "current": 0,  # Will be filled by the caller
                "recommended": pct,
                "action": action,
                "reason": reason,
            }

    # ── CAGR Assessment ──
    cagr_block = re.search(
        r"#{2,3}\s*CAGR Assessment\s*\n(.*?)(?=\n#{2,3} |\n## |\Z)",
        section_text, re.DOTALL | re.IGNORECASE,
    )
    if cagr_block:
        block = cagr_block.group(1)
        growth_m = re.search(r"Growth\s*CAGR\s*:?\s*([\d.]+)", block, re.IGNORECASE)
        blended_m = re.search(r"Blended\s*CAGR\s*:?\s*([\d.]+)", block, re.IGNORECASE)
        # Also try "Current assumption" / "Recommended" format (backward compat)
        current_m = re.search(r"Current\s*assumption\s*:?\s*([\d.]+)", block, re.IGNORECASE)
        rec_m = re.search(r"Recommended\s*:?\s*([\d.]+)", block, re.IGNORECASE)
        reason_m = re.search(r"Reason\s*:?\s*(.+?)(?:\n|$)", block, re.IGNORECASE)

        if growth_m:
            parsed["cagr"]["growth"] = float(growth_m.group(1))
        elif current_m:
            parsed["cagr"]["growth"] = float(current_m.group(1))

        if blended_m:
            parsed["cagr"]["blended"] = float(blended_m.group(1))
        elif rec_m:
            parsed["cagr"]["blended"] = float(rec_m.group(1))

        if reason_m:
            parsed["cagr"]["reason"] = reason_m.group(1).strip()

    # ── Key Recommendations ──
    rec_block = re.search(
        r"#{2,3}\s*Key Recommendations\s*\n(.*?)(?=\n#{2,3} |\n## |\Z)",
        section_text, re.DOTALL | re.IGNORECASE,
    )
    if rec_block:
        for line in rec_block.group(1).strip().split("\n"):
            line = line.strip()
            bullet = re.match(r"-\s*(HIGH|MEDIUM|LOW)\s*:\s*(.+)", line, re.IGNORECASE)
            if bullet:
                prio = bullet.group(1).upper()
                desc = bullet.group(2).strip()
                parsed["recommendations"].append(f"[{prio}] {desc}")

    return parsed


def detect_review_format(content: str) -> str:
    """Detect whether an AI review file is 'persona' or 'standard' format.

    Returns 'persona' if it contains persona section headers, otherwise 'standard'.
    """
    if re.search(r"^##\s+PERSONA\s+\d+\s*:", content, re.MULTILINE | re.IGNORECASE):
        return "persona"
    if re.search(r"^##\s+SYNTHESIS", content, re.MULTILINE | re.IGNORECASE):
        return "persona"
    return "standard"


def persona_review_to_standard(persona_result: dict) -> dict:
    """Convert persona review result to the standard format for backward compatibility.

    Uses the SYNTHESIS section as the canonical allocation to apply.
    Falls back to averaging persona allocations if synthesis is missing.
    """
    synth = persona_result.get("synthesis", {})
    alloc = synth.get("allocation", {})

    # If synthesis has no allocation, merge from personas
    if not alloc:
        persona_allocs = {}
        count = 0
        for pname, pdata in persona_result.get("personas", {}).items():
            for asset, info in pdata.get("allocation", {}).items():
                if asset not in persona_allocs:
                    persona_allocs[asset] = []
                persona_allocs[asset].append(info["recommended"])
            count += 1
        if count > 0:
            alloc = {}
            for asset, vals in persona_allocs.items():
                avg = sum(vals) / len(vals)
                alloc[asset] = {
                    "current": 0,
                    "recommended": round(avg, 1),
                    "action": "Review",
                    "reason": f"Average of {len(vals)} persona(s)",
                }

    cagr = synth.get("cagr", {})
    return {
        "allocation": alloc,
        "cagr": {
            "current": cagr.get("growth"),
            "recommended": cagr.get("blended"),
            "reason": cagr.get("reason", ""),
        },
        "recommendations": synth.get("recommendations", []),
        "market_outlook": synth.get("market_outlook", ""),
        "raw": persona_result.get("raw", ""),
    }
