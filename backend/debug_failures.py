"""Debug which transactions failed to parse and why"""
from app.services.claude_parser import ClaudeDocumentParser
import csv
from io import StringIO

# Read file
file_path = "/app/test_data_ing.csv"
for encoding in ['utf-8', 'iso-8859-2', 'windows-1250', 'latin1']:
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        break
    except UnicodeDecodeError:
        continue

lines = content.split('\n')

# Get format spec
parser = ClaudeDocumentParser()
first_50 = '\n'.join(lines[:50])
format_spec = parser._extract_format_specification(first_50)

print(f"Format spec says transactions start at row {format_spec['format']['transaction_start_row']}")
print(f"Delimiter: '{format_spec['format']['delimiter']}'")
print(f"Date column: {format_spec['columns']['date']}")
print(f"Amount column: {format_spec['columns']['amount']}")
print()

# Try to parse each line manually and see which fail
start_row = format_spec['format']['transaction_start_row']
delimiter = format_spec['format']['delimiter']
quote_char = format_spec['format'].get('quote_char', '"')

failed_lines = []
success_count = 0
empty_count = 0

for i, line in enumerate(lines[start_row:], start=start_row):
    if not line.strip():
        empty_count += 1
        continue
    
    try:
        reader = csv.reader(StringIO(line), delimiter=delimiter, quotechar=quote_char)
        row = next(reader)
        
        # Check if date column exists and has data
        date_col = format_spec['columns']['date']
        amount_col = format_spec['columns']['amount']
        
        if len(row) <= max(date_col, amount_col):
            failed_lines.append({
                'line_num': i,
                'reason': 'Not enough columns',
                'cols': len(row),
                'line': line[:150]
            })
            continue
        
        date_str = row[date_col].strip() if date_col < len(row) else ""
        amount_str = row[amount_col].strip() if amount_col < len(row) else ""
        
        if not date_str:
            failed_lines.append({
                'line_num': i,
                'reason': 'Empty date',
                'date': date_str,
                'amount': amount_str,
                'line': line[:150]
            })
            continue
        
        if not amount_str:
            failed_lines.append({
                'line_num': i,
                'reason': 'Empty amount',
                'date': date_str,
                'amount': amount_str,
                'line': line[:150]
            })
            continue
            
        success_count += 1
        
    except Exception as e:
        failed_lines.append({
            'line_num': i,
            'reason': f'Parse error: {str(e)}',
            'line': line[:150]
        })

print(f"Total lines from row {start_row}: {len(lines) - start_row}")
print(f"Empty lines: {empty_count}")
print(f"Successfully parsed: {success_count}")
print(f"Failed: {len(failed_lines)}")
print()

print("Failed transactions breakdown:")
print("="*80)

# Group by reason
from collections import Counter
reason_counts = Counter([f['reason'] for f in failed_lines])
for reason, count in reason_counts.most_common():
    print(f"{reason}: {count} transactions")

print()
print("First 10 failed transactions:")
print("="*80)
for i, fail in enumerate(failed_lines[:10], 1):
    print(f"\n{i}. Line {fail['line_num']}: {fail['reason']}")
    if 'date' in fail:
        print(f"   Date: '{fail['date']}', Amount: '{fail['amount']}'")
    print(f"   Content: {fail['line']}")
