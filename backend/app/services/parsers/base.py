from abc import ABC, abstractmethod
from typing import List
from io import StringIO
import csv
from ..models import BankStatement


class BankParserError(Exception):
    pass


class BaseBankParser(ABC):
    @property
    @abstractmethod
    def bank_name(self) -> str:
        pass

    @abstractmethod
    def parse(self, csv_content: str) -> BankStatement:
        pass

    def _parse_csv_content(self, csv_content: str) -> List[List[str]]:
        try:
            csv_file = StringIO(csv_content)
            reader = csv.reader(csv_file)
            return list(reader)
        except Exception as e:
            raise BankParserError(f"Failed to parse CSV content: {str(e)}")

    def validate_and_parse(self, csv_content: str) -> BankStatement:
        try:
            return self.parse(csv_content)
        except Exception as e:
            raise BankParserError(f"Error parsing {self.bank_name} statement: {str(e)}")


class BankParserRegistry:
    _parsers = {}

    @classmethod
    def register(cls, parser_class: type[BaseBankParser]):
        parser_instance = parser_class()
        cls._parsers[parser_instance.bank_name.lower()] = parser_instance

    @classmethod
    def get_parser(cls, bank_name: str) -> BaseBankParser:
        parser = cls._parsers.get(bank_name.lower())
        if not parser:
            available_banks = ", ".join(cls._parsers.keys())
            raise BankParserError(f"Bank '{bank_name}' not supported. Available banks: {available_banks}")
        return parser

    @classmethod
    def get_supported_banks(cls) -> List[str]:
        return list(cls._parsers.keys())