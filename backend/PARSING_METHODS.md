# Parsing Methods Documentation

This document describes the different parsing methods used in the CSV2MT conversion system and how they are tracked in the database.

## Overview

The system tracks which parsing route each uploaded file takes through the `parsing_method` field in the `ConversionUsage` table. This allows for analytics on which files require fallbacks, cost analysis, and debugging.

## Parsing Method Types

### 1. Format Specification Methods (CSV/Excel Files)

#### `format_spec_python`
- **Description**: The ideal path - format specification succeeded and Python parsed the file successfully
- **When used**: CSV or Excel files where Claude AI successfully detected the format and the Python parser found valid transactions
- **Success rate**: Highest success rate, most efficient
- **Location**: [claude_parser.py:595](backend/app/services/claude_parser.py#L595)

#### `format_spec_csv_retry`
- **Description**: Excel tab-delimited format failed, but CSV conversion succeeded
- **When used**: Excel files where initial tab-delimited extraction found 0 transactions, but conversion to proper CSV format succeeded
- **Benefits**: Avoids expensive AI extraction, uses Python parsing which is faster and more reliable
- **Location**: [claude_parser.py:548](backend/app/services/claude_parser.py#L548)
- **Note**: Stores both `format_specification` (original tab-delimited) and `csv_format_specification` (CSV retry) for debugging
- **Cost**: Two format detection calls (tab + CSV) but saves full AI extraction cost

#### `format_spec_fallback_single`
- **Description**: Format spec was created but found 0 transactions, fell back to single-chunk AI extraction
- **When used**: Small files (<120 lines) where format detection succeeded but parsing failed. For Excel files, this only happens after CSV retry also fails.
- **Indicates**: Format spec may be incorrect or file has unusual structure
- **Location**: [claude_parser.py:575](backend/app/services/claude_parser.py#L575)
- **Note**: Stores both `format_specification` and `failed_format_specification` for debugging

#### `format_spec_fallback_chunked`
- **Description**: Format spec was created but found 0 transactions, fell back to chunked AI extraction
- **When used**: Large files (≥120 lines) where format detection succeeded but parsing failed. For Excel files, this only happens after CSV retry also fails.
- **Indicates**: Format spec may be incorrect or file has unusual structure
- **Location**: [claude_parser.py:572](backend/app/services/claude_parser.py#L572)
- **Note**: Stores both `format_specification` and `failed_format_specification` for debugging

#### `format_detect_failed_single`
- **Description**: Format detection itself failed, went straight to single-chunk AI extraction
- **When used**: Small files where Claude AI couldn't determine the file format structure
- **Indicates**: Unusual or non-standard file format
- **Location**: [claude_parser.py:432](backend/app/services/claude_parser.py#L432)

#### `format_detect_failed_chunked`
- **Description**: Format detection itself failed, went straight to chunked AI extraction
- **When used**: Large files where Claude AI couldn't determine the file format structure
- **Indicates**: Unusual or non-standard file format
- **Location**: [claude_parser.py:438](backend/app/services/claude_parser.py#L438)

### 2. PDF Methods

#### `pdf_vision`
- **Description**: PDF parsed using Claude's vision API to preserve layout and formatting
- **When used**: All PDF files (primary PDF parsing method)
- **Benefits**: Preserves visual layout, handles complex formatting, most accurate for PDFs
- **Location**: [claude_parser.py:305](backend/app/services/claude_parser.py#L305)

#### `pdf_text_single`
- **Description**: PDF text extraction failed vision parsing, used single-chunk text extraction
- **When used**: Small PDFs where vision API fails (rare fallback case)
- **Indicates**: Vision API issue or unusual PDF structure
- **Location**: [claude_parser.py:406](backend/app/services/claude_parser.py#L406)

#### `pdf_text_chunked`
- **Description**: PDF text extraction failed vision parsing, used chunked text extraction
- **When used**: Large PDFs where vision API fails (rare fallback case)
- **Indicates**: Vision API issue or unusual PDF structure
- **Location**: [claude_parser.py:412](backend/app/services/claude_parser.py#L412)

## Database Schema

The `parsing_method` is stored in the `conversion_usage` table:

```sql
CREATE TABLE conversion_usage (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    file_name VARCHAR,
    bank_name VARCHAR,

    -- Token usage for cost analysis
    input_tokens INTEGER,
    output_tokens INTEGER,

    -- Error tracking
    error_code VARCHAR,  -- e.g., "EMPTY_STATEMENT", "VALIDATION_ERROR"
    error_message TEXT,

    -- Format specification (for CSV/Excel)
    format_specification TEXT,  -- JSON string

    -- Parsing method tracking
    parsing_method VARCHAR,  -- e.g., "format_spec_python", "pdf_vision"

    -- File size metrics (NEW)
    file_line_count INTEGER,  -- Number of lines in CSV/Excel files
    file_page_count INTEGER,  -- Number of pages in PDF files

    -- Conversion success tracking (NEW)
    success BOOLEAN,  -- True if conversion succeeded, False if failed

    conversion_date TIMESTAMP DEFAULT NOW()
);
```

## Analytics Queries

### Success Rate by Parsing Method

```sql
SELECT
    parsing_method,
    COUNT(*) as total_conversions,
    COUNT(CASE WHEN error_code IS NULL THEN 1 END) as successful,
    COUNT(CASE WHEN error_code IS NOT NULL THEN 1 END) as failed,
    ROUND(100.0 * COUNT(CASE WHEN error_code IS NULL THEN 1 END) / COUNT(*), 2) as success_rate_pct
FROM conversion_usage
WHERE parsing_method IS NOT NULL
GROUP BY parsing_method
ORDER BY total_conversions DESC;
```

### Format Spec Fallback Analysis

```sql
-- Find files where format spec was created but parsing failed
SELECT
    file_name,
    format_specification,
    error_message,
    conversion_date
FROM conversion_usage
WHERE parsing_method IN ('format_spec_fallback_single', 'format_spec_fallback_chunked')
ORDER BY conversion_date DESC
LIMIT 20;
```

### Cost Analysis by Parsing Method

```sql
SELECT
    parsing_method,
    COUNT(*) as conversions,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    AVG(input_tokens) as avg_input_tokens,
    AVG(output_tokens) as avg_output_tokens
FROM conversion_usage
WHERE parsing_method IS NOT NULL
GROUP BY parsing_method
ORDER BY total_input_tokens DESC;
```

### Format Detection Failures

```sql
-- Files where format detection completely failed
SELECT
    file_name,
    parsing_method,
    input_tokens,
    output_tokens,
    conversion_date
FROM conversion_usage
WHERE parsing_method IN ('format_detect_failed_single', 'format_detect_failed_chunked')
ORDER BY conversion_date DESC;
```

### Excel CSV Retry Effectiveness

```sql
-- Analyze how often Excel CSV retry saves us from AI extraction
SELECT
    'CSV Retry Success' as category,
    COUNT(*) as count,
    AVG(input_tokens) as avg_input_tokens,
    AVG(output_tokens) as avg_output_tokens
FROM conversion_usage
WHERE parsing_method = 'format_spec_csv_retry'

UNION ALL

SELECT
    'Excel AI Fallback' as category,
    COUNT(*) as count,
    AVG(input_tokens) as avg_input_tokens,
    AVG(output_tokens) as avg_output_tokens
FROM conversion_usage
WHERE parsing_method IN ('format_spec_fallback_single', 'format_spec_fallback_chunked')
  AND file_name LIKE '%.xlsx'
  OR file_name LIKE '%.xls';
```

### File Size vs Token Usage Correlation

```sql
-- Analyze correlation between file size and token usage
SELECT
    CASE
        WHEN file_line_count IS NOT NULL THEN 'CSV/Excel'
        WHEN file_page_count IS NOT NULL THEN 'PDF'
        ELSE 'Unknown'
    END as file_type,
    CASE
        WHEN file_line_count IS NOT NULL THEN
            CASE
                WHEN file_line_count < 50 THEN 'Small (<50 lines)'
                WHEN file_line_count < 150 THEN 'Medium (50-150 lines)'
                ELSE 'Large (>150 lines)'
            END
        WHEN file_page_count IS NOT NULL THEN
            CASE
                WHEN file_page_count = 1 THEN '1 page'
                WHEN file_page_count <= 3 THEN '2-3 pages'
                ELSE '4+ pages'
            END
        ELSE 'Unknown'
    END as size_category,
    COUNT(*) as conversions,
    AVG(input_tokens) as avg_input_tokens,
    AVG(output_tokens) as avg_output_tokens,
    AVG(input_tokens + output_tokens) as avg_total_tokens
FROM conversion_usage
WHERE success = true
GROUP BY file_type, size_category
ORDER BY file_type, size_category;
```

### Success Rate by File Size

```sql
-- Analyze success rate by file size
SELECT
    CASE
        WHEN file_line_count IS NOT NULL THEN
            CASE
                WHEN file_line_count < 50 THEN 'CSV Small (<50 lines)'
                WHEN file_line_count < 150 THEN 'CSV Medium (50-150 lines)'
                ELSE 'CSV Large (>150 lines)'
            END
        WHEN file_page_count IS NOT NULL THEN
            CASE
                WHEN file_page_count = 1 THEN 'PDF 1 page'
                WHEN file_page_count <= 3 THEN 'PDF 2-3 pages'
                ELSE 'PDF 4+ pages'
            END
        ELSE 'Unknown'
    END as size_category,
    COUNT(*) as total,
    COUNT(CASE WHEN success = true THEN 1 END) as successful,
    COUNT(CASE WHEN success = false THEN 1 END) as failed,
    ROUND(100.0 * COUNT(CASE WHEN success = true THEN 1 END) / COUNT(*), 2) as success_rate_pct
FROM conversion_usage
WHERE file_line_count IS NOT NULL OR file_page_count IS NOT NULL
GROUP BY size_category
ORDER BY size_category;
```

### Overall Conversion Success Rate

```sql
-- Overall success vs failure tracking
SELECT
    COUNT(*) as total_conversions,
    COUNT(CASE WHEN success = true THEN 1 END) as successful,
    COUNT(CASE WHEN success = false THEN 1 END) as failed,
    COUNT(CASE WHEN success IS NULL THEN 1 END) as unknown,
    ROUND(100.0 * COUNT(CASE WHEN success = true THEN 1 END) / COUNT(*), 2) as success_rate_pct,
    -- Breakdown by error type
    COUNT(CASE WHEN error_code = 'EMPTY_STATEMENT' THEN 1 END) as empty_statements,
    COUNT(CASE WHEN error_code = 'VALIDATION_ERROR' THEN 1 END) as validation_errors,
    COUNT(CASE WHEN error_code = 'INTERNAL_ERROR' THEN 1 END) as internal_errors
FROM conversion_usage;
```

## Decision Tree

```
File Upload
    |
    ├─ Is PDF?
    |   └─ YES → pdf_vision
    |       └─ FAIL → pdf_text_single/chunked (rare)
    |
    └─ Is CSV/Excel?
        └─ YES → Try format detection
            |
            ├─ Format detection SUCCESS
            |   └─ Try Python parsing with format spec
            |       |
            |       ├─ Found transactions → format_spec_python ✓
            |       |
            |       └─ No transactions
            |           |
            |           ├─ Is Excel?
            |           |   └─ YES → Convert to CSV & retry
            |           |       |
            |           |       ├─ CSV retry found transactions → format_spec_csv_retry ✓
            |           |       └─ CSV retry failed → AI extraction fallback
            |           |
            |           └─ Is CSV?
            |               └─ Direct AI extraction → format_spec_fallback_single/chunked
            |
            └─ Format detection FAILED
                └─ Direct AI extraction → format_detect_failed_single/chunked
```

## File Lifecycle Tracking

For each conversion, we track:

1. **File Details**: `file_name`, `bank_name`
2. **Cost**: `input_tokens`, `output_tokens`
3. **Errors**: `error_code`, `error_message`
4. **Format Spec**: `format_specification` (successful) or `failed_format_specification` (fallback)
5. **Parsing Route**: `parsing_method` (9 possible values)
6. **File Size Metrics**: `file_line_count` (CSV/Excel), `file_page_count` (PDF)
7. **Conversion Outcome**: `success` (True/False/NULL)

This complete tracking allows us to:
- **Identify problematic file formats** that frequently fail
- **Analyze cost per parsing method** and predict costs based on file size
- **Debug format specification issues** with detailed metadata
- **Monitor success rates** overall and by parsing method
- **Optimize parsing strategies** based on real data
- **Correlate file size with token usage** for accurate cost prediction
- **Track conversion quality** and identify error patterns

## Implementation Notes

### Format Specification Storage

When storing format specifications, we:
- Exclude the `metadata` key to avoid circular references
- Store successful specs in `format_specification`
- Store failed specs in `failed_format_specification` with `_fallback_reason`
- Accumulate token usage from both format detection and fallback parsing

### Excel CSV Retry Optimization

Excel files are initially extracted as tab-delimited text. If this fails to find transactions:

1. **Convert to CSV**: Excel is converted to proper comma-delimited CSV format
2. **Retry format detection**: A new format spec is created for the CSV version
3. **Retry parsing**: Python parser attempts to parse the CSV version
4. **Success**: If successful, uses `format_spec_csv_retry` method
5. **Failure**: If this also fails, falls back to expensive AI extraction

**Benefits**:
- Reduces AI extraction costs for Excel files with problematic tab-delimited format
- CSV is more standardized and works better with format spec approach
- Python parsing is faster and more reliable than AI extraction

**Cost trade-off**:
- Two format detection API calls (tab + CSV) ≈ 7,000 tokens
- Full AI extraction ≈ 15,000-50,000+ tokens depending on file size
- **Savings**: 50-85% token reduction when CSV retry succeeds

### Error Codes

Standard error codes tracked:
- `EMPTY_STATEMENT`: File contains no valid transaction data
- `VALIDATION_ERROR`: File could not be validated
- `INTERNAL_ERROR`: Unexpected server error

### Empty Statements

Empty statements:
- Raise `EmptyStatementError` (custom exception)
- Count towards conversion limits (because they consume AI tokens)
- Are NOT logged to Sentry (expected error condition)
- Store error code and message for analytics

## Future Improvements

Potential areas for optimization based on `parsing_method` analytics:

1. **Format Spec Improvement**: If `format_spec_fallback_*` methods are common, improve format detection prompts
2. **Direct Extraction**: If `format_detect_failed_*` methods have high success rate, consider making them primary for certain file types
3. **Cost Optimization**: Identify which methods consume most tokens and optimize prompts
4. **Success Prediction**: Use historical data to predict best method for new files based on file characteristics
