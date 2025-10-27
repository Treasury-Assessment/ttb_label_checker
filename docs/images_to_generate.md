# Sample Label Images Requirements

This document specifies the sample alcohol beverage label images that need to be created for testing the TTB Label Verification System.

## Overview

We need 8-10 sample label images covering different product types and test scenarios. These images will be used for:
- Manual testing during development
- Automated test cases (future)
- User documentation examples
- OCR accuracy validation

## Directory Structure

```
docs/sample-labels/
├── bourbon-whiskey-4yr.jpg          # Spirits: Aged bourbon with age statement
├── bourbon-whiskey-2yr.jpg          # Spirits: Young bourbon (age required)
├── vodka-standard.jpg               # Spirits: Standard vodka
├── beer-ipa-standard.jpg            # Beer: Standard IPA
├── beer-non-alcoholic.jpg           # Beer: Non-alcoholic (<0.5% ABV)
├── wine-red-cabernet.jpg            # Wine: Red wine with vintage
├── wine-white-sulfites.jpg          # Wine: White wine with sulfite declaration
├── mismatch-wrong-abv.jpg           # Test: Intentional mismatch (wrong ABV)
├── mismatch-missing-warning.jpg     # Test: Missing government warning
├── poor-quality-glare.jpg           # Test: Poor OCR conditions (glare/blur)
└── metadata.json                    # Metadata for all labels
```

---

## Image Specifications

### General Requirements (All Labels)

**Technical Specifications:**
- **Format**: JPEG or PNG
- **Minimum Resolution**: 1200x900px (recommended), 800x600px (absolute minimum)
- **File Size**: 1-5MB per image (not compressed excessively)
- **Orientation**: Portrait or landscape, depending on label shape
- **Lighting**: Even, no harsh shadows or glare (except for poor-quality test)
- **Focus**: Sharp, clear text (except for poor-quality test)
- **Background**: Neutral (white, gray, or actual label photo on bottle)

**Label Content Requirements:**
- **Realistic appearance**: Should look like actual alcohol labels
- **TTB compliant format**: Follow 27 CFR regulations (except for intentional mismatch tests)
- **Government Warning**: MUST be clearly visible on all labels (except mismatch test)
- **All required fields visible**: Brand, class/type, ABV, net contents, etc.
- **Text legibility**: All text readable by human and OCR
- **No copyrighted content**: Use fictional brand names and labels

---

## Label Specifications by Type

### 1. bourbon-whiskey-4yr.jpg (Spirits - Aged Bourbon)

**Product Information:**
- **Brand Name**: "Heritage Oak"
- **Product Class**: "Bourbon Whiskey"
- **Alcohol Content**: "45% ALC/VOL" and "90 PROOF"
- **Net Contents**: "750 mL"
- **Age Statement**: "Aged 4 Years" (in approved format)
- **Bottler**: "Heritage Distillery, Bardstown, KY"
- **Country of Origin**: "Product of USA"

**Government Warning Text** (exact):
```
GOVERNMENT WARNING: (1) According to the Surgeon General, women
should not drink alcoholic beverages during pregnancy because of
the risk of birth defects. (2) Consumption of alcoholic beverages
impairs your ability to drive a car or operate machinery, and may
cause health problems.
```

**Visual Layout:**
- Main brand "Heritage Oak" prominently at top
- "Bourbon Whiskey" below brand name
- "45% ALC/VOL" and "90 PROOF" clearly visible
- "Aged 4 Years" in a distinct area
- Government warning at bottom (readable size)
- "750 mL" near bottom

**Purpose**: Test standard bourbon with optional age statement

---

### 2. bourbon-whiskey-2yr.jpg (Spirits - Young Bourbon)

**Product Information:**
- **Brand Name**: "Young Gun"
- **Product Class**: "Straight Bourbon Whiskey"
- **Alcohol Content**: "40% ALC/VOL" and "80 PROOF"
- **Net Contents**: "375 mL"
- **Age Statement**: "Aged 2 Years" (REQUIRED - whisky <4 years)
- **Bottler**: "New Era Distilling, Nashville, TN"
- **Country of Origin**: "Product of USA"

