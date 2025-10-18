"""
E2E Test: mBank Simple Statement

This test validates the complete pipeline:
1. Read CSV file from mBank individual account
2. Parse using ClaudeDocumentParser
3. Convert to MT940 format
4. Write MT940 to disk
5. Compare with expected MT940 using mt940 library
6. Output detailed diff on mismatch for debugging

The test is designed to catch regressions as we iterate on the implementation.
"""

from .base_e2e_test import BaseE2ETest


class TestMBankSimpleE2E(BaseE2ETest):
    """End-to-end test for mBank simple account statement conversion"""

    bank_name = "mBank Simple CSV"
    test_folder_name = "mbank_simple"

    def test_mbank_csv_to_mt940(self, input_file, expected_mt940, output_mt940):
        """Test complete CSV → MT940 conversion pipeline for mBank"""
        self.run_conversion_test(input_file, expected_mt940, output_mt940)
