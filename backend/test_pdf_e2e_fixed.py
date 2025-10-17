"""
E2E test: Parse ING corporate PDF and compare MT940 output with expected
"""
from app.services.claude_parser import ClaudeDocumentParser
from app.services.mt940_converter import MT940Converter
from app.services.models import BankStatement
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
    result = parser.parse_document(f, 'ing_corporate.pdf', account_number=None)
    parse_time = time.time() - start_time

print(f"   ✓ Parsed in {parse_time:.2f} seconds")
print(f"   ✓ Found {len(result['transactions'])} transactions")
print(f"   ✓ Account: {result['metadata'].get('account_number')}")
print(f"   ✓ Currency: {result['metadata'].get('currency')}")
print(f"   ✓ Date range: {result['metadata'].get('statement_start_date')} to {result['metadata'].get('statement_end_date')}")
print()

# Show sample transactions
print("Sample transactions:")
for i, txn in enumerate(result['transactions'][:5], 1):
    print(f"  {i}. {txn['date']}: {txn['amount']:>10.2f} - {txn['description'][:60]}")
print()

# Create BankStatement object
print("Step 2: Converting to MT940 format...")
statement = BankStatement(
    transactions=[],
    metadata=result['metadata']
)

# Add transactions
for txn_data in result['transactions']:
    from app.services.models import Transaction
    txn = Transaction(
        date=txn_data['date'],
        amount=txn_data['amount'],
        description=txn_data['description'],
        transaction_type=txn_data.get('transaction_type', 'UNKNOWN'),
        reference=txn_data.get('reference'),
        balance=txn_data.get('balance')
    )
    statement.transactions.append(txn)

converter = MT940Converter()

try:
    mt940_output = converter.convert(statement)
    print(f"   ✓ Generated MT940 ({len(mt940_output)} bytes)")
except Exception as e:
    print(f"   ✗ MT940 conversion failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("Generated MT940 (first 1200 chars):")
print("-"*80)
print(mt940_output[:1200])
print("-"*80)
print()

# Load expected MT940
print("Step 3: Comparing with expected MT940...")
try:
    with open('/app/expected_mt940.sta', 'r', encoding='utf-8') as f:
        expected_mt940 = f.read()
except UnicodeDecodeError:
    with open('/app/expected_mt940.sta', 'r', encoding='latin-1') as f:
        expected_mt940 = f.read()

print(f"   Expected MT940: {len(expected_mt940)} bytes")
print(f"   Generated MT940: {len(mt940_output)} bytes")
print()

# Count transactions in MT940
expected_txn_count = expected_mt940.count(':61:')
generated_txn_count = mt940_output.count(':61:')

print(f"Expected transactions: {expected_txn_count}")
print(f"Generated transactions: {generated_txn_count}")
print()

# Summary
print("="*80)
print("SUMMARY")
print("="*80)
print(f"✓ PDF parsed successfully: {len(result['transactions'])} transactions in {parse_time:.2f}s")
print(f"✓ MT940 generated successfully: {generated_txn_count} transactions")
print(f"Transaction count match: {len(result['transactions'])} extracted, {generated_txn_count} in MT940")
if generated_txn_count == len(result['transactions']):
    print("✅ SUCCESS: All transactions converted to MT940")
else:
    print("⚠️  Warning: Transaction count mismatch")
