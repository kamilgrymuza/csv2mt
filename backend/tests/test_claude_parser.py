"""
Tests for Claude AI Document Parser

These tests validate that:
1. MT940 output follows the correct format specification
2. Transaction data is correctly converted
3. Edge cases are handled properly
"""

import pytest
import re
from datetime import datetime
from app.services.claude_parser import ClaudeDocumentParser


class TestMT940FormatValidation:
    """Test that generated MT940 files follow the correct format specification"""

    def test_mt940_basic_structure(self):
        """Test that MT940 output contains all required fields in correct order"""
        parser = ClaudeDocumentParser()

        # Sample transaction data
        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-15",
                    "amount": -50.25,
                    "description": "Purchase at Store",
                    "transaction_type": "DEBIT",
                    "reference": "REF123",
                    "balance": 949.75
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "statement_start_date": "2024-01-01",
                "statement_end_date": "2024-01-31",
                "opening_balance": 1000.00,
                "closing_balance": 949.75
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        # Check required fields are present in order
        assert lines[0].startswith(":20:"), "Missing transaction reference (field 20)"
        assert lines[1].startswith(":25:"), "Missing account identification (field 25)"
        assert lines[2].startswith(":28C:"), "Missing statement number (field 28C)"
        assert lines[3].startswith(":60F:"), "Missing opening balance (field 60F)"
        assert lines[4].startswith(":61:"), "Missing statement line (field 61)"
        assert lines[5].startswith(":86:"), "Missing transaction details (field 86)"
        assert lines[6].startswith(":62F:"), "Missing closing balance (field 62F)"

    def test_mt940_field_20_format(self):
        """Test field 20 (Transaction Reference) format"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [],
            "metadata": {
                "account_number": "123456789",
                "opening_balance": 0.0,
                "closing_balance": 0.0
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        field_20 = lines[0]
        assert field_20.startswith(":20:")
        # Field 20 should have a value
        assert len(field_20) > 4

    def test_mt940_field_25_format(self):
        """Test field 25 (Account Identification) format"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [],
            "metadata": {
                "account_number": "DE89370400440532013000",
                "opening_balance": 0.0,
                "closing_balance": 0.0
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        field_25 = lines[1]
        assert field_25.startswith(":25:")
        assert "DE89370400440532013000" in field_25

    def test_mt940_field_60F_format(self):
        """Test field 60F (Opening Balance) format: C/D + YYMMDD + Currency + Amount"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [],
            "metadata": {
                "account_number": "123456789",
                "statement_start_date": "2024-01-15",
                "opening_balance": 1234.56,
                "closing_balance": 1234.56
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        field_60F = lines[3]
        # Format: :60F:C240115EUR1234.56
        assert re.match(r':60F:[CD]\d{6}EUR\d+\.\d{2}$', field_60F), \
            f"Field 60F has invalid format: {field_60F}"

    def test_mt940_field_61_format(self):
        """Test field 61 (Statement Line) format"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-15",
                    "amount": -123.45,
                    "description": "Test transaction",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": None
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "opening_balance": 500.00,
                "closing_balance": 376.55
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        field_61 = lines[4]
        # Format: :61:YYMMDDYYMMDD[C|D]amount[N]type_code
        assert re.match(r':61:\d{6}\d{6}[CD]\d+\.\d{2}N\w+', field_61), \
            f"Field 61 has invalid format: {field_61}"

    def test_mt940_field_62F_format(self):
        """Test field 62F (Closing Balance) format"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [],
            "metadata": {
                "account_number": "123456789",
                "statement_end_date": "2024-01-31",
                "opening_balance": 1000.00,
                "closing_balance": 1234.56
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        field_62F = lines[-1]
        # Format: :62F:C240131EUR1234.56
        assert re.match(r':62F:[CD]\d{6}EUR\d+\.\d{2}$', field_62F), \
            f"Field 62F has invalid format: {field_62F}"

    def test_mt940_debit_credit_indicators(self):
        """Test that debit/credit indicators are correct"""
        parser = ClaudeDocumentParser()

        # Test with credit balance (positive)
        transactions_data = {
            "transactions": [],
            "metadata": {
                "account_number": "123456789",
                "statement_start_date": "2024-01-01",
                "statement_end_date": "2024-01-31",
                "opening_balance": 1000.00,
                "closing_balance": 1500.00
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        assert ":60F:C" in mt940, "Opening balance should be Credit (C)"
        assert ":62F:C" in mt940, "Closing balance should be Credit (C)"

        # Test with debit balance (negative)
        transactions_data["metadata"]["opening_balance"] = -1000.00
        transactions_data["metadata"]["closing_balance"] = -1500.00

        mt940 = parser.convert_to_mt940(transactions_data)
        assert ":60F:D" in mt940, "Opening balance should be Debit (D)"
        assert ":62F:D" in mt940, "Closing balance should be Debit (D)"


class TestTransactionDataAccuracy:
    """Test that transaction data is accurately converted to MT940"""

    def test_transaction_amounts_accuracy(self):
        """Test that transaction amounts are correctly formatted"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-15",
                    "amount": -123.45,
                    "description": "Debit transaction",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": None
                },
                {
                    "date": "2024-01-20",
                    "amount": 678.90,
                    "description": "Credit transaction",
                    "transaction_type": "CREDIT",
                    "reference": None,
                    "balance": None
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "opening_balance": 1000.00,
                "closing_balance": 1555.45
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)

        # Check debit transaction
        assert "D123.45" in mt940, "Debit amount not correctly formatted"

        # Check credit transaction
        assert "C678.90" in mt940, "Credit amount not correctly formatted"

    def test_transaction_dates_format(self):
        """Test that dates are correctly formatted in YYMMDD format"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-03-15",
                    "amount": -100.00,
                    "description": "Test",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": None
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "statement_start_date": "2024-03-01",
                "statement_end_date": "2024-03-31",
                "opening_balance": 1000.00,
                "closing_balance": 900.00
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        # Check opening balance date
        assert "240301" in lines[3], "Opening balance date not in YYMMDD format"

        # Check transaction date
        assert "240315" in lines[4], "Transaction date not in YYMMDD format"

        # Check closing balance date
        assert "240331" in lines[-1], "Closing balance date not in YYMMDD format"

    def test_transaction_descriptions(self):
        """Test that transaction descriptions are included and properly limited"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-15",
                    "amount": -50.00,
                    "description": "This is a very long description that should be truncated to fit within the 65 character limit for MT940 field 86",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": None
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "opening_balance": 1000.00,
                "closing_balance": 950.00
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        # Find the :86: line
        field_86 = [line for line in lines if line.startswith(":86:")][0]

        # Check description is present and limited to 65 chars
        description = field_86[4:]  # Remove ":86:" prefix
        assert len(description) <= 65, f"Description exceeds 65 chars: {len(description)}"

    def test_multiple_transactions_order(self):
        """Test that multiple transactions are in correct order"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-05",
                    "amount": -100.00,
                    "description": "First transaction",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": None
                },
                {
                    "date": "2024-01-10",
                    "amount": 200.00,
                    "description": "Second transaction",
                    "transaction_type": "CREDIT",
                    "reference": None,
                    "balance": None
                },
                {
                    "date": "2024-01-15",
                    "amount": -50.00,
                    "description": "Third transaction",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": None
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "opening_balance": 1000.00,
                "closing_balance": 1050.00
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)

        # Check that transactions appear in order
        first_idx = mt940.index("First transaction")
        second_idx = mt940.index("Second transaction")
        third_idx = mt940.index("Third transaction")

        assert first_idx < second_idx < third_idx, "Transactions not in correct order"


class TestEdgeCases:
    """Test edge cases and missing data scenarios"""

    def test_missing_opening_balance(self):
        """Test handling when opening balance is not provided"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-15",
                    "amount": -50.00,
                    "description": "Test",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": 950.00
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "opening_balance": None,
                "closing_balance": None
            }
        }

        # Should not raise an error
        mt940 = parser.convert_to_mt940(transactions_data)
        assert ":60F:" in mt940, "Opening balance field should be present"
        assert ":62F:" in mt940, "Closing balance field should be present"

    def test_missing_closing_balance(self):
        """Test handling when closing balance is not provided"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-15",
                    "amount": -50.00,
                    "description": "Test",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": None
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "opening_balance": 1000.00,
                "closing_balance": None
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        # Should calculate closing balance: 1000.00 - 50.00 = 950.00
        closing_line = lines[-1]
        assert "950.00" in closing_line, "Closing balance should be calculated"

    def test_balance_calculation_from_transaction_balances(self):
        """Test that balances are derived from transaction balances when available"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-15",
                    "amount": -50.00,
                    "description": "Test",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": 950.00
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "opening_balance": None,
                "closing_balance": None
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)

        # Opening balance should be 950.00 + 50.00 = 1000.00
        assert "1000.00" in mt940.split('\n')[3], "Opening balance should be calculated from first transaction"

        # Closing balance should be 950.00
        assert "950.00" in mt940.split('\n')[-1], "Closing balance should use last transaction balance"

    def test_empty_transactions_list(self):
        """Test handling of empty transactions list"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [],
            "metadata": {
                "account_number": "123456789",
                "statement_start_date": "2024-01-01",
                "statement_end_date": "2024-01-31",
                "opening_balance": 1000.00,
                "closing_balance": 1000.00
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        # Should have header, opening balance, and closing balance
        assert len(lines) >= 4
        assert ":20:" in mt940
        assert ":25:" in mt940
        assert ":60F:" in mt940
        assert ":62F:" in mt940

    def test_missing_dates_uses_transaction_dates(self):
        """Test that missing statement dates are derived from transactions"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-15",
                    "amount": -50.00,
                    "description": "Test",
                    "transaction_type": "DEBIT",
                    "reference": None,
                    "balance": None
                },
                {
                    "date": "2024-01-25",
                    "amount": 100.00,
                    "description": "Test2",
                    "transaction_type": "CREDIT",
                    "reference": None,
                    "balance": None
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "statement_start_date": None,
                "statement_end_date": None,
                "opening_balance": 1000.00,
                "closing_balance": 1050.00
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)

        # Start date should be from first transaction
        assert "240115" in mt940.split('\n')[3], "Start date should be first transaction date"

        # End date should be from last transaction
        assert "240125" in mt940.split('\n')[-1], "End date should be last transaction date"

    def test_unknown_account_number(self):
        """Test handling when account number is missing"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [],
            "metadata": {
                "account_number": None,
                "opening_balance": 0.0,
                "closing_balance": 0.0
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)

        # Should use "UNKNOWN" as fallback
        assert "UNKNOWN" in mt940.split('\n')[1]

    def test_account_number_override(self):
        """Test that provided account number overrides metadata"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [],
            "metadata": {
                "account_number": "111111111",
                "opening_balance": 0.0,
                "closing_balance": 0.0
            }
        }

        mt940 = parser.convert_to_mt940(
            transactions_data,
            account_number="999999999"
        )

        # Should use the override account number
        assert "999999999" in mt940.split('\n')[1]
        assert "111111111" not in mt940

    def test_zero_balances(self):
        """Test handling of zero balances"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [],
            "metadata": {
                "account_number": "123456789",
                "statement_start_date": "2024-01-01",
                "statement_end_date": "2024-01-31",
                "opening_balance": 0.0,
                "closing_balance": 0.0
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)

        # Zero balances should be treated as credit
        assert ":60F:C" in mt940
        assert ":62F:C" in mt940
        assert "0.00" in mt940

    def test_negative_to_positive_transition(self):
        """Test balance that goes from negative to positive"""
        parser = ClaudeDocumentParser()

        transactions_data = {
            "transactions": [
                {
                    "date": "2024-01-15",
                    "amount": 2000.00,
                    "description": "Large deposit",
                    "transaction_type": "CREDIT",
                    "reference": None,
                    "balance": None
                }
            ],
            "metadata": {
                "account_number": "123456789",
                "opening_balance": -500.00,
                "closing_balance": 1500.00
            }
        }

        mt940 = parser.convert_to_mt940(transactions_data)
        lines = mt940.split('\n')

        # Opening should be Debit (negative)
        assert ":60F:D" in lines[3]

        # Transaction should be Credit
        assert "C2000.00" in lines[4]

        # Closing should be Credit (positive)
        assert ":62F:C" in lines[-1]
