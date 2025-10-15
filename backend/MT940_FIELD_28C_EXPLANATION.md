# MT940 Field 28C: Statement Number/Sequence Number - Detailed Explanation

## Overview

**Field 28C** (`:28C:`) is a **mandatory field** in MT940 format that contains the **Statement Number** and optionally the **Sequence Number**.

## Purpose

According to the **SWIFT MT940 specification**:

> *"Sequential number of the statement, optionally followed by the sequence number of the message within that statement when more than one message is sent for one statement"*

## Format Specification

- **Tag:** `:28C:`
- **Format:** `5n[/5n]` (5 numeric digits, optionally followed by `/` and 5 more numeric digits)
- **Status:** Mandatory
- **Components:**
  - **Statement Number** (required): 5 digits
  - **Sequence Number** (optional): 5 digits after `/`

## Format Examples

| Field 28C | Interpretation |
|-----------|----------------|
| `:28C:00001` | Statement number 1 (no sequence) |
| `:28C:00123` | Statement number 123 (no sequence) |
| `:28C:00001/00001` | Statement 1, Message 1 of N |
| `:28C:00001/00002` | Statement 1, Message 2 of N |
| `:28C:00365/00001` | Statement 365, Message 1 of N |

## Two Components Explained

### 1. Statement Number (Required)

**Purpose:** Sequential identifier for the bank statement itself

**Rules:**
- Increments with each new statement period
- Typically resets to `00001` on January 1st each year
- Format: 5 digits with leading zeros (e.g., `00001`, `00002`, `00123`)
- Range: `00001` to `99999`

**Example:**
- January statement: `:28C:00001`
- February statement: `:28C:00002`
- March statement: `:28C:00003`

### 2. Sequence Number (Optional)

**Purpose:** Identifies the message order when a single statement is split across multiple MT940 messages

**When to Use:**
- Only when a statement is **too large** to fit in a single MT940 message
- SWIFT messages have size limits, so large statements must be split
- Each message part gets the same statement number but different sequence numbers

**Rules:**
- Always starts at `00001` for the first message
- Increments sequentially: `00001`, `00002`, `00003`, etc.
- All messages with the same statement number but different sequence numbers belong to the same statement

**Example Scenario:**

A bank statement has 1,000 transactions that won't fit in one MT940 message:

```
:28C:00042/00001  ← Statement 42, Part 1 (transactions 1-400)
:28C:00042/00002  ← Statement 42, Part 2 (transactions 401-800)
:28C:00042/00003  ← Statement 42, Part 3 (transactions 801-1000)
```

## Statement Number Incrementing

### Annual Reset Pattern

Most banks follow this convention:

```
:28C:00001  ← January 2024
:28C:00002  ← February 2024
...
:28C:00012  ← December 2024
:28C:00001  ← January 2025 (reset to 1)
```

### Continuous Incrementing

Some banks never reset and increment indefinitely:

```
:28C:00001  ← Statement 1
:28C:00002  ← Statement 2
...
:28C:99999  ← Statement 99,999
:28C:00001  ← Wraps around after 99,999
```

## Single Statement vs. Multi-Message Statement

### Single Statement (No Sequence Number)

**Format:** `:28C:SSSSS` (statement number only)

Used when the entire statement fits in one MT940 message:

```
:20:241015-STATEMEN
:25:/PL27105010251000009085623719
:28C:00001  ← Single message
:60F:C241001EUR1000,00
:61:241001C100,00NMSC
:62F:C241015EUR1100,00
```

### Multi-Message Statement (With Sequence Number)

**Format:** `:28C:SSSSS/NNNNN` (statement + sequence)

Used when statement is split across multiple messages:

**Message 1:**
```
:20:241015-STATEMEN-1
:25:/PL27105010251000009085623719
:28C:00001/00001  ← Part 1
:60F:C241001EUR1000,00
:61:241001C100,00NMSC
... (transactions 1-500)
:62M:C241010EUR5000,00  ← Intermediate balance (M = More to follow)
```

**Message 2:**
```
:20:241015-STATEMEN-2
:25:/PL27105010251000009085623719
:28C:00001/00002  ← Part 2
:60M:C241010EUR5000,00  ← Continuation from previous (M = More)
:61:241011C200,00NMSC
... (transactions 501-1000)
:62F:C241015EUR15000,00  ← Final balance (F = Final)
```

## Field 60F vs 60M and Field 62F vs 62M

When using sequence numbers:

| Field | Meaning | Usage |
|-------|---------|-------|
| `:60F:` | Opening balance (First) | First message only |
| `:60M:` | Opening balance (More) | Continuation messages |
| `:62F:` | Closing balance (Final) | Last message only |
| `:62M:` | Closing balance (More) | Intermediate messages |

## Your Bank's Usage: `:28C:00002`

Your ING Corporate file contains `:28C:00002`, which means:

- **Statement Number:** `00002` (second statement in the sequence)
- **Sequence Number:** Not present (entire statement in one message)
- **Interpretation:** This is the 2nd statement of the period (likely 2nd month if annual reset)

## What csv2mt Should Use

### Current Implementation

Our code uses:
```python
statement_num = "001"
mt940_lines.append(f":28C:{statement_num}")
```

Output: `:28C:001`

### Analysis: Is This Correct?

**For Single Statement Documents:** ✅ **YES**

When converting a single PDF/CSV/Excel statement:
- It represents ONE statement period
- It's the first (and only) statement we're generating
- No sequence number needed (fits in one message)
- Using `00001` or `001` is appropriate

**Format Options:**

