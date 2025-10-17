# MT940 File Format Specification

This document describes the SWIFT MT940 format implementation in the CSV2MT project.

## Overview

MT940 (Customer Statement Message) is a SWIFT message type used by banks to provide electronic bank statement information. Our implementation generates fully SWIFT-compliant MT940 files from parsed bank statements (CSV, PDF, Excel).

## SWIFT MT940 Required Fields

According to the SWIFT standard, every MT940 statement must contain the following mandatory fields:

### Mandatory Fields

| Field | Name | Description | Format | Example |
|-------|------|-------------|--------|---------|
| `:20:` | Transaction Reference | Unique reference for the statement | Max 16 alphanumeric | `:20:250901-INGCORPO` |
| `:25:` | Account Identification | Account number (IBAN with `/` prefix) | Max 35 characters | `:25:/PL27105010251000009085623719` |
| `:28C:` | Statement/Sequence Number | Statement number and optional sequence | 5n[/5n] | `:28C:00001` |
| `:60F:` | Opening Balance (First) | Balance at start of period | [D/C]YYMMDD[Currency]Amount | `:60F:C250901PLN4700,00` |
| `:61:` | Statement Line | Individual transaction (one per transaction) | YYMMDD[MMDD][D/C][Amount][Type][Ref] | `:61:2509290929D406,45NMSC` |
| `:62F:` | Closing Balance (Final) | Balance at end of period | Same as :60F | `:62F:C250930PLN28131,35` |

### Optional Fields (We Include)

| Field | Name | Description |
|-------|------|-------------|
| `:86:` | Information to Account Owner | Transaction description/details (max 6 lines × 65 chars) |
| `:64:` | Closing Available Balance | Available balance (optional enhancement) |

## Our Implementation

### What We Generate

```
:20:250901-INGCORPO
:25:/PL27105010251000009085623719
:28C:00001
:60F:C250901PLN4700,00
:61:2509290929D406,45NMSC
:86:SWIAT ALKOHOLI RUMIA - Płatność kartą 28.09.2025 Nr karty 5534xx2497
:61:2509260926D184,00NMSC
:86:TEX-MEX S.C. GDYNIA - Płatność kartą 25.09.2025 Nr karty 5534xx2497
...
:62F:C250930PLN28131,35
```

### Field Details

#### :20: Transaction Reference
- Format: `YYMMDD-FILENAME` (first 8 chars of filename)
- Ensures uniqueness per statement
- Max 16 characters

#### :25: Account Identification
- Always prefixed with `/` for IBAN format
- Spaces removed from IBAN (SWIFT standard)
- Falls back to "UNKNOWN" if account not detected

#### :28C: Statement Number
- Default: `00001`
- Can be incremented for multiple statements

#### :60F: Opening Balance
- `C` = Credit (positive balance)
- `D` = Debit (negative balance)
- Date in YYMMDD format
- Currency code (3 letters)
- Amount with comma as decimal separator

#### :61: Statement Line (Transaction)
- Value date (YYMMDD)
- Entry date (MMDD) - same as value date
- Debit/Credit indicator (D/C)
- Amount (no decimal separator in field, implied 2 decimals)
- Transaction type code: `NMSC` (Non-SWIFT)
- Reference (optional)

#### :86: Information to Account Owner
- Free text description
- We use clean, readable format
- Alternative: Structured codes (`~00`, `~20`, etc.) - both valid

#### :62F: Closing Balance
- Same format as :60F
- **Mandatory** - we always calculate and include this
- Derived from opening balance + sum of transactions (if not provided)

## Compliance

Our MT940 implementation is **fully SWIFT-compliant**:

✅ All mandatory fields included
✅ Correct field formats and ordering
✅ Valid debit/credit indicators
✅ Proper IBAN formatting (spaces removed)
✅ Closing balance calculation
✅ Transaction descriptions included

### Comparison with Bank-Generated MT940

| Aspect | Bank Format | Our Format | Valid? |
|--------|-------------|------------|--------|
| Required fields | ✅ All | ✅ All | Both valid |
| :86: format | Structured codes (`~00MD02...`) | Clean text | Both valid |
| Transaction details | Multi-line structured | Single-line readable | Both valid |
| Closing balance | ✅ Included | ✅ Included | Both valid |

**Both formats are valid per SWIFT specification.** Our format prioritizes readability while maintaining full compliance.

## Minimal Valid MT940 Example

The absolute minimum valid MT940 file:

```
:20:STATEMENT001
:25:/GB33BUKB20201555555555
:28C:00001
:60F:C230101GBP1000,00
:61:2301020102D100,00NMSC
:62F:C230102GBP900,00
```

This contains only the 6 mandatory fields and one transaction.

## References

- SWIFT MT940 Format Specification: [SWIFT Standards](https://www.swift.com)
- Implementation: `backend/app/services/mt940_converter.py`
- Conversion: `backend/app/services/claude_parser.py` (`convert_to_mt940` method)

## Testing

MT940 compliance is verified by:
1. Parsing real bank statements (ING, mBank, etc.)
2. Comparing generated MT940 with bank-issued MT940 files
3. Validating all mandatory fields are present
4. E2E tests in `backend/tests/test_e2e_bank_comparison.py`

Last updated: 2025-10-16
