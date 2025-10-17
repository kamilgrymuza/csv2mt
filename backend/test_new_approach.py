"""
Test new two-step parsing approach with ING CSV file
"""
from app.services.claude_parser import ClaudeDocumentParser
import time

# Read the large ING CSV file
file_path = "/app/test_data_ing.csv"
# Try different encodings
for encoding in ['utf-8', 'iso-8859-2', 'windows-1250', 'latin1']:
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        print(f'Detected encoding: {encoding}')
        break
    except UnicodeDecodeError:
        continue

print(f'File has {len(content.split(chr(10)))} lines')
print('='*60)
print('Testing NEW two-step approach (AI format detection + Python parsing)')
print('='*60)
print()

parser = ClaudeDocumentParser()
start_time = time.time()

result = parser._parse_with_claude_text(content, None)

elapsed = time.time() - start_time

print()
print('='*60)
print('RESULTS')
print('='*60)
print(f'⏱️  Time: {elapsed:.2f} seconds')
print(f'📊 Transactions found: {len(result["transactions"])}')
print(f'📅 Date range: {result["metadata"].get("statement_start_date")} to {result["metadata"].get("statement_end_date")}')
print(f'💵 Currency: {result["metadata"].get("currency")}')
print(f'🏦 Account: {result["metadata"].get("account_number")}')
print()
print('First 5 transactions:')
for i, txn in enumerate(result['transactions'][:5], 1):
    print(f'  {i}. {txn["date"]}: {txn["amount"]:>10.2f} PLN - {txn["description"][:70]}')
print()
print('Last 5 transactions:')
for i, txn in enumerate(result['transactions'][-5:], len(result['transactions'])-4):
    print(f'  {i}. {txn["date"]}: {txn["amount"]:>10.2f} PLN - {txn["description"][:70]}')
print()
print(f'Expected: ~792 transactions (from file header)')
print(f'Parsed:   {len(result["transactions"])} transactions')
if len(result["transactions"]) == 792:
    print('✅ SUCCESS: Parsed 100% of transactions')
else:
    print(f'⚠️  WARNING: Only parsed {len(result["transactions"])/792*100:.1f}% of expected transactions')
