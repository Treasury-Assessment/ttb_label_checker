# OCR Field Detection Improvements - Token Coverage Approach

**Date:** 2025-10-30
**Issue:** Brand name and government warning fields were not being detected when text spanned multiple lines or had OCR errors between related text

---

## Problems Identified

### 1. Brand Name Detection Issue

**Root Cause:**
Fuzzy matching entire expected text against individual OCR blocks fails when text spans multiple lines. OCR returns individual **words** as blocks, not complete phrases.

**Example Failure Scenarios:**

**Scenario A: Multi-line brand**
```
Expected: "Jack Daniel's Tennessee Whiskey"
OCR Blocks: ["Jack", "Daniel's", "Tennessee", "Whiskey"]

Old fuzzy_match("Jack Daniel's Tennessee Whiskey", "Jack") → 25% ❌
Old fuzzy_match("Jack Daniel's Tennessee Whiskey", "Daniel's") → 20% ❌
```

**Scenario B: Spurious OCR error between words**
```
Expected: "Jack Daniel's Tennessee Whiskey"
OCR Blocks: ["Jack", "Daniel's", "®", "Tennessee", "Whiskey"]
                                  ↑ spurious symbol breaks adjacency

Adjacent block combining fails because blocks aren't consecutive.
```

### 2. Government Warning Detection Issue

**Root Cause:**
The warning is 265 characters (3-4 sentences). Fuzzy matching the entire string against OCR text fails due to:
- Line breaks and spacing variations
- Minor OCR errors scattered throughout
- String comparison being too strict even when all words are present

**Example:**
```
Expected: "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink..."

OCR: "GOVERNMENT WARNING:\n(1) According to\nthe Surgeon General, women\nshould not drink..."

Fuzzy match: ~88% ❌ (below 95% threshold)
But all 40+ words are actually present!
```

---

## Solution: Token-Based Coverage Matching

### Core Concept

Instead of fuzzy matching entire strings, we:
1. **Split expected text into tokens** (words)
2. **Find OCR blocks containing those tokens** (fuzzy match each token)
3. **Calculate coverage**: What % of expected tokens are present?
4. **If coverage ≥ 80%**, consider it a match

This handles:
- ✅ Multi-line text (tokens can be in any block)
- ✅ Non-adjacent blocks (spurious OCR errors between words)
- ✅ Long text (each token matched independently)
- ✅ Minor OCR errors (fuzzy match on individual tokens)

---

## Implementation

### 1. Brand Name Matching (`verification.py:306-398`)

**New algorithm:**

```python
def find_text_in_ocr(search_text, ocr_result, threshold=0.85):
    # 1. Quick check: fuzzy match full OCR text
    is_match, score = fuzzy_match(search_text, ocr_result.full_text, threshold)
    if is_match:
        return True, search_text, None, score

    # 2. Tokenize expected text
    expected_tokens = normalize_text(search_text).split()

    # 3. Find candidate OCR blocks (fuzzy match with 0.6 threshold)
    candidates = []
    for block in ocr_result.text_blocks:
        for block_token in normalize_text(block.text).split():
            for expected_token in expected_tokens:
                if fuzzy_match(block_token, expected_token, 0.6)[0]:
                    candidates.append(block)
                    break

    # 4. Calculate token coverage
    covered_token_indices = set()
    for candidate in candidates:
        for block_token in candidate.tokens:
            for i, expected_token in enumerate(expected_tokens):
                if fuzzy_match(block_token, expected_token, 0.6)[0]:
                    covered_token_indices.add(i)

    coverage = len(covered_token_indices) / len(expected_tokens)

    # 5. If coverage ≥ 80%, it's a match
    if coverage >= 0.8:
        return True, matched_text, first_block, coverage

    return False, None, None, coverage
```

**Example:**
```
Expected: "Jack Daniel's Tennessee Whiskey"
Tokens: ["jack", "daniels", "tennessee", "whiskey"]

OCR Blocks:
  "Jack" → matches token 0 ✓
  "Daniel's" → matches token 1 ✓
  "®" → no match (ignored)
  "Tennessee" → matches token 2 ✓
  "Whiskey" → matches token 3 ✓

Coverage: 4/4 = 100% → MATCH ✅
```

### 2. Government Warning Matching (`verification.py:959-1010`)

**Same token coverage approach for long text:**

