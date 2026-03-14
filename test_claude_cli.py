"""Tests for Claude CLI integration."""
import sys
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "src")
from utils import (
    is_claude_cli_available,
    run_claude_cli,
    save_review_md,
    detect_review_format,
    parse_ai_review_md,
    parse_persona_review_md,
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


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1: is_claude_cli_available
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== TEST 1: is_claude_cli_available ===")

with patch("utils.shutil.which", return_value="/usr/bin/claude"):
    check("CLI found", is_claude_cli_available() is True)

with patch("utils.shutil.which", return_value=None):
    check("CLI not found", is_claude_cli_available() is False)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2: run_claude_cli — CLI not found
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== TEST 2: run_claude_cli — CLI not found ===")

with patch("utils.is_claude_cli_available", return_value=False):
    result = run_claude_cli("test prompt")
    check("Returns failure", result["success"] is False)
    check("Error message", "not found" in result["error"].lower(), result["error"])
    check("Empty response", result["response"] == "")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3: run_claude_cli — successful call (mocked subprocess)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== TEST 3: run_claude_cli — successful call ===")

MOCK_STANDARD_RESPONSE = """# IRP AI Review — March 2026

## Recommended Allocation

| Asset | Current % | Recommended % | Action | Reason |
|-------|-----------|---------------|--------|--------|
| AI Core Power | 28 | 30 | Add | Strong AI momentum |
| AI Tech TOP10 | 14 | 12 | Trim | High valuation |
| Dividend Stocks | 10 | 10 | Hold | Stable income |
| Consumer Staples | 8 | 8 | Hold | Defensive anchor |
| Treasury Bonds | 11 | 13 | Add | Rising rates |
| Gold | 7 | 7 | Hold | Inflation hedge |
| Japan TOPIX | 2 | 2 | Hold | Diversification |
| Cash | 28 | 18 | Deploy | Opportunity cost |

## CAGR Assessment

- Current assumption: 10.2%
- Recommended: 10.5%
- Reason: Slightly bullish outlook with AI tailwinds

## Key Recommendations

- HIGH: Deploy excess cash into growth equities
- MEDIUM: Add Treasury Bonds position for rate protection
- LOW: Monitor Japan TOPIX for rotation opportunities

## Market Outlook

Markets are moderately bullish with AI sector leading gains.
"""

mock_proc = MagicMock()
mock_proc.returncode = 0
mock_proc.stdout = MOCK_STANDARD_RESPONSE
mock_proc.stderr = ""

with patch("utils.is_claude_cli_available", return_value=True), \
     patch("utils.subprocess.run", return_value=mock_proc) as mock_run:
    result = run_claude_cli("snapshot text", model="sonnet", timeout_seconds=120)

    check("Returns success", result["success"] is True)
    check("Response not empty", len(result["response"]) > 0)
    check("Model recorded", result["model"] == "sonnet")
    check("Elapsed recorded", result["elapsed_seconds"] >= 0)

    # Verify subprocess was called correctly
    call_args = mock_run.call_args
    cmd = call_args[0][0]
    check("Uses -p flag", "-p" in cmd, str(cmd))
    check("Uses --model", "--model" in cmd and "sonnet" in cmd, str(cmd))
    check("Input piped", call_args[1]["input"] == "snapshot text")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4: run_claude_cli — non-zero exit code
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== TEST 4: run_claude_cli — error exit code ===")

mock_err = MagicMock()
mock_err.returncode = 1
mock_err.stdout = ""
mock_err.stderr = "Authentication required"

with patch("utils.is_claude_cli_available", return_value=True), \
     patch("utils.subprocess.run", return_value=mock_err):
    result = run_claude_cli("test")
    check("Returns failure", result["success"] is False)
    check("Error contains stderr", "Authentication" in result["error"], result["error"])


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 5: run_claude_cli — timeout
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== TEST 5: run_claude_cli — timeout ===")

with patch("utils.is_claude_cli_available", return_value=True), \
     patch("utils.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=60)):
    result = run_claude_cli("test", timeout_seconds=60)
    check("Returns failure", result["success"] is False)
    check("Error mentions timeout", "timed out" in result["error"].lower(), result["error"])


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 6: save_review_md
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== TEST 6: save_review_md ===")

saved = save_review_md("# Test Review\nContent here.", review_mode="standard")
check("Returns Path", isinstance(saved, Path))
check("File exists", saved.exists())
check("Filename has Standard tag", "Standard" in saved.name)
check("Content matches", saved.read_text(encoding="utf-8") == "# Test Review\nContent here.")
saved.unlink()  # cleanup

saved_p = save_review_md("# Persona Review", review_mode="persona")
check("Persona filename tag", "Persona" in saved_p.name)
saved_p.unlink()  # cleanup


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 7: End-to-end — CLI response → parser
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== TEST 7: End-to-end — CLI response parses correctly ===")

fmt = detect_review_format(MOCK_STANDARD_RESPONSE)
check("Detected as standard", fmt == "standard")

parsed = parse_ai_review_md(MOCK_STANDARD_RESPONSE)
check("Allocation parsed", len(parsed["allocation"]) == 8, f"got {len(parsed['allocation'])}")
check("CAGR current", parsed["cagr"]["current"] == 10.2)
check("CAGR recommended", parsed["cagr"]["recommended"] == 10.5)
check("Recommendations parsed", len(parsed["recommendations"]) == 3, f"got {len(parsed['recommendations'])}")
check("Market outlook parsed", "bullish" in parsed["market_outlook"].lower())

# Verify allocation values
alloc = parsed["allocation"]
check("AI Core Power = 30%", alloc.get("AI Core Power", {}).get("recommended") == 30)
check("Cash = 18%", alloc.get("Cash", {}).get("recommended") == 18)
total = sum(v["recommended"] for v in alloc.values())
check("Allocations sum to 100", total == 100, f"sum={total}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 8: run_claude_cli — max_budget_usd flag
# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== TEST 8: max_budget_usd flag passed correctly ===")

mock_proc2 = MagicMock()
mock_proc2.returncode = 0
mock_proc2.stdout = "response"
mock_proc2.stderr = ""

with patch("utils.is_claude_cli_available", return_value=True), \
     patch("utils.subprocess.run", return_value=mock_proc2) as mock_run2:
    run_claude_cli("test", max_budget_usd=0.50)
    cmd = mock_run2.call_args[0][0]
    check("Budget flag present", "--max-budget-usd" in cmd, str(cmd))
    check("Budget value", "0.5" in cmd, str(cmd))


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*50}")
print(f"RESULTS: {PASSED} passed, {FAILED} failed, {PASSED + FAILED} total")
if FAILED == 0:
    print("ALL TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    sys.exit(1)
