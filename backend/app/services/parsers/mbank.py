from datetime import datetime
from decimal import Decimal
from typing import List
import re
from .base import BaseBankParser, BankParserError
from ..models import BankStatement, BankStatementHeader, BankTransaction


class MBankParser(BaseBankParser):
    @property
    def bank_name(self) -> str:
        return "mBank"

    def parse(self, csv_content: str) -> BankStatement:
        # mBank uses semicolon as delimiter, so we need to parse it manually
        lines = csv_content.strip().split('\n')
        rows = []
        for line in lines:
            # Split by semicolon and clean up
            row = [cell.strip() for cell in line.split(';')]
            rows.append(row)

        if len(rows) < 10:
            raise BankParserError("mBank CSV file appears to be incomplete")

        # Extract header information
        header = self._parse_header(rows)

        # Find the data section start
        data_start_idx = self._find_data_section_start(rows)

        # Parse transactions
        transactions = []
        if data_start_idx is not None and data_start_idx + 1 < len(rows):
            for i, row in enumerate(rows[data_start_idx + 1:], start=1):
                if len(row) >= 5 and row[0] and not row[0].startswith('#'):
                    try:
                        transaction = self._parse_transaction(row, i)
                        transactions.append(transaction)
                    except Exception as e:
                        raise BankParserError(f"Error parsing transaction row {i}: {str(e)}")

        # Update header with actual transaction count
        header.number_of_entries = len(transactions)

        # Calculate end balance based on transactions
        if transactions:
            header.end_balance = transactions[-1].resulting_balance

        return BankStatement(header=header, transactions=transactions)

    def _find_data_section_start(self, rows: List[List[str]]) -> int:
        """Find the row index where transaction data starts"""
        for i, row in enumerate(rows):
            if (len(row) >= 5 and
                row[0] == "#Data operacji" and
                row[1] == "#Opis operacji" and
                row[2] == "#Rachunek" and
                row[3] == "#Kategoria" and
                row[4] == "#Kwota"):
                return i
        return None

    def _parse_header(self, rows: List[List[str]]) -> BankStatementHeader:
        try:
            # Extract client name - it's on the line after #Klient
            client_name = None
            for i, row in enumerate(rows):
                if len(row) > 0 and row[0] == "#Klient":
                    if i + 1 < len(rows) and len(rows[i + 1]) > 0:
                        client_name = rows[i + 1][0].strip()
                        break

            if not client_name:
                raise BankParserError("Client information not found")
            account_holder = client_name

            # Extract period dates
            start_date = None
            end_date = None
            for i, row in enumerate(rows):
                if len(row) > 0 and row[0] == "#Za okres:":
                    if i + 1 < len(rows) and len(rows[i + 1]) >= 3:
                        period_data = rows[i + 1]
                        start_date = datetime.strptime(period_data[0], "%d.%m.%Y").date()
                        end_date = datetime.strptime(period_data[1], "%d.%m.%Y").date()
                        break

            if not start_date or not end_date:
                raise BankParserError("Period information not found")
            generation_date = datetime.now().date()

            # Extract account number
            account_number = None
            for row in rows:
                for cell in row:
                    if "eKonto -" in cell:
                        account_number = cell.replace("eKonto - ", "").strip()
                        break
                if account_number:
                    break

            if not account_number:
                raise BankParserError("Account information not found")

            # Extract currency (default to PLN for mBank)
            currency = "PLN"
            initial_balance = Decimal("0.00")  # mBank doesn't provide opening balance
            end_balance = Decimal("0.00")  # Will be calculated from transactions

            return BankStatementHeader(
                generation_date=generation_date,
                start_date=start_date,
                end_date=end_date,
                account_holder=account_holder,
                account_number=account_number,
                currency=currency,
                initial_balance=initial_balance,
                end_balance=end_balance,
                number_of_entries=0  # Will be updated after parsing transactions
            )
        except (ValueError, IndexError) as e:
            raise BankParserError(f"Invalid mBank header format: {str(e)}")

    def _find_row_by_prefix(self, rows: List[List[str]], prefix: str) -> List[str]:
        """Find a row that starts with the given prefix"""
        for row in rows:
            if len(row) > 0 and any(cell.startswith(prefix) for cell in row):
                return row
        return None

    def _parse_transaction(self, transaction_row: List[str], entry_number: int) -> BankTransaction:
        if len(transaction_row) < 5:
            raise BankParserError("mBank transaction row must contain at least 5 fields")

        try:
            # Parse date
            date_str = transaction_row[0].strip()
            transaction_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Parse description
            description = transaction_row[1].strip('"').strip()

            # Note: account_info (column 2) and category (column 3) are available but not used

            # Parse amount
            amount_str = transaction_row[4].strip()
            amount = self._parse_amount(amount_str)

            # Extract other party info from description if possible
            other_party_info = self._extract_other_party_info(description)
            other_party_account = self._extract_other_party_account(description)

            return BankTransaction(
                registered_date=transaction_date,
                initiated_date=transaction_date,
                title=description,
                other_party_info=other_party_info,
                other_party_account=other_party_account,
                amount=amount,
                resulting_balance=Decimal("0.00"),  # mBank doesn't provide running balance
                entry_number=entry_number
            )
        except (ValueError, IndexError) as e:
            raise BankParserError(f"Invalid mBank transaction format: {str(e)}")

    def _parse_amount(self, amount_str: str) -> Decimal:
        try:
            # Remove PLN suffix and clean up the amount
            amount_str = amount_str.replace(" PLN", "").replace("PLN", "").strip()
            # Replace comma with dot for decimal separator
            amount_str = amount_str.replace(",", ".")
            # Remove any extra spaces
            amount_str = amount_str.replace(" ", "")
            return Decimal(amount_str)
        except Exception as e:
            raise BankParserError(f"Invalid amount format '{amount_str}': {str(e)}")

    def _extract_other_party_info(self, description: str) -> str:
        """Extract other party information from transaction description"""
        # Split by comma to get potential party info
        parts = description.split(",")
        if len(parts) > 1:
            first_part = parts[0].strip()

            # Skip if it appears to be a self-transfer (contains "PRZELEW ŚRODKÓW")
            if "PRZELEW ŚRODKÓW" in description:
                # Look for the third part that might contain address info
                if len(parts) >= 3:
                    third_part = parts[2].strip()
                    # If the third part looks like an address (contains street indicators or postal codes)
                    if any(keyword in third_part.upper() for keyword in ["UL.", "AL.", "PLAC", "OS."]) or \
                       re.search(r'\d{2}-\d{3}', third_part):  # Polish postal code pattern XX-XXX
                        return third_part
                return None

            # If it's not a self-transfer, return the first part as other party
            return first_part

        # Look for patterns that indicate external transfers
        if "PRZELEW ZEWNĘTRZNY" in description:
            # Try to extract company/person name from the description
            # Look for patterns after common prefixes
            for prefix in ["PRZELEW ZEWNĘTRZNY PRZYCHODZĄCY", "PRZELEW ZEWNĘTRZNY WYCHODZĄCY"]:
                if prefix in description:
                    remaining = description.replace(prefix, "").strip()
                    # Extract meaningful text before account numbers
                    words = remaining.split()
                    meaningful_words = []
                    for word in words:
                        # Stop at account numbers (26 digits)
                        if word.isdigit() and len(word) >= 20:
                            break
                        meaningful_words.append(word)

                    if meaningful_words:
                        return " ".join(meaningful_words[:5])  # Limit to first 5 words

        return None

    def _extract_other_party_account(self, description: str) -> str:
        """Extract other party account number from transaction description"""
        # Look for account number patterns (Polish bank account format: 26 digits)
        # Pattern matches: XX XXXX XXXX XXXX XXXX XXXX XXXX or XXXXXXXXXXXXXXXXXXXXXXXXXX
        account_pattern = r'(\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4})'
        matches = re.findall(account_pattern, description)

        if matches:
            # Return the first account number found
            # Note: In real implementation, you might want to filter out the source account
            # but since we don't know the source account dynamically, we return the first match
            for match in matches:
                account_num = match.replace(" ", "")
                # Basic validation: should be exactly 26 digits
                if len(account_num) == 26:
                    return account_num

        return None