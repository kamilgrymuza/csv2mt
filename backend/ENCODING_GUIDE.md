# MT940 File Encoding Detection Guide

## Official SWIFT MT940 Character Set Standards

According to SWIFT specifications, MT940 messages use specific character sets:

### SWIFT Character Sets

**Character Set X (General FIN Application)**
- **Standard:** EDIFACT Level A (ISO 9735) with extensions
- **Case:** Upper and lower case allowed
- **Allowed characters:**
  - Letters: `a-z`, `A-Z`
  - Numbers: `0-9`
  - Special: `/ - ? : ( ) . , ' + Space`
  - Line breaks: `CrLf` (must be used together)
- **Use case:** Most MT940 fields including descriptions

**Character Set Y (EDIFACT Level A)**
- **Standard:** ISO 9735 EDIFACT Level A
- **Case:** Upper case only
- **Use case:** Specific structured fields

**Character Set Z (Information Service)**
- **Use case:** Special information fields

### Official Encoding Standard

**ISO 9735** - The EDIFACT Syntax Rules standard defines the character sets used in SWIFT messages.

**Important:** While SWIFT defines character sets, the **file encoding** (how characters are stored in bytes) is NOT strictly defined by SWIFT. Banks typically use:
- **ISO-8859-1 (Latin-1)** - Most common in European banks
- **UTF-8** - Modern implementations
- **Windows-1252** - Windows banking systems
- **ISO-8859-2** - Central/Eastern European banks (e.g., Poland)

### Practical Reality

**Theory:** SWIFT MT940 should use EDIFACT character sets (printable ASCII + specific characters)

**Practice:** Banks often include:
- Local currency symbols (€, £, zł)
- Diacritics (ä, ö, ü, ą, ć, ę)
- Company names with special characters
- Free-text descriptions with local characters

**Result:** File encoding varies by bank and region, even though the character set is standardized.

## Quick Commands

### Detect encoding of any file:
```bash
# In Docker
docker-compose exec backend python detect_encoding.py <file_path>

# Example
docker-compose exec backend python detect_encoding.py tests/fixtures/e2e/ing_corporate/expected.mt940
```

### Local Python:
```bash
cd backend
python detect_encoding.py <file_path>
```

## Common MT940 Encodings

### UTF-8
- **Most common:** Modern systems
- **Characteristics:** Can handle all characters, widely supported
- **Use case:** New MT940 files, international transactions

### Latin-1 (ISO-8859-1)
- **Common in:** European banks, older systems
- **Characteristics:** Western European characters (€, £, ä, ö, ü, etc.)
- **Use case:** Your ING Corporate file uses this

### CP1252 (Windows-1252)
- **Common in:** Windows-based banking systems
- **Characteristics:** Similar to Latin-1 with extra characters
- **Use case:** Windows-generated MT940 files

### ISO-8859-2
- **Common in:** Central/Eastern European banks
- **Characteristics:** Polish, Czech, Hungarian characters
- **Use case:** Banks in Poland, Czech Republic, Hungary

## How to Check Your File

### Method 1: Using the detect_encoding.py script (Recommended)

```bash
docker-compose exec backend python detect_encoding.py tests/fixtures/e2e/your_test/expected.mt940
```

**Output example:**
```
Analyzing: tests/fixtures/e2e/ing_corporate/expected.mt940

✅ Detected encoding: latin-1
   File size: 4613 characters
   MT940 markers found: :20:, :25:, :28C:, :60F:, :61:, :86:, :62F:

📄 First 10 lines:
    1: :20:MT940
    2: :25:/PL27105010251000009085623719
    3: :28C:00002
    ...

⚠️  Non-ASCII characters found: 12 unique
   Samples: 'ä', '©', 'à', ...
```

### Method 2: Using the file command (macOS/Linux)

```bash
file -i tests/fixtures/e2e/ing_corporate/expected.mt940
```

**Output:**
```
expected.mt940: text/plain; charset=iso-8859-1
```

### Method 3: Manual inspection with hexdump

```bash
hexdump -C tests/fixtures/e2e/ing_corporate/expected.mt940 | head -20
```

Look for byte sequences:
- `C3` followed by `80`-`BF` = UTF-8
- `80`-`FF` without `C3` = Latin-1 or CP1252
- `00` bytes = UTF-16

## Common Issues

### Issue: "UnicodeDecodeError: 'utf-8' codec can't decode byte..."

**Cause:** File is not UTF-8 encoded

**Solution:**
1. Detect the actual encoding:
   ```bash
   docker-compose exec backend python detect_encoding.py <file>
   ```

2. The E2E test framework automatically handles this by trying multiple encodings

### Issue: Special characters display as "�" or garbled

**Cause:** Wrong encoding used to read the file