**Government Warning**: Same as above

**Visual Layout:**
- Bold brand name "Young Gun"
- "Straight Bourbon Whiskey" prominent
- "Aged 2 Years" clearly displayed (regulatory requirement)
- All other fields visible

**Purpose**: Test conditional age statement requirement (whisky < 4 years MUST have age)

---

### 3. vodka-standard.jpg (Spirits - Standard Vodka)

**Product Information:**
- **Brand Name**: "Crystal Peak"
- **Product Class**: "Vodka"
- **Alcohol Content**: "40% ALC/VOL" and "80 PROOF"
- **Net Contents**: "1 L"
- **Bottler**: "Premium Spirits Co., Portland, OR"
- **Country of Origin**: "Product of USA"
- **NO Age Statement** (not required for vodka)

**Government Warning**: Same as above

**Visual Layout:**
- Minimalist design typical of vodka
- Clear "Crystal Peak Vodka" branding
- ABV and proof clearly stated
- "1 Liter" or "1 L" visible

**Purpose**: Test spirits without age statement (not required)

---

### 4. beer-ipa-standard.jpg (Beer - Standard IPA)

**Product Information:**
- **Brand Name**: "Hop Valley"
- **Product Class**: "India Pale Ale" (or "IPA")
- **Alcohol Content**: "6.5% ALC/VOL" (optional for beer)
- **Net Contents**: "12 FL OZ" (355 mL)
- **Brewer**: "Hop Valley Brewing, Eugene, OR"
- **Style**: "West Coast IPA"
- **NO Standards of Fill Check** (beer has no standard sizes)

**Government Warning**: Same as above (required for all alcohol)

**Visual Layout:**
- Bold "Hop Valley" brand
- "India Pale Ale" or "IPA" subtitle
- "6.5% ALC/VOL" visible
- "12 FL OZ" near bottom
- Government warning text

**Purpose**: Test beer with standard fields, no age statement, any container size valid

---

### 5. beer-non-alcoholic.jpg (Beer - Non-Alcoholic)

**Product Information:**
- **Brand Name**: "Near Beer"
- **Product Class**: "Non-Alcoholic Malt Beverage"
- **Alcohol Content**: "LESS THAN 0.5% ALC/VOL" or "NON-ALCOHOLIC"
- **Net Contents**: "12 FL OZ" (355 mL)
- **Brewer**: "Health Brew Co., Boulder, CO"

**Government Warning**: May be smaller or abbreviated for <0.5% ABV products

**Visual Layout:**
- "Near Beer" brand prominent
- "NON-ALCOHOLIC" or "<0.5% ALC/VOL" very clear
- "Malt Beverage" visible

**Purpose**: Test non-alcoholic labeling (<0.5% ABV)

---

### 6. wine-red-cabernet.jpg (Wine - Red Wine with Vintage)

**Product Information:**
- **Brand Name**: "Valley View"
- **Product Class**: "Cabernet Sauvignon"
- **Alcohol Content**: "13.5% ALC/VOL"
- **Net Contents**: "750 mL"
- **Vintage Year**: "2020"
- **Appellation**: "Napa Valley" (optional)
- **Producer**: "Valley View Vineyards, Napa, CA"
- **Contains Sulfites**: "CONTAINS SULFITES" (required if ≥10 ppm)

**Government Warning**: Same as above

**Visual Layout:**
- "Valley View" brand at top
- "Cabernet Sauvignon" below brand
- "2020" vintage year prominent
- "13.5% ALC/VOL" visible
- "Contains Sulfites" near bottom
- "750 mL" displayed
- Government warning at bottom

**Purpose**: Test wine with vintage, sulfite declaration, standard size

---

### 7. wine-white-sulfites.jpg (Wine - White Wine with Sulfites)

