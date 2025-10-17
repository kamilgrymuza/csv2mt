"""
Test Claude Haiku performance with large ING CSV file
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
print('Testing with Claude Haiku 3.5...')
print()

parser = ClaudeDocumentParser()
start_time = time.time()

result = parser._parse_with_claude_text(content, None)

elapsed = time.time() - start_time

print(f'✅ Parsing completed in {elapsed:.2f} seconds')
print(f'📊 Transactions found: {len(result["transactions"])}')
print(f'💰 Input tokens: {result["metadata"].get("input_tokens", 0):,}')
print(f'💰 Output tokens: {result["metadata"].get("output_tokens", 0):,}')
print(f'📅 Date range: {result["metadata"].get("statement_start_date")} to {result["metadata"].get("statement_end_date")}')
print(f'💵 Currency: {result["metadata"].get("currency")}')
print(f'🏦 Account: {result["metadata"].get("account_number")}')
print()
print('First 3 transactions:')
for i, txn in enumerate(result['transactions'][:3], 1):
    print(f'  {i}. {txn["date"]}: {txn["amount"]:>10.2f} {txn["description"][:60]}')
print()
print('Last 3 transactions:')
for i, txn in enumerate(result['transactions'][-3:], len(result['transactions'])-2):
    print(f'  {i}. {txn["date"]}: {txn["amount"]:>10.2f} {txn["description"][:60]}')
