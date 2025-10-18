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

from .base_e2e_test import BaseE2ETest


class TestMBankEmptyE2E(BaseE2ETest):
    """End-to-end test for mBank empty statement conversion"""

    bank_name = "mBank Empty CSV"
    test_folder_name = "mbank_empty"

    def test_mbank_empty_csv_to_mt940(self, input_file, expected_mt940, output_mt940):
        """Test CSV → MT940 conversion for empty statement (no transactions)"""
        self.run_conversion_test(input_file, expected_mt940, output_mt940, allow_empty=True)
