#!/usr/bin/env python3
"""
Document to MT940 Converter CLI Tool

This script converts bank statement documents (PDF, CSV, Excel) to MT940 format
using Claude AI, then parses and displays the results in a beautiful tabular format.

Usage:
    python convert_document.py input.pdf
    python convert_document.py input.csv --account-number 123456789
    python convert_document.py input.xlsx --json --output statement.mt940
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional
import io

# Rich library for beautiful terminal output
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.style import Style
from rich import box
from rich.json import JSON

# MT940 parsing library
try:
    # Try the newer mt-940 library first
    import mt940
    if hasattr(mt940, 'parse'):
        MT940_PARSER = 'mt940'
    else:
        MT940_PARSER = None
except ImportError:
    MT940_PARSER = None

# Our custom parser
from app.services.claude_parser import ClaudeDocumentParser


console = Console()


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Convert bank statement documents to MT940 format and display results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a PDF statement
  python convert_document.py statement.pdf

  # Convert with specific account number
  python convert_document.py statement.csv --account-number 123456789

  # Show JSON debug output
  python convert_document.py statement.xlsx --json

  # Save MT940 output to file
  python convert_document.py statement.pdf --output result.mt940

  # Show both JSON and save MT940
  python convert_document.py statement.csv --json --output result.mt940
        """
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="Input file (PDF, CSV, XLS, or XLSX)"
    )

    parser.add_argument(
        "-a", "--account-number",
        type=str,
        help="Override account number (optional)"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output MT940 file path (optional)"
    )

    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Display JSON structure for debugging"
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    return parser.parse_args()


def validate_input_file(file_path: str) -> Path:
    """Validate input file exists and has correct extension"""
    path = Path(file_path)

    if not path.exists():
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        sys.exit(1)

    allowed_extensions = ['.pdf', '.csv', '.xls', '.xlsx']
    if path.suffix.lower() not in allowed_extensions:
        console.print(f"[red]Error:[/red] Unsupported file type: {path.suffix}")
        console.print(f"Supported types: {', '.join(allowed_extensions)}")
        sys.exit(1)

    return path


