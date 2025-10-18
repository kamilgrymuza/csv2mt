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
- **Location**: [claude_parser.py:488](backend/app/services/claude_parser.py#L488)

#### `format_spec_fallback_single`
- **Description**: Format spec was created but found 0 transactions, fell back to single-chunk AI extraction
- **When used**: Small files (<120 lines) where format detection succeeded but parsing failed
- **Indicates**: Format spec may be incorrect or file has unusual structure
- **Location**: [claude_parser.py:478](backend/app/services/claude_parser.py#L478)
- **Note**: Stores both `format_specification` and `failed_format_specification` for debugging

#### `format_spec_fallback_chunked`
- **Description**: Format spec was created but found 0 transactions, fell back to chunked AI extraction
- **When used**: Large files (≥120 lines) where format detection succeeded but parsing failed
- **Indicates**: Format spec may be incorrect or file has unusual structure
- **Location**: [claude_parser.py:475](backend/app/services/claude_parser.py#L475)
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

    -- Parsing method tracking (NEW)
    parsing_method VARCHAR,  -- e.g., "format_spec_python", "pdf_vision"

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
            |       └─ No transactions → format_spec_fallback_single/chunked
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
5. **Parsing Route**: `parsing_method` (8 possible values)

This complete tracking allows us to:
- Identify problematic file formats that frequently fail
- Analyze cost per parsing method
- Debug format specification issues
- Monitor success rates
- Optimize parsing strategies based on real data

## Implementation Notes

### Format Specification Storage

When storing format specifications, we:
- Exclude the `metadata` key to avoid circular references
- Store successful specs in `format_specification`
- Store failed specs in `failed_format_specification` with `_fallback_reason`
- Accumulate token usage from both format detection and fallback parsing

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