**Product Information:**
- **Brand Name**: "Sunset Ridge"
- **Product Class**: "Chardonnay"
- **Alcohol Content**: "12.5% ALC/VOL"
- **Net Contents**: "750 mL"
- **Vintage Year**: "2021"
- **Producer**: "Sunset Ridge Winery, Sonoma, CA"
- **Contains Sulfites**: "CONTAINS SULFITES" (clearly visible)

**Government Warning**: Same as above

**Visual Layout:**
- "Sunset Ridge Chardonnay" prominent
- "2021" vintage
- "Contains Sulfites" declaration
- All standard fields visible

**Purpose**: Test sulfite declaration verification

---

### 8. mismatch-wrong-abv.jpg (Test - Intentional Mismatch)

**Product Information:**
- **Brand Name**: "Test Whiskey"
- **Product Class**: "Tennessee Whiskey"
- **Alcohol Content ON LABEL**: "40% ALC/VOL"
- **Net Contents**: "750 mL"
- **Bottler**: "Test Distillery, TN"

**Government Warning**: Present and correct

**Test Scenario:**
User will enter form data with ABV = 45%, but label shows 40%.
This should result in MISMATCH detection.

**Purpose**: Test mismatch detection when user-provided data doesn't match label

---

### 9. mismatch-missing-warning.jpg (Test - Missing Government Warning)

**Product Information:**
- **Brand Name**: "Warning Test"
- **Product Class**: "Vodka"
- **Alcohol Content**: "40% ALC/VOL"
- **Net Contents**: "750 mL"

**Government Warning**: INTENTIONALLY MISSING OR INCOMPLETE

**Test Scenario:**
Label is missing the required government warning statement.
Should fail verification with "GOVERNMENT WARNING NOT FOUND" error.

**Purpose**: Test critical government warning detection

---

### 10. poor-quality-glare.jpg (Test - Poor OCR Conditions)

**Product Information:**
- **Brand Name**: "Challenge Gin"
- **Product Class**: "Gin"
- **Alcohol Content**: "42% ALC/VOL"
- **Net Contents**: "750 mL"

**Government Warning**: Present but partially obscured

**Image Conditions:**
- **Glare/reflection** on part of label
- **Slight blur** or low focus
- **Angled perspective** (not perfectly straight-on)
- **Shadows** creating contrast issues

**Purpose**: Test OCR robustness and error handling with poor image quality

---

## Metadata File (metadata.json)

Create a `metadata.json` file with expected values for each label:

