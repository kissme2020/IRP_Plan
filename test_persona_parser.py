"""Test persona parser against sample files."""
import sys
sys.path.insert(0, "src")
from utils import detect_review_format, parse_persona_review_md, persona_review_to_standard, parse_ai_review_md

# Test 1: Persona format detection and parsing
with open("data/sample_persona_review.md", "r", encoding="utf-8") as f:
    persona_content = f.read()

fmt = detect_review_format(persona_content)
print("=== FORMAT DETECTION ===")
print(f"Detected: {fmt}")
assert fmt == "persona", f"Expected persona, got {fmt}"

result = parse_persona_review_md(persona_content)
print("\n=== PERSONAS FOUND ===")
for name, pdata in result["personas"].items():
    alloc = pdata.get("allocation", {})
    total = sum(v["recommended"] for v in alloc.values())
    print(f'{name}: {len(alloc)} assets, total={total}%, CAGR growth={pdata["cagr"]["growth"]}, blended={pdata["cagr"]["blended"]}')
    print(f'  Recommendations: {len(pdata["recommendations"])} items')
    for a, v in alloc.items():
        print(f'    {a}: {v["recommended"]}% ({v["action"]})')

print("\n=== SYNTHESIS ===")
synth = result["synthesis"]
synth_alloc = synth["allocation"]
synth_total = sum(v["recommended"] for v in synth_alloc.values())
print(f"Assets: {len(synth_alloc)}, total={synth_total}%")
for a, v in synth_alloc.items():
    print(f'  {a}: {v["recommended"]}% ({v["action"]})')
print(f'CAGR: growth={synth["cagr"]["growth"]}, blended={synth["cagr"]["blended"]}')
print(f'Recommendations: {len(synth["recommendations"])} items')
for r in synth["recommendations"]:
    print(f"  {r}")
print(f'Market Outlook: {len(synth["market_outlook"])} chars')
print(f'Implementation Plan: {len(synth["implementation_plan"])} chars')

# Test 2: Convert to standard format
standard = persona_review_to_standard(result)
print("\n=== STANDARD CONVERSION ===")
print(f'Allocation: {len(standard["allocation"])} assets')
std_total = sum(v["recommended"] for v in standard["allocation"].values())
print(f"Total: {std_total}%")
print(f'CAGR: current={standard["cagr"]["current"]}, recommended={standard["cagr"]["recommended"]}')

# Test 3: Standard format still works
with open("data/sample_ai_review.md", "r", encoding="utf-8") as f:
    standard_content = f.read()
fmt2 = detect_review_format(standard_content)
print("\n=== STANDARD FILE ===")
print(f"Detected format: {fmt2}")
assert fmt2 == "standard", f"Expected standard, got {fmt2}"
std_result = parse_ai_review_md(standard_content)
print(f'Allocations: {len(std_result["allocation"])} assets')

# Validate key assertions
assert len(result["personas"]) == 3, f'Expected 3 personas, got {len(result["personas"])}'
assert "Cathie Wood" in result["personas"], "Missing Cathie Wood"
assert "Peter Lynch" in result["personas"], "Missing Peter Lynch"
assert "Ray Dalio" in result["personas"], "Missing Ray Dalio"
assert len(synth_alloc) == 8, f"Expected 8 synthesis assets, got {len(synth_alloc)}"
assert abs(synth_total - 100) <= 1, f"Synthesis total should be ~100%, got {synth_total}%"
assert synth["cagr"]["blended"] == 11.5, f'Expected blended 11.5, got {synth["cagr"]["blended"]}'
assert len(synth["recommendations"]) >= 4, f'Expected >=4 recommendations, got {len(synth["recommendations"])}'
assert len(synth["market_outlook"]) > 50, "Market outlook too short"
assert len(synth["implementation_plan"]) > 50, "Implementation plan too short"

print("\n=== ALL TESTS PASSED ===")
