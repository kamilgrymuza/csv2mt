"""Debug PDF parsing"""
from app.services.claude_parser import ClaudeDocumentParser

parser = ClaudeDocumentParser()

with open('/app/test_ing_corporate.pdf', 'rb') as f:
    # Extract text from PDF
    text = parser._extract_pdf_content(f)

print("PDF Text Content (first 2000 chars):")
print("="*80)
print(text[:2000])
print("="*80)
print()
print(f"Total lines: {len(text.split(chr(10)))}")
print()

# Show first 50 lines for format detection
lines = text.split('\n')
print("First 50 lines:")
print("="*80)
for i, line in enumerate(lines[:50]):
    print(f"{i:3d}: {line[:100]}")