```json
{
  "labels": [
    {
      "filename": "bourbon-whiskey-4yr.jpg",
      "product_type": "spirits",
      "expected_values": {
        "brand_name": "Heritage Oak",
        "product_class": "Bourbon Whiskey",
        "alcohol_content": 45.0,
        "proof": 90,
        "net_contents": "750 mL",
        "age_statement": "Aged 4 Years",
        "bottler_name": "Heritage Distillery",
        "address": "Bardstown, KY",
        "country_of_origin": "USA",
        "is_imported": false,
        "has_government_warning": true
      },
      "test_type": "standard",
      "expected_result": "pass",
      "notes": "Standard bourbon with optional age statement (>4 years)"
    },
    {
      "filename": "bourbon-whiskey-2yr.jpg",
      "product_type": "spirits",
      "expected_values": {
        "brand_name": "Young Gun",
        "product_class": "Straight Bourbon Whiskey",
        "alcohol_content": 40.0,
        "proof": 80,
        "net_contents": "375 mL",
        "age_statement": "Aged 2 Years",
        "bottler_name": "New Era Distilling",
        "address": "Nashville, TN",
        "country_of_origin": "USA",
        "is_imported": false,
        "has_government_warning": true
      },
      "test_type": "conditional_requirement",
      "expected_result": "pass",
      "notes": "Age statement REQUIRED for whisky < 4 years (27 CFR 5.74)"
    },
    {
      "filename": "vodka-standard.jpg",
      "product_type": "spirits",
      "expected_values": {
        "brand_name": "Crystal Peak",
        "product_class": "Vodka",
        "alcohol_content": 40.0,
        "proof": 80,
        "net_contents": "1 L",
        "bottler_name": "Premium Spirits Co.",
        "address": "Portland, OR",
        "country_of_origin": "USA",
        "is_imported": false,
        "has_government_warning": true
      },
      "test_type": "standard",
      "expected_result": "pass",
      "notes": "No age statement (not required for vodka)"
    },
    {
      "filename": "beer-ipa-standard.jpg",
      "product_type": "beer",
      "expected_values": {
        "brand_name": "Hop Valley",
        "product_class": "India Pale Ale",
        "alcohol_content": 6.5,
        "net_contents": "12 FL OZ",
        "style": "West Coast IPA",
        "brewer": "Hop Valley Brewing",
        "address": "Eugene, OR",
        "has_government_warning": true
      },
      "test_type": "standard",
      "expected_result": "pass",
      "notes": "Beer has NO standards of fill - any container size valid (27 CFR 7.70)"
    },
    {
      "filename": "beer-non-alcoholic.jpg",
      "product_type": "beer",
      "expected_values": {
        "brand_name": "Near Beer",
        "product_class": "Non-Alcoholic Malt Beverage",
        "alcohol_content": 0.5,
        "net_contents": "12 FL OZ",
        "brewer": "Health Brew Co.",
        "address": "Boulder, CO"
      },
      "test_type": "special_case",
      "expected_result": "pass",
      "notes": "Non-alcoholic (<0.5% ABV) labeling requirements"
    },
    {
      "filename": "wine-red-cabernet.jpg",
      "product_type": "wine",
      "expected_values": {
        "brand_name": "Valley View",
        "product_class": "Cabernet Sauvignon",
        "alcohol_content": 13.5,
        "net_contents": "750 mL",
        "vintage_year": 2020,
        "appellation": "Napa Valley",
        "contains_sulfites": true,
        "producer": "Valley View Vineyards",
        "address": "Napa, CA",
        "has_government_warning": true
      },
      "test_type": "standard",
      "expected_result": "pass",
      "notes": "Wine with vintage, sulfite declaration, standard size (27 CFR 4.71)"
    },
    {
      "filename": "wine-white-sulfites.jpg",
      "product_type": "wine",
      "expected_values": {
        "brand_name": "Sunset Ridge",
        "product_class": "Chardonnay",
        "alcohol_content": 12.5,
        "net_contents": "750 mL",
        "vintage_year": 2021,
        "contains_sulfites": true,
        "producer": "Sunset Ridge Winery",
        "address": "Sonoma, CA",
        "has_government_warning": true
      },
      "test_type": "conditional_requirement",
      "expected_result": "pass",
      "notes": "Sulfite declaration required when contains_sulfites=true (27 CFR 5.63(c)(7))"
    },
    {
      "filename": "mismatch-wrong-abv.jpg",
      "product_type": "spirits",
      "form_data": {
        "brand_name": "Test Whiskey",
        "product_class": "Tennessee Whiskey",
        "alcohol_content": 45.0,
        "net_contents": "750 mL"
      },
      "label_shows": {
        "brand_name": "Test Whiskey",
        "product_class": "Tennessee Whiskey",
        "alcohol_content": 40.0,
        "net_contents": "750 mL"
      },
      "test_type": "mismatch",
      "expected_result": "fail",
      "expected_error": "ABV mismatch: Expected 45.0%, Found 40.0%",
      "notes": "Intentional mismatch to test detection logic"
    },
    {
      "filename": "mismatch-missing-warning.jpg",
      "product_type": "spirits",
      "expected_values": {
        "brand_name": "Warning Test",
        "product_class": "Vodka",
        "alcohol_content": 40.0,
        "net_contents": "750 mL",
        "has_government_warning": false
      },
      "test_type": "missing_critical_field",
      "expected_result": "fail",
      "expected_error": "Government warning not found or incomplete",
      "notes": "Critical field missing - should always fail verification"
    },
    {
      "filename": "poor-quality-glare.jpg",
      "product_type": "spirits",
      "expected_values": {
        "brand_name": "Challenge Gin",
        "product_class": "Gin",
        "alcohol_content": 42.0,
        "net_contents": "750 mL"
      },
      "test_type": "ocr_quality",
      "expected_result": "partial_success_or_fail",
      "notes": "Test OCR robustness with poor image conditions (glare, blur, angle)"
    }
  ]
}
```

