"""
End-to-End Tests: Compare Claude AI Generated MT940 Against Bank-Provided MT940

These tests verify that MT940 files generated from bank statements (PDF/CSV/Excel)
match the official MT940 files provided by the bank.

IMPORTANT: These tests consume Claude API credits and should not run on every test execution.
Run manually with: pytest tests/test_e2e_bank_comparison.py --run-e2e

Test fixtures should be placed in: tests/fixtures/e2e/
Each test case should have:
  - statement.pdf (or statement.csv, statement.xlsx) - The source document
  - expected.mt940 - The official MT940 file from the bank
"""

import pytest
import os
import io
from pathlib import Path
from typing import List, Dict, Tuple
import mt940

from app.services.claude_parser import ClaudeDocumentParser


class MT940Comparator:
    """Utility class for comparing MT940 files"""

    @staticmethod
    def is_summary_transaction(txn_line: str, field_86_lines: List[str]) -> bool:
        """
        Detect if a transaction line (:61:) is a summary/informational transaction
        that should be excluded from comparison.

        According to MT940 specification, some banks add informational transactions
        that contain statement metadata (balances, summary info) but aren't real
        transactions. These can be identified by:

        1. Zero amount (C0,00 or D0,00 or C0.00 or D0.00)
        2. Reference contains NONREF or similar non-standard reference
        3. Field 86 subfield code is 940 (MT940 statement message type)

        Args:
            txn_line: The :61: transaction line
            field_86_lines: Following :86: field lines

        Returns:
            True if this is a summary transaction to be excluded
        """
        # Check for zero amount (European or US format)
        has_zero_amount = (
            'C0,00' in txn_line or 'D0,00' in txn_line or
            'C0.00' in txn_line or 'D0.00' in txn_line
        )

        if not has_zero_amount:
            return False

        # Check for non-standard reference (NONREF, 940, etc.)
        has_nonref = 'NONREF' in txn_line or 'S940' in txn_line

        # Check if field 86 starts with 940 (MT940 message type code)
        # Field 86 format: :86:XXX where XXX is the transaction type code
        # Code 940 = MT940 message type, used for summaries/metadata
        has_940_code = any(':86:940' in line for line in field_86_lines)

        # If zero amount AND (nonref OR 940 code), it's a summary
        return has_zero_amount and (has_nonref or has_940_code)

    @staticmethod
    def remove_summary_transactions(content: str) -> str:
        """
        Remove summary/informational transactions from MT940 content.

        Banks often add zero-amount summary transactions at the end of statements
        that contain balance information but aren't real transactions. These are
        identified by zero amount + NONREF reference + field 86 code 940.

        Args:
            content: MT940 file content

        Returns:
            MT940 content with summary transactions removed
        """
        lines = content.split('\n')
        filtered_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this is a transaction line
            if line.startswith(':61:'):
                # Collect field 86 lines that follow
                field_86_lines = []
                j = i + 1
                while j < len(lines) and (lines[j].startswith(':86:') or not lines[j].startswith(':')):
                    field_86_lines.append(lines[j])
                    j += 1

                # Check if this is a summary transaction
                if MT940Comparator.is_summary_transaction(line, field_86_lines):
                    # Skip this transaction and its field 86 lines
                    i = j  # Skip to next field
                    continue

            # Keep this line
            filtered_lines.append(line)
            i += 1

        return '\n'.join(filtered_lines)

    @staticmethod
    def normalize_mt940_content(content: str) -> str:
        """
        Normalize MT940 content for comparison by:
        - Removing whitespace variations
        - Normalizing line endings
        - Removing trailing dashes
        """
        lines = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if line and line != '-':
                lines.append(line)
        return '\n'.join(lines)

    @staticmethod
    def parse_mt940_fields(content: str) -> Dict[str, List[str]]:
        """
        Parse MT940 content into a dictionary of fields for detailed comparison

        Returns:
            Dict mapping field tags (e.g., '20', '25', '60F') to lists of values
        """
        fields = {}
        current_field = None
        current_value = []

        for line in content.strip().split('\n'):
            line = line.strip()
            if not line or line == '-':
                continue

            # Check if line starts with a field tag
            if line.startswith(':') and line[1:].find(':') > 0:
                # Save previous field
                if current_field:
                    field_tag = current_field[1:current_field.index(':', 1)]
                    if field_tag not in fields:
                        fields[field_tag] = []
                    fields[field_tag].append('\n'.join(current_value))

                # Start new field
                colon_pos = line.index(':', 1)
                current_field = line[:colon_pos + 1]
                current_value = [line[colon_pos + 1:]]
            else:
                # Continuation line
                if current_field:
                    current_value.append(line)

        # Save last field
        if current_field:
            field_tag = current_field[1:current_field.index(':', 1)]
            if field_tag not in fields:
                fields[field_tag] = []
            fields[field_tag].append('\n'.join(current_value))

        return fields

    @staticmethod
    def normalize_field_28c(value: str) -> tuple:
        """
        Normalize Field 28C (Statement Number/Sequence Number) for comparison

        Format: SSSSS[/NNNNN] where:
        - SSSSS = Statement number (5 digits)
        - NNNNN = Sequence number (optional, 5 digits)

        Returns: (statement_number: int, sequence_number: int or None)

        Examples:
            "001" -> (1, None)
            "00001" -> (1, None)
            "00002" -> (2, None)
            "00001/00001" -> (1, 1)
        """
        parts = value.split('/')
        stmt_num = int(parts[0])  # Remove leading zeros
        seq_num = int(parts[1]) if len(parts) > 1 else None
        return (stmt_num, seq_num)

    @staticmethod
    def format_field_diff(field_name: str, generated_value: str, expected_value: str) -> str:
        """Format a field difference with visual diff markers"""
        return (
            f"  Field {field_name}:\n"
            f"    - Expected: {expected_value}\n"
            f"    + Generated: {generated_value}"
        )

    @staticmethod
    def compare_mt940_fields(generated_content: str, expected_content: str) -> Tuple[bool, List[str]]:
        """
        Compare MT940 files field by field with detailed diff output

        Returns:
            Tuple of (is_match, list_of_differences)
        """
        differences = []
        comparator = MT940Comparator()

        # Parse field-level structure
        gen_fields = comparator.parse_mt940_fields(generated_content)
        exp_fields = comparator.parse_mt940_fields(expected_content)

        # Compare meta fields (25, 28C)
        # NOTE: Field 20 is intentionally excluded from comparison because:
        # - Banks use arbitrary values (e.g., "MT940", static identifiers)
        # - csv2mt generates unique references (DATE-FILENAME format)
        # - There's no standard format - each implementation differs
        # - Field 20 is tested separately in unit tests
        meta_fields = ['25', '28C']
        meta_diffs = []

        for field_tag in meta_fields:
            gen_values = gen_fields.get(field_tag, [])
            exp_values = exp_fields.get(field_tag, [])

            # Special handling for Field 28C: Compare statement numbers (not literal strings)
            # Banks may have statement #N, we generate statement #1 - both are valid
            if field_tag == '28C':
                # Normalize and compare
                # Different statement numbers are acceptable (bank's Nth vs our 1st)
                # We only check format validity and sequence consistency
                gen_normalized = [comparator.normalize_field_28c(v) for v in gen_values]
                exp_normalized = [comparator.normalize_field_28c(v) for v in exp_values]

                # Check: All our generated statements should have same format (no sequence by default)
                gen_has_sequence = any(seq is not None for _, seq in gen_normalized)
                exp_has_sequence = any(seq is not None for _, seq in exp_normalized)

                if gen_has_sequence != exp_has_sequence:
                    # One uses sequences, other doesn't - this could be an issue
                    meta_diffs.append(
                        f"  Field :28C: Sequence number usage mismatch:\n"
                        f"    - Expected uses sequences: {exp_has_sequence}\n"
                        f"    + Generated uses sequences: {gen_has_sequence}"
                    )
                # Note: We don't compare actual statement numbers because:
                # - Bank file is statement #N in their sequence
                # - csv2mt generates statement #1 (fresh conversion)
                # - Both are correct in their context
            else:
                # Standard comparison for other fields
                if gen_values != exp_values:
                    meta_diffs.append(
                        comparator.format_field_diff(
                            f":{field_tag}:",
                            ' | '.join(gen_values) if gen_values else '(missing)',
                            ' | '.join(exp_values) if exp_values else '(missing)'
                        )
                    )

        if meta_diffs:
            differences.append("❌ META FIELDS DIFFER:\n" + "\n".join(meta_diffs))

        return len(differences) == 0, differences

    @staticmethod
    def compare_transactions(generated_content: str, expected_content: str) -> Tuple[bool, List[str]]:
        """
        Compare transactions in generated vs expected MT940 with detailed diff

        Returns:
            Tuple of (is_match, list_of_differences)
        """
        differences = []

        # Remove summary transactions before comparison
        # Banks often add zero-amount summary transactions with statement metadata
        # that aren't real transactions (identified by zero amount + NONREF + field 86 code 940)
        comparator = MT940Comparator()
        generated_filtered = comparator.remove_summary_transactions(generated_content)
        expected_filtered = comparator.remove_summary_transactions(expected_content)

        # Parse both MT940 files
        try:
            generated_statements = list(mt940.parse(generated_filtered))
            expected_statements = list(mt940.parse(expected_filtered))
        except Exception as e:
            differences.append(f"❌ PARSE ERROR: {e}")
            return False, differences

        # Compare statement count
        if len(generated_statements) != len(expected_statements):
            # Count raw transaction lines in the filtered MT940 content (after removing summaries)
            exp_raw_txn_count = expected_filtered.count('\n:61:')
            gen_raw_txn_count = generated_filtered.count('\n:61:')

            # Count total transactions as parsed by mt940 library
            exp_parsed_txn_count = sum(len(list(s.transactions)) for s in expected_statements)
            gen_parsed_txn_count = sum(len(list(s.transactions)) for s in generated_statements)

            mismatch_details = [
                f"❌ STATEMENT COUNT MISMATCH:",
                f"  - Expected: {len(expected_statements)} statement(s) (as parsed by mt940 library)",
                f"  + Generated: {len(generated_statements)} statement(s) (as parsed by mt940 library)",
                "",
                f"📊 Raw Transaction Counts (actual :61: lines in MT940):",
                f"  - Expected file: {exp_raw_txn_count} transaction line(s)",
                f"  + Generated file: {gen_raw_txn_count} transaction line(s)",
                "",
                f"📊 Parsed Transaction Counts (as interpreted by mt940 library):",
                f"  - Expected: {exp_parsed_txn_count} transaction(s) total",
                f"  + Generated: {gen_parsed_txn_count} transaction(s) total",
                ""
            ]

            # Note if there's a discrepancy between raw and parsed
            if exp_raw_txn_count != exp_parsed_txn_count:
                mismatch_details.append(
                    f"⚠️  Note: Expected file has {exp_raw_txn_count} transaction lines "
                    f"but mt940 library parsed {exp_parsed_txn_count} transactions. "
                    f"This may indicate a parsing issue with the library."
                )
                mismatch_details.append("")

            # Show summary of statements as parsed
            mismatch_details.append("📋 Expected Statements (as parsed by mt940 library):")
            for idx, stmt in enumerate(expected_statements[:5], 1):  # Show first 5
                txn_count = len(list(stmt.transactions))
                stmt_data = stmt.data if hasattr(stmt, 'data') else {}
                opening = stmt_data.get('opening_balance', 'N/A')
                closing = stmt_data.get('closing_balance', 'N/A')
                mismatch_details.append(
                    f"  Statement {idx}: {txn_count} transaction(s), "
                    f"Opening: {opening}, Closing: {closing}"
                )
            if len(expected_statements) > 5:
                mismatch_details.append(f"  ... and {len(expected_statements) - 5} more")

            mismatch_details.append("")
            mismatch_details.append("📋 Generated Statements (as parsed by mt940 library):")
            for idx, stmt in enumerate(generated_statements[:5], 1):  # Show first 5
                txn_count = len(list(stmt.transactions))
                stmt_data = stmt.data if hasattr(stmt, 'data') else {}
                opening = stmt_data.get('opening_balance', 'N/A')
                closing = stmt_data.get('closing_balance', 'N/A')
                mismatch_details.append(
                    f"  Statement {idx}: {txn_count} transaction(s), "
                    f"Opening: {opening}, Closing: {closing}"
                )
            if len(generated_statements) > 5:
                mismatch_details.append(f"  ... and {len(generated_statements) - 5} more")

            # Summary
            mismatch_details.append("")
            if exp_raw_txn_count > gen_raw_txn_count:
                missing = exp_raw_txn_count - gen_raw_txn_count
                mismatch_details.append(f"⚠️  Missing {missing} transaction(s) in generated output")
            elif gen_raw_txn_count > exp_raw_txn_count:
                extra = gen_raw_txn_count - exp_raw_txn_count
                mismatch_details.append(f"⚠️  Extra {extra} transaction(s) in generated output")

            differences.append("\n".join(mismatch_details))
            return False, differences

        # Compare each statement
        for stmt_idx, (gen_stmt, exp_stmt) in enumerate(zip(generated_statements, expected_statements)):
            stmt_diffs = []

            # Compare opening/closing balances
            if hasattr(gen_stmt, 'data') and hasattr(exp_stmt, 'data'):
                gen_data = gen_stmt.data
                exp_data = exp_stmt.data

                # Opening balance
                gen_opening = gen_data.get('opening_balance')
                exp_opening = exp_data.get('opening_balance')
                if gen_opening != exp_opening:
                    stmt_diffs.append(
                        f"  Opening Balance:\n"
                        f"    - Expected: {exp_opening}\n"
                        f"    + Generated: {gen_opening}"
                    )

                # Closing balance
                gen_closing = gen_data.get('closing_balance')
                exp_closing = exp_data.get('closing_balance')
                if gen_closing != exp_closing:
                    stmt_diffs.append(
                        f"  Closing Balance:\n"
                        f"    - Expected: {exp_closing}\n"
                        f"    + Generated: {gen_closing}"
                    )

            # Compare transaction count
            gen_txns = list(gen_stmt.transactions)
            exp_txns = list(exp_stmt.transactions)

            if len(gen_txns) != len(exp_txns):
                stmt_diffs.append(
                    f"  Transaction Count:\n"
                    f"    - Expected: {len(exp_txns)} transaction(s)\n"
                    f"    + Generated: {len(gen_txns)} transaction(s)"
                )

                # Show which transactions are missing/extra
                if len(gen_txns) < len(exp_txns):
                    missing_count = len(exp_txns) - len(gen_txns)
                    stmt_diffs.append(f"  ⚠️  Missing {missing_count} transaction(s)")
                else:
                    extra_count = len(gen_txns) - len(exp_txns)
                    stmt_diffs.append(f"  ⚠️  Extra {extra_count} transaction(s)")

            # Compare each transaction
            txn_diffs = []
            for txn_idx, (gen_txn, exp_txn) in enumerate(zip(gen_txns, exp_txns)):
                gen_data = gen_txn.data
                exp_data = exp_txn.data
                txn_diff_parts = []

                # Compare date
                gen_date = gen_data.get('date')
                exp_date = exp_data.get('date')
                if gen_date != exp_date:
                    txn_diff_parts.append(
                        f"    Date: Expected {exp_date}, Got {gen_date}"
                    )

                # Compare amount
                gen_amount = gen_data.get('amount')
                exp_amount = exp_data.get('amount')
                if gen_amount and exp_amount:
                    try:
                        gen_val = float(str(gen_amount).split()[0])
                        exp_val = float(str(exp_amount).split()[0])
                        if abs(gen_val - exp_val) > 0.01:  # Allow 1 cent difference
                            txn_diff_parts.append(
                                f"    Amount: Expected {exp_val}, Got {gen_val}"
                            )
                    except (ValueError, IndexError):
                        txn_diff_parts.append(
                            f"    Amount: Expected {exp_amount}, Got {gen_amount}"
                        )

                # NOTE: We intentionally DO NOT compare descriptions because:
                # - Bank files use structured Field 86 format with codes (073, 020, etc.)
                # - Claude extracts human-readable descriptions from PDFs
                # - These will always differ in format, but semantic content is similar
                # - Dates and amounts are the critical data to verify

                if txn_diff_parts:
                    txn_diffs.append(
                        f"  Transaction #{txn_idx + 1}:\n" + "\n".join(txn_diff_parts)
                    )

            if stmt_diffs or txn_diffs:
                stmt_header = f"❌ STATEMENT {stmt_idx + 1} DIFFERENCES:"
                all_diffs = stmt_diffs + txn_diffs
                differences.append(stmt_header + "\n" + "\n".join(all_diffs))

        return len(differences) == 0, differences


