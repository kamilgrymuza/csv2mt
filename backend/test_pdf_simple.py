"""
E2E test: Parse ING corporate PDF and convert to MT940
"""
from app.services.claude_parser import ClaudeDocumentParser
import time

print("="*80)
print("E2E TEST: ING Corporate PDF → MT940")
print("="*80)
print()

# Parse PDF
print("Step 1: Parsing PDF...")
parser = ClaudeDocumentParser()

with open('/app/test_ing_corporate.pdf', 'rb') as f:
    start_time = time.time()
    result = parser.parse_document(f, 'ing_corporate.pdf')
    parse_time = time.time() - start_time

print(f"   ✓ Parsed in {parse_time:.2f} seconds")
print(f"   ✓ Found {len(result['transactions'])} transactions")
print(f"   ✓ Account: {result['metadata'].get('account_number')}")
print(f"   ✓ Currency: {result['metadata'].get('currency')}")
print()

# Convert to MT940
print("Step 2: Converting to MT940...")
try:
    mt940_output = parser.convert_to_mt940(result)
    print(f"   ✓ Generated MT940 ({len(mt940_output)} bytes)")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("Generated MT940 (first 1500 chars):")
print("-"*80)
print(mt940_output[:1500])
print()

# Load expected
print("Step 3: Loading expected MT940...")
try:
    with open('/app/expected_mt940.sta', 'r') as f:
        expected = f.read()
except:
    with open('/app/expected_mt940.sta', 'r', encoding='latin-1') as f:
        expected = f.read()

print()
print("Expected MT940 (first 1500 chars):")
print("-"*80)
print(expected[:1500])
print()

# Compare
expected_count = expected.count(':61:')
generated_count = mt940_output.count(':61:')

print("="*80)
print("SUMMARY")
print("="*80)
print(f"Parse time: {parse_time:.2f} seconds")
print(f"Extracted: {len(result['transactions'])} transactions")
print(f"Expected MT940: {expected_count} transactions")
print(f"Generated MT940: {generated_count} transactions")
print()
if generated_count == len(result['transactions']):
    print("✅ SUCCESS: All transactions converted!")
else:
    print(f"⚠️  Mismatch: {len(result['transactions'])} extracted, {generated_count} in MT940")
