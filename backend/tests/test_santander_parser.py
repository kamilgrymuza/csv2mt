import pytest
from datetime import date
from decimal import Decimal
from app.services.parsers.santander import SantanderParser
from app.services.parsers.base import BankParserError


class TestSantanderParser:
    def setup_method(self):
        self.parser = SantanderParser()

    def test_bank_name(self):
        assert self.parser.bank_name == "Santander"

    def test_parse_valid_csv(self):
        csv_content = """2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA UL. BUKOWIŃSKA 24C/8 02-703 WARSZAWA,PLN,"-2317,82","-3681,08",2,
19-09-2025,19-09-2025,Opłata za odnowienie kred. w rach. pł.,,,"-500,00","-3681,08",1,
08-09-2025,08-09-2025,Splata karty kredytowej,Centrum Kart,98 1090 1489 4000 0001 1351 0822,"-637,56","-3181,08",2,"""

        result = self.parser.parse(csv_content)

        # Check header
        assert result.header.generation_date == date(2025, 9, 22)
        assert result.header.start_date == date(2025, 9, 1)
        assert result.header.account_number == "64 1500 1878 1018 7023 1577 0000"
        assert result.header.account_holder == "KAMIL GRYMUZA UL. BUKOWIŃSKA 24C/8 02-703 WARSZAWA"
        assert result.header.currency == "PLN"
        assert result.header.initial_balance == Decimal("-2317.82")
        assert result.header.end_balance == Decimal("-3681.08")
        assert result.header.number_of_entries == 2

        # Check transactions
        assert len(result.transactions) == 2

        # First transaction
        tx1 = result.transactions[0]
        assert tx1.registered_date == date(2025, 9, 19)
        assert tx1.initiated_date == date(2025, 9, 19)
        assert tx1.title == "Opłata za odnowienie kred. w rach. pł."
        assert tx1.other_party_info is None
        assert tx1.other_party_account is None
        assert tx1.amount == Decimal("-500.00")
        assert tx1.resulting_balance == Decimal("-3681.08")
        assert tx1.entry_number == 1

        # Second transaction
        tx2 = result.transactions[1]
        assert tx2.registered_date == date(2025, 9, 8)
        assert tx2.initiated_date == date(2025, 9, 8)
        assert tx2.title == "Splata karty kredytowej"
        assert tx2.other_party_info == "Centrum Kart"
        assert tx2.other_party_account == "98 1090 1489 4000 0001 1351 0822"
        assert tx2.amount == Decimal("-637.56")
        assert tx2.resulting_balance == Decimal("-3181.08")
        assert tx2.entry_number == 2

    def test_parse_empty_csv(self):
        with pytest.raises(BankParserError, match="CSV file must contain at least a header and one transaction"):
            self.parser.parse("")

    def test_parse_header_only(self):
        csv_content = "2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA,PLN,\"-2317,82\",\"-3681,08\",1,"
        with pytest.raises(BankParserError, match="CSV file must contain at least a header and one transaction"):
            self.parser.parse(csv_content)

    def test_parse_invalid_header_format(self):
        csv_content = """invalid,header,format
19-09-2025,19-09-2025,Opłata za odnowienie kred. w rach. pł.,,,"-500,00","-3681,08",1,"""
        with pytest.raises(BankParserError, match="Header row must contain at least 8 fields"):
            self.parser.parse(csv_content)

    def test_parse_invalid_transaction_format(self):
        csv_content = """2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA,PLN,"-2317,82","-3681,08",1,
invalid,transaction,format"""
        with pytest.raises(BankParserError, match="Error parsing transaction row 1"):
            self.parser.parse(csv_content)

    def test_parse_transaction_count_mismatch(self):
        csv_content = """2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA,PLN,"-2317,82","-3681,08",2,
19-09-2025,19-09-2025,Opłata za odnowienie kred. w rach. pł.,,,"-500,00","-3681,08",1,"""
        with pytest.raises(BankParserError, match="Number of transactions .* doesn't match header count"):
            self.parser.parse(csv_content)

    def test_parse_amount_with_quotes(self):
        csv_content = """2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA,PLN,"-2317,82","-3681,08",1,
19-09-2025,19-09-2025,Test transaction,,,"-500,00","-3681,08",1,"""

        result = self.parser.parse(csv_content)
        assert result.transactions[0].amount == Decimal("-500.00")

    def test_parse_amount_invalid_format(self):
        csv_content = """2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA,PLN,"-2317,82","-3681,08",1,
19-09-2025,19-09-2025,Test transaction,,,invalid_amount,"-3681,08",1,"""
        with pytest.raises(BankParserError, match="Invalid amount format"):
            self.parser.parse(csv_content)