| Format | Valid? | Recommendation |
|--------|--------|----------------|
| `:28C:001` | ⚠️ Valid but non-standard | Should use 5 digits |
| `:28C:00001` | ✅ Correct (5 digits) | **Best practice** |
| `:28C:1` | ❌ Invalid (< 5 digits) | Don't use |

### Recommendation: Use 5-Digit Format

We should change from `001` to `00001` to follow SWIFT standard:

```python
statement_num = "001"
# Pad to 5 digits as per SWIFT specification
statement_num_formatted = statement_num.zfill(5)  # "00001"
mt940_lines.append(f":28C:{statement_num_formatted}")
```

## Should We Ever Use Sequence Numbers?

### For csv2mt: **NO** (in most cases)

**Reasons:**
1. ✅ We're converting **single documents** (PDF/CSV/Excel)
2. ✅ Each document is one statement period
3. ✅ Modern MT940 parsers handle large messages
4. ✅ File-based MT940 (not SWIFT network) has no strict size limits
5. ✅ Adding complexity without benefit

**When You Might Need Sequences:**
- Converting very large statements (1000+ transactions)
- Generating MT940 for SWIFT network transmission (strict size limits)
- System has message size restrictions

### Implementation for Sequence Numbers (if needed)

```python
def split_mt940_by_size(transactions, max_transactions_per_message=500):
    """Split large statements into multiple messages"""
    statement_num = "00001"
    messages = []

    for seq_num, chunk in enumerate(chunked(transactions, max_transactions_per_message), 1):
        if len(transactions) <= max_transactions_per_message:
            # Single message, no sequence number
            field_28c = f":28C:{statement_num}"
        else:
            # Multiple messages, add sequence number
            seq_formatted = str(seq_num).zfill(5)
            field_28c = f":28C:{statement_num}/{seq_formatted}"

        messages.append(generate_mt940_message(chunk, field_28c))

    return messages
```

## E2E Test Context

### The Difference

- **Bank file:** `:28C:00002` (Statement #2)
- **csv2mt:** `:28C:001` (Statement #1, wrong format)

### Why They Differ

1. **Bank's perspective:**
   - This is the 2nd statement of the year/period
   - Uses 5-digit format (`00002`)

2. **csv2mt's perspective:**
   - We're converting a single document
   - It's the 1st (and only) statement we're generating
   - Currently uses 3-digit format (`001`)

### Should E2E Test Ignore Field 28C?

**Option 1: ❌ Ignore Field 28C** (Not Recommended)
- Lose important validation
- Statement numbering is meaningful

**Option 2: ✅ Normalize Comparison** (Recommended)
- Compare numeric values (ignore leading zeros)
- Allow both `001` and `00001` to match `1`
- Focus on semantic equality, not format

**Option 3: ✅ Fix csv2mt Format** (Best)
- Change csv2mt to use 5-digit format: `00001`
- Still won't match bank's `00002`, but that's expected
- Different statement numbers are acceptable (bank's 2nd vs our 1st)

## Recommendation for csv2mt

### 1. Fix Format (5 Digits)

Change:
```python
statement_num = "001"
```

To:
```python
statement_num = "00001"
```

### 2. E2E Test: Normalize Comparison

In E2E tests, compare statement numbers numerically:

```python
def normalize_field_28c(value: str) -> tuple:
    """
    Normalize Field 28C for comparison

    Returns: (statement_number, sequence_number)
    """
    parts = value.split('/')
    stmt_num = int(parts[0])  # Remove leading zeros
    seq_num = int(parts[1]) if len(parts) > 1 else None
    return (stmt_num, seq_num)

# Compare
gen_28c = normalize_field_28c("001")    # (1, None)
exp_28c = normalize_field_28c("00002")  # (2, None)

# Expected: Different statement numbers are acceptable
# (Bank's 2nd statement vs our generated 1st statement)
```

### 3. Document the Difference

E2E test should **accept** different statement numbers because:
- Bank file is statement #N in their sequence
- csv2mt generates statement #1 (fresh conversion)
- **This is expected and correct**

## Summary

| Question | Answer |
|----------|--------|
| **What is Field 28C?** | Statement Number / Sequence Number |
| **Format?** | `5n[/5n]` (e.g., `00001` or `00001/00001`) |
| **Statement Number?** | Sequential statement identifier (resets yearly) |
| **Sequence Number?** | Message order when statement split across multiple messages |
| **When use sequence?** | Only when statement too large for one message |
| **csv2mt current?** | `001` (3 digits) |
| **Should be?** | `00001` (5 digits per SWIFT standard) |
| **E2E difference OK?** | Yes - bank's statement #N vs our statement #1 is expected |
| **Mandatory?** | Yes |

## References

- **SWIFT MT940 Standards:** [SWIFT Customer Statement Message](https://www2.swift.com/knowledgecentre/publications/usgf_20230720/2.0?topic=idx_mt940_2.htm)
- **SEPA for Corporates:** [MT940 Format Overview](https://www.sepaforcorporates.com/swift-for-corporates/account-statement-mt940-file-format-overview/)
- **SAP Community:** [MT940 Statement Number Discussion](https://answers.sap.com/questions/8045075/mt940-format-on-statement-numbersequence-number.html)

## Conclusion

**Field 28C contains the statement number and optional sequence number.**

**For csv2mt:**
1. ✅ Fix format: Use `00001` (5 digits) instead of `001`
2. ✅ No sequence number needed (single-message statements)
3. ✅ E2E test should accept different statement numbers (bank's #N vs our #1)
4. ✅ Consider numeric comparison in E2E tests to ignore leading zeros

**The difference between bank's `00002` and csv2mt's `00001` is expected and correct** - the bank file is their 2nd statement, while csv2mt generates the 1st statement from a single document.
