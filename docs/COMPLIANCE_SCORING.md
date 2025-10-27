# TTB Label Compliance Scoring System

## Overview

The compliance scoring system provides a **numerical quality rating (0-100)** and **letter grade (A-F)** in addition to the binary pass/fail determination. This helps users understand the quality of their label compliance.

---

## Scoring Components

### 1. Pass/Fail Determination (`overall_match`)

**Binary result:** Label either PASSES (true) or FAILS (false) TTB requirements.

**Fails if ANY critical error exists:**
- Missing or mismatched brand name
- Missing or mismatched product class
- Missing or mismatched ABV
- Missing or incomplete government warning
- Required conditional fields missing (age statement, sulfites, country of origin)

### 2. Compliance Score (`compliance_score`)

**Numerical rating:** 0-100 points based on weighted field verification.

**Field Weights:**

| Field Category | Weight | Fields |
|----------------|--------|--------|
| **CRITICAL** | 40 pts each | brand_name, alcohol_content, product_class, government_warning |
| **IMPORTANT** | 20 pts each | net_contents, sulfites (if applicable) |
| **OPTIONAL** | 10 pts each | age_statement, proof, vintage, country_of_origin, appellation, style |

### 3. Compliance Grade (`compliance_grade`)

**Letter grade:** A, B, C, D, or F based on score percentage.

| Grade | Percentage | Meaning |
|-------|------------|---------|
| **A** | 90-100% | Excellent compliance - all or nearly all requirements met |
| **B** | 80-89% | Good compliance - minor issues or missing optional fields |
| **C** | 70-79% | Acceptable compliance - some issues but passes critical checks |
| **D** | 60-69% | Poor compliance - multiple issues, may fail soon |
| **F** | <60% | Failed compliance - critical requirements not met |

---

## Point Calculation Logic

### Status-Based Scoring

For each verified field, points are awarded based on verification status:

| Status | Points Awarded | Explanation |
|--------|---------------|-------------|
| **MATCH** | 100% | Field matches perfectly |
| **WARNING** | 80% | Field matches but has non-critical issue (e.g., non-standard size) |
| **MISMATCH** | 0% | Field value doesn't match expected |
| **NOT_FOUND** | 0% or 100% | 0% if required, 100% if marked "Not required" |
| **ERROR** | 0% | Critical validation error |

---

## Example Scenarios

### Scenario 1: Perfect Compliance

**Label Details:**
- Brand name: ✅ Match
- Product class: ✅ Match
- ABV: ✅ Match
- Government warning: ✅ Match
- Net contents: ✅ Match (750 mL - standard size)
- Age statement: ✅ Match (optional, provided)
- Proof: ✅ Match (optional, provided)

**Scoring:**
```
CRITICAL (4 fields × 40 pts):  160/160 pts
IMPORTANT (1 field × 20 pts):   20/20 pts
OPTIONAL (2 fields × 10 pts):   20/20 pts
────────────────────────────────────────
TOTAL:                         200/200 pts = 100%
```

**Result:**
- ✅ `overall_match: true` (PASS)
- 🎯 `compliance_score: 100`
- 📊 `compliance_grade: "A"`

---

### Scenario 2: Good Compliance with Minor Issue

**Label Details:**
- Brand name: ✅ Match
- Product class: ✅ Match
- ABV: ✅ Match
- Government warning: ✅ Match
- Net contents: ⚠️ Match but non-standard size (355 mL spirits - WARNING)
- Age statement: ❌ Not provided (optional, not required)
- Proof: ❌ Not provided (optional)

**Scoring:**
```
CRITICAL (4 fields × 40 pts):  160/160 pts (100%)
IMPORTANT (1 field × 20 pts):   16/20 pts  (80% - WARNING)
OPTIONAL (2 fields × 10 pts):    0/20 pts  (not provided)
────────────────────────────────────────
TOTAL:                         176/200 pts = 88%
```

**Result:**
- ✅ `overall_match: true` (PASS)
- 🎯 `compliance_score: 88`
- 📊 `compliance_grade: "B"`
- ⚠️ Warning: "Volume matches (355ml) but non-standard size for spirits"

---

### Scenario 3: Acceptable Compliance with Issues

**Label Details:**
- Brand name: ✅ Match
- Product class: ✅ Match
- ABV: ✅ Match
- Government warning: ✅ Match
- Net contents: ❌ Not found
- Age statement: ❌ Not found (was required for whisky < 4 years)
- Proof: ✅ Match

**Scoring:**
```
CRITICAL (4 fields × 40 pts):  160/160 pts (100%)
IMPORTANT (1 field × 20 pts):    0/20 pts  (not found)
OPTIONAL (2 fields × 10 pts):   10/20 pts  (1 match, 1 missing)
────────────────────────────────────────
TOTAL:                         170/200 pts = 85%
```

**Actually:** Since age statement was REQUIRED and not found, this would be an ERROR, so:

```
CRITICAL (4 fields × 40 pts):  160/160 pts
IMPORTANT (1 field × 20 pts):    0/20 pts
OPTIONAL (1 field × 10 pts):     0/10 pts  (age statement ERROR)
OPTIONAL (1 field × 10 pts):    10/10 pts  (proof match)
────────────────────────────────────────
TOTAL:                         170/200 pts = 85%
```

**Result:**
- ✅ `overall_match: true` (PASS - if age not truly required)
- 🎯 `compliance_score: 85`
- 📊 `compliance_grade: "B"`

---

### Scenario 4: Failed Compliance

**Label Details:**
- Brand name: ❌ Not found
- Product class: ✅ Match
- ABV: ❌ Mismatch (40% vs expected 45%)
- Government warning: ❌ Missing
- Net contents: ✅ Match

