"""
E2E Test: Santander Individual Bank Statement

This test validates the complete pipeline:
1. Read CSV file from Santander individual account
2. Parse using ClaudeDocumentParser
3. Convert to MT940 format
4. Write MT940 to disk
5. Compare with expected MT940 using mt940 library
6. Output detailed diff on mismatch for debugging

The test is designed to catch regressions as we iterate on the implementation.
"""

from .base_e2e_test import BaseE2ETest


class TestSantanderIndividualE2E(BaseE2ETest):
    """End-to-end test for Santander individual account statement conversion"""

    bank_name = "Santander Individual CSV"
    test_folder_name = "santander_individual"

    def test_santander_csv_to_mt940(self, input_file, expected_mt940, output_mt940):
        """Test complete CSV → MT940 conversion pipeline for Santander"""
        self.run_conversion_test(input_file, expected_mt940, output_mt940)