def display_json_output(data: dict):
    """Display JSON structure in a formatted panel"""
    console.print("\n")
    console.print(Panel(
        JSON(json.dumps(data, indent=2)),
        title="[bold cyan]📋 Parsed JSON Data Structure[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))


def display_metadata(metadata: dict):
    """Display statement metadata in a formatted table"""
    # Get currency symbol from metadata
    currency = metadata.get("currency", "EUR")
    currency_symbols = {
        "EUR": "€",
        "USD": "$",
        "GBP": "£",
        "PLN": "zł",
        "CHF": "CHF",
        "JPY": "¥",
        "CNY": "¥"
    }
    currency_symbol = currency_symbols.get(currency, currency)

    table = Table(
        title="📊 Statement Metadata",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        title_style="bold magenta"
    )

    table.add_column("Field", style="cyan", width=25)
    table.add_column("Value", style="white")

    # Add metadata rows
    field_labels = {
        "account_number": "Account Number",
        "currency": "Currency",
        "statement_start_date": "Statement Period Start",
        "statement_end_date": "Statement Period End",
        "opening_balance": "Opening Balance",
        "closing_balance": "Closing Balance"
    }

    for field, label in field_labels.items():
        value = metadata.get(field)

        if value is None:
            value_str = "[dim]Not available[/dim]"
        elif field in ["opening_balance", "closing_balance"]:
            # Format currency with color coding
            if value < 0:
                value_str = f"[red bold]{currency_symbol}{abs(value):,.2f} DR[/red bold]"
            else:
                value_str = f"[green bold]{currency_symbol}{value:,.2f} CR[/green bold]"
        else:
            value_str = str(value)

        table.add_row(label, value_str)

    console.print("\n")
    console.print(table)


def display_transactions(transactions: list, currency: str = "EUR"):
    """Display transactions in a formatted table"""
    if not transactions:
        console.print("\n[yellow]No transactions found in the statement.[/yellow]\n")
        return

    # Get currency symbol
    currency_symbols = {
        "EUR": "€",
        "USD": "$",
        "GBP": "£",
        "PLN": "zł",
        "CHF": "CHF",
        "JPY": "¥",
        "CNY": "¥"
    }
    currency_symbol = currency_symbols.get(currency, currency)

    table = Table(
        title=f"💳 Transactions ({len(transactions)} total)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold blue",
        title_style="bold blue"
    )

    table.add_column("Date", style="cyan", width=12)
    table.add_column("Type", width=10)
    table.add_column("Amount", justify="right", width=15)
    table.add_column("Description", style="white", no_wrap=False, overflow="fold")
    table.add_column("Balance", justify="right", width=15)

    for txn in transactions:
        date = txn.get("date", "N/A")
        txn_type = txn.get("transaction_type", "UNKNOWN")
        amount = txn.get("amount", 0.0)
        description = txn.get("description", "")
        balance = txn.get("balance")

        # Color code transaction type
        if txn_type == "DEBIT":
            type_str = "[red]DEBIT[/red]"
        elif txn_type == "CREDIT":
            type_str = "[green]CREDIT[/green]"
        elif txn_type == "TRANSFER":
            type_str = "[blue]TRANSFER[/blue]"
        elif txn_type == "FEE":
            type_str = "[yellow]FEE[/yellow]"
        elif txn_type == "INTEREST":
            type_str = "[magenta]INTEREST[/magenta]"
        else:
            type_str = "[dim]OTHER[/dim]"

        # Color code amount
        if amount < 0:
            amount_str = f"[red bold]-{currency_symbol}{abs(amount):,.2f}[/red bold]"
        else:
            amount_str = f"[green bold]+{currency_symbol}{amount:,.2f}[/green bold]"

        # Format balance
        if balance is not None:
            if balance < 0:
                balance_str = f"[red]{currency_symbol}{abs(balance):,.2f} DR[/red]"
            else:
                balance_str = f"[green]{currency_symbol}{balance:,.2f} CR[/green]"
        else:
            balance_str = "[dim]N/A[/dim]"

        # Don't truncate - Rich library will wrap long descriptions automatically
        table.add_row(
            date,
            type_str,
            amount_str,
            description,
            balance_str
        )

    console.print("\n")
    console.print(table)


def display_mt940_summary(mt940_content: str):
    """
    Parse and display summary from MT940 content using external library

    Returns:
        tuple: (success: bool, statement: object or None) - validation result and parsed statement
    """
    if not MT940_PARSER:
        return False, None  # Skip validation if parser not available

    try:
        # Parse MT940 content using the mt-940 library
        transactions = mt940.parse(mt940_content)

        # Convert generator to list
        statements = list(transactions)

        if not statements:
            console.print("\n[yellow]Note: No statements found in MT940 output[/yellow]")
            return False, None

        # Only display the first statement (avoid repetition)
        statement = statements[0]

        # Display summary panel
        summary_text = Text()

        # Account identification
        if hasattr(statement.data, 'account_identification'):
            summary_text.append("Account: ", style="cyan bold")
            summary_text.append(f"{statement.data.account_identification}\n", style="white")

        # Statement number
        if hasattr(statement.data, 'statement_number'):
            summary_text.append("Statement Number: ", style="cyan bold")
            summary_text.append(f"{statement.data.statement_number}\n", style="white")

        # Sequence number
        if hasattr(statement.data, 'sequence_number'):
            summary_text.append("Sequence Number: ", style="cyan bold")
            summary_text.append(f"{statement.data.sequence_number}\n\n", style="white")

        # Opening balance (available_balance or opening_balance)
        opening_balance = None
        if hasattr(statement.data, 'opening_balance') and statement.data.opening_balance:
            opening_balance = statement.data.opening_balance
        elif hasattr(statement.data, 'available_balance') and statement.data.available_balance:
            opening_balance = statement.data.available_balance[0] if isinstance(statement.data.available_balance, list) else statement.data.available_balance

        if opening_balance:
            summary_text.append("Opening Balance: ", style="cyan bold")
            amount = opening_balance.amount.amount if hasattr(opening_balance.amount, 'amount') else opening_balance.amount
            if amount < 0:
                summary_text.append(f"€{abs(amount):,.2f} DR\n", style="red bold")
            else:
                summary_text.append(f"€{amount:,.2f} CR\n", style="green bold")

        # Closing balance
        closing_balance = None
        if hasattr(statement.data, 'final_closing_balance') and statement.data.final_closing_balance:
            closing_balance = statement.data.final_closing_balance
        elif hasattr(statement.data, 'closing_balance') and statement.data.closing_balance:
            closing_balance = statement.data.closing_balance

        if closing_balance:
            summary_text.append("Closing Balance: ", style="cyan bold")
            amount = closing_balance.amount.amount if hasattr(closing_balance.amount, 'amount') else closing_balance.amount
            if amount < 0:
                summary_text.append(f"€{abs(amount):,.2f} DR\n", style="red bold")
            else:
                summary_text.append(f"€{amount:,.2f} CR\n", style="green bold")

        # Transaction count
        if hasattr(statement, 'transactions') and statement.transactions:
            summary_text.append("\nTransactions: ", style="cyan bold")
            summary_text.append(f"{len(statement.transactions)}\n", style="white")

        console.print("\n")
        console.print(Panel(
            summary_text,
            title="[bold green]✓ MT940 Validation (Parsed Successfully)[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))

        return True, statement

    except Exception as e:
        console.print(f"\n[yellow]Note: Could not validate MT940 format: {e}[/yellow]")
        console.print("[dim]The MT940 file was generated but external validation failed.[/dim]")
        return False, None


def reconstruct_mt940_from_parsed(statement) -> str:
    """
    Reconstruct MT940 content from a parsed statement object

    This shows what the external library actually read from the MT940 file,
    providing round-trip validation that the file is correctly formatted.
    """
    lines = []

    # Get the metadata from transactions.data
    metadata = statement.transactions.data if hasattr(statement.transactions, 'data') else {}

    # Field 20: Transaction Reference
    txn_ref = metadata.get('transaction_reference', 'STATEMENT')
    lines.append(f":20:{txn_ref}")

    # Field 25: Account Identification
    acc_id = metadata.get('account_identification')
    if acc_id:
        lines.append(f":25:{acc_id}")

    # Field 28C: Statement Number
    stmt_num = metadata.get('statement_number')
    seq_num = metadata.get('sequence_number')
    if stmt_num:
        if seq_num:
            lines.append(f":28C:{stmt_num}/{seq_num}")
        else:
            lines.append(f":28C:{stmt_num}")

    # Field 60F: Opening Balance
    ob = metadata.get('final_opening_balance')
    if ob:
        # Extract amount from Balance object
        amount_str_raw = str(ob).split()[0]  # "1000.00 EUR @ 2024-01-05" -> "1000.00"
        amount = float(amount_str_raw)
        currency = str(ob).split()[1]  # Get currency
        date_obj = ob.date if hasattr(ob, 'date') else None
        if date_obj:
            date_str = date_obj.strftime("%y%m%d")
        else:
            # Parse from string
            from datetime import datetime
            date_str_raw = str(ob).split()[-1]  # Get date
            date_obj = datetime.strptime(date_str_raw, "%Y-%m-%d")
            date_str = date_obj.strftime("%y%m%d")

        status = 'C' if amount >= 0 else 'D'
        amount_str = f"{abs(amount):.2f}".replace('.', ',')
        lines.append(f":60F:{status}{date_str}{currency}{amount_str}")

    # Field 61: Statement Lines (Transactions)
    if hasattr(statement, 'transactions'):
        for txn in statement.transactions:
            # Get transaction data
            txn_data = txn.data if hasattr(txn, 'data') else {}

            # Date
            date_obj = txn_data.get('date') or txn_data.get('entry_date')
            if not date_obj:
                continue

            date_str = date_obj.strftime("%y%m%d")
            entry_date = txn_data.get('entry_date', date_obj).strftime("%m%d")

            # Amount and debit/credit
            amount_obj = txn_data.get('amount')
            if not amount_obj:
                continue

            # Extract numeric value from Amount object
            amount = float(str(amount_obj).split()[0])
            status = txn_data.get('status', 'C' if amount >= 0 else 'D')
            amount_str = f"{abs(amount):.2f}".replace('.', ',')

            # Transaction code
            txn_code = txn_data.get('id', 'NMSC')

            lines.append(f":61:{date_str}{entry_date}{status}{amount_str}{txn_code}")

            # Field 86: Transaction details - max 6 lines of 65 characters each
            description = txn_data.get('transaction_details', '').replace('\n', ' ')
            if description:
                # Split long descriptions across multiple lines (SWIFT MT940 spec: 6*65x)
                max_lines = 6
                line_length = 65
                desc_lines = []

                for i in range(0, min(len(description), max_lines * line_length), line_length):
                    desc_lines.append(description[i:i+line_length])

                # First line starts with :86:, continuation lines don't have the tag
                if desc_lines:
                    lines.append(f":86:{desc_lines[0]}")
                    for continuation_line in desc_lines[1:]:
                        lines.append(continuation_line)

    # Field 62F: Closing Balance
    cb = metadata.get('final_closing_balance')
    if cb:
        # Extract amount from Balance object
        amount_str_raw = str(cb).split()[0]  # "2776.76 EUR @ 2024-01-31" -> "2776.76"
        amount = float(amount_str_raw)
        currency = str(cb).split()[1]  # Get currency
        date_obj = cb.date if hasattr(cb, 'date') else None
        if date_obj:
            date_str = date_obj.strftime("%y%m%d")
        else:
            # Parse from string
            from datetime import datetime
            date_str_raw = str(cb).split()[-1]  # Get date
            date_obj = datetime.strptime(date_str_raw, "%Y-%m-%d")
            date_str = date_obj.strftime("%y%m%d")

        status = 'C' if amount >= 0 else 'D'
        amount_str = f"{abs(amount):.2f}".replace('.', ',')
        lines.append(f":62F:{status}{date_str}{currency}{amount_str}")

    # Add ending marker
    lines.append("-")

    return "\n".join(lines)


def main():
    """Main entry point"""
    args = parse_arguments()

    # Disable colors if requested
    if args.no_color:
        console._color_system = None

    # Validate input file
    input_path = validate_input_file(args.input_file)

    # Display header
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]🤖 AI-Powered Document to MT940 Converter[/bold cyan]\n"
        f"Processing: [white]{input_path.name}[/white]",
        border_style="cyan"
    ))

    try:
        # Initialize parser
        with console.status("[bold green]Initializing Claude AI parser...[/bold green]"):
            parser = ClaudeDocumentParser()

        # Read file
        with console.status(f"[bold green]Reading {input_path.suffix.upper()} file...[/bold green]"):
            with open(input_path, 'rb') as f:
                file_content = f.read()
                file_stream = io.BytesIO(file_content)

        # Parse document with AI
        with console.status("[bold yellow]🧠 Analyzing document with Claude AI...[/bold yellow]"):
            parsed_data = parser.parse_document(
                file_content=file_stream,
                filename=input_path.name,
                account_number=args.account_number
            )

        console.print("[green]✓[/green] Document successfully parsed!")

        # Display JSON if requested
        if args.json:
            display_json_output(parsed_data)

        # Display metadata
        if "metadata" in parsed_data:
            display_metadata(parsed_data["metadata"])

        # Display transactions
        if "transactions" in parsed_data:
            currency = parsed_data.get("metadata", {}).get("currency", "EUR")
            display_transactions(parsed_data["transactions"], currency)

        # Convert to MT940
        with console.status("[bold green]Converting to MT940 format...[/bold green]"):
            mt940_content = parser.convert_to_mt940(
                transactions_data=parsed_data,
                account_number=args.account_number
            )

        console.print("[green]✓[/green] MT940 conversion complete!")

        # Display MT940 summary and get parsed statement
        validation_success, parsed_statement = display_mt940_summary(mt940_content)

        # Save to file if requested (always use UTF-8 encoding)
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(mt940_content, encoding='utf-8')
            console.print(f"\n[green]✓[/green] MT940 file saved to: [cyan]{output_path}[/cyan] (UTF-8)")
        else:
            # Display what the library actually parsed (round-trip validation)
            console.print("\n")
            if validation_success and parsed_statement:
                reconstructed_mt940 = reconstruct_mt940_from_parsed(parsed_statement)
                console.print(Panel(
                    reconstructed_mt940,
                    title="[bold green]📄 MT940 Output (As Parsed by External Library)[/bold green]",
                    border_style="green",
                    padding=(1, 2)
                ))
            else:
                # Fall back to showing generated content if parsing failed
                console.print(Panel(
                    mt940_content,
                    title="[bold yellow]📄 MT940 Output (Generated)[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2)
                ))

        # Display success message
        console.print("\n")
        console.print(Panel.fit(
            "[bold green]✓ Conversion completed successfully![/bold green]",
            border_style="green"
        ))
        console.print("\n")

    except ValueError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] File not found: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] An unexpected error occurred: {e}")
        if args.json:
            console.print("\n[dim]Full error details:[/dim]")
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
