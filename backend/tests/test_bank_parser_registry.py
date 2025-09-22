import pytest
from app.services.parsers.base import BankParserRegistry, BankParserError, BaseBankParser
from app.services.parsers.santander import SantanderParser
from app.services.parsers.mbank import MBankParser


class MockParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "MockBank"

    def parse(self, csv_content: str):
        return None


class TestBankParserRegistry:
    def test_register_and_get_parser(self):
        # Register a mock parser
        BankParserRegistry.register(MockParser)

        # Get the parser
        parser = BankParserRegistry.get_parser("MockBank")
        assert isinstance(parser, MockParser)

        # Test case insensitive lookup
        parser = BankParserRegistry.get_parser("mockbank")
        assert isinstance(parser, MockParser)

    def test_get_unsupported_bank(self):
        with pytest.raises(BankParserError, match="Bank 'UnsupportedBank' not supported"):
            BankParserRegistry.get_parser("UnsupportedBank")

    def test_get_supported_banks(self):
        # Should include at least Santander and mBank (registered in __init__.py)
        banks = BankParserRegistry.get_supported_banks()
        assert isinstance(banks, list)
        assert "santander" in banks
        assert "mbank" in banks

    def test_santander_is_registered(self):
        # Test that Santander parser is properly registered
        parser = BankParserRegistry.get_parser("Santander")
        assert isinstance(parser, SantanderParser)

    def test_mbank_is_registered(self):
        # Test that mBank parser is properly registered
        parser = BankParserRegistry.get_parser("mBank")
        assert isinstance(parser, MBankParser)

    def test_case_insensitive_bank_names(self):
        # Test various cases for Santander
        parser1 = BankParserRegistry.get_parser("santander")
        parser2 = BankParserRegistry.get_parser("SANTANDER")
        parser3 = BankParserRegistry.get_parser("Santander")
        assert all(isinstance(p, SantanderParser) for p in [parser1, parser2, parser3])

        # Test various cases for mBank
        parser4 = BankParserRegistry.get_parser("mbank")
        parser5 = BankParserRegistry.get_parser("MBANK")
        parser6 = BankParserRegistry.get_parser("mBank")
        assert all(isinstance(p, MBankParser) for p in [parser4, parser5, parser6])