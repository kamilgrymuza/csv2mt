"""Show the format specification that AI detected"""
from app.services.claude_parser import ClaudeDocumentParser
import json

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
first_50 = '\n'.join(lines[:50])

parser = ClaudeDocumentParser()
format_spec = parser._extract_format_specification(first_50)

print("Format Specification Detected by AI:")
print("="*60)
print(json.dumps(format_spec, indent=2, ensure_ascii=False))
