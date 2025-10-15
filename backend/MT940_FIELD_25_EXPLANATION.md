# MT940 Field 25: Account Identification - Slash Prefix Explanation

## Overview

Field `:25:` in MT940 format identifies the account being reported. It can appear with or without a leading slash `/`.

## Format Variants

### 1. **With Slash Prefix: `/ACCOUNT_NUMBER`**

Example: `:25:/PL27105010251000009085623719`

The slash prefix is part of the **SWIFT MT940 standard** and follows this structure:

```
:25:/[IBAN or account number]
```

**Why use the slash?**

The slash (`/`) is a **SWIFT delimiter** that separates different parts of a field. According to SWIFT MT standards:

- **Field 25 Full Format:** `:25:[Bank BIC]/[Account Number]`
- When only the account number is present (BIC omitted), the slash remains: `:25:/[Account Number]`

**Example with BIC:**
```
:25:INGBPLPW/PL27105010251000009085623719
```

**Example without BIC (BIC omitted):**
```
:25:/PL27105010251000009085623719
```

### 2. **Without Slash Prefix: `ACCOUNT_NUMBER`**

Example: `:25:PL27105010251000009085623719`

Some banks **omit the slash** entirely when:
- The account number is the only identifier
- They follow a simpler implementation
- Internal systems don't require the BIC/account delimiter

## SWIFT Standard (Official)

According to **SWIFT MT940 Customer Statement Message** specification:

**Field 25: Account Identification**
- **Format:** `35x` (max 35 characters)
- **Structure (Option P):** `//Account` or `/Account`
- **Structure (Option F):** `Account`

The specification allows multiple formats:
- `//` prefix for party identifier
- `/` prefix for account without BIC
- No prefix for simple account number

## Regional Differences

### European Banks (Common Practice)
Most European banks use the slash prefix:
```
:25:/DE89370400440532013000
:25:/FR1420041010050500013M02606
:25:/PL27105010251000009085623719
```

### Other Regions
Some banks (especially in Asia, Americas) may omit the slash:
```
:25:1234567890
:25:ACCOUNTNUMBER
```

## Which Format Should You Use?

### **Best Practice: Use `/IBAN` (with slash)**

**Reasons:**
1. ✅ **SWIFT Compliant:** Follows the official SWIFT MT940 standard
2. ✅ **International Compatibility:** Most SWIFT parsers expect this format
3. ✅ **Future-proof:** Allows for BIC prefix if needed later
4. ✅ **Standard Interpretation:** Clear distinction between identifier parts

### **When to Omit the Slash:**
- Your bank's MT940 files consistently omit it
- You're matching a specific bank's format exactly
- Internal system requirements

## Implementation in csv2mt

Currently, our implementation outputs:
```python
mt940_lines.append(f":25:{acc_num}")
```

### Recommendation: **Add the slash prefix for IBANs**

We should detect IBANs and add the slash prefix:

```python
# Add slash prefix for IBANs (standard SWIFT format)
if acc_num and (len(acc_num) >= 15 and acc_num[:2].isalpha()):
    # Looks like IBAN (starts with 2 letters, 15+ chars)
    mt940_lines.append(f":25:/{acc_num}")
else:
    # Non-IBAN account number
    mt940_lines.append(f":25:{acc_num}")
```

## Summary

| Aspect | With Slash (`/`) | Without Slash |
|--------|------------------|---------------|
| **SWIFT Standard** | ✅ Yes (preferred) | ⚠️ Allowed but less common |
| **IBAN Format** | ✅ Recommended | ❌ Non-standard |
| **International** | ✅ Widely accepted | ⚠️ May cause issues |
| **Parser Compatibility** | ✅ High | ⚠️ Variable |

## References

- **SWIFT MT940 Format Guide:** [SWIFT Standards MT940](https://www2.swift.com/knowledgecentre/publications/usgf_20230720/2.0?topic=idx_mt940_2.htm)
- **ISO 9362 (BIC codes):** Bank Identifier Code standard
- **ISO 13616 (IBAN):** International Bank Account Number standard

## Conclusion

The **slash prefix (`/`)** in field 25 is the **SWIFT-compliant standard** for separating the BIC from the account number. When the BIC is omitted, the slash remains to indicate "no BIC, just account number."

**For maximum compatibility with SWIFT systems worldwide, IBANs should be prefixed with `/`.**
