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
            result = self._parse_with_claude_text(text_content, account_number)
        elif file_type == "pdf":
            text_content = self._extract_pdf_content(file_content)
            result = self._parse_with_claude_text(text_content, account_number)
        elif file_type in ["xls", "xlsx"]:
            text_content = self._extract_excel_content(file_content)
            result = self._parse_with_claude_text(text_content, account_number)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Store original filename in metadata for Field 20 reference generation
        if "metadata" not in result:
            result["metadata"] = {}
        result["metadata"]["source_filename"] = filename

        return result

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

    def _chunk_text_by_lines(self, text_content: str, lines_per_chunk: int = 100) -> List[str]:
        """
        Split text content into chunks by lines (for large files)

        Args:
            text_content: The full text content
            lines_per_chunk: Number of lines per chunk (targets ~80-90 transactions = ~6000 output tokens with 8192 limit)

        Returns:
            List of text chunks
        """
        lines = text_content.split('\n')

        # Keep header lines (first 20 lines usually contain metadata)
        header_lines = lines[:20]
        data_lines = lines[20:]

        # If file is small enough, return as single chunk
        if len(data_lines) <= lines_per_chunk:
            return [text_content]

        # Split into chunks
        chunks = []
        for i in range(0, len(data_lines), lines_per_chunk):
            chunk_data = data_lines[i:i + lines_per_chunk]
            # Each chunk includes header + data portion
            chunk_text = '\n'.join(header_lines + chunk_data)
            chunks.append(chunk_text)

        return chunks

    def _parse_with_claude_text(
        self,
        text_content: str,
        account_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use Claude AI to extract transaction data from text content.
        Automatically handles large files by splitting into chunks.

        Args:
            text_content: The text extracted from the document
            account_number: Optional account number

        Returns:
            Dict with transactions and metadata
        """
        # Check if we need to chunk the file (more than 100 lines after header)
        lines = text_content.split('\n')
        needs_chunking = len(lines) > 120  # 20 header + 100 data lines

        if needs_chunking:
            print(f"📄 Large file detected ({len(lines)} lines). Processing in chunks...")
            return self._parse_large_file_in_chunks(text_content, account_number)

        # For small files, process normally
        return self._parse_single_chunk(text_content, account_number)

    def _parse_large_file_in_chunks(
        self,
        text_content: str,
        account_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse a large file by splitting into chunks and merging results

        Args:
            text_content: The full text content
            account_number: Optional account number

        Returns:
            Merged Dict with all transactions and metadata
        """
        chunks = self._chunk_text_by_lines(text_content, lines_per_chunk=100)
        print(f"   Split into {len(chunks)} chunks")

        all_transactions = []
        merged_metadata = {}
        total_input_tokens = 0
        total_output_tokens = 0

        for i, chunk in enumerate(chunks, 1):
            print(f"   Processing chunk {i}/{len(chunks)}...")
            try:
                chunk_result = self._parse_single_chunk(chunk, account_number)

                # Collect transactions
                all_transactions.extend(chunk_result.get("transactions", []))

                # Merge metadata (take from first chunk, update dates from all chunks)
                if not merged_metadata:
                    merged_metadata = chunk_result.get("metadata", {})
                else:
                    # Update date ranges
                    chunk_meta = chunk_result.get("metadata", {})
                    if chunk_meta.get("statement_start_date"):
                        if not merged_metadata.get("statement_start_date") or \
                           chunk_meta["statement_start_date"] < merged_metadata["statement_start_date"]:
                            merged_metadata["statement_start_date"] = chunk_meta["statement_start_date"]
                    if chunk_meta.get("statement_end_date"):
                        if not merged_metadata.get("statement_end_date") or \
                           chunk_meta["statement_end_date"] > merged_metadata["statement_end_date"]:
                            merged_metadata["statement_end_date"] = chunk_meta["statement_end_date"]
                    # Update closing balance from last chunk
                    if chunk_meta.get("closing_balance") is not None:
                        merged_metadata["closing_balance"] = chunk_meta["closing_balance"]

                # Accumulate token usage
                total_input_tokens += chunk_result.get("metadata", {}).get("input_tokens", 0)
                total_output_tokens += chunk_result.get("metadata", {}).get("output_tokens", 0)

            except Exception as e:
                print(f"   ⚠️  Chunk {i} failed: {e}")
                # Continue with other chunks

        # Update token usage in metadata
        merged_metadata["input_tokens"] = total_input_tokens
        merged_metadata["output_tokens"] = total_output_tokens

        print(f"✓ Processed all chunks. Total transactions: {len(all_transactions)}")

        return {
            "transactions": all_transactions,
            "metadata": merged_metadata
        }

    def _parse_single_chunk(
        self,
        text_content: str,
        account_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse a single chunk of text content with Claude AI

        Args:
            text_content: The text to parse
            account_number: Optional account number

        Returns:
            Dict with transactions and metadata
        """
        prompt = """You are a financial document parser. Analyze the following document and extract ALL transaction data.

The document may be a bank statement, credit card statement, or any financial transaction record.

Your task:
1. Extract metadata first (one line starting with "METADATA,")
2. Then extract all transactions (one transaction per line starting with "TXN,")

Output format - CSV with properly quoted fields:

METADATA,account_number,currency,statement_start_date,statement_end_date,opening_balance,closing_balance
TXN,date,amount,"description",transaction_type,reference,balance
TXN,date,amount,"description",transaction_type,reference,balance
...

Example output:
METADATA,123456789,USD,2024-01-01,2024-01-31,2000.00,1949.75
TXN,2024-01-15,-50.25,"Amazon Purchase",DEBIT,REF123456,1949.75
TXN,2024-01-16,500.00,"Salary | Deposit",CREDIT,SAL2024,2449.75

Field details:
- date: ISO format YYYY-MM-DD
- amount: positive for credits/deposits, negative for debits/withdrawals
- description: transaction description/payee (MUST be quoted if contains commas or special chars)
- transaction_type: CREDIT, DEBIT, TRANSFER, FEE, INTEREST, or OTHER
- reference: transaction ID/reference number (empty if not available)
- balance: account balance after transaction (empty if not available)
- account_number: remove ALL whitespace/spaces from IBANs (e.g., "PL 27 1050..." → "PL271050...")
- currency: 3-letter ISO code (USD, EUR, GBP, PLN, etc.) - look for symbols (€,$,£,zł) or codes in document
- If currency not found, use EUR as default
- opening_balance/closing_balance: empty if not available

IMPORTANT:
- Return ONLY the CSV format, no other text or explanations
- ALWAYS quote description fields (they may contain commas, pipes, or other special characters)
- One METADATA line, then TXN lines for ALL transactions
- Be thorough - extract ALL transactions you find
- Amounts: negative for money going out, positive for money coming in

Document content:

"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": prompt + text_content
                }
            ]
        )

        # Extract pipe-delimited response
        response_text = response.content[0].text

        # Capture token usage for cost analysis
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Parse pipe-delimited format
        try:
            result = self._parse_pipe_delimited_response(response_text)
        except Exception as e:
            # Save the raw response for debugging
            import tempfile
            debug_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_claude_response.txt')
            debug_file.write(response_text)
            debug_file.close()
            print(f"⚠️  Parse error. Raw response saved to: {debug_file.name}")
            raise ValueError(f"Could not parse Claude response: {str(e)}")

        # Override account number if provided
        if account_number:
            result["metadata"]["account_number"] = account_number

        # Add token usage to metadata for tracking
        if "metadata" not in result:
            result["metadata"] = {}
        result["metadata"]["input_tokens"] = input_tokens
        result["metadata"]["output_tokens"] = output_tokens

        return result

    def _parse_pipe_delimited_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Claude's CSV response format into structured data

        Args:
            response_text: The raw response from Claude (CSV format)

        Returns:
            Dict with transactions and metadata
        """
        import csv
        from io import StringIO

        lines = response_text.strip().split('\n')
        transactions = []
        metadata = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Use CSV reader to properly handle quoted fields
            try:
                reader = csv.reader(StringIO(line))
                parts = next(reader)
            except Exception as e:
                print(f"   Skipping malformed line: {line[:100]}")
                continue

            if not parts:
                continue

            # Check the first field to determine line type
            line_type = parts[0]

            if line_type == 'METADATA':
                # Parse: METADATA,account,currency,start_date,end_date,opening_bal,closing_bal
                if len(parts) >= 7:
                    metadata = {
                        "account_number": parts[1].strip() or None,
                        "currency": parts[2].strip() or "EUR",
                        "statement_start_date": parts[3].strip() or None,
                        "statement_end_date": parts[4].strip() or None,
                        "opening_balance": float(parts[5].strip()) if parts[5].strip() else None,
                        "closing_balance": float(parts[6].strip()) if parts[6].strip() else None
                    }

            elif line_type == 'TXN':
                # Parse: TXN,date,amount,description,type,reference,balance
                if len(parts) >= 5:  # At least TXN,date,amount,description,type
                    try:
                        txn = {
                            "date": parts[1].strip(),
                            "amount": float(parts[2].strip()),
                            "description": parts[3].strip(),
                            "transaction_type": parts[4].strip() if len(parts) > 4 else "OTHER",
                            "reference": parts[5].strip() if len(parts) > 5 and parts[5].strip() else None,
                            "balance": float(parts[6].strip()) if len(parts) > 6 and parts[6].strip() else None
                        }
                        transactions.append(txn)
                    except (ValueError, IndexError) as e:
                        # Skip malformed transaction lines
                        print(f"   Skipping malformed transaction: {line[:100]}")
                        continue

        if not transactions:
            raise ValueError("No transactions found in response")

        return {
            "transactions": transactions,
            "metadata": metadata
        }

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

        # Remove all whitespace from account number (IBANs should not have spaces)
        # BUT preserve any existing slashes
        acc_num = acc_num.replace(" ", "").replace("\t", "").replace("\n", "")

        # Add slash prefix for IBANs (SWIFT MT940 standard: :25:/IBAN)
        # IBAN format: 2 letters + 2 digits + up to 30 alphanumeric characters
        # Only add slash if account looks like IBAN and doesn't already have it
        acc_num_without_slash = acc_num.lstrip('/')
        if (acc_num_without_slash and
            len(acc_num_without_slash) >= 15 and
            acc_num_without_slash[:2].isalpha() and
            not acc_num.startswith('/')):
            # Add slash prefix for IBAN (best practice per SWIFT MT940 standard)
            acc_num = f"/{acc_num_without_slash}"

        # Get dates
        start_date = metadata.get("statement_start_date")
        end_date = metadata.get("statement_end_date")

        if not start_date and transactions:
            start_date = transactions[0]["date"]
        if not end_date and transactions:
            end_date = transactions[-1]["date"]

        # Format dates for MT940
        # Field 28C: Statement number (5 digits per SWIFT standard)
        statement_num = "00001"  # First statement (we're generating from a single document)
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

        # Generate Field 20: Transaction Reference Number (unique message identifier)
        # Format: DATE-FILENAME (max 16 chars per SWIFT standard)
        # This provides uniqueness by combining date with source file identifier
        # Example: 20241015-ABC123 or 241015-STATEMENT
        if start_date:
            # Use YYMMDD format to save space (vs YYYYMMDD)
            date_part = datetime.strptime(start_date, "%Y-%m-%d").strftime("%y%m%d")

            # Extract meaningful part from filename (if available)
            source_filename = metadata.get("source_filename", "")
            if source_filename:
                # Remove extension and take first 8 chars of basename
                basename = source_filename.rsplit('.', 1)[0]  # Remove extension
                # Keep only alphanumeric chars
                basename_clean = ''.join(c for c in basename if c.isalnum())
                filename_part = basename_clean[:8].upper() if basename_clean else "STMT"
            else:
                filename_part = "STMT"

            # Combine: DATE-FILE (e.g., 241015-STATEMENT, 241015-INGCORP)
            field_20_ref = f"{date_part}-{filename_part}"

            # Ensure max 16 characters (SWIFT requirement)
            field_20_ref = field_20_ref[:16]
        else:
            # Fallback if no date available - use timestamp
            field_20_ref = datetime.now().strftime("%y%m%d%H%M%S")[:16]

        # Header
        mt940_lines.append(f":20:{field_20_ref}")
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

            # Transaction details - Field 86: max 6 lines of 65 characters each
            description = txn.get("description", "").replace("\n", " ")
            # Split long descriptions across multiple lines (SWIFT MT940 spec: 6*65x)
            max_lines = 6
            line_length = 65
            desc_lines = []

            for i in range(0, min(len(description), max_lines * line_length), line_length):
                desc_lines.append(description[i:i+line_length])

            # First line starts with :86:, continuation lines don't have the tag
            if desc_lines:
                mt940_lines.append(f":86:{desc_lines[0]}")
                for continuation_line in desc_lines[1:]:
                    mt940_lines.append(continuation_line)

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
