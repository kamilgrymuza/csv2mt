from .parsers.base import BankParserRegistry
from .parsers.santander import SantanderParser
from .parsers.mbank import MBankParser

# Register all bank parsers
BankParserRegistry.register(SantanderParser)
BankParserRegistry.register(MBankParser)

__all__ = ["BankParserRegistry"]