"""
E2E Test: ING Corporate Bank Statement (Windows-1250 encoding)

This test validates the complete pipeline:
1. Read CSV file from ING corporate account (Windows-1250 encoded)
2. Parse using ClaudeDocumentParser
3. Convert to MT940 format
4. Write MT940 to disk
5. Compare with expected MT940 using mt940 library
6. Output detailed diff on mismatch for debugging

The test is designed to catch regressions as we iterate on the implementation.
"""

from .base_e2e_test import BaseE2ETest


class TestINGCorporateE2E(BaseE2ETest):
    """End-to-end test for ING corporate account statement conversion (CP1250 encoding)"""

    bank_name = "ING Corporate CSV (Windows-1250)"
    test_folder_name = "ing_corporate_cp1250"

    def test_ing_corporate_csv_to_mt940(self, input_file, expected_mt940, output_mt940):
        """Test complete CSV → MT940 conversion pipeline for ING Corporate"""
        self.run_conversion_test(input_file, expected_mt940, output_mt940)
