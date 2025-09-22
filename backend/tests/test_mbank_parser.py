import pytest
from datetime import date
from decimal import Decimal
from app.services.parsers.mbank import MBankParser
from app.services.parsers.base import BankParserError


class TestMBankParser:
    def setup_method(self):
        self.parser = MBankParser()

    def test_bank_name(self):
        assert self.parser.bank_name == "mBank"

    def test_parse_valid_csv_with_transactions(self):
        csv_content = """mBank S.A. Bankowość Detaliczna;
        Skrytka Pocztowa 2108;
        90-959 Łódź 2;
        www.mBank.pl;
        mLinia: 801 300 800;
        +48 (42) 6 300 800;


#Klient;
KAMIL GRYMUZA;

Lista operacji;

#Za okres:;
22.09.2024;22.09.2025;

#zgodnie z wybranymi filtrami wyszukiwania;
      #dla rachunków:;
      eKonto - 95114020040000370280414931;

      #Lista nie jest dokumentem w rozumieniu art. 7 Ustawy Prawo Bankowe (Dz. U. Nr 140 z 1997 roku, poz.939 z późniejszymi zmianami), ponieważ operacje można samodzielnie edytować.;

      #Waluta;#Wpływy;#Wydatki;
PLN;301 132,84;-321 430,40;

#Data operacji;#Opis operacji;#Rachunek;#Kategoria;#Kwota;
2025-07-18;"KAMIL GRYMUZA, PRZELEW ŚRODKÓW                                                                         PRZELEW ZEWNĘTRZNY WYCHODZĄCY                                                     34105010541000009803463893  ";"eKonto 9511 ... 4931";"Bez kategorii";-40 000,00 PLN;;
2025-07-18;"KAMIL GRYMUZA, PRZELEW ŚRODKÓW  UL.BUKOWIŃSKA 24C M.8              02-703 WARSZAWA                     PRZELEW WEWNĘTRZNY PRZYCHODZĄCY                                                   72114020040000300280415009  ";"eKonto 9511 ... 4931";"Przelew własny";40 000,00 PLN;;"""

        result = self.parser.parse(csv_content)

        # Check header
        assert result.header.account_holder == "KAMIL GRYMUZA"
        assert result.header.start_date == date(2024, 9, 22)
        assert result.header.end_date == date(2025, 9, 22)
        assert result.header.account_number == "95114020040000370280414931"
        assert result.header.currency == "PLN"
        assert result.header.number_of_entries == 2

        # Check transactions
        assert len(result.transactions) == 2

        # First transaction
        tx1 = result.transactions[0]
        assert tx1.registered_date == date(2025, 7, 18)
        assert tx1.initiated_date == date(2025, 7, 18)
        assert "KAMIL GRYMUZA, PRZELEW ŚRODKÓW" in tx1.title
        assert tx1.amount == Decimal("-40000.00")
        assert tx1.entry_number == 1

        # Second transaction
        tx2 = result.transactions[1]
        assert tx2.registered_date == date(2025, 7, 18)
        assert tx2.initiated_date == date(2025, 7, 18)
        assert "PRZELEW WEWNĘTRZNY PRZYCHODZĄCY" in tx2.title
        assert tx2.amount == Decimal("40000.00")
        assert tx2.entry_number == 2

    def test_parse_empty_csv(self):
        csv_content = """mBank S.A. Bankowość Detaliczna;
        Skrytka Pocztowa 2108;
        90-959 Łódź 2;
        www.mBank.pl;
        mLinia: 801 300 800;
        +48 (42) 6 300 800;


#Klient;
KAMIL GRYMUZA;

Lista operacji;

#Za okres:;
01.09.2025;22.09.2025;

#zgodnie z wybranymi filtrami wyszukiwania;
      #dla rachunków:;
      eKonto - 95114020040000370280414931;

      #Lista nie jest dokumentem w rozumieniu art. 7 Ustawy Prawo Bankowe (Dz. U. Nr 140 z 1997 roku, poz.939 z późniejszymi zmianami), ponieważ operacje można samodzielnie edytować.;

      #Waluta;#Wpływy;#Wydatki;

#Data operacji;#Opis operacji;#Rachunek;#Kategoria;#Kwota;"""

        result = self.parser.parse(csv_content)

        # Check header
        assert result.header.account_holder == "KAMIL GRYMUZA"
        assert result.header.start_date == date(2025, 9, 1)
        assert result.header.end_date == date(2025, 9, 22)
        assert result.header.account_number == "95114020040000370280414931"
        assert result.header.currency == "PLN"
        assert result.header.number_of_entries == 0

        # Check no transactions
        assert len(result.transactions) == 0

    def test_parse_incomplete_csv(self):
        csv_content = "mBank S.A.;incomplete"
        with pytest.raises(BankParserError, match="mBank CSV file appears to be incomplete"):
            self.parser.parse(csv_content)

    def test_parse_missing_client_info(self):
        csv_content = """mBank S.A. Bankowość Detaliczna;
        Skrytka Pocztowa 2108;
        90-959 Łódź 2;
        www.mBank.pl;
        mLinia: 801 300 800;
        +48 (42) 6 300 800;


Lista operacji;

#Za okres:;
22.09.2024;22.09.2025;

#Data operacji;#Opis operacji;#Rachunek;#Kategoria;#Kwota;"""

        with pytest.raises(BankParserError, match="Client information not found"):
            self.parser.parse(csv_content)

    def test_parse_missing_period_info(self):
        csv_content = """mBank S.A. Bankowość Detaliczna;
        Skrytka Pocztowa 2108;
        90-959 Łódź 2;
        www.mBank.pl;
        mLinia: 801 300 800;
        +48 (42) 6 300 800;


#Klient;
KAMIL GRYMUZA;

Lista operacji;

#Data operacji;#Opis operacji;#Rachunek;#Kategoria;#Kwota;"""

        with pytest.raises(BankParserError, match="Period information not found"):
            self.parser.parse(csv_content)

    def test_parse_missing_account_info(self):
        csv_content = """mBank S.A. Bankowość Detaliczna;
        Skrytka Pocztowa 2108;
        90-959 Łódź 2;
        www.mBank.pl;
        mLinia: 801 300 800;
        +48 (42) 6 300 800;


#Klient;
KAMIL GRYMUZA;

Lista operacji;

#Za okres:;
22.09.2024;22.09.2025;

#Data operacji;#Opis operacji;#Rachunek;#Kategoria;#Kwota;"""

        with pytest.raises(BankParserError, match="Account information not found"):
            self.parser.parse(csv_content)

    def test_parse_amount_formats(self):
        # Test various amount formats that mBank might use
        assert self.parser._parse_amount("1 000,50 PLN") == Decimal("1000.50")
        assert self.parser._parse_amount("-1 000,50 PLN") == Decimal("-1000.50")
        assert self.parser._parse_amount("40 000,00 PLN") == Decimal("40000.00")
        assert self.parser._parse_amount("-40 000,00 PLN") == Decimal("-40000.00")
        assert self.parser._parse_amount("100,00PLN") == Decimal("100.00")

    def test_parse_amount_invalid_format(self):
        with pytest.raises(BankParserError, match="Invalid amount format"):
            self.parser._parse_amount("invalid_amount")

    def test_extract_other_party_info(self):
        # Test external party with address info
        description1 = "SOME COMPANY LTD AL. MAIN STREET 27 00-867 CITYNAME, zasilenie konta"
        assert self.parser._extract_other_party_info(description1) == "SOME COMPANY LTD AL. MAIN STREET 27 00-867 CITYNAME"

        # Test self-transfer (should return None)
        description2 = "JAN KOWALSKI, PRZELEW ŚRODKÓW"
        assert self.parser._extract_other_party_info(description2) is None

        # Test external company
        description3 = "EXTERNAL COMPANY, transfer description"
        assert self.parser._extract_other_party_info(description3) == "EXTERNAL COMPANY"

        # Test external transfer with meaningful text
        description4 = "PRZELEW ZEWNĘTRZNY PRZYCHODZĄCY ABC COMPANY SP Z O O 12345678901234567890123456"
        result = self.parser._extract_other_party_info(description4)
        assert result == "ABC COMPANY SP Z O"

        # Test self-transfer with address info (should extract address part)
        description5 = "JAN KOWALSKI, PRZELEW ŚRODKÓW, UL. TESTOWA 123 12-345 TESTCITY"
        result = self.parser._extract_other_party_info(description5)
        assert result == "UL. TESTOWA 123 12-345 TESTCITY"

    def test_extract_other_party_account(self):
        description_with_account = "PRZELEW ZEWNĘTRZNY WYCHODZĄCY 34105010541000009803463893"
        result = self.parser._extract_other_party_account(description_with_account)
        assert result == "34105010541000009803463893"

        description_without_account = "Simple transfer without account"
        result = self.parser._extract_other_party_account(description_without_account)
        assert result is None

    def test_find_data_section_start(self):
        rows = [
            ["mBank S.A."],
            ["#Klient", "KAMIL GRYMUZA"],
            ["#Data operacji", "#Opis operacji", "#Rachunek", "#Kategoria", "#Kwota"],
            ["2025-07-18", "Some transaction", "eKonto", "Category", "100,00 PLN"]
        ]

        data_start = self.parser._find_data_section_start(rows)
        assert data_start == 2

    def test_find_data_section_start_not_found(self):
        rows = [
            ["mBank S.A."],
            ["#Klient", "KAMIL GRYMUZA"],
            ["Some other data"]
        ]

        data_start = self.parser._find_data_section_start(rows)
        assert data_start is None