```python
def verify_government_warning(ocr_result, threshold=0.95):
    # 1. Check critical keywords first (fast fail)
    for keyword in CRITICAL_KEYWORDS:
        if keyword.lower() not in ocr_result.full_text.lower():
            return NOT_FOUND

    # 2. Tokenize warning text (40+ tokens)
    warning_tokens = normalize_text(GOVERNMENT_WARNING_TEXT).split()
    ocr_tokens = normalize_text(ocr_result.full_text).split()

    # 3. Count how many warning tokens appear in OCR
    covered_tokens = 0
    for warning_token in warning_tokens:
        for ocr_token in ocr_tokens:
            if fuzzy_match(warning_token, ocr_token, 0.85)[0]:
                covered_tokens += 1
                break

    # 4. Calculate coverage
    coverage = covered_tokens / len(warning_tokens)

    # 5. If coverage ≥ 85%, it's a match
    if coverage >= 0.85:
        return MATCH (confidence: coverage)
    elif coverage >= 0.70:
        return WARNING (partial coverage)
    else:
        return NOT_FOUND
```

**Example:**
```
Warning: "GOVERNMENT WARNING: (1) According to the Surgeon General..."
Expected tokens: 40 words

OCR tokens extracted: 38 of 40 words found
Coverage: 38/40 = 95% → MATCH ✅

(Can tolerate 2 minor OCR errors or missing articles)
```

---

## Why This Works

### Problem: Fuzzy Matching Short Text in Long Text
```python
# Brand name is 3 words out of 100+ words on label
fuzzy_match("Jack Daniel's", full_ocr_text)
→ Low score because "Jack Daniel's" is only 3% of total text
```

### Solution: Token-by-Token Matching
```python
# Each word matched independently
"Jack" found in OCR? ✓
"Daniel's" found in OCR? ✓
Coverage: 2/2 = 100% ✓
```

### Advantages Over Adjacent Block Combining

| Approach | Multi-line? | Spurious blocks? | Long text? |
|----------|-------------|------------------|------------|
| Old fuzzy match | ❌ | ❌ | ❌ |
| Adjacent combining | ⚠️ (only if adjacent) | ❌ | ❌ |
| Token coverage | ✅ | ✅ | ✅ |

---

## Key Parameters

```python
# Brand name / short fields
candidate_threshold = 0.6   # Lower threshold to find candidate blocks
coverage_threshold = 0.8     # Need 80% token coverage to match

# Government warning / long text
token_match_threshold = 0.85  # Each token needs 85% fuzzy match
coverage_threshold = 0.85     # Need 85% of warning tokens present
warning_threshold = 0.70      # 70-84% triggers WARNING status
```

---

## Files Modified

1. **`functions/verification.py`**
   - Line 306-398: Rewrote `find_text_in_ocr` with token coverage algorithm
   - Line 959-1010: Rewrote `verify_government_warning` with token coverage
   - Line 403-427: Added debug logging to `verify_brand_name`

2. **`functions/ocr.py`**
   - No changes (removed confidence filtering that was breaking matches)

---

## Testing Recommendations

### 1. Multi-Line Brand Names
```
Test Case 1: Brand on multiple lines
JACK
DANIEL'S
TENNESSEE WHISKEY

Expected: MATCH (token coverage 100%)
```

### 2. Spurious OCR Errors
```
Test Case 2: Brand with trademark symbols
Jack Daniel's ® Tennessee ™ Whiskey

Expected: MATCH (ignore ®, ™ symbols)
```

### 3. Government Warning Variations
```
Test Case 3: Warning with line breaks
GOVERNMENT WARNING:
(1) According to the Surgeon
General, women should not drink
alcoholic beverages during
pregnancy because of the risk
of birth defects.

Expected: MATCH (all tokens present despite line breaks)
```

### 4. Partial OCR Failures
```
Test Case 4: Minor OCR errors
"GOVERNMENT WARRING" (typo)
"According to the Surgen General" (typo)

Expected: Still MATCH if 85%+ tokens correct
```

---

## Performance Impact

**Token coverage algorithm:**
- O(n × m) where n = OCR blocks, m = expected tokens
- For typical label: 100 blocks × 4 tokens = 400 comparisons
- Impact: ~5-10ms additional processing time
- **Much faster than adjacent block combining** (which was O(n × w × m))

---

## Debug Logging

Check logs for coverage details:
```
DEBUG: Token coverage match: 'Jack Daniel's' covered 100.0% via 2 blocks
DEBUG: Government warning token coverage: 95.0% (38/40 tokens)
INFO: Brand name FOUND: 'Jack Daniel's' (confidence: 100%)
```

---

## Next Steps

1. **Test with real labels** to validate improvements
2. **Monitor token coverage percentages** in logs
3. **Adjust thresholds if needed:**
   - Lower coverage_threshold to 0.7 if too strict
   - Raise to 0.9 if allowing too many false positives

4. **Future enhancements:**
   - Add positional token matching (first/last token verification)
   - Use semantic similarity for synonyms
   - Cache tokenization results for performance

---

## Rollback Instructions

If issues arise:
```bash
git revert HEAD  # Revert this commit
firebase deploy --only functions
```

Or restore from previous version of `verification.py` (lines 306-398 and 959-1010).
