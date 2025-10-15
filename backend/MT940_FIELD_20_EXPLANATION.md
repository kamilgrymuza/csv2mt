# MT940 Field 20: Transaction Reference Number - Detailed Explanation

## Overview

**Field 20** (`:20:`) is a **mandatory field** in MT940 format that contains the **Transaction Reference Number**.

## Purpose

According to the **SWIFT MT940 specification**:

> *"This field specifies the reference assigned by the Sender to unambiguously identify the message."*

The primary purpose is to provide a **unique identifier** for the statement message, allowing:
- Tracking and reconciliation of statements
- Prevention of duplicate processing
- Reference in correspondence between bank and customer
- Linking to request messages (MT920)

## Format Specification

- **Tag:** `:20:`
- **Format:** `16x` (up to 16 alphanumeric characters)
- **Status:** Mandatory
- **Content:** Free-form alphanumeric string

## Is "MT940" Standard or Arbitrary?

### Answer: **ARBITRARY (Non-Standard)**

The value "MT940" in Field 20 is **NOT part of the SWIFT standard** - it's a **bank-specific choice**.

Different banks use different approaches:

### Common Patterns Used by Banks

1. **Static Identifier** (like "MT940")
   - Simple, but not unique
   - Used by some banks as a placeholder
   - **Not recommended** - violates the "unambiguous identification" requirement

2. **Statement Number**
   - Example: `STMT001`, `00001`, `12345`
   - Sequential numbering
   - Simple but may reset periodically

3. **Date-Based References**
   - Example: `20241015`, `2024-10-15`
   - Ties reference to statement date
   - Easy to understand

4. **Date + Sequence Number**
   - Example: `20241015-001`, `20241015STMT001`
   - Combines date with sequence
   - **Recommended** - provides uniqueness over time

5. **Account + Date**
   - Example: `ACC123-20241015`, `12345678-241015`
   - Includes account identifier
   - Good for multi-account systems

6. **Complex Identifiers**
   - Example: `INGPL20241015STMT001`, `MT940-20241015-12345`
   - Includes bank code, date, sequence
   - **Best practice** - maximizes uniqueness

7. **UUID/GUID-based**
   - Example: `A1B2C3D4E5F6G7H8`
   - Cryptographically unique
   - Excellent for automated systems

## What Your Bank Used: "MT940"

Your ING Corporate file contains `:20:MT940`, which means:

- **ING chose to use a static identifier** instead of a unique reference
- This is **technically valid** (meets format requirements)
- But it **doesn't follow best practices** (not truly unique)
- It's a **simplified implementation** that works for their use case

Many banks do this when:
- Statements are generated on-demand (not stored long-term)
- Internal systems track statements differently
- Uniqueness is ensured at a different level (filename, timestamps, etc.)

## What Should csv2mt Use?

### Current Implementation

Our code uses:
```python
mt940_lines.append(":20:STATEMENT")
```

This is similar to ING's approach - a static identifier.

### Recommendation: Generate Unique References

We should generate **unique, meaningful references** to follow SWIFT best practices:

**Option 1: Date + Statement Number** (Recommended)
```python
# Format: YYYYMMDD-NNN
reference = f"{start_date.replace('-', '')}-{statement_num.zfill(3)}"
# Example: :20:20241015-001
```

**Option 2: Timestamp-based**
```python
# Format: YYYYMMDDHHMMSS
reference = datetime.now().strftime("%Y%m%d%H%M%S")
# Example: :20:20241015143022
```

**Option 3: Account + Date**
```python
# Format: Last6OfAccount-YYYYMMDD
account_suffix = acc_num[-6:] if len(acc_num) > 6 else acc_num
reference = f"{account_suffix}-{start_date.replace('-', '')}"
# Example: :20:623719-20241015
```

**Option 4: User-specified + fallback**
```python
# Allow user to provide custom reference, fall back to auto-generated
reference = user_provided_ref or f"STMT-{start_date.replace('-', '')}-{statement_num.zfill(3)}"
```

## Field 20 in MT920 Request/Response Flow

When MT940 is sent **in response to an MT920 Request Message**:
- Field 20 **MUST** contain the same reference as Field 20 from the MT920 request
- This links the response to the original request

In our case (generating statements from documents):
- There is **no MT920 request**
- We're creating statements independently
- We can use any unique identifier we choose

## Comparison: Field 20 vs Field 28C

