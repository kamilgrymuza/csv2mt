# End-to-End Test Fixtures

This directory contains test fixtures for end-to-end validation of MT940 generation.

## Purpose

These tests verify that MT940 files generated from bank statements (PDF/CSV/Excel) using Claude AI match the official MT940 files provided by the bank.

**⚠️ IMPORTANT:** These tests consume Claude API credits and should NOT run on every test execution.

## Directory Structure

Each test case should be in its own subdirectory with the following files:

```
e2e/
├── test_case_1/
│   ├── statement.pdf          # Source bank statement (PDF, CSV, or XLSX)
│   ├── expected.mt940          # Official MT940 from the bank
│   └── generated.mt940         # (Auto-generated) Claude AI generated MT940
├── test_case_2/
│   ├── statement.csv
│   └── expected.mt940
└── README.md
```

## Adding a New Test Case

1. **Create a test case directory:**
   ```bash
   mkdir -p backend/tests/fixtures/e2e/my_bank_statement
   ```

2. **Add your bank statement file:**
   - Name it `statement.pdf` (or `.csv`, `.xlsx`)
   - This is the source document that will be parsed by Claude AI

3. **Add the expected MT940 file:**
   - Name it `expected.mt940`
   - This should be the official MT940 file downloaded from your bank

4. **Optional: Add a description file:**
   ```bash
   echo "Test case description" > backend/tests/fixtures/e2e/my_bank_statement/README.txt
   ```

## Running the Tests

### Run all E2E tests:
```bash
# From the backend directory
pytest tests/test_e2e_bank_comparison.py --run-e2e -v
```

### Run a specific test case:
```bash
pytest tests/test_e2e_bank_comparison.py::TestEndToEndBankComparison::test_pdf_to_mt940_matches_bank[my_bank_statement] --run-e2e -v
```

### Check if test cases exist (doesn't consume credits):
```bash
pytest tests/test_e2e_bank_comparison.py::test_e2e_has_test_cases -v
```

### Run in Docker:
```bash
docker-compose exec backend pytest tests/test_e2e_bank_comparison.py --run-e2e -v
```

## What the Test Does

1. **Reads** your bank statement file (PDF/CSV/Excel)
2. **Parses** it using Claude AI to extract transactions
3. **Generates** an MT940 file from the parsed data
4. **Compares** the generated MT940 against the expected MT940 from your bank
5. **Saves** the generated MT940 as `generated.mt940` for debugging

## Comparison Logic

The test compares:

### Hard Checks (Must Match):
- ✅ Number of transactions
- ✅ Transaction dates
- ✅ Transaction amounts (±1 cent tolerance)

### Soft Checks (Warning Only):
- ⚠️ Transaction descriptions (may differ due to AI interpretation)

## Interpreting Results

### ✅ Test Passes:
The generated MT940 matches the bank's MT940. The conversion is accurate!

### ❌ Test Fails:
The test will show detailed differences:
```
Statement 0, Transaction 5: Amount differs: generated=-123.45, expected=-123.50
Statement 0, Transaction 7: Date differs: generated=2024-01-15, expected=2024-01-16
```

Check the `generated.mt940` file to see what was produced.

## Security Note

**⚠️ The files in this directory may contain sensitive financial information:**
- Account numbers
- Transaction details
- Personal information

**This directory is listed in `.gitignore` to prevent accidental commits.**

If you need to commit test cases:
1. Use anonymized/sanitized data
2. Remove or redact sensitive information
3. Use example data that doesn't correspond to real accounts

## Example Test Case

See `example_test_case/` for a sample test case structure (if available).

## Troubleshooting

### "No test cases found"
- Check that your test case directory exists in `tests/fixtures/e2e/`
- Verify you have both `statement.*` and `expected.mt940` files

### "Need --run-e2e option to run"
- Add the `--run-e2e` flag to your pytest command
- This is intentional to prevent accidental API credit consumption

### Test fails with parsing errors
- Verify your `expected.mt940` file is valid MT940 format
- Check that the statement file is readable (not corrupted)

### Comparison fails on descriptions
- This is normal - AI may interpret descriptions differently
- Focus on amounts and dates being correct
- Review the `generated.mt940` to see if descriptions are reasonable

## Notes

- Generated MT940 files (`generated.mt940`) are created automatically during test runs
- You can compare them manually against `expected.mt940` to see differences
- Tests use the same Claude AI parser as the production application
