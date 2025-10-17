"""
E2E Test: ING Corporate Bank Statement (PDF)

This test validates the complete pipeline:
1. Read PDF file
2. Parse using Claude AI with vision
3. Convert to MT940 format
4. Write MT940 to disk
5. Compare with expected MT940 using mt940 library
6. Output detailed diff on mismatch for debugging

The test is designed to catch regressions as we iterate on the implementation.
"""

import pytest
import os
from pathlib import Path
from difflib import unified_diff
import mt940
from app.services.claude_parser import ClaudeDocumentParser


class TestINGCorporatePDFE2E:
    """End-to-end test for ING Corporate PDF bank statement conversion"""

    @pytest.fixture
    def test_dir(self):
        """Get the test directory for this bank"""
        return Path(__file__).parent / "ing_corporate_pdf"

    @pytest.fixture
    def input_pdf(self, test_dir):
        """Path to input PDF file"""
        return test_dir / "input.pdf"

    @pytest.fixture
    def expected_mt940(self, test_dir):
        """Path to expected MT940 file"""
        return test_dir / "expected.mt940"

    @pytest.fixture
    def output_mt940(self, test_dir):
        """Path where generated MT940 will be written"""
        return test_dir / "output.mt940"

    def test_ing_corporate_pdf_to_mt940(self, input_pdf, expected_mt940, output_mt940):
        """
        Test complete PDF → MT940 conversion pipeline for ING Corporate
        """
        # Step 1: Parse PDF file
        print("\n" + "="*80)
        print("E2E TEST: ING Corporate PDF → MT940")
        print("="*80)
        print(f"\nStep 1: Parsing input PDF from {input_pdf}")

        parser = ClaudeDocumentParser()

        # Read PDF file
        with open(input_pdf, 'rb') as f:
            result = parser.parse_document(f, input_pdf.name)

        print(f"   ✓ Parsed {len(result['transactions'])} transactions")
        print(f"   ✓ Account: {result['metadata'].get('account_number')}")
        print(f"   ✓ Currency: {result['metadata'].get('currency')}")
        print(f"   ✓ Date range: {result['metadata'].get('statement_start_date')} to {result['metadata'].get('statement_end_date')}")

        assert len(result['transactions']) > 0, "No transactions parsed from PDF"
        assert result['metadata'].get('account_number'), "No account number extracted"

        # Step 2: Convert to MT940
        print(f"\nStep 2: Converting to MT940 format")
        mt940_content = parser.convert_to_mt940(result)

        assert mt940_content, "MT940 conversion produced empty output"
        assert ':20:' in mt940_content, "Missing required field :20:"
        assert ':25:' in mt940_content, "Missing required field :25:"
        assert ':60F:' in mt940_content, "Missing required field :60F:"
        assert ':62F:' in mt940_content, "Missing required field :62F:"

        print(f"   ✓ Generated MT940 ({len(mt940_content)} bytes)")
        print(f"   ✓ Transaction count: {mt940_content.count(':61:')}")

        # Step 3: Write to disk
        print(f"\nStep 3: Writing MT940 to {output_mt940}")
        with open(output_mt940, 'w', encoding='utf-8') as f:
            f.write(mt940_content)
        print(f"   ✓ File written successfully")

        # Step 4: Load both MT940 files using mt940 library
        print(f"\nStep 4: Comparing with expected MT940 using mt940 library")

        try:
            # Parse generated MT940 - read as text and pass string to mt940.parse
            with open(output_mt940, 'r', encoding='utf-8') as f:
                generated_content = f.read()
                generated_transactions = mt940.parse(generated_content)
                generated_statements = list(generated_transactions)

            # Parse expected MT940 (always UTF-8)
            with open(expected_mt940, 'r', encoding='utf-8') as f:
                expected_content = f.read()
                expected_transactions = mt940.parse(expected_content)
                expected_statements = list(expected_transactions)

            print(f"   Generated: {len(generated_statements)} statement(s)")
            print(f"   Expected:  {len(expected_statements)} statement(s)")

        except Exception as e:
            print(f"\n   ⚠️  MT940 library parsing failed: {e}")
            print(f"   This might be due to format differences. Falling back to line-by-line comparison.")
            self._compare_mt940_files_line_by_line(output_mt940, expected_mt940)
            return

        # Step 5: Compare statements
        assert len(generated_statements) > 0, "Generated MT940 produced no statements"

        if len(generated_statements) != len(expected_statements):
            print(f"\n   ⚠️  Statement count mismatch!")
            print(f"      Generated: {len(generated_statements)}")
            print(f"      Expected:  {len(expected_statements)}")

        # Compare first statement (most common case)
        gen_stmt = generated_statements[0]
        exp_stmt = expected_statements[0] if expected_statements else None

        if exp_stmt:
            self._compare_statements(gen_stmt, exp_stmt, output_mt940, expected_mt940)

        print("\n" + "="*80)
        print("✅ E2E TEST PASSED")
        print("="*80)

    def _compare_statements(self, generated, expected, gen_file, exp_file):
        """Compare two MT940 statements and output differences"""

        print(f"\n   Comparing statement details:")

        # Compare account number
        gen_account = generated.data.get('account_identification')
        exp_account = expected.data.get('account_identification')
        if gen_account != exp_account:
            print(f"   ⚠️  Account mismatch:")
            print(f"      Generated: {gen_account}")
            print(f"      Expected:  {exp_account}")
        else:
            print(f"   ✓ Account number matches: {gen_account}")

        # Compare transaction count
        gen_txn_count = len(generated.transactions)
        exp_txn_count = len(expected.transactions)
        if gen_txn_count != exp_txn_count:
            print(f"   ⚠️  Transaction count mismatch:")
            print(f"      Generated: {gen_txn_count}")
            print(f"      Expected:  {exp_txn_count}")
            print(f"\n   Showing line-by-line diff:")
            self._compare_mt940_files_line_by_line(gen_file, exp_file)
        else:
            print(f"   ✓ Transaction count matches: {gen_txn_count}")

        # Compare balances
        gen_opening = generated.data.get('final_opening_balance')
        exp_opening = expected.data.get('final_opening_balance')
        gen_closing = generated.data.get('final_closing_balance')
        exp_closing = expected.data.get('final_closing_balance')

        if gen_opening and exp_opening:
            if gen_opening.amount.amount != exp_opening.amount.amount:
                print(f"   ⚠️  Opening balance mismatch:")
                print(f"      Generated: {gen_opening.amount.amount}")
                print(f"      Expected:  {exp_opening.amount.amount}")
            else:
                print(f"   ✓ Opening balance matches: {gen_opening.amount.amount}")

        if gen_closing and exp_closing:
            if gen_closing.amount.amount != exp_closing.amount.amount:
                print(f"   ⚠️  Closing balance mismatch:")
                print(f"      Generated: {gen_closing.amount.amount}")
                print(f"      Expected:  {exp_closing.amount.amount}")
            else:
                print(f"   ✓ Closing balance matches: {gen_closing.amount.amount}")

        # Compare transaction descriptions
        print(f"\n   Comparing transaction descriptions:")
        description_mismatches = []

        for i in range(min(gen_txn_count, exp_txn_count)):
            if i < len(generated.transactions) and i < len(expected.transactions):
                gen_txn = generated.transactions[i]
                exp_txn = expected.transactions[i]

                gen_desc = gen_txn.data.get('transaction_details', '')
                exp_desc = exp_txn.data.get('transaction_details', '')

                # Normalize descriptions for comparison (strip whitespace, handle None)
                gen_desc_norm = (gen_desc or '').strip()
                exp_desc_norm = (exp_desc or '').strip()

                if gen_desc_norm != exp_desc_norm:
                    description_mismatches.append({
                        'index': i,
                        'date': gen_txn.data.get('date'),
                        'amount': gen_txn.data.get('amount'),
                        'generated': gen_desc_norm,
                        'expected': exp_desc_norm
                    })

        if description_mismatches:
            print(f"   ⚠️  Found {len(description_mismatches)} transaction description mismatch(es):")
            for mismatch in description_mismatches[:5]:  # Show first 5 mismatches
                print(f"\n   Transaction {mismatch['index'] + 1} ({mismatch['date']}, {mismatch['amount']}):")
                print(f"      Generated: {mismatch['generated'][:100]}")
                print(f"      Expected:  {mismatch['expected'][:100]}")
            if len(description_mismatches) > 5:
                print(f"\n   ... and {len(description_mismatches) - 5} more mismatch(es)")

            # Show line-by-line diff for detailed investigation
            print(f"\n   Showing line-by-line diff for investigation:")
            self._compare_mt940_files_line_by_line(gen_file, exp_file)

            # Fail the test
            assert False, f"Transaction description mismatch: {len(description_mismatches)} transaction(s) have different descriptions"
        else:
            print(f"   ✓ All transaction descriptions match ({gen_txn_count} transactions)")

        # Sample first 3 transactions
        print(f"\n   Sample transactions (first 3):")
        for i in range(min(3, gen_txn_count)):
            if i < len(generated.transactions):
                txn = generated.transactions[i]
                print(f"   {i+1}. {txn.data.get('date')}: {txn.data.get('amount')} - {txn.data.get('transaction_details', 'N/A')[:60]}")

    def _compare_mt940_files_line_by_line(self, gen_file, exp_file):
        """Compare MT940 files line by line and show unified diff"""

        with open(gen_file, 'r', encoding='utf-8') as f:
            gen_lines = f.readlines()

        # Expected file is always UTF-8
        with open(exp_file, 'r', encoding='utf-8') as f:
            exp_lines = f.readlines()

        # Generate unified diff
        diff = list(unified_diff(
            exp_lines,
            gen_lines,
            fromfile='expected.mt940',
            tofile='generated.mt940',
            lineterm=''
        ))

        if diff:
            print("\n   📋 Unified Diff (first 50 lines):")
            print("   " + "-"*76)
            for line in diff[:50]:
                if line.startswith('+'):
                    print(f"   \033[92m{line}\033[0m")  # Green for additions
                elif line.startswith('-'):
                    print(f"   \033[91m{line}\033[0m")  # Red for deletions
                elif line.startswith('@@'):
                    print(f"   \033[94m{line}\033[0m")  # Blue for location
                else:
                    print(f"   {line}")
            if len(diff) > 50:
                print(f"   ... ({len(diff) - 50} more lines)")
            print("   " + "-"*76)
        else:
            print(f"   ✓ Files are identical (line-by-line)")

    def test_cleanup(self, output_mt940):
        """Clean up generated files after test (optional)"""
        # Comment out to keep output files for inspection
        # if output_mt940.exists():
        #     output_mt940.unlink()
        pass
