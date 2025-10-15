#!/usr/bin/env python3
"""
Utility script to detect the encoding of an MT940 file

Usage:
    python detect_encoding.py <file_path>

Example:
    python detect_encoding.py tests/fixtures/e2e/ing_corporate/expected.mt940
"""

import sys
from pathlib import Path
from typing import Optional, Tuple


def detect_encoding(file_path: str) -> Tuple[Optional[str], str]:
    """
    Detect the encoding of a file by trying multiple common encodings

    Args:
        file_path: Path to the file to analyze

    Returns:
        Tuple of (detected_encoding, sample_text)
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read file as bytes
    with open(path, 'rb') as f:
        raw_data = f.read()

    # Common encodings to try (in order of likelihood)
    encodings = [
        'utf-8',
        'utf-8-sig',  # UTF-8 with BOM
        'latin-1',    # ISO-8859-1 (Western European)
        'cp1252',     # Windows-1252 (Western European)
        'iso-8859-1', # Alternative name for latin-1
        'iso-8859-2', # Central/Eastern European
        'cp1250',     # Windows Central/Eastern European
        'utf-16',
        'utf-16-le',
        'utf-16-be',
    ]

    results = []

    for encoding in encodings:
        try:
            decoded_text = raw_data.decode(encoding)

            # Count how many non-ASCII characters
            non_ascii = sum(1 for c in decoded_text if ord(c) > 127)
            ascii_ratio = (len(decoded_text) - non_ascii) / len(decoded_text) if decoded_text else 0

            # Check for common MT940 markers
            has_mt940_markers = any(marker in decoded_text for marker in [':20:', ':25:', ':60F:', ':61:', ':62F:'])

            # Count replacement characters (indicates bad encoding)
            replacement_chars = decoded_text.count('\ufffd')

            results.append({
                'encoding': encoding,
                'success': True,
                'text': decoded_text,
                'ascii_ratio': ascii_ratio,
                'has_mt940_markers': has_mt940_markers,
                'replacement_chars': replacement_chars,
                'length': len(decoded_text)
            })

        except (UnicodeDecodeError, UnicodeError):
            results.append({
                'encoding': encoding,
                'success': False
            })

    # Filter successful decodings
    successful = [r for r in results if r['success']]

    if not successful:
        return None, "Could not decode file with any common encoding"

    # Score each encoding
    for result in successful:
        score = 0

        # Prefer encodings with MT940 markers
        if result['has_mt940_markers']:
            score += 100

        # Prefer encodings with no replacement characters
        if result['replacement_chars'] == 0:
            score += 50
        else:
            score -= result['replacement_chars'] * 10

        # Prefer higher ASCII ratio (most MT940 files are mostly ASCII)
        score += result['ascii_ratio'] * 20

        result['score'] = score

    # Sort by score
    successful.sort(key=lambda r: r['score'], reverse=True)

    best = successful[0]
    return best['encoding'], best['text']


def analyze_file(file_path: str):
    """Analyze and display encoding information for a file"""
    print(f"Analyzing: {file_path}\n")

    try:
        encoding, text = detect_encoding(file_path)

        if encoding is None:
            print(f"❌ {text}")
            return

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
