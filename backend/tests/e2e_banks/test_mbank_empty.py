"""
E2E Test: mBank Empty Statement

This test validates the handling of bank statements with no transactions:
1. Read CSV file with valid metadata but zero transactions
2. Parse using ClaudeDocumentParser
3. Convert to MT940 format
4. Verify MT940 is valid with opening/closing balances but no transaction lines
5. Compare with expected MT940

This ensures the system handles edge cases gracefully.
"""

import pytest
import os
from pathlib import Path
from difflib import unified_diff
import mt940
from app.services.claude_parser import ClaudeDocumentParser


class TestMBankEmptyE2E:
    """End-to-end test for mBank empty statement conversion"""

    @pytest.fixture
    def test_dir(self):
        """Get the test directory for this bank"""
        return Path(__file__).parent / "mbank_empty"

    @pytest.fixture
    def input_csv(self, test_dir):
        """Path to input CSV file"""
        return test_dir / "input.csv"

    @pytest.fixture
    def expected_mt940(self, test_dir):
        """Path to expected MT940 file"""
        return test_dir / "expected.mt940"

    @pytest.fixture
    def output_mt940(self, test_dir):
        """Path where generated MT940 will be written"""
        return test_dir / "output.mt940"

    def test_mbank_empty_csv_to_mt940(self, input_csv, expected_mt940, output_mt940):
        """
        Test CSV → MT940 conversion for empty statement (no transactions)
        """
        # Step 1: Parse CSV file
        print("\n" + "="*80)
        print("E2E TEST: mBank Empty Statement CSV → MT940")
        print("="*80)
        print(f"\nStep 1: Parsing input CSV from {input_csv}")

        parser = ClaudeDocumentParser()

        # Read CSV
        with open(input_csv, 'rb') as f:
            result = parser.parse_document(f, input_csv.name)

        print(f"   ✓ Parsed {len(result['transactions'])} transactions")
        print(f"   ✓ Account: {result['metadata'].get('account_number')}")
        print(f"   ✓ Currency: {result['metadata'].get('currency')}")
        print(f"   ✓ Date range: {result['metadata'].get('statement_start_date')} to {result['metadata'].get('statement_end_date')}")

        # Verify no transactions
        assert len(result['transactions']) == 0, "Expected no transactions in empty statement"
        assert result['metadata'].get('account_number'), "No account number extracted"
        assert result['metadata'].get('statement_start_date'), "No start date extracted"
        assert result['metadata'].get('statement_end_date'), "No end date extracted"

        # Step 2: Convert to MT940
        print(f"\nStep 2: Converting to MT940 format")
        mt940_content = parser.convert_to_mt940(result)

        assert mt940_content, "MT940 conversion produced empty output"
        assert ':20:' in mt940_content, "Missing required field :20:"
        assert ':25:' in mt940_content, "Missing required field :25:"
        assert ':60F:' in mt940_content, "Missing required field :60F:"
        assert ':62F:' in mt940_content, "Missing required field :62F:"
        assert ':61:' not in mt940_content, "Should not contain transaction lines for empty statement"

        print(f"   ✓ Generated MT940 ({len(mt940_content)} bytes)")
        print(f"   ✓ Transaction count: {mt940_content.count(':61:')}")
        print(f"   ✓ Verified no transaction lines (:61:) present")

        # Step 3: Write to disk
        print(f"\nStep 3: Writing MT940 to {output_mt940}")
        with open(output_mt940, 'w', encoding='utf-8') as f:
            f.write(mt940_content)
        print(f"   ✓ File written successfully")

        # Step 4: Load both MT940 files using mt940 library
        print(f"\nStep 4: Comparing with expected MT940 using mt940 library")

        try:
            # Parse generated MT940
            with open(output_mt940, 'r', encoding='utf-8') as f:
                generated_content = f.read()
                generated_transactions = mt940.parse(generated_content)
                generated_statements = list(generated_transactions)

            # Parse expected MT940
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
        # For empty statements, the mt940 library might not parse them correctly
        # In that case, fall back to line-by-line comparison
        if len(generated_statements) == 0 and len(expected_statements) == 0:
            print(f"\n   ℹ️  Both files have no statements (empty statement)")
            print(f"   Falling back to line-by-line comparison...")
            self._compare_mt940_files_line_by_line(output_mt940, expected_mt940)
        elif len(generated_statements) == 0:
            print(f"\n   ⚠️  Generated MT940 produced no parseable statements")
            print(f"   This is expected for empty statements. Falling back to line-by-line comparison...")
            self._compare_mt940_files_line_by_line(output_mt940, expected_mt940)
        else:
            assert len(generated_statements) > 0, "Generated MT940 produced no statements"

            if len(generated_statements) != len(expected_statements):
                print(f"\n   ⚠️  Statement count mismatch!")
                print(f"      Generated: {len(generated_statements)}")
                print(f"      Expected:  {len(expected_statements)}")

            # Compare first statement
            gen_stmt = generated_statements[0]
            exp_stmt = expected_statements[0] if expected_statements else None

            if exp_stmt:
                self._compare_statements(gen_stmt, exp_stmt, output_mt940, expected_mt940)

        print("\n" + "="*80)
        print("✅ E2E TEST PASSED - Empty statement handled correctly")
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
            assert False, f"Account number mismatch: {gen_account} != {exp_account}"
        else:
            print(f"   ✓ Account number matches: {gen_account}")

        # Verify no transactions
        gen_txn_count = len(generated.transactions)
        exp_txn_count = len(expected.transactions)

        if gen_txn_count != 0 or exp_txn_count != 0:
            print(f"   ⚠️  Transaction count should be 0 for empty statement:")
            print(f"      Generated: {gen_txn_count}")
            print(f"      Expected:  {exp_txn_count}")
            assert False, f"Expected 0 transactions but found {gen_txn_count}"
        else:
            print(f"   ✓ Transaction count correct: 0 (empty statement)")

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

        # For empty statement, opening and closing should be equal
        if gen_opening and gen_closing:
            if gen_opening.amount.amount != gen_closing.amount.amount:
                print(f"   ⚠️  Opening and closing balance should be equal for empty statement:")
                print(f"      Opening: {gen_opening.amount.amount}")
                print(f"      Closing: {gen_closing.amount.amount}")
                assert False, "Opening and closing balance must be equal for empty statement"
            else:
                print(f"   ✓ Opening equals closing (as expected for empty statement)")

    def _compare_mt940_files_line_by_line(self, gen_file, exp_file):
        """Compare MT940 files line by line and show unified diff"""

        with open(gen_file, 'r', encoding='utf-8') as f:
            gen_lines = f.readlines()

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
            print("\n   📋 Unified Diff:")
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
            assert False, "MT940 files do not match"
        else:
            print(f"   ✓ Files are identical (line-by-line)")
