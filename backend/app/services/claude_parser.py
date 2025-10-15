"""
Claude AI Document Parser Service

This service uses Claude AI to automatically extract transaction data from
various document formats (CSV, PDF, XLS/XLSX) without needing bank-specific parsers.

The AI identifies transaction data, extracts it into a standardized format,
and converts it to MT940 format.
"""

import base64
import csv
import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, BinaryIO
from anthropic import Anthropic
import PyPDF2
import openpyxl

from ..config import settings


class Transaction:
    """Standardized transaction representation"""

    def __init__(
        self,
        date: str,
        amount: float,
        description: str,
        transaction_type: str = "UNKNOWN",
        reference: Optional[str] = None,
        balance: Optional[float] = None
    ):
        self.date = date
        self.amount = amount
        self.description = description
        self.transaction_type = transaction_type
        self.reference = reference
        self.balance = balance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "amount": self.amount,
            "description": self.description,
            "transaction_type": self.transaction_type,
            "reference": self.reference,
            "balance": self.balance
        }


class ClaudeDocumentParser:
    """Service for parsing documents using Claude AI"""

    def __init__(self):
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def parse_document(
        self,
        file_content: BinaryIO,
        filename: str,
        account_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse a document and extract transaction data using Claude AI

        Args:
            file_content: Binary file content
            filename: Original filename (used to determine file type)
            account_number: Optional account number for MT940 generation

        Returns:
            Dict containing transactions and metadata
        """
        file_type = self._get_file_type(filename)

        # Extract text content based on file type
        if file_type == "csv":
            text_content = self._extract_csv_content(file_content)
            return self._parse_with_claude_text(text_content, account_number)
        elif file_type == "pdf":
            text_content = self._extract_pdf_content(file_content)
            return self._parse_with_claude_text(text_content, account_number)
        elif file_type in ["xls", "xlsx"]:
            text_content = self._extract_excel_content(file_content)
            return self._parse_with_claude_text(text_content, account_number)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _get_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        extension = filename.lower().split('.')[-1]
        if extension in ['xls', 'xlsx']:
            return 'xlsx'
        return extension

    def _extract_csv_content(self, file_content: BinaryIO) -> str:
        """Extract text from CSV file"""
        content = file_content.read()
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                text = content.decode(encoding)
                return text
            except UnicodeDecodeError:
                continue
        raise ValueError("Unable to decode CSV file")

    def _extract_pdf_content(self, file_content: BinaryIO) -> str:
        """Extract text from PDF file"""
        pdf_reader = PyPDF2.PdfReader(file_content)
        text_parts = []
        for page in pdf_reader.pages:
            text_parts.append(page.extract_text())
        return "\n".join(text_parts)

    def _extract_excel_content(self, file_content: BinaryIO) -> str:
        """Extract text from Excel file"""
        workbook = openpyxl.load_workbook(file_content, data_only=True)
        text_parts = []

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text_parts.append(f"=== Sheet: {sheet_name} ===")

            for row in sheet.iter_rows(values_only=True):
                # Convert all values to strings and join
                row_text = "\t".join([str(cell) if cell is not None else "" for cell in row])
                if row_text.strip():
                    text_parts.append(row_text)

        return "\n".join(text_parts)

    def _parse_with_claude_text(
        self,
        text_content: str,
        account_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use Claude AI to extract transaction data from text content

        Args:
            text_content: The text extracted from the document
            account_number: Optional account number

        Returns:
            Dict with transactions and metadata
        """
        prompt = """You are a financial document parser. Analyze the following document and extract ALL transaction data.

The document may be a bank statement, credit card statement, or any financial transaction record.

Your task:
1. Identify all transactions in the document
2. Extract the following information for each transaction:
   - Date (in ISO format YYYY-MM-DD)
   - Amount (positive for credits/deposits, negative for debits/withdrawals)
   - Description (transaction description/payee)
   - Transaction type (one of: CREDIT, DEBIT, TRANSFER, FEE, INTEREST, OTHER)
   - Reference (transaction ID/reference number if available)
   - Balance (account balance after transaction if available)

3. Also extract metadata:
   - account_number (if found in document)
   - currency (3-letter ISO currency code like USD, EUR, GBP, PLN, etc. - REQUIRED)
   - statement_start_date (first transaction date)
   - statement_end_date (last transaction date)
   - opening_balance (starting balance if available)
   - closing_balance (ending balance if available)

Return ONLY a valid JSON object with this structure:
{
  "transactions": [
    {
      "date": "2024-01-15",
      "amount": -50.25,
      "description": "Amazon Purchase",
      "transaction_type": "DEBIT",
      "reference": "REF123456",
      "balance": 1949.75
    }
  ],
  "metadata": {
    "account_number": "123456789",
    "currency": "USD",
    "statement_start_date": "2024-01-01",
    "statement_end_date": "2024-01-31",
    "opening_balance": 2000.00,
    "closing_balance": 1949.75
  }
}

IMPORTANT:
- Return ONLY the JSON object, no other text
- If a field is not available, use null
- For currency: Look for currency symbols (€, $, £, zł) or currency codes (EUR, USD, GBP, PLN) in the document
- If no currency is specified in the document, use "EUR" as default
- Amounts: use negative for money going out, positive for money coming in
- Be thorough - extract ALL transactions you find

Document content:

"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt + text_content
                }
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to parse JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # If response isn't pure JSON, try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # Try to find JSON object in the text
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not extract JSON from Claude response")

        # Override account number if provided
        if account_number:
            result["metadata"]["account_number"] = account_number

        return result

    def convert_to_mt940(
        self,
        transactions_data: Dict[str, Any],
        account_number: Optional[str] = None
    ) -> str:
        """
        Convert parsed transactions to MT940 format

        Args:
            transactions_data: Dict with transactions and metadata from parse_document
            account_number: Override account number

        Returns:
            MT940 formatted string
        """
        metadata = transactions_data.get("metadata", {})
        transactions = transactions_data.get("transactions", [])

        # Use provided account number or from metadata
        acc_num = account_number or metadata.get("account_number") or "UNKNOWN"

        # Get dates
        start_date = metadata.get("statement_start_date")
        end_date = metadata.get("statement_end_date")

        if not start_date and transactions:
            start_date = transactions[0]["date"]
        if not end_date and transactions:
            end_date = transactions[-1]["date"]

        # Format dates for MT940
        statement_num = "001"
        opening_balance = metadata.get("opening_balance")
        closing_balance = metadata.get("closing_balance")

        # Calculate balances from transactions if not provided
        if opening_balance is None and transactions:
            # If we have first transaction balance, use it as opening
            first_txn_balance = transactions[0].get("balance")
            if first_txn_balance is not None:
                opening_balance = first_txn_balance - transactions[0]["amount"]
            else:
                opening_balance = 0.0
        elif opening_balance is None:
            opening_balance = 0.0

        if closing_balance is None and transactions:
            # Use last transaction balance if available
            last_txn_balance = transactions[-1].get("balance")
            if last_txn_balance is not None:
                closing_balance = last_txn_balance
            else:
                # Calculate from opening balance and all transactions
                closing_balance = opening_balance + sum(txn["amount"] for txn in transactions)
        elif closing_balance is None:
            closing_balance = 0.0

        # Build MT940
        mt940_lines = []

        # Header
        mt940_lines.append(":20:STATEMENT")
        mt940_lines.append(f":25:{acc_num}")
        mt940_lines.append(f":28C:{statement_num}")

        # Opening balance
        if start_date:
            start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d").strftime("%y%m%d")
            opening_sign = "C" if opening_balance >= 0 else "D"
            opening_amount = abs(opening_balance)
            # Use comma for decimal separator (European MT940 format)
            opening_amount_str = f"{opening_amount:.2f}".replace('.', ',')
            # Get currency from metadata, default to EUR
            currency = metadata.get("currency", "EUR")
            mt940_lines.append(f":60F:{opening_sign}{start_date_formatted}{currency}{opening_amount_str}")

        # Transactions
        for idx, txn in enumerate(transactions, 1):
            date_obj = datetime.strptime(txn["date"], "%Y-%m-%d")
            value_date = date_obj.strftime("%y%m%d")  # YYMMDD format
            entry_date = date_obj.strftime("%m%d")     # MMDD format (optional entry date)

            amount = txn["amount"]
            debit_credit = "D" if amount < 0 else "C"
            amount_abs = abs(amount)

            # Format amount with comma (European format for MT940)
            amount_str = f"{amount_abs:.2f}".replace('.', ',')

            # Transaction type code
            # Format: [funds_code][3-char type code]
            # N = non-urgent, MSC = miscellaneous, TRF = transfer
            type_code = "NMSC"  # N=funds code, MSC=miscellaneous

            # Statement line format: :61:YYMMDD[MMDD][D|C]amount,decimals[N]TYPE
            # Value date (6) + Entry date (4) + Debit/Credit + Amount + Type code
            mt940_lines.append(f":61:{value_date}{entry_date}{debit_credit}{amount_str}{type_code}")

            # Transaction details
            description = txn.get("description", "").replace("\n", " ")[:65]
            mt940_lines.append(f":86:{description}")

        # Closing balance
        if end_date:
            end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d").strftime("%y%m%d")
            closing_sign = "C" if closing_balance >= 0 else "D"
            closing_amount = abs(closing_balance)
            # Use comma for decimal separator (European MT940 format)
            closing_amount_str = f"{closing_amount:.2f}".replace('.', ',')
            # Get currency from metadata, default to EUR
            currency = metadata.get("currency", "EUR")
            mt940_lines.append(f":62F:{closing_sign}{end_date_formatted}{currency}{closing_amount_str}")

        return "\n".join(mt940_lines)
