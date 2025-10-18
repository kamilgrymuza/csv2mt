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

from .base_e2e_test import BaseE2ETest


class TestINGCorporatePDFE2E(BaseE2ETest):
    """End-to-end test for ING Corporate PDF bank statement conversion"""

    bank_name = "ING Corporate PDF"
    test_folder_name = "ing_corporate_pdf"

    def test_ing_corporate_pdf_to_mt940(self, input_file, expected_mt940, output_mt940):
        """Test complete PDF → MT940 conversion pipeline for ING Corporate"""
        self.run_conversion_test(input_file, expected_mt940, output_mt940)
