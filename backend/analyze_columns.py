"""Analyze the actual column structure"""
import csv
from io import StringIO

file_path = "/app/test_data_ing.csv"
for encoding in ['utf-8', 'iso-8859-2', 'windows-1250', 'latin1']:
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        break
    except UnicodeDecodeError:
        continue

lines = content.split('\n')

# Find header row
print("Looking for header row...")
for i in range(15, 25):
    if '"Data transakcji"' in lines[i]:
        print(f"\nHeader row found at line {i}:")
        print(lines[i])
        print()
        
        # Parse header
        reader = csv.reader(StringIO(lines[i]), delimiter=';', quotechar='"')
        headers = next(reader)
        print(f"Total columns: {len(headers)}")
        print("\nColumn mapping:")
        for j, h in enumerate(headers):
            if h.strip():
                print(f"  {j}: {h.strip()}")
        
        # Now show first few data rows with column indices
        print(f"\n\nFirst 3 data rows (starting at line {i+1}):")
        for k in range(3):
            row_idx = i + 1 + k
            print(f"\nLine {row_idx}:")
            reader = csv.reader(StringIO(lines[row_idx]), delimiter=';', quotechar='"')
            row = next(reader)
            print(f"Total columns: {len(row)}")
            for j, cell in enumerate(row):
                if cell.strip():
                    print(f"  Col {j}: {cell.strip()[:60]}")
        break
