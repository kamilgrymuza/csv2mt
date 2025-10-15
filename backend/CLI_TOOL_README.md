# Document to MT940 Converter CLI Tool

A powerful command-line tool that converts bank statement documents (PDF, CSV, Excel) to MT940 format using Claude AI, with beautiful terminal output.

## Features

- 🤖 **AI-Powered Parsing**: Uses Claude AI to automatically detect and extract transaction data from any document format
- 📊 **Beautiful Output**: Rich, colorful tables and panels using the `rich` library
- 💳 **Multi-Format Support**: CSV, PDF, XLS, and XLSX files
- ✅ **MT940 Validation**: Parses generated MT940 files to validate format compliance
- 🐛 **Debug Mode**: Optional JSON output to inspect parsed data structure
- 💾 **File Export**: Save MT940 output to file
- 🎨 **Color Coding**:
  - Green for credits/positive balances
  - Red for debits/negative balances
  - Different colors for transaction types

## Installation

The tool is already installed in the Docker container. If running locally:

```bash
pip install -r requirements.txt
```

Required packages:
- `anthropic` - Claude AI API
- `rich` - Terminal formatting
- `mt940` - MT940 parsing
- `openpyxl` - Excel file support
- `PyPDF2` - PDF parsing

## Usage

### Basic Usage

```bash
# Using Docker
docker-compose exec backend python convert_document.py <input_file>

# Or if running locally
python convert_document.py <input_file>
```

### Command-Line Options

```
positional arguments:
  input_file            Input file (PDF, CSV, XLS, or XLSX)

options:
  -h, --help            Show help message
  -a, --account-number  Override account number (optional)
  -o, --output         Output MT940 file path (optional)
  -j, --json           Display JSON structure for debugging
  --no-color           Disable colored output
```

### Examples

**1. Convert a PDF statement**
```bash
docker-compose exec backend python convert_document.py statement.pdf
```

**2. Convert CSV with specific account number**
```bash
docker-compose exec backend python convert_document.py statement.csv --account-number 123456789
```

**3. Show JSON debug output**
```bash
docker-compose exec backend python convert_document.py statement.xlsx --json
```

**4. Save MT940 to file**
```bash
docker-compose exec backend python convert_document.py statement.pdf --output result.mt940
```

**5. Debug and save MT940**
```bash
docker-compose exec backend python convert_document.py statement.csv --json --output result.mt940
```

**6. Convert sample file (included)**
```bash
docker-compose exec backend python convert_document.py sample_statement.csv
```

## Output Format

The tool displays three main sections:

### 1. Statement Metadata
A table showing:
- Account Number
- Statement Period (Start/End dates)
- Opening Balance (color-coded)
- Closing Balance (color-coded)

### 2. Transactions Table
A detailed table with:
- **Date**: Transaction date
- **Type**: DEBIT, CREDIT, TRANSFER, FEE, INTEREST, or OTHER (color-coded)
- **Amount**: Transaction amount (color-coded: red for negative, green for positive)
- **Description**: Transaction description
- **Balance**: Running balance after transaction (color-coded)

### 3. MT940 Validation Summary
After conversion, displays:
- Account identification
- Statement number
- Opening balance
- Closing balance

### 4. MT940 Output
The complete MT940-formatted text, either displayed in terminal or saved to file.

## JSON Debug Mode

When using the `--json` flag, you'll see the complete parsed data structure:

```json
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
    "statement_start_date": "2024-01-01",
    "statement_end_date": "2024-01-31",
    "opening_balance": 2000.00,
    "closing_balance": 1949.75
  }
}
```

## Color Coding

### Transaction Types
- 🟢 **CREDIT** - Money in
- 🔴 **DEBIT** - Money out
- 🔵 **TRANSFER** - Transfer between accounts
- 🟡 **FEE** - Bank fees
- 🟣 **INTEREST** - Interest payments

### Amounts and Balances
- 🟢 **Green** - Positive amounts (credits) and credit balances (CR)
- 🔴 **Red** - Negative amounts (debits) and debit balances (DR)

## How It Works

1. **File Reading**: Reads the input file (CSV, PDF, Excel)
2. **Text Extraction**: Extracts text content based on file type
3. **AI Analysis**: Sends to Claude AI to identify and extract transactions
4. **Standardization**: Converts to standardized JSON structure
5. **MT940 Generation**: Converts standardized data to MT940 format
6. **Validation**: Parses MT940 to validate format compliance
7. **Display**: Shows results in beautiful formatted tables

## Sample Output

```
╭────────────────────────────────────────────────────────╮
│   🤖 AI-Powered Document to MT940 Converter           │
│   Processing: statement.csv                            │
╰────────────────────────────────────────────────────────╯

✓ Document successfully parsed!

              📊 Statement Metadata
╭─────────────────────────┬──────────────────────────╮
│ Field                   │ Value                    │
├─────────────────────────┼──────────────────────────┤
│ Account Number          │ 123456789                │
│ Statement Period Start  │ 2024-01-01               │
│ Statement Period End    │ 2024-01-31               │
│ Opening Balance         │ €1,000.00 CR             │
│ Closing Balance         │ €2,776.76 CR             │
╰─────────────────────────┴──────────────────────────╯

           💳 Transactions (9 total)
╭────────────┬──────────┬────────────┬──────────────────┬────────────╮
│ Date       │ Type     │ Amount     │ Description      │ Balance    │
├────────────┼──────────┼────────────┼──────────────────┼────────────┤
│ 2024-01-05 │ CREDIT   │ +€2,500.00 │ Salary Deposit   │ €3,500.00  │
│ 2024-01-08 │ DEBIT    │ -€87.50    │ Grocery Store    │ €3,412.50  │
│ 2024-01-10 │ DEBIT    │ -€125.00   │ Electric Bill    │ €3,287.50  │
...
╰────────────┴──────────┴────────────┴──────────────────┴────────────╯
```

## Troubleshooting

### API Key Not Set
```
Error: ANTHROPIC_API_KEY not configured
```
**Solution**: Set the `ANTHROPIC_API_KEY` environment variable in your `.env` file.

### File Not Found
```
Error: File not found: statement.pdf
```
**Solution**: Check the file path. Use absolute paths or ensure you're in the correct directory.

### Unsupported File Type
```
Error: Unsupported file type: .txt
```
**Solution**: Only PDF, CSV, XLS, and XLSX files are supported.

### Invalid MT940 Format
If the MT940 validation fails, the raw MT940 content will still be displayed. Use `--json` to inspect the parsed data structure.

## Technical Details

### Supported File Formats
- **CSV**: Plain text, comma-separated values
- **PDF**: Extracts text using PyPDF2
- **XLS/XLSX**: Reads Excel workbooks using openpyxl

### MT940 Format Compliance
The generated MT940 files follow the SWIFT MT940 specification:
- Field 20: Transaction Reference
- Field 25: Account Identification
- Field 28C: Statement Number/Sequence Number
- Field 60F: Opening Balance
- Field 61: Statement Line (transactions)
- Field 86: Transaction Details
- Field 62F: Closing Balance

### AI Model
Uses Claude 3.5 Sonnet (`claude-sonnet-4-5-20250929`) for document analysis.

## Contributing

To improve the CLI tool:
1. Modify `convert_document.py`
2. Test with various document formats
3. Update this README if adding new features

## License

Same as the main project (MIT License).
