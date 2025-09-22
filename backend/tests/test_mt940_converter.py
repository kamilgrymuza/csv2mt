import pytest
from datetime import date
from decimal import Decimal
from app.services.mt940_converter import MT940Converter, MT940ConverterError
from app.services.models import BankStatement, BankStatementHeader, BankTransaction


class TestMT940Converter:
    def test_convert_simple_statement(self):
        header = BankStatementHeader(
            generation_date=date(2025, 9, 22),
            start_date=date(2025, 9, 1),
            end_date=date(2025, 9, 1),
            account_holder="KAMIL GRYMUZA",
            account_number="64 1500 1878 1018 7023 1577 0000",
            currency="PLN",
            initial_balance=Decimal("-2317.82"),
            end_balance=Decimal("-3681.08"),
            number_of_entries=1
        )

        transaction = BankTransaction(
            registered_date=date(2025, 9, 19),
            initiated_date=date(2025, 9, 19),
            title="Test payment",
            other_party_info="Test party",
            other_party_account="12 3456 7890",
            amount=Decimal("-500.00"),
            resulting_balance=Decimal("-3681.08"),
            entry_number=1
        )

        statement = BankStatement(header=header, transactions=[transaction])
        result = MT940Converter.convert(statement)

        lines = result.split('\n')

        # Check basic structure
        assert lines[0].startswith(":20:")
        assert lines[1].startswith(":25:")
        assert lines[2].startswith(":28C:")
        assert lines[3].startswith(":60F:")
        assert lines[4].startswith(":61:")
        assert lines[5].startswith(":86:")
        assert lines[6].startswith(":62F:")
        assert lines[7] == "-"

        # Check account reference (MT940 field 20 is limited to 16 chars)
        assert "64 1500 1878 101" in lines[0]

        # Check account identification
        assert "64 1500 1878 1018 7023 1577 0000" in lines[1]

        # Check opening balance (debit)
        assert ":60F:D250901PLN2317,82" in lines[3]

        # Check transaction
        assert ":61:250919" in lines[4]  # Value date
        assert "0919" in lines[4]        # Entry date
        assert "D500,00" in lines[4]     # Debit amount
        assert "NTRF" in lines[4]        # Transaction type

        # Check closing balance (debit)
        assert ":62F:D250901PLN3681,08" in lines[6]

    def test_convert_positive_balance(self):
        header = BankStatementHeader(
            generation_date=date(2025, 9, 22),
            start_date=date(2025, 9, 1),
            end_date=date(2025, 9, 1),
            account_holder="TEST USER",
            account_number="12345678901234567890",
            currency="EUR",
            initial_balance=Decimal("1000.00"),
            end_balance=Decimal("1500.00"),
            number_of_entries=1
        )

        transaction = BankTransaction(
            registered_date=date(2025, 9, 15),
            initiated_date=date(2025, 9, 15),
            title="Salary payment",
            other_party_info=None,
            other_party_account=None,
            amount=Decimal("500.00"),
            resulting_balance=Decimal("1500.00"),
            entry_number=1
        )

        statement = BankStatement(header=header, transactions=[transaction])
        result = MT940Converter.convert(statement)

        lines = result.split('\n')

        # Check credit opening balance
        assert ":60F:C250901EUR1000,00" in lines[3]

        # Check credit transaction
        assert "C500,00" in lines[4]

        # Check credit closing balance
        assert ":62F:C250901EUR1500,00" in lines[6]

    def test_split_description_short(self):
        result = MT940Converter._split_description("Short description")
        assert result == ["Short description"]

    def test_split_description_long(self):
        long_desc = "This is a very long description that should be split into multiple lines because it exceeds the maximum length allowed"
        result = MT940Converter._split_description(long_desc, max_length=30)

        assert len(result) > 1
        for line in result:
            assert len(line) <= 30

    def test_split_description_no_spaces(self):
        no_spaces = "A" * 100
        result = MT940Converter._split_description(no_spaces, max_length=30)

        assert len(result) > 1
        for line in result[:-1]:  # All but the last line should be exactly 30 chars
            assert len(line) == 30

    def test_convert_empty_transaction_list(self):
        header = BankStatementHeader(
            generation_date=date(2025, 9, 22),
            start_date=date(2025, 9, 1),
            end_date=date(2025, 9, 1),
            account_holder="TEST USER",
            account_number="12345678901234567890",
            currency="PLN",
            initial_balance=Decimal("0.00"),
            end_balance=Decimal("0.00"),
            number_of_entries=0
        )

        statement = BankStatement(header=header, transactions=[])
        result = MT940Converter.convert(statement)

        lines = result.split('\n')

        # Should have header, opening balance, statement number, closing balance, and end marker
        assert len(lines) == 6
        assert lines[5] == "-"