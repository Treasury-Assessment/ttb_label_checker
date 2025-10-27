# Manual Testing Guide - TTB Label Verification System

> **Purpose:** Comprehensive manual testing procedures for validating the TTB Label Verification System against requirements defined in the PRD.

**Date Created:** 2024-10-27
**Testing Phase:** Phase 4 - Manual Testing with Sample Labels
**Prerequisites:** Backend and frontend implementations complete (Phase 2 & 3)

---

## Table of Contents

1. [Setup Instructions](#setup-instructions)
2. [Test Environment Configuration](#test-environment-configuration)
3. [Test Scenarios Overview](#test-scenarios-overview)
4. [Detailed Test Cases](#detailed-test-cases)
5. [Government Warning Verification Tests](#government-warning-verification-tests)
6. [Conditional Field Validation Tests](#conditional-field-validation-tests)
7. [Edge Case Tests](#edge-case-tests)
8. [Compliance Scoring Validation](#compliance-scoring-validation)
9. [Expected Results Reference](#expected-results-reference)
10. [Bug Reporting Template](#bug-reporting-template)

---

## Setup Instructions

### 1. Local Development Environment

**Backend Setup:**
```bash
# Navigate to functions directory
cd functions

# Activate virtual environment
source venv/bin/activate  # Unix/Mac
# OR
venv\Scripts\activate     # Windows

# Verify dependencies installed
uv pip list | grep google-cloud-vision
uv pip list | grep firebase-functions

# Set up environment variables
cp .env.example .env
# Edit .env with your Google Cloud credentials

# Start Firebase Functions emulator
firebase emulators:start --only functions
# Expected output: Functions emulator running on http://localhost:5001
```

**Frontend Setup:**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:5001/ttb-label-checker/us-central1

# Start development server
npm run dev
# Expected output: Next.js running on http://localhost:3000
```

### 2. Google Cloud Vision API Setup

**Option A: Service Account (Recommended for Testing)**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select project
3. Enable Vision API
4. Create service account with "Cloud Vision API User" role
5. Download JSON key file
6. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
   ```

**Option B: Application Default Credentials**
```bash
gcloud auth application-default login
```

### 3. Verify Setup

**Test Backend Health:**
```bash
curl -X POST http://localhost:5001/ttb-label-checker/us-central1/verify_label \
  -H "Content-Type: application/json" \
  -d '{"product_type": "spirits", "form_data": {"brand_name": "Test", "product_class": "Bourbon", "alcohol_content": 40}, "image": "data:image/png;base64,..."}'
```

**Expected:** JSON response with `status: "success"` or appropriate error

**Test Frontend:**
1. Open http://localhost:3000
2. Verify page loads without console errors
3. Check product type selector displays 3 options (spirits, wine, beer)
4. Verify form fields change when switching product types

---

## Test Environment Configuration

### Test Data Location
- Sample label images: `/docs/sample-labels/` (to be generated per `images_to_generate.md`)
- Test scenarios: This document
- Expected results: Section 9 below

### Browser Testing Matrix
Test on the following browsers (minimum):
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest, macOS only)
- ✅ Edge (latest)

### Screen Sizes
- Desktop: 1920x1080, 1366x768
- Tablet: 768x1024 (iPad)
- Mobile: 375x667 (iPhone SE), 390x844 (iPhone 12)

---

## Test Scenarios Overview

| Scenario | Product Type | Label Image | Expected Outcome | Priority |
|----------|--------------|-------------|------------------|----------|
| TC-001 | Spirits (Bourbon) | `bourbon_exact_match.png` | 100% match, Grade A, PASSED | HIGH |
| TC-002 | Spirits (Vodka) | `vodka_mismatch.png` | Mismatch on ABV, Grade C/D, FAILED | HIGH |
| TC-003 | Wine (Red) | `wine_exact_match.png` | 100% match, Grade A, PASSED | HIGH |
| TC-004 | Wine (White) | `wine_sulfites.png` | Match with sulfites, Grade A, PASSED | MEDIUM |
| TC-005 | Beer (IPA) | `beer_exact_match.png` | 100% match, Grade A, PASSED | HIGH |
| TC-006 | Beer (Lager) | `beer_no_abv.png` | Missing ABV (optional for beer), Grade B, WARNING | MEDIUM |
| TC-007 | Spirits (Bourbon) | `bourbon_poor_quality.png` | OCR errors, low confidence, Grade C/D | HIGH |
| TC-008 | Spirits | `bourbon_missing_warning.png` | Missing government warning, Grade F, FAILED | CRITICAL |
| TC-009 | Wine | `wine_wrong_vintage.png` | Vintage mismatch, Grade C, WARNING | MEDIUM |
| TC-010 | Spirits | `bourbon_age_4years.png` | Age statement required, verified | HIGH |

---

## Detailed Test Cases

### TC-001: Bourbon Exact Match (Happy Path)

**Objective:** Verify system correctly validates a compliant bourbon label with all required fields matching.

**Product Type:** Spirits

**Label Image:** `bourbon_exact_match.png`

**Form Data Input:**
```json
{
  "brand_name": "Eagle Rare",
  "product_class": "Straight Bourbon Whiskey",
  "alcohol_content": 45.0,
  "net_contents": "750 mL",
  "bottler_name": "Buffalo Trace Distillery",
  "address": "Frankfort, KY",
  "country_of_origin": "United States",
  "is_imported": false,
  "age_statement": "Aged 10 Years",
  "proof": 90
}
```

**Expected OCR Text (Extracted):**
- Brand: "EAGLE RARE"
- Class: "KENTUCKY STRAIGHT BOURBON WHISKEY"
- ABV: "45% ALC/VOL"
- Net Contents: "750 mL"
- Age: "AGED 10 YEARS"
- Warning: Full government warning text (27 CFR Part 16)

**Expected Results:**
```json
{
  "status": "success",
  "overall_match": true,
  "compliance_score": 100,
  "compliance_grade": "A",
  "confidence_score": 0.95,
  "field_results": [
    {
      "field_name": "brand_name",
      "status": "match",
      "expected": "Eagle Rare",
      "found": "EAGLE RARE",
      "confidence": 0.98,
      "message": "Brand name verified"
    },
    {
      "field_name": "alcohol_content",
      "status": "match",
      "expected": "45.0",
      "found": "45% ALC/VOL",
      "confidence": 0.97
    },
    // ... all other fields with "match" status
    {
      "field_name": "government_warning",
      "status": "match",
      "expected": "GOVERNMENT WARNING: (1) According to...",
      "found": "GOVERNMENT WARNING: (1) According to...",
      "confidence": 0.92,
      "cfr_reference": "27 CFR Part 16"
    }
  ],
  "warnings": [],
  "errors": [],
  "processing_time_ms": 1200
}
```

**UI Verification:**
1. ✅ Overall status shows "PASSED" with green badge
2. ✅ Compliance score displays "100/100"
3. ✅ Grade shows "A" in green
4. ✅ All field results show green checkmarks (✅)
5. ✅ Expanding each field shows "Expected" matches "Found"
6. ✅ Processing time displayed
7. ✅ "Verify Another Label" button appears

**Pass Criteria:**
- `overall_match === true`
- `compliance_score === 100`
- `compliance_grade === "A"`
- All field statuses are "match"
- No warnings or errors

---

### TC-002: Vodka ABV Mismatch

**Objective:** Verify system detects mismatch when label ABV differs from form data.

**Product Type:** Spirits

**Label Image:** `vodka_mismatch.png`

**Form Data Input:**
```json
{
  "brand_name": "Crystal Lake Vodka",
  "product_class": "Vodka",
  "alcohol_content": 40.0,  // INTENTIONAL MISMATCH
  "net_contents": "1 L",
  "is_imported": false
}
```

**Expected OCR Text:**
- Brand: "CRYSTAL LAKE VODKA"
- Class: "VODKA"
- ABV: "37.5% ALC/VOL"  // Mismatch with form (40.0)
- Net Contents: "1 L"
- Warning: Full government warning

**Expected Results:**
```json
{
  "status": "success",
  "overall_match": false,
  "compliance_score": 60,  // Lost 40 pts for ABV (critical field)
  "compliance_grade": "D",
  "field_results": [
    {
      "field_name": "brand_name",
      "status": "match"
    },
    {
      "field_name": "alcohol_content",
      "status": "mismatch",
      "expected": "40.0",
      "found": "37.5% ALC/VOL",
      "confidence": 0.96,
      "message": "Alcohol content does not match label (expected 40.0%, found 37.5%)",
      "cfr_reference": "27 CFR 5.37"
    },
    // ... other fields
  ],
  "errors": ["Alcohol content mismatch: Expected 40.0%, found 37.5%"],
  "warnings": []
}
```

**UI Verification:**
1. ✅ Overall status shows "FAILED" with red badge
2. ✅ Compliance score shows "60/100"
3. ✅ Grade shows "D" in orange
4. ✅ Alcohol content field shows red X (❌)
5. ✅ Error message displayed at top: "Alcohol content mismatch"
6. ✅ Expanding alcohol_content field shows expected vs found mismatch

**Pass Criteria:**
- `overall_match === false`
- `compliance_score` in range 50-70 (critical field penalty)
- `compliance_grade === "D"`
- alcohol_content field status is "mismatch"
- Error message mentions "alcohol content mismatch"

---

### TC-003: Wine Exact Match with Sulfites

**Objective:** Verify wine-specific fields including sulfite declaration.

**Product Type:** Wine

**Label Image:** `wine_sulfites.png`

**Form Data Input:**
```json
{
  "brand_name": "Napa Valley Reserve",
  "product_class": "Cabernet Sauvignon",
  "alcohol_content": 13.5,
  "net_contents": "750 mL",
  "vintage_year": 2019,
  "contains_sulfites": true,
  "appellation": "Napa Valley",
  "country_of_origin": "United States",
  "is_imported": false
}
```

**Expected OCR Text:**
- Brand: "NAPA VALLEY RESERVE"
- Class: "CABERNET SAUVIGNON"
- ABV: "13.5% ALC/VOL"
- Net Contents: "750 mL"
- Vintage: "2019"
- Sulfites: "CONTAINS SULFITES"
- Appellation: "NAPA VALLEY"
- Warning: Full government warning

**Expected Results:**
- `overall_match === true`
- `compliance_score === 100`
- `compliance_grade === "A"`
- Field `contains_sulfites` status: "match"
- Found text: "CONTAINS SULFITES"

**UI Verification:**
1. ✅ All wine-specific fields validated (vintage, sulfites, appellation)
2. ✅ Sulfite field shows match with "CONTAINS SULFITES" found
3. ✅ Grade A, PASSED

**Pass Criteria:**
- All wine fields verified
- Sulfite declaration matched (27 CFR 4.32(e))

---

### TC-004: Beer Without ABV (Optional Field)

**Objective:** Verify beer can pass without ABV (optional per PRD 3.4.2).

**Product Type:** Beer

**Label Image:** `beer_no_abv.png`

**Form Data Input:**
```json
{
  "brand_name": "Hazy Days IPA",
  "product_class": "India Pale Ale",
  "alcohol_content": null,  // Optional for beer
  "net_contents": "12 fl oz",
  "style": "New England IPA"
}
```

**Expected OCR Text:**
- Brand: "HAZY DAYS IPA"
- Class: "INDIA PALE ALE"
- Net Contents: "12 FL OZ"
- Warning: Full government warning
- (No ABV present on label)

**Expected Results:**
- `overall_match === true`
- `compliance_score >= 80` (B or higher)
- alcohol_content field status: "not_found" or "warning" (not "mismatch")
- No critical errors

**UI Verification:**
1. ✅ Overall PASSED (beer without ABV is valid)
2. ✅ Grade B or A
3. ✅ ABV field shows warning icon (⚠️) or "not required"

**Pass Criteria:**
- System recognizes ABV is optional for beer
- Does not fail for missing ABV
- Warning message may appear but not error

---

### TC-005: Poor Quality Image (OCR Challenges)

**Objective:** Verify system handles low-quality images with degraded OCR confidence.

**Product Type:** Spirits

**Label Image:** `bourbon_poor_quality.png` (blurry, low resolution, poor lighting)

**Form Data:** Same as TC-001 (Eagle Rare bourbon)

**Expected Behavior:**
- OCR extracts partial text with low confidence (<0.7)
- Some fields may be "not_found"
- Overall confidence_score < 0.7
- Compliance score reduced
- Possible warning messages about image quality

**Expected Results:**
```json
{
  "status": "success",
  "overall_match": false,
  "compliance_score": 40-60,  // Reduced due to not_found fields
  "compliance_grade": "D" or "F",
  "confidence_score": 0.55,  // Low confidence
  "field_results": [
    {
      "field_name": "brand_name",
      "status": "match",
      "confidence": 0.62  // Lower than usual
    },
    {
      "field_name": "age_statement",
      "status": "not_found",
      "expected": "Aged 10 Years",
      "found": null,
      "confidence": 0.0,
      "message": "Text not found on label (may be due to poor image quality)"
    }
    // ... some fields found, some not_found
  ],
  "warnings": ["Low OCR confidence (55%). Consider uploading higher quality image."],
  "errors": ["Required field 'age_statement' not found on label"]
}
```

**UI Verification:**
1. ✅ Warning message about low confidence
2. ✅ Some fields show 🔍 "not found" icon
3. ✅ Confidence percentage displayed and low
4. ✅ Suggestion to re-upload better quality image

**Pass Criteria:**
- System processes image without crashing
- Low confidence reflected in results
- User guidance provided for better results

---

### TC-006: Missing Government Warning (Critical Failure)

**Objective:** Verify system fails label missing required government warning.

**Product Type:** Spirits

**Label Image:** `bourbon_missing_warning.png` (intentionally no warning text)

**Form Data:** Same as TC-001

**Expected Results:**
- `overall_match === false`
- `compliance_score <= 60` (lost 40 pts for critical field)
- `compliance_grade === "F"`
- government_warning field status: "not_found" or "mismatch"
- CRITICAL error in errors array

**UI Verification:**
1. ✅ FAILED status in red
2. ✅ Grade F
3. ✅ Government warning field shows red X (❌) or 🔍
4. ✅ Critical error message: "Government warning not found" or similar
5. ✅ CFR reference displayed: "27 CFR Part 16"

**Pass Criteria:**
- System correctly identifies missing warning as critical failure
- Grade F due to missing critical field
- Clear error messaging

---

### TC-007: Age Statement Required (Conditional Field)

**Objective:** Verify system enforces age statement for whisky < 4 years.

**Product Type:** Spirits

**Label Image:** `bourbon_age_4years.png`

**Form Data:**
```json
{
  "brand_name": "Young Bourbon",
  "product_class": "Bourbon Whiskey",  // Note: "Bourbon" triggers age check
  "alcohol_content": 43.0,
  "net_contents": "750 mL",
  "age_statement": "Aged 3 Years"  // Less than 4 years
}
```

**Expected OCR Text:**
- Must include "AGED 3 YEARS" or equivalent

**Expected Results:**
- age_statement field status: "match"
- If age NOT on label: CRITICAL error (required for whisky < 4 years per 27 CFR 5.40)

**Test Variations:**
1. **Present and correct:** age_statement="Aged 3 Years" → match ✅
2. **Missing on label:** → error ❌
3. **Whisky ≥ 4 years:** age_statement optional → not_found OK ✅

**Pass Criteria:**
- System correctly enforces conditional requirement
- Age statement mandatory for whisky < 4 years
- Age statement optional for whisky ≥ 4 years or non-whisky

---

### TC-008: Imported Product (Country of Origin Required)

**Objective:** Verify country of origin required when is_imported=true.

**Product Type:** Spirits

**Label Image:** `scotch_imported.png`

**Form Data:**
```json
{
  "brand_name": "Highland Single Malt",
  "product_class": "Scotch Whisky",
  "alcohol_content": 40.0,
  "net_contents": "700 mL",
  "is_imported": true,
  "country_of_origin": "Scotland"  // REQUIRED when is_imported=true
}
```

**Expected OCR Text:**
- Must include "PRODUCT OF SCOTLAND" or "SCOTLAND" in address

**Expected Results:**
- country_of_origin field status: "match"
- Found text: "SCOTLAND" or "PRODUCT OF SCOTLAND"

**Test Variations:**
1. **is_imported=true, country present:** → match ✅
2. **is_imported=true, country missing:** → error ❌ (critical)
3. **is_imported=false, no country:** → not required ✅

**Pass Criteria:**
- Conditional logic correctly enforces country_of_origin for imports (27 CFR 5.36)

---

### TC-009: Non-Standard Net Contents (Warning)

**Objective:** Verify system warns on non-standard bottle sizes.

**Product Type:** Spirits

**Form Data:**
```json
{
  "brand_name": "Craft Spirits",
  "product_class": "Gin",
  "alcohol_content": 42.0,
  "net_contents": "725 mL"  // NOT a standard size
}
```

**Expected Results:**
- net_contents field status: "warning" (not "match", not "mismatch")
- Warning message: "Non-standard bottle size (725 mL). Standard sizes: 50ml, 100ml, 200ml, 375ml, 500ml, 750ml, 1L, 1.75L..."
- Compliance score reduced by 20% (important field with warning)
- Grade: B or C (not A, not F)

**Pass Criteria:**
- System recognizes non-standard size as warning (not error)
- Standards of fill reference: 27 CFR 5.47a

---

### TC-010: Proof Calculation Verification

**Objective:** Verify system correctly validates Proof = ABV × 2.

**Product Type:** Spirits

**Form Data:**
```json
{
  "brand_name": "Test Bourbon",
  "product_class": "Bourbon Whiskey",
  "alcohol_content": 50.0,
  "proof": 100  // Correct: 50 × 2 = 100
}
```

**Test Variations:**
1. **Correct proof (50% ABV, 100 proof):** → match ✅
2. **Incorrect proof (50% ABV, 95 proof):** → mismatch or warning ❌
3. **Missing proof (optional field):** → not_found (acceptable) ⚠️
4. **Proof tolerance (50% ABV, 99 proof):** → match if ±1 tolerance ✅

**Expected Results (Variation 2 - Incorrect):**
- proof field status: "mismatch" or "warning"
- Message: "Proof should be approximately 100 (ABV × 2), found 95"

**Pass Criteria:**
- System calculates and verifies proof correctly
- Tolerance of ±1 proof is acceptable (allows for rounding)

---

## Government Warning Verification Tests

### GW-001: Exact Text Match (Fuzzy 95%)

**Test Data:**
```
Expected: "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."

Label OCR: "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."
```

**Expected:** status="match", confidence > 0.95

---

### GW-002: Minor OCR Errors (Still Pass)

**Label OCR:**
```
"GOVERNMENT WARNlNG: (1) According to the Surgeon Genera1, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."

(Note: "WARNlNG" with lowercase L instead of I, "Genera1" with digit 1)
```

**Expected:** status="match" (95% fuzzy match allows minor OCR errors)

---

### GW-003: Wrong Case (Should Fail)

**Label OCR:**
```
"Government Warning: (1) According to the surgeon general, women should not drink..."
```

**Expected:** status="mismatch" or "warning"
**Reason:** "GOVERNMENT WARNING" must be ALL CAPS per 27 CFR Part 16.21(a)

---

### GW-004: Missing Keywords (Should Fail)

**Label OCR:**
```
"GOVERNMENT WARNING: (1) Women should avoid alcohol during pregnancy. (2) Don't drink and drive."
```

**Expected:** status="mismatch"
**Reason:** Missing required keywords:
- "Surgeon General"
- "birth defects"
- "impairs your ability"
- "operate machinery"

---

### GW-005: Completely Missing (Critical Fail)

**Label OCR:** (No warning text found)

**Expected:**
- status="not_found"
- compliance_score <= 60 (lost 40 pts)
- compliance_grade="F"
- Critical error message

---

## Conditional Field Validation Tests

### CV-001: Age Statement - Whisky < 4 Years

| Product Class | Age Statement (Form) | Label Has Age? | Expected Result |
|---------------|---------------------|----------------|-----------------|
| Bourbon Whiskey | "Aged 2 Years" | Yes, "2 YEARS" | Match ✅ |
| Bourbon Whiskey | "Aged 2 Years" | No | Critical Error ❌ |
| Bourbon Whiskey | None (≥4 years assumed) | Yes, "Aged 6 Years" | Match ✅ |
| Vodka | None | No | Not required ✅ |

---

### CV-002: Age Statement - Brandy < 2 Years

| Product Class | Age Statement (Form) | Label Has Age? | Expected Result |
|---------------|---------------------|----------------|-----------------|
| Brandy | "Aged 1 Year" | Yes, "1 YEAR" | Match ✅ |
| Brandy | "Aged 1 Year" | No | Critical Error ❌ |
| Brandy | None (≥2 years assumed) | Yes, "Aged 5 Years" | Match ✅ |

---

### CV-003: Sulfites - Wine Only

| Product Type | contains_sulfites | Label Has "CONTAINS SULFITES"? | Expected Result |
|--------------|-------------------|--------------------------------|-----------------|
| Wine | true | Yes | Match ✅ |
| Wine | true | No | Error ❌ (required if ≥10 ppm) |
| Wine | false | No | Not required ✅ |
| Beer | N/A | N/A | Field not applicable |
| Spirits | N/A | N/A | Field not applicable |

---

### CV-004: Country of Origin - Imported Products

| is_imported | country_of_origin (Form) | Label Has Country? | Expected Result |
|-------------|-------------------------|-------------------|-----------------|
| true | "Scotland" | Yes, "SCOTLAND" | Match ✅ |
| true | "Scotland" | No | Critical Error ❌ |
| false | None | No | Not required ✅ |
| false | "United States" | Yes | Optional info ✅ |

---

## Edge Case Tests

### EC-001: Empty/Null Fields

**Test:** Submit form with minimal required fields only
**Expected:** Optional fields should have status="not_found" (not "mismatch")

---

### EC-002: Special Characters in Brand Name

**Form Data:** `brand_name: "Jack Daniel's"`
**Label OCR:** `"JACK DANIEL'S"` or `"JACK DANIELS"`
**Expected:** Match (fuzzy matching handles apostrophes, case)

---

### EC-003: Multiple Unit Formats

**Form Data:** `net_contents: "750 mL"`
**Label OCR Variations:**
- "750ml" → Match ✅
- "750 ML" → Match ✅
- "25.4 fl oz" → Match ✅ (equivalent conversion)
- "0.75 L" → Match ✅

**Expected:** All variations should match (unit conversion logic)

---

### EC-004: Very Large Image (10MB)

**Test:** Upload 10MB image (max allowed size)
**Expected:**
- Upload succeeds
- OCR processes (may take longer)
- No timeout errors
- Processing time < 30 seconds

---

### EC-005: Unsupported Image Format

**Test:** Upload .gif or .bmp file
**Expected:**
- Client-side validation error
- Error message: "Unsupported format. Please use JPEG, PNG, or WebP."
- Upload rejected before API call

---

### EC-006: Image Too Small (< 100x100px)

**Test:** Upload 50x50px image
**Expected:**
- Validation error
- Message: "Image too small. Minimum dimensions: 100x100 pixels."

---

### EC-007: Base64 Encoding Edge Cases

**Test:** Ensure API correctly handles:
- Very long base64 strings (8-10MB images)
- Different base64 formats (with/without data URI prefix)

**Expected:** No encoding/decoding errors

---

### EC-008: Concurrent Requests

**Test:** Submit 5 verification requests simultaneously
**Expected:**
- All requests process successfully
- No race conditions
- Each returns correct results for its input
- Processing time remains reasonable

---

### EC-009: Network Timeout

**Test:** Simulate slow network (throttle to 3G speeds)
**Expected:**
- Request completes (may take 10-20 seconds)
- Loading indicator displays
- Timeout at 30 seconds with user-friendly error

---

### EC-010: Missing Environment Variables

**Test:** Start backend without GOOGLE_APPLICATION_CREDENTIALS
**Expected:**
- Function fails gracefully
- Error response: "OCR service not configured"
- No exposed stack traces to client

---

## Compliance Scoring Validation

### Scoring Test Matrix

| Scenario | Critical (40pts each) | Important (20pts each) | Optional (10pts each) | Total Score | Grade | Overall Match |
|----------|---------------------|----------------------|---------------------|-------------|-------|---------------|
| All Match | brand✅ abv✅ class✅ warning✅ | net_contents✅ | proof✅ age✅ | 100 | A | true |
| Missing Optional | brand✅ abv✅ class✅ warning✅ | net_contents✅ | proof❌ age❌ | 80 | B | true |
| Missing Important | brand✅ abv✅ class✅ warning✅ | net_contents❌ | proof✅ age✅ | 80 | B | true |
| Missing 1 Critical | brand✅ abv✅ class✅ warning❌ | net_contents✅ sulfites✅ | age✅ | 60 | D | false |
| Missing 2 Critical | brand❌ abv✅ class✅ warning❌ | net_contents✅ | proof✅ | 20 | F | false |
| ABV Mismatch | brand✅ abv❌ class✅ warning✅ | net_contents✅ | proof✅ | 60 | D | false |
| Warning Only | brand✅ abv✅ class✅ warning✅ | net_contents⚠️ | proof✅ | 96 | A | true |

**Note:**
- ✅ MATCH = 100% of points
- ⚠️ WARNING = 80% of points (e.g., non-standard size)
- ❌ MISMATCH/NOT_FOUND = 0% of points (unless marked "Not required")

---

### Score Calculation Examples

**Example 1: Bourbon with All Required Fields**
```
Critical Fields (40 pts each):
  - brand_name: MATCH → 40 pts
  - alcohol_content: MATCH → 40 pts
  - product_class: MATCH → 40 pts
  - government_warning: MATCH → 40 pts

Important Fields (20 pts each):
  - net_contents: MATCH → 20 pts

Optional Fields (10 pts each):
  - age_statement: MATCH → 10 pts
  - proof: NOT FOUND (optional) → 0 pts

Total: 40+40+40+40+20+10 = 190 pts earned
Max Possible: 40+40+40+40+20+10+10 = 200 pts
Percentage: 190/200 = 95%
Grade: A
Overall Match: true
```

**Example 2: Vodka Missing Net Contents**
```
Critical: brand(40) + abv(40) + class(40) + warning(40) = 160
Important: net_contents NOT FOUND → 0
Optional: proof NOT FOUND → 0

Total: 160 pts earned
Max: 180 pts (no optional fields for vodka)
Percentage: 160/180 = 88.9%
Grade: B
Overall Match: true (important field can be missing for B)
```

**Example 3: Wine Missing Sulfites (Required if ≥10ppm)**
```
If contains_sulfites=true but NOT FOUND on label:
  - sulfites: Important field → 0 pts

Critical: 160 pts
Important: sulfites(0) → 0
Optional: vintage(10) + appellation(10) = 20

Total: 180/200 = 90%
Grade: A (but warning message issued)
Overall Match: true
```

---

## Expected Results Reference

### Status Values

| Status | Icon | Meaning | Points Awarded |
|--------|------|---------|----------------|
| match | ✅ | Found and correct | 100% |
| mismatch | ❌ | Found but incorrect | 0% |
| not_found | 🔍 | Not on label | 0% (or N/A if optional) |
| warning | ⚠️ | Found with issue | 80% |
| error | 💥 | Processing error | 0% |

### Grade Scale

| Grade | Score Range | Color | Meaning |
|-------|-------------|-------|---------|
| A | 90-100% | Green | Excellent compliance |
| B | 80-89% | Blue | Good compliance (minor issues) |
| C | 70-79% | Yellow | Acceptable (some warnings) |
| D | 60-69% | Orange | Poor (critical issues) |
| F | <60% | Red | Failed (major violations) |

### overall_match Logic

```python
overall_match = (compliance_score >= 60) AND (no critical field mismatches)
```

- Grade A/B/C → overall_match can be true
- Grade D → overall_match likely false (unless only warnings)
- Grade F → overall_match always false

---

## Bug Reporting Template

When you find a bug, please document using this template:

```markdown
### BUG-XXX: [Short Title]

**Severity:** Critical / High / Medium / Low

**Test Case:** TC-XXX or scenario description

**Steps to Reproduce:**
1. Navigate to...
2. Select product type...
3. Upload image...
4. Fill form with...
5. Click verify...

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Screenshots/Logs:**
[Attach images or error logs]

**Environment:**
- Browser: Chrome 120.0.6099.109
- OS: macOS 14.2
- Backend: Firebase Functions Emulator
- Frontend: Next.js dev server

**Additional Context:**
[Any other relevant information]
```

---

## Testing Checklist

Use this checklist to track testing progress:

### Phase 4.1: Manual Testing with Sample Labels
- [ ] TC-001: Bourbon exact match ✅
- [ ] TC-002: Vodka ABV mismatch ❌
- [ ] TC-003: Wine with sulfites ✅
- [ ] TC-004: Beer without ABV ⚠️
- [ ] TC-005: Poor quality image 🔍
- [ ] TC-006: Missing government warning ❌
- [ ] TC-007: Age statement conditional ✅
- [ ] TC-008: Imported product ✅
- [ ] TC-009: Non-standard net contents ⚠️
- [ ] TC-010: Proof calculation ✅

### Phase 4.2: Government Warning Tests
- [ ] GW-001: Exact text match ✅
- [ ] GW-002: Minor OCR errors ✅
- [ ] GW-003: Wrong case ❌
- [ ] GW-004: Missing keywords ❌
- [ ] GW-005: Completely missing ❌

### Phase 4.3: Conditional Field Tests
- [ ] CV-001: Whisky age statement
- [ ] CV-002: Brandy age statement
- [ ] CV-003: Wine sulfites
- [ ] CV-004: Country of origin

### Phase 4.4: Edge Case Tests
- [ ] EC-001: Empty/null fields
- [ ] EC-002: Special characters
- [ ] EC-003: Unit conversions
- [ ] EC-004: Large images (10MB)
- [ ] EC-005: Unsupported formats
- [ ] EC-006: Small images
- [ ] EC-007: Base64 encoding
- [ ] EC-008: Concurrent requests
- [ ] EC-009: Network timeout
- [ ] EC-010: Missing env vars

### Phase 4.5: Compliance Scoring
- [ ] All scenarios from scoring matrix tested
- [ ] Score calculations verified
- [ ] Grade assignments correct
- [ ] Overall match logic correct

### Phase 4.6: Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Phase 4.7: Responsive Testing
- [ ] Desktop (1920x1080)
- [ ] Desktop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)
- [ ] Mobile (390x844)

---

## Next Steps After Manual Testing

Once manual testing is complete:

1. **Document Results:**
   - Fill out testing checklist
   - Record any bugs using bug template
   - Note performance metrics (processing times)

2. **Proceed to Automated Tests:**
   - Phase 4.5: Backend unit tests (pytest)
   - Phase 4.6: Frontend unit tests (Jest)

3. **Address Bugs:**
   - Fix critical bugs before deployment
   - Document known issues for release notes

4. **Performance Optimization:**
   - If processing times > 5 seconds, investigate
   - Optimize OCR confidence thresholds if needed

---

**Last Updated:** 2024-10-27
**Document Version:** 1.0
**Status:** Ready for Testing
