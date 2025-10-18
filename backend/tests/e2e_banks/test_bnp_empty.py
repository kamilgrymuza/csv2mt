"""
E2E Test: BNP Paribas Empty Statement

This test validates the handling of completely empty bank statements:
1. Read XLSX file with no data (no dates, no transactions, no balances)
2. Parse using ClaudeDocumentParser
3. Attempt to convert to MT940 format
4. Verify EmptyStatementError is raised (cannot generate valid MT940 without dates)

This ensures the system handles edge cases gracefully and provides meaningful errors.
"""

from .base_e2e_test import BaseE2ETest
from app.services.claude_parser import EmptyStatementError


class TestBNPEmptyE2E(BaseE2ETest):
    """End-to-end test for BNP Paribas empty statement conversion"""

    bank_name = "BNP Paribas Empty XLSX"
    test_folder_name = "bnp_empty"

    def test_bnp_empty_xlsx_raises_error(self, input_file, expected_mt940, output_mt940):
        """Test that completely empty statement raises EmptyStatementError during MT940 conversion"""
        self.run_conversion_test(
            input_file,
            expected_mt940,
            output_mt940,
            allow_empty=True,
            expect_exception=(EmptyStatementError, "does not contain valid transaction data")
        )
