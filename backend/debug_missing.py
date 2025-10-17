"""Debug why some transactions are missing"""
from app.services.claude_parser import ClaudeDocumentParser

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
print(f"Total lines: {len(lines)}")

# Count non-empty lines after row 23
non_empty = 0
for i, line in enumerate(lines[23:], 23):
    if line.strip() and not line.startswith('"Data transakcji"'):
        non_empty += 1

print(f"Non-empty data lines after row 23: {non_empty}")
print()
print("Showing lines 23-30:")
for i, line in enumerate(lines[23:30], 23):
    print(f"{i}: {line[:100]}")