def get_test_fixtures_dir() -> Path:
    """Get the path to the E2E test fixtures directory"""
    return Path(__file__).parent / "fixtures" / "e2e"


def discover_test_cases() -> List[str]:
    """
    Discover test cases in the fixtures directory

    Each test case is a subdirectory containing:
    - statement.{pdf,csv,xlsx} - Source document
    - expected.mt940 - Expected MT940 output from bank
    """
    fixtures_dir = get_test_fixtures_dir()
    if not fixtures_dir.exists():
        return []

    test_cases = []
    for subdir in fixtures_dir.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('.'):
            # Check if directory has required files
            expected_mt940 = subdir / "expected.mt940"
            statement_files = list(subdir.glob("statement.*"))

            if expected_mt940.exists() and statement_files:
                test_cases.append(subdir.name)

    return test_cases


@pytest.mark.e2e
class TestEndToEndBankComparison:
    """End-to-end tests comparing generated MT940 against bank-provided MT940"""

    def test_fixture_directory_exists(self):
        """Verify that the E2E test fixtures directory exists"""
        fixtures_dir = get_test_fixtures_dir()
        assert fixtures_dir.exists(), (
            f"E2E test fixtures directory not found: {fixtures_dir}\n"
            "Create it with: mkdir -p tests/fixtures/e2e"
        )

    def test_has_test_cases(self):
        """Verify that at least one test case exists"""
        test_cases = discover_test_cases()
        assert len(test_cases) > 0, (
            "No test cases found in fixtures/e2e/\n"
            "Create a test case directory with:\n"
            "  - statement.pdf (or .csv, .xlsx)\n"
            "  - expected.mt940"
        )

    @pytest.mark.parametrize("test_case_name", [
        pytest.param(tc, id=tc)
        for tc in discover_test_cases()
    ])
    def test_pdf_to_mt940_matches_bank(self, test_case_name: str):
        """
        Test that Claude AI generated MT940 matches bank-provided MT940

        This test:
        1. Reads the source document (PDF/CSV/Excel)
        2. Uses Claude AI to parse it
        3. Generates MT940 format
        4. Compares against the expected MT940 from the bank
        """
        # Get test case directory
        test_case_dir = get_test_fixtures_dir() / test_case_name

        # Find statement file
        statement_files = (
            list(test_case_dir.glob("statement.pdf")) +
            list(test_case_dir.glob("statement.csv")) +
            list(test_case_dir.glob("statement.xlsx"))
        )
        assert len(statement_files) > 0, f"No statement file found in {test_case_dir}"
        statement_file = statement_files[0]

        # Load expected MT940 - try multiple encodings
        expected_mt940_file = test_case_dir / "expected.mt940"
        assert expected_mt940_file.exists(), f"Expected MT940 not found: {expected_mt940_file}"

        # Try different encodings (banks may use different character sets)
        detected_encoding = None
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-8-sig']:
            try:
                expected_mt940_content = expected_mt940_file.read_text(encoding=encoding)
                detected_encoding = encoding
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError(
                f"Could not decode {expected_mt940_file} with any common encoding.\n"
                f"Run: docker-compose exec backend python detect_encoding.py {expected_mt940_file}"
            )

        print(f"\n📄 Expected MT940 encoding: {detected_encoding}")

        # Normalize expected MT940 to UTF-8 (if not already UTF-8)
        if detected_encoding != 'utf-8':
            print(f"   Converting from {detected_encoding} to UTF-8 for comparison")
            # Already decoded as Unicode string, now we just ensure it's UTF-8 compatible
            # Re-save as UTF-8 for future comparisons
            expected_mt940_utf8_file = test_case_dir / "expected_utf8.mt940"
            expected_mt940_utf8_file.write_text(expected_mt940_content, encoding='utf-8')
            print(f"   Saved UTF-8 version: {expected_mt940_utf8_file.name}")

        # Parse statement with Claude AI
        parser = ClaudeDocumentParser()
        with open(statement_file, 'rb') as f:
            file_content = f.read()

        parsed_data = parser.parse_document(
            file_content=io.BytesIO(file_content),
            filename=statement_file.name
        )

        # Generate MT940 (already in UTF-8 as Python strings are UTF-8)
        generated_mt940_content = parser.convert_to_mt940(parsed_data)

        # Save generated MT940 for debugging (before comparison)
        output_file = test_case_dir / "generated.mt940"
        output_file.write_text(generated_mt940_content, encoding='utf-8')

        # Both MT940 contents are now UTF-8 Unicode strings - compare them
        comparator = MT940Comparator()
        all_differences = []

        # 1. Compare meta fields
        print("\n🔍 Comparing meta fields (statement headers)...")
        meta_match, meta_diffs = comparator.compare_mt940_fields(
            generated_mt940_content,
            expected_mt940_content
        )
        if not meta_match:
            all_differences.extend(meta_diffs)
            print("  ❌ Meta fields differ")
        else:
            print("  ✓ Meta fields match")

        # 2. Compare transactions
        print("🔍 Comparing transactions...")
        txn_match, txn_diffs = comparator.compare_transactions(
            generated_mt940_content,
            expected_mt940_content
        )
        if not txn_match:
            all_differences.extend(txn_diffs)
            print(f"  ❌ Found {len(txn_diffs)} difference(s)")
        else:
            print("  ✓ Transactions match")

        # Report results
        if all_differences:
            diff_report = "\n\n".join(all_differences)
            pytest.fail(
                f"\n{'='*80}\n"
                f"❌ E2E TEST FAILED: Generated MT940 does not match expected MT940\n"
                f"{'='*80}\n\n"
                f"{diff_report}\n\n"
                f"{'='*80}\n"
                f"📁 Files for comparison:\n"
                f"  Generated: {output_file}\n"
                f"  Expected:  {expected_mt940_file}\n"
                f"{'='*80}"
            )

        # Test passes
        print(f"\n✅ Test case '{test_case_name}' PASSED")
        print(f"   Generated MT940 matches bank MT940")
        print(f"   Generated: {output_file}")
        print(f"   Expected:  {expected_mt940_file}")


# Standalone test functions for pytest discovery
def test_e2e_fixture_directory_exists():
    """Wrapper for pytest discovery"""
    test = TestEndToEndBankComparison()
    test.test_fixture_directory_exists()


def test_e2e_has_test_cases():
    """Wrapper for pytest discovery"""
    test = TestEndToEndBankComparison()
    test.test_has_test_cases()
