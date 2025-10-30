# Bug Fix: Newline Characters Breaking Keyword Matching

**Date:** 2025-10-30
**Issue:** Government warning and sulfite declarations were not being detected even though they were present in OCR text

---

## Root Cause

OCR text contains NEWLINE characters (`\n`) between words, but the verification code was searching for keywords with SPACES.

### Example from Actual Label

**OCR Text:**
```
GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON
GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC...
CONTAINS SULFITES
```

**Code Search:**
```python
if "surgeon general" not in ocr_text_lower:  # Searching with SPACE
```

**Problem:**
- `"surgeon general"` (with space) is NOT a substring of `"the surgeon\ngeneral"` (with newline)
- Python's `in` operator does exact substring matching
- `"surgeon general" != "surgeon\ngeneral"`

---

## The Bug

### Government Warning (`verification.py:947-952`)

**Before (BROKEN):**
```python
ocr_text_lower = ocr_result.full_text.lower()

for keyword in GOVERNMENT_WARNING_CRITICAL_KEYWORDS:
    if keyword.lower() not in ocr_text_lower:  # FAILS: space != newline
        missing_keywords.append(keyword)
```

**After (FIXED):**
```python
ocr_text_lower = ocr_result.full_text.lower()
# Normalize whitespace (convert newlines to spaces)
ocr_text_normalized = re.sub(r'\s+', ' ', ocr_text_lower).strip()

for keyword in GOVERNMENT_WARNING_CRITICAL_KEYWORDS:
    if keyword.lower() not in ocr_text_normalized:  # WORKS: all whitespace is spaces
        missing_keywords.append(keyword)
```

### Sulfite Declaration (`verification.py:1313-1324`)

**Before (BROKEN):**
```python
ocr_lower = ocr_result.full_text.lower()
sulfite_pattern = r'\b(?:contains\s+)?sul[fp]hite?s?\b'
match = re.search(sulfite_pattern, ocr_lower)  # May fail on "CONTAINS\nSULFITES"
```

**After (FIXED):**
```python
ocr_lower = ocr_result.full_text.lower()
# Normalize whitespace
ocr_normalized = re.sub(r'\s+', ' ', ocr_lower).strip()
sulfite_pattern = r'\b(?:contains\s+)?sul[fp]hite?s?\b'
match = re.search(sulfite_pattern, ocr_normalized)  # Works with normalized text
```

---

## Why This Happened

OCR text from labels naturally contains line breaks:
```
GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON
GENERAL, WOMEN SHOULD NOT DRINK...
```

When converted to a string, these become literal `\n` characters:
```python
"GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON\nGENERAL, WOMEN SHOULD NOT DRINK..."
```

The keyword list uses normal spaces:
```python
GOVERNMENT_WARNING_CRITICAL_KEYWORDS = [
    "surgeon general",  # ← space, not newline
]
```

---

## Why Regex `\s+` Wasn't Enough

While regex patterns like `\s+` match newlines, the **keyword substring check** doesn't use regex:

```python
if "surgeon general" not in ocr_text_lower:  # Plain string search, not regex!
```

This is a plain Python string operation, not regex. It does exact character matching.

---

## The Fix

**Use `re.sub(r'\s+', ' ', text)` to normalize whitespace:**

```python
# Convert all whitespace (spaces, newlines, tabs, multiple spaces) to single spaces
normalized = re.sub(r'\s+', ' ', text).strip()
```

**Examples:**
```python
"SURGEON\nGENERAL"     → "SURGEON GENERAL"
"CONTAINS  \n SULFITES" → "CONTAINS SULFITES"
"word1\t\tword2"       → "word1 word2"
```

---

## Files Modified

1. **`functions/verification.py`**
   - Line 943-945: Added whitespace normalization for government warning keywords
   - Line 1314-1315: Added whitespace normalization for sulfite pattern matching

---

## Testing

Deploy and test with the Veuve Clicquot label:

```bash
firebase deploy --only functions
```

**Expected Results:**
```json
{
  "field_name": "government_warning",
  "status": "match",  // ✅ Previously "not_found"
  "message": "Government warning matches"
}

{
  "field_name": "sulfites",
  "status": "match",  // ✅ Previously "not_found"
  "message": "Sulfite declaration found on label"
}
```

---

## Lesson Learned

**Always normalize whitespace when doing text matching on OCR output!**

OCR text inherently contains:
- Newlines (`\n`) from multi-line labels
- Carriage returns (`\r`) on some systems
- Tabs (`\t`) from formatting
- Multiple consecutive spaces from layout

**Best practice:**
```python
# ALWAYS do this before text matching on OCR output
text_normalized = re.sub(r'\s+', ' ', text).strip()
```

---

## Related Issues

This same bug could affect:
- Any field verification using substring matching
- Brand names split across lines
- Multi-word product classes

**Recommendation:** Audit all verification functions to ensure whitespace normalization is applied before text matching.