**Scoring:**
```
CRITICAL (4 fields × 40 pts):   80/160 pts (2 failures)
IMPORTANT (1 field × 20 pts):   20/20 pts
OPTIONAL (0 fields):             0/0 pts
────────────────────────────────────────
TOTAL:                         100/180 pts = 56%
```

**Result:**
- ❌ `overall_match: false` (FAIL)
- 🎯 `compliance_score: 56`
- 📊 `compliance_grade: "F"`
- ❌ Errors:
  - "Brand name 'Expected Brand' not found on label"
  - "ABV mismatch: Expected 45.0%, Found 40.0%"
  - "Government warning missing or incomplete (CRITICAL)"

---

## Special Cases

### Case 1: Optional Fields Marked "Not Required"

Fields with expected value "Not required", "Not provided", "Not applicable", or "Domestic product" receive **full points**.

**Example:**
```python
FieldResult(
    field_name="country_of_origin",
    status=VerificationStatus.MATCH,
    expected="Not required",
    found="Domestic product",
    confidence=1.0
)
```
**Points:** 10/10 (full credit)

### Case 2: Warnings vs Failures

**WARNING status** (e.g., non-standard bottle size) receives **80% of points** but doesn't cause overall failure.

**Example:**
```python
FieldResult(
    field_name="net_contents",
    status=VerificationStatus.WARNING,
    expected="355 mL",
    found="355 mL",
    confidence=0.95,
    message="Volume matches (355ml) but non-standard size for spirits"
)
```
**Points:** 16/20 (80% of 20 points)
**Overall Match:** Still TRUE (warnings don't fail)

### Case 3: Conditional Requirements

Fields that are conditionally required only count toward score when the condition applies.

**Example - Age Statement:**
- **Whisky ≥4 years:** Age statement optional → If not provided, receives full credit
- **Whisky <4 years:** Age statement required → If not found, receives 0 points and may FAIL

---

## API Response Format

### Complete Response Example

```json
{
  "status": "success",
  "overall_match": true,
  "confidence_score": 0.92,
  "compliance_score": 85,
  "compliance_grade": "B",
  "field_results": [
    {
      "field_name": "brand_name",
      "status": "match",
      "expected": "Heritage Oak",
      "found": "Heritage Oak",
      "confidence": 0.98,
      "location": { "x": 120, "y": 50, "width": 300, "height": 80 },
      "message": "Brand name matches (confidence: 98.0%)",
      "cfr_reference": "27 CFR 5.32, 4.33, 7.23"
    },
    {
      "field_name": "net_contents",
      "status": "warning",
      "expected": "355 mL",
      "found": "355 mL",
      "confidence": 0.92,
      "message": "Volume matches (355ml) but NON-STANDARD size for spirits. Standard sizes required per 27 CFR 5.47a.",
      "cfr_reference": "27 CFR 5.47a"
    }
  ],
  "ocr_full_text": "Heritage Oak Bourbon Whiskey...",
  "processing_time_ms": 2847.5,
  "warnings": [
    "Volume matches (355ml) but NON-STANDARD size for spirits. Standard sizes required per 27 CFR 5.47a."
  ],
  "errors": []
}
```

---

## Interpretation Guide

### For Users

**Grade A (90-100%):**
- ✅ Excellent compliance
- ✅ Label is ready for submission
- ✅ All critical requirements met
- ✅ Few or no issues

**Grade B (80-89%):**
- ✅ Good compliance
- ⚠️ Minor issues or warnings
- ✅ Likely acceptable for submission
- 📝 Review warnings

**Grade C (70-79%):**
- ⚠️ Acceptable but has issues
- 📝 Several fields missing or problematic
- 🔍 Review and fix issues before submission
- May need revisions

**Grade D (60-69%):**
- ⚠️ Poor compliance
- ❌ Multiple significant issues
- 🔍 Requires substantial revisions
- Not recommended for submission

**Grade F (<60%):**
- ❌ Failed compliance
- ❌ Critical requirements not met
- 🔍 Major revisions required
- Cannot be submitted as-is

---

## Technical Implementation

### Function: `calculate_compliance_score()`

**Location:** `functions/verification.py`

**Signature:**
```python
def calculate_compliance_score(field_results: List[FieldResult]) -> Tuple[int, int, float, str]:
    """
    Returns: (earned_score, max_score, percentage, grade)
    """
```

**Integration:**
```python
# In verify_label() function
earned_score, max_score, percentage, grade = calculate_compliance_score(field_results)

return VerificationResult(
    overall_match=overall_match,
    confidence_score=confidence_score,
    compliance_score=int(percentage),  # 0-100
    compliance_grade=grade,            # A-F
    field_results=field_results,
    ...
)
```

---

## Summary

The compliance scoring system provides three complementary metrics:

1. **overall_match (bool):** Binary pass/fail for TTB submission
2. **compliance_score (0-100):** Numerical quality rating
3. **compliance_grade (A-F):** Letter grade for easy interpretation

This allows users to:
- ✅ Quickly see if label passes TTB requirements (overall_match)
- 📊 Understand compliance quality (compliance_score)
- 📝 Identify areas for improvement (field_results + warnings)
- 🎯 Compare labels against a standard (compliance_grade)

**Key Principle:** A label can PASS (overall_match=true) but still have a grade below A if optional fields are missing or non-critical warnings exist. Conversely, a label with grade F has definitely FAILED critical requirements.

---

**Reference:** PRD Section 10.3 - Compliance Scoring
**Implementation:** `functions/verification.py` - `calculate_compliance_score()`

*Last Updated: 2025-10-27*
