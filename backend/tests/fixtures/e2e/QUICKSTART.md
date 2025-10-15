# Quick Start: Adding Your Bank Statement Test Case

Follow these steps to create an E2E test with your PDF and MT940 files:

## Step 1: Create Test Case Directory

```bash
# From the project root
mkdir -p backend/tests/fixtures/e2e/my_bank_test
```

Choose a descriptive name for your test case (e.g., `mbank_2024_jan`, `santander_q4_2023`).

## Step 2: Copy Your Files

Copy your two files into the test case directory:

```bash
# Copy the PDF bank statement
cp /path/to/your/bank_statement.pdf backend/tests/fixtures/e2e/my_bank_test/statement.pdf

# Copy the MT940 file from the bank
cp /path/to/your/bank.mt940 backend/tests/fixtures/e2e/my_bank_test/expected.mt940
```

**Important:** The files MUST be named:
- `statement.pdf` (or `statement.csv`, `statement.xlsx`)
- `expected.mt940`

## Step 3: Verify Files

Check that both files are in place:

```bash
ls -lh backend/tests/fixtures/e2e/my_bank_test/
# Should show:
#   statement.pdf
#   expected.mt940
```

## Step 4: Run the Test

### Option A: Run locally (if you have Python environment set up)

```bash
cd backend
pytest tests/test_e2e_bank_comparison.py --run-e2e -v
```

### Option B: Run in Docker (recommended)

```bash
# Make sure Docker is running
docker-compose up -d

# Run the test
docker-compose exec backend pytest tests/test_e2e_bank_comparison.py --run-e2e -v
```

## Step 5: Check Results

### ✅ If the test passes:

You'll see:
```
tests/test_e2e_bank_comparison.py::TestEndToEndBankComparison::test_pdf_to_mt940_matches_bank[my_bank_test] PASSED

✓ Test case 'my_bank_test' passed: Generated MT940 matches bank MT940
```

Great! The conversion is accurate.

### ❌ If the test fails:

You'll see detailed differences:
```
Statement 0, Transaction 5: Amount differs: generated=-123.45, expected=-123.50
```

Check the generated file to see what was produced:
```bash
cat backend/tests/fixtures/e2e/my_bank_test/generated.mt940
```

Compare it with the expected file:
```bash
diff backend/tests/fixtures/e2e/my_bank_test/expected.mt940 \
     backend/tests/fixtures/e2e/my_bank_test/generated.mt940
```

## Step 6: Review Generated MT940

Even if the test passes, you can review the generated MT940:

```bash
# View the generated MT940
cat backend/tests/fixtures/e2e/my_bank_test/generated.mt940

# Or use the CLI tool to pretty-print it
docker-compose exec backend python -c "
import mt940
with open('tests/fixtures/e2e/my_bank_test/generated.mt940', 'r') as f:
    statements = list(mt940.parse(f.read()))
    for stmt in statements:
        print(f'Transactions: {len(list(stmt.transactions))}')
        for txn in stmt.transactions:
            print(f'  {txn.data[\"date\"]}: {txn.data[\"amount\"]}')
"
```

## Troubleshooting

### "No test cases found"
- Check that your directory is in the correct location: `backend/tests/fixtures/e2e/`
- Verify file names are exactly `statement.pdf` and `expected.mt940`

### "Need --run-e2e option to run"
- Remember to add `--run-e2e` flag: `pytest ... --run-e2e`
- This prevents accidental API credit usage

### Test fails with "Failed to parse MT940"
- Your `expected.mt940` file might not be valid MT940 format
- Try parsing it manually:
  ```bash
  docker-compose exec backend python -c "
  import mt940
  with open('tests/fixtures/e2e/my_bank_test/expected.mt940', 'r') as f:
      try:
          statements = list(mt940.parse(f.read()))
          print(f'Valid MT940: {len(statements)} statement(s)')
      except Exception as e:
          print(f'Invalid MT940: {e}')
  "
  ```

### Claude API errors
- Check that your `ANTHROPIC_API_KEY` is set in `.env`
- Verify you have API credits available

## Multiple Test Cases

You can create multiple test cases:

```bash
backend/tests/fixtures/e2e/
├── mbank_january_2024/
│   ├── statement.pdf
│   └── expected.mt940
├── mbank_february_2024/
│   ├── statement.pdf
│   └── expected.mt940
└── santander_q4_2023/
    ├── statement.csv
    └── expected.mt940
```

Run all of them at once:
```bash
docker-compose exec backend pytest tests/test_e2e_bank_comparison.py --run-e2e -v
```

## Security Reminder

⚠️ These files contain your real banking data!

- They are already in `.gitignore` and won't be committed
- If you want to share test cases, anonymize the data first
- Consider deleting test files after validation

## Next Steps

Once your test passes, you can:

1. **Try with different statements** - Test various date ranges and transaction types
2. **Share results** - Report any issues or improvements
3. **Automate** - Integrate into CI/CD (with caution about API credits)

## Need Help?

Check the full documentation in `README.md` or open an issue on GitHub.
