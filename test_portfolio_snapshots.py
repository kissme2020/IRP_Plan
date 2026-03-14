"""Tests for Portfolio Snapshots feature."""
import sys
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, "src")
from utils import (
    is_kr_business_day,
    should_auto_snapshot,
    create_portfolio_snapshot,
    KR_TZ,
)

PASSED = 0
FAILED = 0


def check(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS: {name}")
    else:
        FAILED += 1
        print(f"  FAIL: {name} — {detail}")


# ── is_kr_business_day ──────────────────────────────────────────────────────

print("\n=== is_kr_business_day ===")

# 2026-03-15 is Sunday
check("Sunday is not business day", not is_kr_business_day(date(2026, 3, 15)))

# 2026-03-14 is Saturday
check("Saturday is not business day", not is_kr_business_day(date(2026, 3, 14)))

# 2026-03-13 is Friday
check("Friday is business day", is_kr_business_day(date(2026, 3, 13)))

# 2026-03-16 is Monday
check("Monday is business day", is_kr_business_day(date(2026, 3, 16)))

# 2026-03-01 is Korean holiday (Independence Movement Day)
check("Korean holiday is not business day", not is_kr_business_day(date(2026, 3, 1)))

# 2026-01-01 is New Year's Day (Korean holiday)
check("New Year is not business day", not is_kr_business_day(date(2026, 1, 1)))


# ── should_auto_snapshot ────────────────────────────────────────────────────

print("\n=== should_auto_snapshot ===")


def _mock_now(target_date):
    """Return a mock for datetime.now(KR_TZ) returning target_date."""
    return datetime(target_date.year, target_date.month, target_date.day,
                    10, 0, 0, tzinfo=KR_TZ)


# Before the 15th — should not trigger
with patch("utils.datetime") as mock_dt:
    mock_dt.now.return_value = _mock_now(date(2026, 3, 10))
    mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
    check("Before 15th: no trigger", not should_auto_snapshot([]))

# On the 15th (business day, no existing snapshot) — should trigger
# 2026-04-15 is Wednesday
with patch("utils.datetime") as mock_dt:
    mock_dt.now.return_value = _mock_now(date(2026, 4, 15))
    mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
    check("15th (Wed, no snapshot): trigger", should_auto_snapshot([]))

# On the 15th but snapshot already exists for this month — should NOT trigger
with patch("utils.datetime") as mock_dt:
    mock_dt.now.return_value = _mock_now(date(2026, 4, 15))
    mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
    existing = [{"date": "2026-04-15T10:00:00+09:00"}]
    check("15th with existing snapshot: no trigger", not should_auto_snapshot(existing))

# On Saturday the 15th — should NOT trigger (weekend + Korean Liberation Day)
# 2026-08-15 is Saturday
with patch("utils.datetime") as mock_dt:
    mock_dt.now.return_value = _mock_now(date(2026, 8, 15))
    mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
    check("Saturday 15th: no trigger", not should_auto_snapshot([]))

# Monday 17th is a substitute holiday — should NOT trigger
with patch("utils.datetime") as mock_dt:
    mock_dt.now.return_value = _mock_now(date(2026, 8, 17))
    mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
    check("Mon 17th (substitute holiday): no trigger", not should_auto_snapshot([]))

# Tuesday 18th is the first business day >= 15 — should trigger
with patch("utils.datetime") as mock_dt:
    mock_dt.now.return_value = _mock_now(date(2026, 8, 18))
    mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
    check("Tue 18th (first biz day >= 15): trigger", should_auto_snapshot([]))

# On the 20th, but snapshot already taken on the 18th — no trigger
with patch("utils.datetime") as mock_dt:
    mock_dt.now.return_value = _mock_now(date(2026, 8, 20))
    mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
    existing = [{"date": "2026-08-18T10:00:00+09:00"}]
    check("20th with snapshot on 18th: no trigger", not should_auto_snapshot(existing))

# Snapshot from different month should not block current month
with patch("utils.datetime") as mock_dt:
    mock_dt.now.return_value = _mock_now(date(2026, 4, 15))
    mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
    existing = [{"date": "2026-03-16T10:00:00+09:00"}]
    check("Snapshot from prev month: trigger", should_auto_snapshot(existing))


# ── create_portfolio_snapshot ───────────────────────────────────────────────

print("\n=== create_portfolio_snapshot ===")

test_shares = {
    "AI Core Power": 1000,
    "Gold": 500,
    "Cash": 10_000_000,
}
test_prices = {
    "AI Core Power": {"price": 20000},
    "Gold": {"price": 30000},
}
test_targets = {
    "AI Core Power": 0.30,
    "Gold": 0.10,
    "Cash": 0.60,
}

snap = create_portfolio_snapshot(test_shares, test_prices, test_targets, trigger="manual", note="test")

check("snapshot has date", "date" in snap)
check("trigger is manual", snap["trigger"] == "manual")
check("note is 'test'", snap["note"] == "test")
check("AI Core Power value = 20M", snap["values"]["AI Core Power"] == 20_000_000)
check("Gold value = 15M", snap["values"]["Gold"] == 15_000_000)
check("Cash value = 10M", snap["values"]["Cash"] == 10_000_000)
check("total_value = 45M", snap["total_value"] == 45_000_000)
check("allocation_pct sums to ~1.0",
      abs(sum(snap["allocation_pct"].values()) - 1.0) < 0.01)
check("prices stored for ETFs", snap["prices"]["AI Core Power"] == 20000)
check("targets stored", snap["allocation_targets"]["AI Core Power"] == 0.30)

# Auto trigger
snap_auto = create_portfolio_snapshot(test_shares, test_prices, test_targets, trigger="auto")
check("auto trigger", snap_auto["trigger"] == "auto")
check("auto note is empty", snap_auto["note"] == "")

# Empty portfolio
snap_empty = create_portfolio_snapshot({}, {}, {}, trigger="manual")
check("empty portfolio total = 0", snap_empty["total_value"] == 0)
check("empty portfolio alloc = {}", snap_empty["allocation_pct"] == {})


# ── Summary ─────────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"Results: {PASSED} passed, {FAILED} failed out of {PASSED + FAILED}")
if FAILED == 0:
    print("All tests passed!")
else:
    print("Some tests FAILED.")
    sys.exit(1)
