from io import StringIO
import mt940
from decimal import Decimal
from .models import BankStatement


class MT940ConverterError(Exception):
    pass


class MT940Converter:
    @staticmethod
    def convert(bank_statement: BankStatement) -> str:
        try:
            lines = []

            # Start of message
            lines.append(f":20:{bank_statement.header.account_number[:16]}")

            # Account identification
            lines.append(f":25:{bank_statement.header.account_number}")

            # Statement number (using generation date)
            generation_date_str = bank_statement.header.generation_date.strftime("%y%m%d")
            lines.append(f":28C:1/{generation_date_str}")

            # Opening balance
            balance_date = bank_statement.header.start_date.strftime("%y%m%d")
            balance_sign = "C" if bank_statement.header.initial_balance >= 0 else "D"
            balance_amount = abs(bank_statement.header.initial_balance)
            balance_formatted = f"{balance_amount:.2f}".replace(".", ",")
            lines.append(f":60F:{balance_sign}{balance_date}{bank_statement.header.currency}{balance_formatted}")

            # Transaction details
            for transaction in bank_statement.transactions:
                # Value date and entry date
                value_date = transaction.initiated_date.strftime("%y%m%d")
                entry_date = transaction.registered_date.strftime("%m%d")

                # Credit/Debit mark
                credit_debit = "C" if transaction.amount >= 0 else "D"
                amount_abs = abs(transaction.amount)
                amount_formatted = f"{amount_abs:.2f}".replace(".", ",")

                # Transaction type code (NTRF for normal transfer)
                transaction_type = "NTRF"

                # Reference for account owner
                reference = f"{transaction.entry_number:04d}"

                lines.append(f":61:{value_date}{entry_date}{credit_debit}{amount_formatted}{transaction_type}{reference}")

                # Transaction details
                purpose_code = "SALA" if "salary" in transaction.title.lower() else "OTHR"

                # Supplementary details
                lines.append(f":86:{purpose_code}")

                # Transaction description (split into multiple lines if needed)
                description = transaction.title
                if transaction.other_party_info:
                    description += f" {transaction.other_party_info}"

                # MT940 field 86 can have multiple lines, each max 65 chars
                desc_lines = MT940Converter._split_description(description)
                for i, desc_line in enumerate(desc_lines):
                    if i == 0:
                        lines[-1] += desc_line
                    else:
                        lines.append(f"?{i+20}{desc_line}")

            # Closing balance
            closing_date = bank_statement.header.end_date.strftime("%y%m%d")
            closing_sign = "C" if bank_statement.header.end_balance >= 0 else "D"
            closing_amount = abs(bank_statement.header.end_balance)
            closing_formatted = f"{closing_amount:.2f}".replace(".", ",")
            lines.append(f":62F:{closing_sign}{closing_date}{bank_statement.header.currency}{closing_formatted}")

            # End of message
            lines.append("-")

            return "\n".join(lines)

        except Exception as e:
            raise MT940ConverterError(f"Failed to convert to MT940 format: {str(e)}")

    @staticmethod
    def _split_description(description: str, max_length: int = 65) -> list[str]:
        if len(description) <= max_length:
            return [description]

        lines = []
        while description:
            if len(description) <= max_length:
                lines.append(description)
                break

            # Find the last space before max_length
            split_pos = description.rfind(' ', 0, max_length)
            if split_pos == -1:
                # No space found, force split at max_length
                split_pos = max_length

            lines.append(description[:split_pos])
            description = description[split_pos:].lstrip()

        return lines