**Solution:**
1. Use `detect_encoding.py` to find correct encoding
2. When reading manually, use the detected encoding:
   ```python
   with open('file.mt940', 'r', encoding='latin-1') as f:
       content = f.read()
   ```

### Issue: Polish/Special characters in bank names or descriptions

**Example:** "SPÓŁKA" appears as "SP�KA"

**Cause:** File uses Latin-2 (ISO-8859-2) or CP1250 for Polish characters

**Solution:**
- Try `iso-8859-2` or `cp1250` encoding
- The E2E test will try common encodings automatically

## Encoding Priority in E2E Tests

The test framework tries encodings in this order:

1. **UTF-8** - Try first (most common modern encoding)
2. **Latin-1** - Western European (€, £, ä, ö, ü)
3. **CP1252** - Windows Western European
4. **ISO-8859-1** - Alternative name for Latin-1
5. **UTF-8-SIG** - UTF-8 with BOM (Byte Order Mark)

## Converting Encodings

### If you need to convert to UTF-8:

```bash
# Using iconv (macOS/Linux)
iconv -f ISO-8859-1 -t UTF-8 expected.mt940 > expected_utf8.mt940

# Using Python
docker-compose exec backend python -c "
import sys
with open('expected.mt940', 'r', encoding='latin-1') as f:
    content = f.read()
with open('expected_utf8.mt940', 'w', encoding='utf-8') as f:
    f.write(content)
print('Converted to UTF-8')
"
```

## Bank-Specific Notes

### ING Corporate (Poland)
- **Encoding:** Latin-1 (ISO-8859-1)
- **Special chars:** Polish characters (ą, ć, ę, ł, ń, ó, ś, ź, ż)
- **Note:** Some special chars may not render correctly in Latin-1

### mBank (Poland)
- **Encoding:** Usually UTF-8 or CP1250
- **Special chars:** Full Polish character support

### Santander
- **Encoding:** Usually UTF-8
- **Special chars:** Euro symbols, accented characters

## Best Practices

1. **Always check encoding** before processing MT940 files
2. **Use the detect_encoding.py script** for unknown files
3. **Keep original encoding** in expected.mt940 (E2E test handles it)
4. **Convert to UTF-8** only if necessary for compatibility
5. **Document encoding** in test case README if unusual

## Troubleshooting Commands

### View file in hex to see raw bytes:
```bash
hexdump -C file.mt940 | less
```

### Check for BOM (Byte Order Mark):
```bash
head -c 3 file.mt940 | hexdump -C
```

UTF-8 BOM: `EF BB BF`
UTF-16 LE BOM: `FF FE`
UTF-16 BE BOM: `FE FF`

### Test reading with specific encoding:
```bash
docker-compose exec backend python -c "
with open('tests/fixtures/e2e/ing_corporate/expected.mt940', 'r', encoding='latin-1') as f:
    print(f.read()[:200])
"
```

## Summary: What You Need to Know

### For Developers

**Q: What encoding should I use for MT940 files?**
- **A:** There's no single answer. SWIFT defines character sets (ISO 9735 EDIFACT), but not file encodings.

**Q: What encoding do banks actually use?**
- **A:** Most common: ISO-8859-1 (Latin-1), UTF-8, Windows-1252, ISO-8859-2
- **Varies by:** Bank, country, system age

**Q: What should I do for new MT940 files I generate?**
- **A:** Use **UTF-8** - it's modern, supports all characters, and widely compatible

**Q: How do I handle MT940 files from banks?**
- **A:** Use the `detect_encoding.py` script or try multiple encodings (our E2E test does this automatically)

### For This Project

✅ **E2E Tests:** Automatically try multiple encodings
✅ **Generated MT940:** Uses UTF-8
✅ **Bank MT940:** Accepts any common encoding
✅ **Detection Tool:** `detect_encoding.py` available

### Key Takeaway

**SWIFT Standard ≠ File Encoding**
- SWIFT defines what characters are allowed (ISO 9735 EDIFACT)
- SWIFT does NOT define how those characters are encoded in files
- Banks choose their own encodings (usually ISO-8859-1 or UTF-8)
- Always detect encoding before processing unknown MT940 files

## References

- [SWIFT MT940 Format](https://www.paiementor.com/swift-mt940-format-specifications/)
- [ISO 9735 EDIFACT Standard](https://www.iso.org/standard/80091.html)
- [SWIFT Character Sets](https://paymerix.com/swift-formatting-rules-character-sets-mt-messages/)
- [Python codecs](https://docs.python.org/3/library/codecs.html)
- [Character encoding](https://en.wikipedia.org/wiki/Character_encoding)
- [ISO-8859-1 / Latin-1](https://en.wikipedia.org/wiki/ISO/IEC_8859-1)
- [Windows-1252](https://en.wikipedia.org/wiki/Windows-1252)
