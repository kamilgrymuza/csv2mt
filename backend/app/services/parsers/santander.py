from datetime import datetime
from decimal import Decimal
from typing import List
from .base import BaseBankParser, BankParserError
from ..models import BankStatement, BankStatementHeader, BankTransaction


class SantanderParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "Santander"

    def parse(self, csv_content: str) -> BankStatement:
        rows = self._parse_csv_content(csv_content)

        if len(rows) < 2:
            raise BankParserError("CSV file must contain at least a header and one transaction")

        header = self._parse_header(rows[0])
        transactions = []

        for i, row in enumerate(rows[1:], start=1):
            try:
                transaction = self._parse_transaction(row)
                transactions.append(transaction)
            except Exception as e:
                raise BankParserError(f"Error parsing transaction row {i}: {str(e)}")

        if len(transactions) != header.number_of_entries:
            raise BankParserError(
                f"Number of transactions ({len(transactions)}) doesn't match header count ({header.number_of_entries})"
            )

        return BankStatement(header=header, transactions=transactions)

    def _parse_header(self, header_row: List[str]) -> BankStatementHeader:
        if len(header_row) < 8:
            raise BankParserError("Header row must contain at least 8 fields")

        try:
            generation_date = datetime.strptime(header_row[0], "%Y-%m-%d").date()
            start_date = datetime.strptime(header_row[1], "%d-%m-%Y").date()
            account_number = header_row[2].strip("'")
            account_holder = header_row[3]
            currency = header_row[4]
            initial_balance = self._parse_amount(header_row[5])
            end_balance = self._parse_amount(header_row[6])
            number_of_entries = int(header_row[7])

            end_date = start_date

            return BankStatementHeader(
                generation_date=generation_date,
                start_date=start_date,
                end_date=end_date,
                account_holder=account_holder,
                account_number=account_number,
                currency=currency,
                initial_balance=initial_balance,
                end_balance=end_balance,
                number_of_entries=number_of_entries
            )
        except (ValueError, IndexError) as e:
            raise BankParserError(f"Invalid header format: {str(e)}")

    def _parse_transaction(self, transaction_row: List[str]) -> BankTransaction:
        if len(transaction_row) < 8:
            raise BankParserError("Transaction row must contain at least 8 fields")

        try:
            registered_date = datetime.strptime(transaction_row[0], "%d-%m-%Y").date()
            initiated_date = datetime.strptime(transaction_row[1], "%d-%m-%Y").date()
            title = transaction_row[2]
            other_party_info = transaction_row[3] if transaction_row[3] else None
            other_party_account = transaction_row[4] if transaction_row[4] else None
            amount = self._parse_amount(transaction_row[5])
            resulting_balance = self._parse_amount(transaction_row[6])
            entry_number = int(transaction_row[7])

            return BankTransaction(
                registered_date=registered_date,
                initiated_date=initiated_date,
                title=title,
                other_party_info=other_party_info,
                other_party_account=other_party_account,
                amount=amount,
                resulting_balance=resulting_balance,
                entry_number=entry_number
            )
        except (ValueError, IndexError) as e:
            raise BankParserError(f"Invalid transaction format: {str(e)}")

    def _parse_amount(self, amount_str: str) -> Decimal:
        try:
            amount_str = amount_str.strip('"').replace(",", ".")
            return Decimal(amount_str)
        except Exception as e:
            raise BankParserError(f"Invalid amount format '{amount_str}': {str(e)}")