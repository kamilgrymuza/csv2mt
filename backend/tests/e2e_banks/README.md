# E2E Bank Statement Tests

This directory contains end-to-end tests for bank statement conversion. Each test validates the complete pipeline from CSV/PDF input to MT940 output.

## Structure

```
e2e_banks/
├── README.md                    # This file
├── test_ing_corporate_cp1250.py        # ING Corporate test
├── ing_corporate/
│   ├── input.csv               # Input CSV file
│   ├── expected.mt940          # Expected MT940 output
│   └── output.mt940            # Generated MT940 (created during test)
├── test_mbank.py               # (Future) mBank test
└── mbank/
    ├── input.csv
    └── expected.mt940
```

## How It Works

Each test follows this pattern:

1. **Read Input** - Load CSV/PDF file with encoding detection
2. **Parse** - Use current implementation (Claude AI, format detection, etc.)
3. **Convert** - Generate MT940 format
4. **Write** - Save MT940 to `output.mt940`
5. **Compare** - Use `mt940` library to parse both files
6. **Diff** - Show detailed differences if mismatch

## Running Tests

```bash
# Run all E2E tests
pytest tests/e2e_banks/ -v

# Run specific bank test
pytest tests/e2e_banks/test_ing_corporate_cp1250.py -v

# Run with output
pytest tests/e2e_banks/test_ing_corporate_cp1250.py -v -s
```

## Adding a New Bank Test

1. Create directory: `tests/e2e_banks/new_bank/`
2. Add files:
   - `input.csv` - The bank's CSV export
   - `expected.mt940` - Valid MT940 for comparison (can be from bank or manually verified)
3. Create test: `test_new_bank.py`
4. Copy structure from `test_ing_corporate_cp1250.py`
5. Update bank name and paths

## Test Features

### Encoding Detection
- Automatically tries: utf-8, latin-1, iso-8859-2, windows-1250
- Handles Polish and other special characters

### MT940 Validation
- Uses `mt940` library to parse generated files
- Validates all required SWIFT fields
- Compares transaction counts, balances, account numbers

### Debugging Output
- Colored unified diff (red/green/blue)
- Line-by-line comparison
- Sample transactions display
- Token usage (if applicable)

### Regression Protection
- Tests fail if output changes
- Catches format regressions
- Validates end-to-end pipeline

## Test Output Example

```
================================================================================
E2E TEST: ING Corporate CSV → MT940
================================================================================

Step 1: Parsing input CSV from input.csv
   ✓ Parsed 13 transactions
   ✓ Account: PL27105010251000009085623719
   ✓ Currency: PLN
   ✓ Date range: 2025-09-01 to 2025-09-30

Step 2: Converting to MT940 format
   ✓ Generated MT940 (2438 bytes)
   ✓ Transaction count: 13

Step 3: Writing MT940 to output.mt940
   ✓ File written successfully

Step 4: Comparing with expected MT940 using mt940 library
   Generated: 1 statement(s)
   Expected:  1 statement(s)

   Comparing statement details:
   ✓ Account number matches: PL27105010251000009085623719
   ✓ Transaction count matches: 13
   ✓ Opening balance matches: 4700.00
   ✓ Closing balance matches: 28131.35

   Sample transactions (first 3):
   1. 2025-09-29: -406.45 - SWIAT ALKOHOLI RUMIA...
   2. 2025-09-26: -184.00 - TEX-MEX S.C. GDYNIA...
   3. 2025-09-19: -3373.20 - Hotel at Booking.com...

================================================================================
✅ E2E TEST PASSED
================================================================================
```

## Maintenance

- Update `expected.mt940` if format intentionally changes
- Add new tests for each supported bank
- Keep input files realistic (real anonymized data)
- Document encoding issues in comments

## Current Tests

- ✅ ING Corporate (CSV → MT940)
- 🔜 mBank (CSV → MT940)
- 🔜 Santander (CSV → MT940)
- 🔜 ING Private (CSV → MT940)
