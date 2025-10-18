"""
E2E Test: BNP Paribas Corporate Account (Excel)

This test validates the complete pipeline:
1. Read XLSX file from BNP Paribas corporate account
2. Parse using ClaudeDocumentParser
3. Convert to MT940 format
4. Write MT940 to disk
5. Compare with expected MT940 using mt940 library
6. Output detailed diff on mismatch for debugging

The test is designed to catch regressions as we iterate on the implementation.
"""

from .base_e2e_test import BaseE2ETest


class TestBNPFirmoweE2E(BaseE2ETest):
    """End-to-end test for BNP Paribas corporate Excel statement conversion"""

    bank_name = "BNP Paribas Corporate XLSX"
    test_folder_name = "bnp_firmowe"

    def test_bnp_xlsx_to_mt940(self, input_file, expected_mt940, output_mt940):
        """Test complete XLSX → MT940 conversion pipeline for BNP Paribas"""
        self.run_conversion_test(input_file, expected_mt940, output_mt940)