---

## Image Creation Methods

### Recommended Approaches:

1. **AI Image Generation** (Easiest):
   - Use DALL-E, Midjourney, or Stable Diffusion
   - Prompt: "Product photograph of a [product type] bottle label, showing [brand name], [ABV], [net contents], and government warning text, professional photography, clear text, realistic"
   - May need multiple attempts to get clear, readable text

2. **Graphic Design Software** (Most Control):
   - Use Figma, Canva, Photoshop, or Illustrator
   - Create label designs from scratch
   - Export as high-resolution JPG/PNG
   - Ensures all text is perfectly readable

3. **Template Modification** (Fastest):
   - Find public domain/CC0 label templates
   - Modify text to match specifications above
   - Ensure no copyrighted brand names or logos

4. **Real Label Photography** (Most Realistic):
   - NOT RECOMMENDED due to copyright concerns
   - If used, must be public domain or permission obtained
   - OCR may still struggle with real-world conditions

### Critical Success Factors:

✅ **Text must be clear and readable** (by humans and OCR)
✅ **Government warning must be legible** (at least 6pt font equivalent)
✅ **All required fields present and visible**
✅ **Realistic label layouts** (match TTB-approved label styles)
✅ **High resolution** (1200x900px minimum recommended)
✅ **Good contrast** (dark text on light background or vice versa)

---

## Testing Checklist

Once images are created, verify:

- [ ] All 10 images created and saved in `docs/sample-labels/`
- [ ] metadata.json file created with all label specifications
- [ ] Each image is minimum 800x600px resolution
- [ ] All text is human-readable at 100% zoom
- [ ] Government warning text is complete and legible (except mismatch test)
- [ ] No copyrighted brand names or logos used
- [ ] File sizes are reasonable (1-5MB each)
- [ ] Images load correctly in web browser
- [ ] Manual OCR test with Google Cloud Vision API (optional verification)

---

## Usage in Testing

### Manual Testing Flow:

1. Upload image to application
2. Fill form with data from metadata.json
3. Click "Verify Label"
4. Compare results against expected_result in metadata.json
5. Document any discrepancies

### Automated Testing (Future):

```python
# Example pytest test case
def test_bourbon_4yr_standard():
    with open('docs/sample-labels/metadata.json') as f:
        metadata = json.load(f)

    label = metadata['labels'][0]  # bourbon-whiskey-4yr.jpg

    image_data = encode_image('docs/sample-labels/bourbon-whiskey-4yr.jpg')
    form_data = label['expected_values']

    result = verify_label(form_data, image_data)

    assert result.overall_match == True
    assert result.confidence_score > 0.85
```

---

## Maintenance

- **Update images** if TTB regulations change (27 CFR updates)
- **Add new test cases** as edge cases are discovered
- **Regenerate images** if OCR accuracy is consistently poor
- **Document findings** in test results (docs/test-results.md)

---

## References

- **27 CFR Part 5** - Distilled Spirits Labeling
- **27 CFR Part 4** - Wine Labeling
- **27 CFR Part 7** - Beer/Malt Beverage Labeling
- **27 CFR Part 16** - Health Warning Statement
- **TTB Label Examples**: https://www.ttb.gov/labeling/sample-labels

---

**Document Status**: Specification Complete - Awaiting Image Generation
**Created**: 2025-10-27
**Last Updated**: 2025-10-27