| Field | Purpose | Format | Example |
|-------|---------|--------|---------|
| **:20:** Transaction Reference | Identifies the **message** | 16x | `20241015-001` |
| **:28C:** Statement Number | Identifies the **statement sequence** | 5n[/5n] | `00001` or `00001/00001` |

**Key Difference:**
- **Field 20** = Message-level identifier (like an envelope ID)
- **Field 28C** = Statement sequence number (like a page number)

## Implementation in csv2mt

### ✅ Current Implementation (DATE-FILENAME Format)

We have implemented Field 20 generation using **date + filename** combination:

**Format:** `YYMMDD-FILENAME` (max 16 characters)

**Algorithm:**
```python
# 1. Extract date in YYMMDD format (6 chars)
date_part = start_date.strftime("%y%m%d")  # e.g., "241015"

# 2. Extract meaningful filename part (up to 8 chars)
basename = source_filename.rsplit('.', 1)[0]  # Remove extension
basename_clean = ''.join(c for c in basename if c.isalnum())  # Remove special chars
filename_part = basename_clean[:8].upper()  # Take first 8 chars, uppercase

# 3. Combine: DATE-FILENAME
field_20_ref = f"{date_part}-{filename_part}"[:16]  # Max 16 chars
```

**Examples:**

| Source File | Statement Date | Field 20 Value | Explanation |
|-------------|----------------|----------------|-------------|
| `statement.pdf` | 2024-10-15 | `241015-STATEMEN` | Date + first 8 chars of filename |
| `ING_Corporate_Sep_2024.pdf` | 2024-10-15 | `241015-INGCORPO` | Date + sanitized filename |
| `My Bank Statement.xlsx` | 2024-10-15 | `241015-MYBANKST` | Spaces removed, alphanumeric only |
| `report_123456.csv` | 2024-10-15 | `241015-REPORT12` | Underscores removed |
| (no filename) | 2024-10-15 | `241015-STMT` | Fallback to "STMT" |

### Benefits of This Approach

1. ✅ **Unique** - Combines date with file identifier
2. ✅ **Meaningful** - Shows when and from what file statement was generated
3. ✅ **Traceable** - Can correlate MT940 back to source document
4. ✅ **SWIFT Compliant** - Meets "unambiguous identification" requirement
5. ✅ **Compact** - Fits within 16 character limit
6. ✅ **Human-readable** - Easy to understand at a glance

### Comparison with Bank Files

| Source | Field 20 Value | Quality |
|--------|----------------|---------|
| **Your bank (ING)** | `MT940` | ❌ Static, not unique, arbitrary |
| **csv2mt (old)** | `STATEMENT` | ❌ Static, not unique |
| **csv2mt (new)** | `241015-STATEMEN` | ✅ Unique, meaningful, traceable |

### Code Location

Implementation in: `backend/app/services/claude_parser.py` (lines 329-356)

The source filename is captured during document parsing and stored in metadata, then used when generating the MT940 output.

## Summary

| Question | Answer |
|----------|--------|
| **What is Field 20?** | Transaction Reference Number - unique message identifier |
| **Is "MT940" standard?** | **No** - it's arbitrary. Banks choose their own format. |
| **What does csv2mt use?** | Date + filename (e.g., `241015-STATEMEN`) |
| **Why not keep "STATEMENT"?** | Not unique, doesn't follow SWIFT best practices |
| **Max length?** | 16 characters |
| **Mandatory?** | Yes |

## References

- **SWIFT MT940 Standards:** [SWIFT Customer Statement Message](https://www2.swift.com/knowledgecentre/publications/usgf_20230720/2.0?topic=idx_mt940_2.htm)
- **SEPA for Corporates:** [MT940 Format Overview](https://www.sepaforcorporates.com/swift-for-corporates/account-statement-mt940-file-format-overview/)
- **ISO 15022 Standard:** MT940 Message Type Specification

## Conclusion

**Your bank's use of "MT940" in Field 20 is arbitrary and non-standard.** While technically valid (meets format requirements), it doesn't fulfill the SWIFT requirement for "unambiguous identification."

**csv2mt now generates unique references** using date + filename format (e.g., `241015-STATEMEN`) to follow SWIFT best practices and ensure proper statement tracking. This provides:

- ✅ Uniqueness across time and files
- ✅ Traceability back to source documents
- ✅ SWIFT compliance
- ✅ Human readability
