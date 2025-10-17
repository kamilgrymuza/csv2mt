#!/usr/bin/env python3
"""
Utility script to detect the encoding of a file

This script uses the centralized encoding detection utility to analyze file encodings.

Usage:
    python detect_encoding.py <file_path>

Example:
    python detect_encoding.py tests/fixtures/e2e/ing_corporate/expected.mt940
"""

import sys
from pathlib import Path

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.services.encoding_detector import decode_file_content, EncodingDetectionError


def analyze_file(file_path: str):
    """Analyze and display encoding information for a file"""
    print(f"Analyzing: {file_path}\n")

    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return

    try:
        # Read file as bytes
        with open(path, 'rb') as f:
            content = f.read()

        # Detect encoding using centralized utility
        text, encoding = decode_file_content(
            content,
            min_confidence=0.7,
            filename=file_path
        )

        print(f"✅ Detected encoding: {encoding}")
        print(f"   File size: {len(text)} characters")

        # Check for MT940 markers
        markers = [':20:', ':25:', ':28C:', ':60F:', ':61:', ':86:', ':62F:']
        found_markers = [m for m in markers if m in text]

        if found_markers:
            print(f"   MT940 markers found: {', '.join(found_markers)}")

        # Show first few lines
        lines = text.split('\n')[:10]
        print(f"\n📄 First {len(lines)} lines:")
        for i, line in enumerate(lines, 1):
            # Truncate long lines
            display_line = line[:80] + '...' if len(line) > 80 else line
            print(f"   {i:2d}: {display_line}")

        # Check for non-ASCII characters
        non_ascii_chars = set(c for c in text if ord(c) > 127)
        if non_ascii_chars:
            print(f"\n⚠️  Non-ASCII characters found: {len(non_ascii_chars)} unique")
            # Show first few
            samples = list(non_ascii_chars)[:10]
            print(f"   Samples: {', '.join(repr(c) for c in samples)}")

    except EncodingDetectionError as e:
        print(f"❌ Encoding detection failed:")
        print(f"   {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    file_path = sys.argv[1]
    analyze_file(file_path)


if __name__ == '__main__':
    main()
