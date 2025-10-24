# Product Requirements Document: TTB Label Verification System

## Executive Summary

The TTB Label Verification System is an AI-powered web application that automates the verification process for alcohol beverage labels against submitted form data. The system simulates the Alcohol and Tobacco Tax and Trade Bureau (TTB) label approval workflow by comparing label images with application form information to ensure compliance with federal regulations.

**Target Deployment:** Firebase (Hosting, Functions, Storage)
**Frontend Stack:** TypeScript, React/Next.js
**Backend Stack:** Python (Firebase Cloud Functions), uv for environment management
**Timeline:** MVP in 1 day, Full feature set in 2-3 days

---

## 1. Product Overview

### 1.1 Purpose
Create a web application that accepts alcohol label images and product information forms, then uses AI/OCR to verify if the label content matches the submitted data—simulating a TTB compliance review.

### 1.2 Core Value Proposition
- **For TTB Agents/Producers:** Automated pre-check of label compliance before official submission
- **For Users:** Immediate feedback on label discrepancies with detailed explanations
- **For Quality Assurance:** Systematic verification of all required label elements

### 1.3 Success Metrics
- Label text extraction accuracy > 90%
- Match/mismatch detection accuracy > 95%
- End-to-end verification time < 5 seconds
- User comprehension of results > 95% (clear messaging)

---

## 2. User Stories & Use Cases

### 2.1 Primary User Stories

**US-1: Basic Label Verification**
- As a producer, I want to upload my label image and form data so I can verify they match before submission
- Acceptance: System returns match/mismatch result with specific field comparisons

**US-2: Detailed Discrepancy Reporting**
- As a user, I want to see exactly which fields don't match so I can correct specific issues
- Acceptance: Results show field-by-field comparison with visual indicators

**US-3: Multiple Product Type Support**
- As a producer, I want to verify different beverage types (spirits, wine, beer) with type-specific requirements
- Acceptance: Form adapts to product type with relevant fields and compliance checks

**US-4: Image Quality Feedback**
- As a user, I want to know if my image quality is insufficient so I can resubmit a better image
- Acceptance: System detects poor OCR results and prompts for clearer image

**US-5: Visual Label Highlighting**
- As a user, I want to see where on the label each piece of information was found so I can verify the detection
- Acceptance: Results display annotated image with highlighted text regions

### 2.2 Use Case Flow

```
1. User selects product type (Beer/Wine/Spirits)
2. User fills out type-specific form fields
3. User uploads label image (drag-drop or file picker)
4. System validates inputs and image format
5. Backend processes image with OCR
6. Backend compares extracted text with form data
7. System generates detailed compliance report
8. User views results with visual highlighting
9. User can modify form/image and re-verify
```

---

## 3. Functional Requirements

### 3.1 Form Input Module (Frontend - TypeScript/React)

#### 3.1.1 Core Fields (MVP - All Products)
| Field | Type | Validation | Example |
|-------|------|------------|---------|
| Brand Name | Text | Required, 2-100 chars | "Old Tom Distillery" |
| Product Class/Type | Select/Text | Required | "Kentucky Straight Bourbon Whiskey" |
| Alcohol Content (ABV) | Number | Required, 0-100% | "45" or "45%" |
| Net Contents | Select | Optional (MVP), Required for full compliance | "750 mL", "12 fl oz" |
| Bottler/Importer Name | Text | Optional (bonus feature) | "Old Tom Distillery" |
| Address (City, State) | Text | Optional (bonus feature) | "Louisville, KY" |
| Country of Origin | Select | Conditional (required if imported) | "Scotland", "Mexico" |

#### 3.1.2 Product Type Specific Fields
**Distilled Spirits:**
- Class/Type designation (Bourbon, Vodka, Rum, etc.)
- Proof (auto-calculated from ABV, optional display on label)
- Age statement (conditional based on product and age duration)
  - **Mandatory if:** Whisky aged < 4 years
  - **Mandatory if:** Grape brandy aged < 2 years
  - Format must match TTB-approved formats (see verification logic)
- State of Distillation (conditional - if not in bottler address)
- Commodity Statement (if neutral spirits used in blending)

**Wine:**
- Varietal/Type (Cabernet, Chardonnay, Table Wine)
- Vintage year (optional)
- **Sulfite Declaration:** Checkbox "Contains Sulfites (≥10 ppm)"
  - If checked, must verify "Contains Sulfites" on label
  - Required by law if sulfur dioxide ≥10 ppm
- Appellation (optional)

**Beer:**
- Style (IPA, Lager, Stout, etc.)
- Ingredients list (optional for MVP)
- May use "Malt Beverage" instead of "Beer"

#### 3.1.3 Additional Optional Fields (Bonus Features)
- Health warning statement verification toggle (always checked by default)
- Lot/batch number
- Formula number (for products requiring TTB formula approval)
- Coloring materials disclosure

#### 3.1.4 Form Behavior
- Dynamic field visibility based on product type selection
- Real-time validation with inline error messages
- Auto-save to browser localStorage (prevent data loss)
- Clear/reset functionality
- Form state persistence across page refreshes

### 3.2 Image Upload Module (Frontend - TypeScript)

#### 3.2.1 Upload Mechanisms
- **Drag-and-Drop Zone:** Primary interface, visual feedback on hover
- **File Picker:** Fallback click-to-browse functionality
- **Paste from Clipboard:** Bonus feature for screenshots

#### 3.2.2 Image Requirements
- **Supported Formats:** JPEG, PNG, WebP, HEIC (auto-convert)
- **File Size Limit:** 10 MB max
- **Resolution:** Minimum 800x600px recommended
- **Aspect Ratio:** Any (system handles orientation)

#### 3.2.3 Image Preprocessing (Client-Side)
- Client-side compression if > 5MB
- Orientation correction (EXIF data)
- Preview with zoom/pan capability
- Remove EXIF metadata before upload (privacy)

#### 3.2.4 Validation & Error Handling
- File type validation with clear error messages
- File size check before upload
- Image dimension check (warn if too small)
- Duplicate detection (same image hash)

### 3.3 Backend OCR & Processing Module (Python/Firebase Functions)

#### 3.3.1 OCR Technology Stack
**Primary:** Google Cloud Vision API
- Reasons: High accuracy, text location coordinates, Firebase integration
- Fallback: Tesseract OCR (pytesseract) via local processing

**Environment Setup (uv):**
```bash
uv venv
uv pip install google-cloud-vision pillow firebase-admin
```

#### 3.3.2 Text Extraction Pipeline
```python
1. Receive image from Firebase Storage
2. Preprocess image (resize, contrast adjustment, grayscale)
3. Execute OCR via Cloud Vision API
4. Extract text blocks with bounding box coordinates
5. Normalize extracted text (lowercase, remove punctuation)
6. Structure data for comparison
```

#### 3.3.3 Text Normalization Rules
- Case-insensitive comparison (convert to lowercase)
- Punctuation stripping (except decimal points for ABV)
- Common OCR error correction:
  - "0" (zero) vs "O" (letter)
  - "1" (one) vs "l" (lowercase L) vs "I" (uppercase i)
  - "5" vs "S"
- Whitespace normalization (multiple spaces to single)
- Unit standardization ("ml" = "mL" = "milliliter")

### 3.4 Verification & Matching Logic (Python Backend)

#### 3.4.1 Field-by-Field Comparison Rules

**Brand Name:**
- Exact match (after normalization)
- Fuzzy match threshold: 85% similarity (Levenshtein distance)
- Must appear on label

**Product Class/Type:**
- Keyword matching (e.g., "bourbon" must appear for Bourbon Whiskey)
- Synonyms allowed (e.g., "IPA" = "India Pale Ale")
- Not found = fail

**Alcohol Content:**
- Number extraction with regex: `(\d+\.?\d*)\s*%`
- Match tolerance: ±0.5% (account for rounding)
- Must include "%" or "alcohol" nearby

**Net Contents:**
- Volume extraction: `(\d+\.?\d*)\s*(ml|mL|oz|fl oz)`
- Exact match required
- Unit conversion support (750ml = 25.36 fl oz)
- **Standards of Fill Validation:**
  - Compare against TTB-approved standard container sizes
  - Approved metric sizes: 50ml, 100ml, 200ml, 375ml, 500ml, 750ml, 1L, 1.75L
  - Warn if non-standard size detected (not automatically fail)
  - Reference: 27 CFR 5.203

**Government Warning (Compliance Check - Exact Text Required):**
- **Required exact text (with minor OCR tolerance):**
  ```
  GOVERNMENT WARNING: (1) According to the Surgeon General, women should not
  drink alcoholic beverages during pregnancy because of the risk of birth defects.
  (2) Consumption of alcoholic beverages impairs your ability to drive a car or
  operate machinery, and may cause health problems.
  ```
- **Verification Algorithm:**
  1. Extract suspected warning section from OCR text
  2. Normalize whitespace (multiple spaces → single space)
  3. Fuzzy string match with 95% similarity threshold (allows minor OCR errors)
  4. **Critical checks (must pass):**
     - "GOVERNMENT WARNING" in ALL CAPS (not "Government Warning")
     - "Surgeon General" with capital S and G (not "surgeon general")
     - Contains "pregnancy" and "birth defects"
     - Contains "impair" or "impairs"
     - Contains "operate machinery" or "drive a car"
  5. If fuzzy match < 95%, provide detailed failure reason
- **Reference:** 27 CFR Part 16
- **Note:** Cannot verify bold formatting via OCR (documented limitation)

#### 3.4.2 Matching Algorithm
```python
def verify_label(form_data: dict, ocr_text: str, ocr_blocks: list) -> dict:
    results = {
        "overall_match": True,
        "field_results": [],
        "confidence_score": 0.0
    }

    for field in form_data:
        field_result = {
            "field_name": field.name,
            "status": "match" | "mismatch" | "not_found",
            "expected": field.value,
            "found": extracted_value,
            "confidence": 0.0-1.0,
            "location": {"x": 0, "y": 0, "width": 0, "height": 0}
        }
        results["field_results"].append(field_result)

    return results
```

#### 3.4.3 Compliance Rule Engine (Product-Type Specific)

**Distilled Spirits Rules:**

1. **Age Statement (Conditional Requirement):**
   - **Mandatory if:**
     - Product class contains "whisky" OR "whiskey" AND age < 4 years
     - Product class contains "brandy" AND made from grape lees/pomace/marc AND age < 2 years
     - Label contains any age reference (e.g., "3 Year", "Aged 18 Months")
     - Label contains distillation date
   - **Approved formats (27 CFR 5.74):**
     - "X years old"
     - "X months old"
     - "Aged X years"
     - "Aged at least X years"
     - "Aged a minimum of X months"
     - "Over X years old"
     - "Aged not less than X years"
     - "X% whisky aged Y years; Z% whisky aged W years" (blended)
   - **Validation:**
     - Extract age value and format from label
     - If mandatory conditions met but statement missing → FAIL
     - If format doesn't match approved list → FAIL
     - If math doesn't match (e.g., "3 Year Old" but form says 5 years) → FAIL

2. **Proof Statement (Optional but Regulated if Present):**
   - If proof appears on label, verify:
     - Proof = ABV × 2 (allow ±1 for rounding)
     - Must be distinguished from ABV statement (e.g., in parentheses or separate line)
     - Example valid formats: "90 Proof", "(90 Proof)", "45% Alc./Vol. (90 Proof)"
   - If proof calculation incorrect → WARNING (not automatic fail)
   - Reference: 27 CFR 5.65

3. **Class Designation:**
   - Must match TTB-approved class/type for distilled spirits
   - Common types: Vodka, Gin, Rum, Tequila, Whisky/Whiskey (Bourbon, Rye, etc.), Brandy, Liqueur
   - Check for spelling consistency
   - Reference: 27 CFR 5.165

4. **State of Distillation (Conditional):**
   - Required for certain whisky types if state ≠ address state
   - Example: "Distilled in Idaho" or "Idaho Corn Whisky"
   - Reference: 27 CFR 5.66(f)

5. **Commodity Statement (Conditional):**
   - If neutral spirits used in blending, must state percentage and source grain
   - Example: "50% Neutral Spirits Distilled From Corn"
   - Reference: 27 CFR 5.71

**Wine Rules:**

1. **Vintage Year:**
   - If vintage year specified in form, must appear on label
   - Must be ≥95% from that year (not verified by OCR, assumes form is truthful)

2. **Sulfite Declaration:**
   - If form checkbox "Contains Sulfites (≥10 ppm)" is checked:
     - Label MUST contain "Contains Sulfites" or "Contains Sulfur Dioxide"
     - If missing → FAIL
   - If checkbox NOT checked but statement found on label → WARNING (potential mismatch)
   - Reference: 27 CFR 5.63(c)(7)

3. **Alcohol Content:**
   - May be omitted for "Table Wine" (7-14% ABV range)
   - If "Table Wine" and ABV shown, verify 7-14% range

4. **Appellation:**
   - Optional verification (bonus feature)

**Beer Rules:**

1. **Class Designation:**
   - "Malt Beverage" is acceptable synonym for "Beer"
   - Style (IPA, Lager, etc.) is informational, not regulatory requirement

2. **ABV:**
   - Often optional for beer
   - If present on label, must match form
   - If < 0.5%, may be labeled "non-alcoholic"

3. **Ingredients:**
   - Optional for MVP (allergens would be regulatory, but not in scope)

### 3.5 Results Display Module (Frontend - TypeScript/React)

#### 3.5.1 Results Page Layout
```
┌─────────────────────────────────────────────┐
│  Overall Status Badge                       │
│  ✅ PASSED / ❌ FAILED                       │
│  Confidence Score: 87%                      │
├─────────────────────────────────────────────┤
│  Field-by-Field Results                     │
│  ┌────────────────────────────────-─────┐   │
│  │ ✅ Brand Name: Match                 │   │
│  │    Expected: "Old Tom Distillery"    │   │
│  │    Found: "OLD TOM DISTILLERY"       │   │
│  │    Confidence: 98%                   │   │
│  └─────────────────────────────────-────┘   │
│  ┌──────────────────────────────────-───┐   │
│  │ ❌ Alcohol Content: Mismatch         │   │
│  │    Expected: "45%"                   │   │
│  │    Found: "40%"                      │   │
│  │    Confidence: 95%                   │   │
│  └───────────────────────────────────-──┘   │
├─────────────────────────────────────────────┤
│  Annotated Label Image                      │
│  [Image with highlighted regions]           │
└─────────────────────────────────────────────┘
```

#### 3.5.2 Visual Design Elements
- **Color Coding:**
  - Green (#10B981): Match
  - Red (#EF4444): Mismatch
  - Yellow (#F59E0B): Warning/Low Confidence
  - Gray (#6B7280): Not Found
- **Icons:**
  - ✅ Check mark: Match
  - ❌ X mark: Mismatch
  - ⚠️ Warning triangle: Low confidence
  - 🔍 Magnifying glass: Not found
- **Typography:**
  - Field names: Bold, 16px
  - Expected/Found values: Monospace font, 14px
  - Confidence scores: Italic, 12px

#### 3.5.3 Interactive Features
- **Highlight Toggles:** Click field result to highlight/unhighlight on image
- **Image Zoom:** Pinch/scroll to zoom into label details
- **Copy to Clipboard:** Copy discrepancy report
- **Export Options:** Download PDF report (bonus)
- **Re-verification Button:** Modify form and re-check without re-upload

#### 3.5.4 Error State Handling
- **Poor Image Quality:**
  ```
  ⚠️ Image Quality Issue
  Could not extract text reliably from this image.
  Suggestions:
  - Ensure good lighting
  - Avoid glare/reflections
  - Use higher resolution image
  - Try a different angle
  ```

- **No Text Detected:**
  ```
  ❌ No Text Found
  The OCR system could not detect any text on this image.
  Please verify:
  - Image contains actual label (not blank)
  - Text is clearly visible
  - Image is not corrupted
  ```

- **Partial Match:**
  ```
  ⚠️ Partial Match (3/5 fields matched)
  Some required information could not be verified.
  Review the discrepancies below and update your label or form.
  ```

### 3.6 Image Highlighting Feature (Bonus - High Priority)

#### 3.6.1 Technical Implementation
**Approach:** Canvas API overlay with bounding boxes from OCR

**Data Structure:**
```typescript
interface TextBoundingBox {
  text: string;
  vertices: { x: number; y: number }[];
  confidence: number;
  field_match: string | null; // "brand_name", "abv", etc.
}
```

**Rendering Logic:**
```typescript
function renderHighlights(canvas: HTMLCanvasElement, boxes: TextBoundingBox[]) {
  const ctx = canvas.getContext('2d');
  boxes.forEach(box => {
    ctx.strokeStyle = getColorForMatch(box.field_match);
    ctx.lineWidth = 3;
    ctx.strokeRect(
      box.vertices[0].x,
      box.vertices[0].y,
      box.vertices[2].x - box.vertices[0].x,
      box.vertices[2].y - box.vertices[0].y
    );
    ctx.fillStyle = 'rgba(0,0,0,0.7)';
    ctx.fillText(box.field_match, box.vertices[0].x, box.vertices[0].y - 5);
  });
}
```

#### 3.6.2 User Interaction
- Hover over field result → corresponding region highlights on image
- Click field result → zoom to region on image
- Toggle all highlights on/off
- Color-coded boxes matching field status (green/red/yellow)

---

## 4. Non-Functional Requirements

### 4.1 Performance
- **Page Load Time:** < 2 seconds (LCP)
- **Image Upload:** < 1 second for 5MB image
- **OCR Processing:** < 3 seconds for typical label
- **Total Verification Time:** < 5 seconds end-to-end
- **Concurrent Users:** Support 100 simultaneous verifications (Firebase scaling)

### 4.2 Security
- **Input Validation:** Sanitize all form inputs
- **File Validation:** Strict MIME type checking
- **HTTPS Only:** Enforce SSL for all traffic
- **No PII Storage:** Don't persist images or form data long-term
- **API Key Protection:** Use Firebase security rules and environment variables
- **CORS Policy:** Whitelist only production domain

### 4.3 Scalability
- **Serverless Architecture:** Firebase Cloud Functions auto-scale
- **Storage:** Firebase Storage with lifecycle policies (auto-delete after 24h)
- **CDN:** Firebase Hosting with global CDN
- **Database:** Firestore for optional usage analytics (not required for MVP)

### 4.4 Reliability
- **Uptime:** 99.5% availability (Firebase SLA)
- **Error Recovery:** Graceful degradation if OCR API fails (fallback to Tesseract)
- **Retry Logic:** 3 retries with exponential backoff for API calls
- **Monitoring:** Firebase Crashlytics for error tracking

### 4.5 Usability
- **Accessibility:** WCAG 2.1 AA compliance
  - Keyboard navigation support
  - Screen reader compatible (ARIA labels)
  - Color contrast ratio > 4.5:1
- **Responsive Design:** Support desktop, tablet, mobile (320px - 2560px)
- **Browser Support:** Chrome, Firefox, Safari, Edge (last 2 versions)
- **Language:** English only (MVP), i18n-ready architecture

### 4.6 Maintainability
- **Code Style:** ESLint + Prettier for TypeScript, Black + isort for Python
- **Type Safety:** Strict TypeScript mode, Python type hints
- **Documentation:** JSDoc/TSDoc comments, Python docstrings
- **Version Control:** Git with conventional commits
- **CI/CD:** GitHub Actions for automated testing and deployment

---

## 5. Technical Architecture

### 5.1 System Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Firebase Hosting)          │
│  ┌─-────────────────────────────────────────────────┐   │
│  │   React + TypeScript Application                 │   │
│  │   - Form Component (Product Type Selector)       │   │
│  │   - Image Upload Component (Drag-Drop)           │   │
│  │   - Results Display Component (Highlights)       │   │
│  └─────────────┬────────────────────────────────-───┘   │
└────────────────┼────────────────────────────────────────┘
                 │
                 │ HTTPS (REST API)
                 ▼
┌─────────────────────────────────────────────────────────┐
│        Backend (Firebase Cloud Functions - Python)      │
│  ┌──────────────-───────────────────────────────────┐   │
│  │   Endpoint: /verify-label (POST)                 │   │
│  │   - Receive form data + image                    │   │
│  │   - Upload image to Firebase Storage             │   │
│  │   - Call OCR service                             │   │
│  │   - Run verification logic                       │   │
│  │   - Return results with bounding boxes           │   │
│  └─────────────┬──────────────────────────────-─────┘   │
└────────────────┼────────────────────────────────────────┘
                 │
                 │
    ┌────────────┴──────────────┐
    │                           │
    ▼                           ▼
┌───────────────────┐   ┌──────────────────┐
│  Google Cloud     │   │  Firebase        │
│  Vision API       │   │  Storage         │
│  (OCR Service)    │   │  (Image Temp     │
│                   │   │   Storage)       │
└───────────────────┘   └──────────────────┘
```

### 5.2 Frontend Tech Stack

**Core Framework:**
- **Next.js 14** (React framework with TypeScript)
- **App Router** for server-side rendering
- **Tailwind CSS** for styling (utility-first)

**Key Libraries:**
- `react-dropzone`: File upload with drag-drop
- `react-hook-form`: Form state management
- `zod`: Schema validation for type-safe forms
- `axios`: HTTP client for API calls
- `canvas-confetti`: Success animation (bonus)
- `framer-motion`: Smooth animations and transitions

**Development Tools:**
- TypeScript 5.x (strict mode)
- ESLint + Prettier
- Husky for pre-commit hooks

### 5.3 Backend Tech Stack

**Runtime:**
- **Firebase Cloud Functions** (2nd gen) with Python 3.11
- **uv** for Python dependency management

**Core Libraries:**
```toml
[project]
dependencies = [
    "google-cloud-vision>=3.4.0",
    "pillow>=10.0.0",
    "firebase-admin>=6.2.0",
    "functions-framework>=3.4.0",
    "python-dotenv>=1.0.0",
    "fuzzywuzzy>=0.18.0",
    "python-Levenshtein>=0.21.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "black>=23.7.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",
]
```

**OCR Services:**
- **Primary:** Google Cloud Vision API (Text Detection)
- **Fallback:** Tesseract OCR via pytesseract

**Python Environment Setup:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv .venv

# Activate
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e .
```

### 5.4 Firebase Configuration

**Firebase Services Used:**
1. **Firebase Hosting:** Static frontend hosting
2. **Cloud Functions (2nd Gen):** Python backend
3. **Firebase Storage:** Temporary image storage (24h retention)

**Environment Variables (.env):**
```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT_ID=ttb-label-checker
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Firebase
FIREBASE_STORAGE_BUCKET=ttb-label-checker.appspot.com

# OCR Config
OCR_CONFIDENCE_THRESHOLD=0.7
```

**Firebase Security Rules (Storage):**
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /label-uploads/{imageId} {
      allow write: if request.auth == null  // Allow public uploads (temp)
                   && request.resource.size < 10 * 1024 * 1024  // 10MB max
                   && request.resource.contentType.matches('image/.*');
      allow read: if request.auth == null;
    }
  }
}
```

### 5.5 API Design

**Endpoint: POST /verify-label**

**Request:**
```typescript
{
  "product_type": "spirits" | "wine" | "beer",
  "form_data": {
    "brand_name": string,
    "product_class": string,
    "alcohol_content": number,
    "net_contents"?: string,
    "bottler_name"?: string,
    "address"?: string,  // "City, State" format
    "country_of_origin"?: string,  // Required if is_imported = true
    "is_imported"?: boolean,
    // Product-type specific fields
    "age_statement"?: string,  // e.g., "3 Years Old"
    "contains_sulfites"?: boolean,  // Wine: true if ≥10 ppm
    "vintage_year"?: number,  // Wine only
    "style"?: string,  // Beer only
  },
  "image": string  // Base64 encoded or multipart form-data
}
```

**Response (Success):**
```typescript
{
  "status": "success",
  "overall_match": boolean,
  "confidence_score": number,  // 0.0 - 1.0
  "results": [
    {
      "field_name": string,
      "status": "match" | "mismatch" | "not_found",
      "expected": string,
      "found": string | null,
      "confidence": number,
      "location": {
        "x": number,
        "y": number,
        "width": number,
        "height": number
      }
    }
  ],
  "ocr_full_text": string,
  "processing_time_ms": number
}
```

**Response (Error):**
```typescript
{
  "status": "error",
  "error_code": "INVALID_IMAGE" | "OCR_FAILED" | "INVALID_INPUT",
  "message": string,
  "details"?: any
}
```

---

## 6. Data Models

### 6.1 Frontend Models (TypeScript)

```typescript
// Product type enum
enum ProductType {
  SPIRITS = 'spirits',
  WINE = 'wine',
  BEER = 'beer'
}

// Form data interface
interface LabelFormData {
  productType: ProductType;
  brandName: string;
  productClass: string;
  alcoholContent: number;
  netContents?: string;

  // Optional bonus fields
  bottlerName?: string;
  address?: string;  // "City, State" format
  countryOfOrigin?: string;
  isImported?: boolean;

  // Type-specific fields - Spirits
  ageStatement?: string;  // e.g., "3 Years Old"
  proof?: number;  // Auto-calculated from ABV
  stateOfDistillation?: string;

  // Type-specific fields - Wine
  vintage?: number;
  containsSulfites?: boolean;  // true if ≥10 ppm
  appellation?: string;

  // Type-specific fields - Beer
  style?: string;  // IPA, Lager, etc.
}

// Verification result interface
interface VerificationResult {
  overallMatch: boolean;
  confidenceScore: number;
  fieldResults: FieldResult[];
  ocrFullText: string;
  processingTimeMs: number;
  annotatedImageUrl?: string;
}

interface FieldResult {
  fieldName: string;
  status: 'match' | 'mismatch' | 'not_found';
  expected: string;
  found: string | null;
  confidence: number;
  location?: BoundingBox;
}

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}
```

### 6.2 Backend Models (Python)

```python
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

class ProductType(Enum):
    SPIRITS = "spirits"
    WINE = "wine"
    BEER = "beer"

@dataclass
class FormData:
    product_type: ProductType
    brand_name: str
    product_class: str
    alcohol_content: float
    net_contents: Optional[str] = None

    # Optional bonus fields
    bottler_name: Optional[str] = None
    address: Optional[str] = None
    country_of_origin: Optional[str] = None
    is_imported: Optional[bool] = None

    # Type-specific fields - Spirits
    age_statement: Optional[str] = None
    proof: Optional[float] = None
    state_of_distillation: Optional[str] = None

    # Type-specific fields - Wine
    vintage: Optional[int] = None
    contains_sulfites: Optional[bool] = None
    appellation: Optional[str] = None

    # Type-specific fields - Beer
    style: Optional[str] = None

@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

@dataclass
class FieldResult:
    field_name: str
    status: Literal["match", "mismatch", "not_found"]
    expected: str
    found: Optional[str]
    confidence: float
    location: Optional[BoundingBox] = None

@dataclass
class VerificationResult:
    overall_match: bool
    confidence_score: float
    field_results: list[FieldResult]
    ocr_full_text: str
    processing_time_ms: float
```

---

## 7. User Interface Design

### 7.1 Page Structure

**Single Page Application (SPA) Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Header: TTB Label Verification System                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────┐  ┌──────────────────────────┐   │
│  │                   │  │                          │   │
│  │  Form Section     │  │  Image Upload Section    │   │
│  │  (Left 40%)       │  │  (Right 60%)             │   │
│  │                   │  │                          │   │
│  │  [Product Type]   │  │  ┌────────────────────┐  │   │
│  │  [Brand Name]     │  │  │  Drag & Drop Zone  │  │   │
│  │  [Product Class]  │  │  │  or Click to       │  │   │
│  │  [ABV %]          │  │  │  Upload Image      │  │   │
│  │  [Net Contents]   │  │  └────────────────────┘  │   │
│  │                   │  │                          │   │
│  │  [Verify Button]  │  │  [Image Preview]         │   │
│  │                   │  │                          │   │
│  └───────────────────┘  └──────────────────────────┘   │
│                                                        │
├────────────────────────────────────────────────────────┤
│  Results Section (Appears after verification)          │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Overall Status: ✅ PASSED                        │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │ Field Results (Expandable List)             │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  │  [Annotated Label Image with Highlights]          │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### 7.2 Responsive Breakpoints
- **Desktop (>1024px):** Side-by-side form and image
- **Tablet (768-1024px):** Stacked form on top, image below
- **Mobile (<768px):** Single column, collapsible sections

### 7.3 Design System

**Colors (Tailwind):**
- Primary: `blue-600` (#2563EB)
- Success: `green-600` (#10B981)
- Error: `red-600` (#EF4444)
- Warning: `yellow-500` (#F59E0B)
- Neutral: `gray-700` (#374151)

**Typography:**
- Headings: `font-bold text-2xl` (Inter font family)
- Body: `font-normal text-base`
- Monospace: `font-mono` (for expected/found values)

**Spacing:**
- Section padding: `p-6`
- Card gap: `gap-4`
- Input margins: `mb-4`

---

## 8. Testing Strategy

### 8.1 Test Cases

**TC-1: Exact Match (Happy Path)**
- Form: Brand="Old Tom", ABV=45%, Class="Bourbon"
- Label: Contains exact text
- Expected: All fields match, overall PASS

**TC-2: Case Insensitive Match**
- Form: Brand="OLD TOM DISTILLERY"
- Label: "old tom distillery"
- Expected: Match after normalization

**TC-3: ABV Mismatch**
- Form: ABV=45%
- Label: 40% visible
- Expected: Mismatch flagged, specific error message

**TC-4: Missing Field on Label**
- Form: Net Contents=750ml
- Label: No volume text
- Expected: "Not Found" status for net contents

**TC-5: Poor Image Quality**
- Upload blurry/dark image
- Expected: OCR confidence < 50%, prompt for better image

**TC-6: No Text Detected**
- Upload blank/corrupted image
- Expected: Error message, suggest re-upload

**TC-7: Government Warning Verification**
- Label with complete warning text
- Expected: Warning check passes

**TC-8: Multiple Product Types**
- Test with beer, wine, spirits labels
- Expected: Type-specific validations apply

### 8.2 Testing Tools

**Frontend:**
- **Jest + React Testing Library:** Component unit tests
- **Cypress:** E2E testing for full user flow
- **Lighthouse:** Performance and accessibility audits

**Backend:**
- **pytest:** Python function unit tests
- **pytest-mock:** Mock OCR API responses
- **coverage.py:** Code coverage reporting (target >80%)

**Manual Testing:**
- Test with 10+ different real label images
- Cross-browser testing (Chrome, Firefox, Safari)
- Mobile device testing (iOS, Android)

---

## 9. Deployment & DevOps

### 9.1 Firebase Deployment

**Project Structure:**
```
ttb-label-checker/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── next.config.js
├── functions/
│   ├── main.py
│   ├── requirements.txt (generated by uv)
│   ├── pyproject.toml
│   └── .python-version
├── firebase.json
├── .firebaserc
└── README.md
```

**Deployment Commands:**
```bash
# Frontend deployment
cd frontend
npm run build
firebase deploy --only hosting

# Backend deployment
cd functions
uv pip compile pyproject.toml -o requirements.txt
firebase deploy --only functions

# Full deployment
firebase deploy
```

### 9.2 Environment Setup

**Development:**
```bash
# Clone repository
git clone https://github.com/username/ttb-label-checker
cd ttb-label-checker

# Frontend setup
cd frontend
npm install
npm run dev  # Starts on localhost:3000

# Backend setup (separate terminal)
cd functions
uv venv
source .venv/bin/activate
uv pip install -e .
functions-framework --target=verify_label --debug  # Local testing
```

**Production:**
- Firebase Hosting: Auto-deploy on git push (GitHub Actions)
- Cloud Functions: Deploy via `firebase deploy --only functions`
- Environment variables: Set via Firebase Console or CLI

### 9.3 CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy to Firebase

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Build Frontend
        run: |
          cd frontend
          npm ci
          npm run build

      - name: Prepare Backend
        run: |
          cd functions
          uv pip compile pyproject.toml -o requirements.txt

      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: '${{ secrets.GITHUB_TOKEN }}'
          firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
          projectId: ttb-label-checker
```

### 9.4 Monitoring & Analytics

**Firebase Performance Monitoring:**
- Track page load times
- Monitor API latency
- Alert on error rate > 5%

**Google Analytics (Optional):**
- User flow tracking
- Conversion funnel (upload → verify → results)
- Device/browser distribution

**Error Tracking:**
- Firebase Crashlytics for frontend errors
- Cloud Functions logs for backend errors
- Sentry integration (optional)

---

## 10. Compliance & Regulations

### 10.1 TTB Regulatory Requirements (Simplified)

**Mandatory Label Elements (27 CFR):**

1. **Brand Name** (27 CFR 5.64)
   - Name under which product is sold
   - Must appear in same field of vision with ABV and class/type*
   - *Note: Spatial validation out of scope for image-only verification

2. **Class and Type Designation** (27 CFR 5.165)
   - Must match TTB-approved classes
   - Must appear in same field of vision with brand and ABV*
   - Must be separate and apart from other information*
   - *Note: Visual separation validation limited by OCR capabilities

3. **Alcohol Content (ABV %)** (27 CFR 5.65)
   - Required as percentage by volume
   - Must appear in same field of vision with brand and class*
   - Acceptable formats: "Alc.", "Alc", "Vol.", "Vol", "%"
   - Proof statement optional (if shown, must equal ABV × 2 and be distinguished)

4. **Net Contents** (27 CFR 5.70, 5.203)
   - Volume of product in container
   - Must meet TTB-approved standards of fill
   - Metric standards required (general rule)
   - Approved sizes: 50ml, 100ml, 200ml, 375ml, 500ml, 750ml, 1L, 1.75L

5. **Name and Address** (27 CFR 5.66, 5.67, 5.68)
   - Bottler/Importer name (or trade name)
   - City and state from permit
   - Must follow phrase like "Bottled By" or "Imported By"
   - Implementation: Optional bonus feature (not MVP)

6. **Health Warning Statement** (27 CFR Part 16) **[CRITICAL]**
   - **Exact wording required** (see Section 3.4.1 for full text)
   - "GOVERNMENT WARNING" in ALL CAPS and bold type
   - "Surgeon General" with capital S and G
   - Must be separate and apart from other information*
   - Must contain pregnancy and driving/machinery warnings
   - *Note: Bold formatting cannot be verified via OCR

7. **Country of Origin** (19 CFR 134.11, 27 CFR 5.69)
   - **Mandatory for imported distilled spirits only**
   - Must comply with U.S. Customs and Border Protection regulations

8. **Sulfite Declaration** (27 CFR 5.63(c)(7))
   - **Mandatory if product contains ≥10 ppm sulfur dioxide**
   - Text: "Contains Sulfites" or "Contains Sulfur Dioxide"

9. **Age Statement** (27 CFR 5.74) **[CONDITIONAL]**
   - **Mandatory for:**
     - Whisky aged < 4 years
     - Grape brandy (lees/pomace/marc) aged < 2 years
     - Any product with age reference on label
     - Any product with distillation date
   - Must use TTB-approved format (see Section 3.4.3)

10. **State of Distillation** (27 CFR 5.66(f)) **[CONDITIONAL]**
    - Required for certain whisky types if state ≠ bottler address state

11. **Commodity Statement** (27 CFR 5.71) **[CONDITIONAL]**
    - Required if neutral spirits used in blending
    - Must state percentage and source grain

**Verification Priorities:**
- **Critical (Must Pass):** Health Warning (exact text), Brand, ABV, Product Class
- **High Priority:** Net Contents (with standards of fill), Age Statement (if applicable)
- **Medium Priority:** Sulfite Declaration (if applicable), Country of Origin (if imported)
- **Low Priority (Bonus):** Name/Address, Proof formatting, State of Distillation

**Out of Scope (Documented Limitations):**
- Same field of vision spatial validation (requires label layout analysis)
- Visual separation verification (requires spatial analysis)
- Bold/font styling verification (OCR limitation)
- Font size requirements (OCR limitation)
- Color requirements (OCR processes text only)

### 10.2 Product-Specific Rules

**Distilled Spirits (27 CFR Part 5):**
- Must state class/type matching TTB standards (Whiskey, Vodka, Rum, Gin, Tequila, Brandy, Liqueur, etc.)
- Age statement conditional on product type and duration (see Section 3.4.3)
- Proof statement optional, but if present: Proof = ABV × 2 (±1 tolerance)
- State of distillation required for certain whisky if state differs from address
- Commodity statement required if neutral spirits in blend
- Minimum font size requirements (not checked in MVP - out of scope)

**Wine (27 CFR Part 4):**
- Varietal must be >75% of that grape (not verified - assumes form truthful)
- Vintage year must be ≥95% from that year (not verified - assumes form truthful)
- "Contains Sulfites" required if ≥10 ppm (verified via form checkbox)
- Alcohol content may be omitted for "Table Wine" (7-14% ABV implicit)
- Appellation of origin (optional verification)

**Beer/Malt Beverages (27 CFR Part 7):**
- "Malt Beverage" acceptable synonym for "Beer"
- ABV often optional (common practice)
- If ABV < 0.5%, may be labeled "non-alcoholic"
- Ingredients list optional (except allergens - not in MVP scope)
- Style designation (IPA, Lager, etc.) is informational, not regulatory

### 10.3 Compliance Scoring

```python
def calculate_compliance_score(results: VerificationResult) -> dict:
    """
    Weighted scoring system for compliance
    High priority fields: 40 points each
    Medium priority: 20 points each
    Low priority: 10 points each
    """
    score = 0
    max_score = 0

    weights = {
        "brand_name": 40,
        "alcohol_content": 40,
        "product_class": 40,
        "government_warning": 40,
        "net_contents": 20,
        "sulfites": 20,
        "address": 10
    }

    for field_result in results.field_results:
        weight = weights.get(field_result.field_name, 10)
        max_score += weight
        if field_result.status == "match":
            score += weight

    return {
        "score": score,
        "max_score": max_score,
        "percentage": (score / max_score) * 100,
        "grade": get_grade(score / max_score)  # A/B/C/D/F
    }
```

---

## 11. Future Enhancements (Post-MVP)

### 11.1 Phase 2 Features
1. **Batch Processing:** Upload multiple labels at once
2. **Historical Tracking:** Save past verifications (with user accounts)
3. **Label Template Library:** Pre-approved label templates
4. **PDF Export:** Download compliance report as PDF
5. **Email Notifications:** Send results via email

### 11.2 Phase 3 Features
1. **Advanced OCR:** Handwriting recognition for craft labels
2. **Multi-Language Support:** Spanish, French labels
3. **API Access:** RESTful API for third-party integrations
4. **Admin Dashboard:** Analytics for TTB agents
5. **Mobile App:** Native iOS/Android apps

### 11.3 Technical Debt Items
- Implement comprehensive error logging
- Add rate limiting to prevent abuse
- Optimize image processing (WebP format, lazy loading)
- Add Redis caching for repeated verifications
- Implement A/B testing framework

---

## 12. Success Criteria & KPIs

### 12.1 MVP Launch Criteria
- [ ] All core form fields functional
- [ ] Image upload with 3 format support (JPEG, PNG, WebP)
- [ ] OCR accuracy >85% on test label set
- [ ] Match/mismatch detection >90% accuracy
- [ ] Results display with clear messaging
- [ ] Mobile responsive design
- [ ] Deployed to Firebase and accessible via URL
- [ ] Page load < 3 seconds on 4G connection

### 12.2 Key Performance Indicators
- **User Engagement:** 70% complete verification flow
- **Error Rate:** <5% failed verifications (technical errors)
- **Processing Time:** <5 seconds average
- **User Satisfaction:** 4+ star rating (post-launch survey)
- **Accessibility:** Lighthouse accessibility score >90

---

## 13. Project Timeline

### 13.1 MVP Development (Day 1)
**Morning (4 hours):**
- [ ] Project setup (Firebase, Next.js, Python environment with uv)
- [ ] Basic form UI (product type selector, core fields)
- [ ] Image upload component (drag-drop)
- [ ] Firebase Cloud Function skeleton

**Afternoon (4 hours):**
- [ ] OCR integration (Google Vision API)
- [ ] Basic comparison logic (brand, ABV, class)
- [ ] Results display (simple list)
- [ ] Deploy to Firebase
- [ ] Manual testing with 3 sample labels

### 13.2 Polish & Bonus Features (Day 2)
**Morning:**
- [ ] Image highlighting with bounding boxes
- [ ] Government warning verification
- [ ] Net contents verification
- [ ] Improved error handling

**Afternoon:**
- [ ] Product-type specific validations
- [ ] Fuzzy matching for typo tolerance
- [ ] UX refinements (animations, loading states)
- [ ] Cross-browser testing
- [ ] Documentation (README, deployment guide)

### 13.3 Optional Day 3 (Extended Features)
- [ ] PDF export functionality
- [ ] Historical verification log (Firestore)
- [ ] Advanced compliance scoring
- [ ] Automated tests (Jest, pytest)
- [ ] Performance optimization

---

## 14. Documentation Requirements

### 14.1 README.md
Must include:
- Project overview and purpose
- Tech stack summary
- Local development setup instructions
- Firebase deployment guide
- Environment variables configuration
- Sample API requests/responses
- Known limitations
- Future roadmap

### 14.2 Code Documentation
- **TypeScript:** TSDoc comments for all public functions
- **Python:** Docstrings with Google style format
- **Inline Comments:** For complex logic only

### 14.3 User Guide
- How to use the application (with screenshots)
- Troubleshooting common issues
- Sample label images for testing
- FAQ section

---

## 15. Risk Assessment

### 15.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| OCR accuracy <85% | Medium | High | Use Google Vision API (high accuracy), fallback to Tesseract |
| Firebase costs exceed budget | Low | Medium | Implement storage lifecycle policies (auto-delete after 24h) |
| Image upload fails on slow networks | Medium | Medium | Client-side compression, chunked upload |
| API rate limits exceeded | Low | High | Implement request queuing, show wait time |
| Poor mobile UX | Medium | Medium | Early responsive testing, touch-optimized controls |

### 15.2 Scope Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Feature creep beyond 1-day scope | High | Medium | Strict prioritization, move extras to Phase 2 |
| Compliance rules too complex | Medium | High | Focus on 4 core fields only, document limitations |
| Testing insufficient | Medium | High | Allocate 20% of time for testing, use real label samples |

---

## 16. Assumptions & Constraints

### 16.1 Assumptions
- Users have stable internet connection (>1 Mbps)
- Label images are clear enough for human reading
- Users understand basic alcohol labeling concepts
- English-language labels only
- Desktop/mobile browser access (no IE11 support)
- Form data provided by user is truthful (e.g., actual sulfite content, grape percentages)
- Label image shows a single, flat label view (not 3D bottle rotation)

### 16.2 Constraints
- **Time:** MVP in 1 day (8 hours), full feature set in 2-3 days
- **Budget:** Free tier only (Firebase, Google Cloud Vision API)
- **OCR Limits:** Google Vision API free tier (1000 requests/month)
- **Storage:** Firebase Storage free tier (5 GB)
- **Team:** Solo developer
- **Scope:** Simplified TTB compliance check (not full certification process)

### 16.3 Known Limitations & Out-of-Scope Items

**Technical Limitations (OCR-Based):**
1. **Same Field of Vision Verification**
   - Regulatory Requirement: Brand, ABV, and Class/Type must appear in same field of vision (40% circumference or single side)
   - Limitation: Requires 3D label layout analysis and container geometry
   - Status: **Out of scope** for image-only verification
   - Impact: System cannot verify spatial positioning of fields

2. **Visual Separation Verification**
   - Regulatory Requirement: Class/Type and Health Warning must be "separate and apart" from other information
   - Limitation: Requires spatial analysis of text positioning and visual boundaries
   - Status: **Out of scope** - OCR provides text content, not precise layout
   - Impact: Cannot verify visual distinctiveness of fields

3. **Font Styling Verification**
   - Regulatory Requirement: "GOVERNMENT WARNING" must be in bold type
   - Limitation: OCR extracts text content only, not font weight/style
   - Status: **Out of scope** - fundamental OCR limitation
   - Impact: Cannot verify bold, italic, or font family requirements

4. **Font Size Requirements**
   - Regulatory Requirement: Minimum font sizes specified in 27 CFR
   - Limitation: OCR does not reliably measure point sizes from images
   - Status: **Out of scope** - would require pixel-to-physical-size conversion with scale reference
   - Impact: Cannot verify minimum font size compliance

5. **Color Requirements**
   - Regulatory Requirement: Certain text may have color contrast requirements
   - Limitation: OCR processes images in grayscale for text detection
   - Status: **Out of scope** - not addressed by text extraction
   - Impact: Cannot verify color compliance

**Regulatory Scope Limitations:**

6. **Full TTB Certification Process**
   - System provides pre-check only, not official TTB certificate of label approval
   - Does not replace formal COL application through TTB
   - User must still submit official application to TTB

7. **Formula Approval Verification**
   - Some products require TTB-approved formulas (cordials, liqueurs, specialty items)
   - System does not verify formula approval status
   - Status: **Out of scope** - requires TTB database access

8. **Production Process Verification**
   - Cannot verify actual production methods match label claims (e.g., actual aging duration)
   - Assumes user form data is truthful
   - TTB would verify through distillery inspection

9. **Grape Varietal Percentages (Wine)**
   - Regulatory Requirement: Varietal must be ≥75% of stated grape
   - System cannot verify actual grape composition from label alone
   - Status: Assumes form data is accurate

10. **Import Documentation (Country of Origin)**
    - Cannot verify actual country of origin or import status
    - Relies on user indication of imported vs. domestic

**Intentional Simplifications:**

11. **Address Verification**
    - Name and address verification marked as bonus feature
    - Not critical for MVP label content matching
    - Would require TTB permit database integration for full verification

12. **Allergen Warnings**
    - Not included in MVP scope
    - Would be regulatory requirement for certain ingredients

13. **Multi-Language Labels**
    - English-only support in MVP
    - Spanish, French labels not supported

14. **Batch/Lot Number Validation**
    - Format varies by producer
    - No standard validation rules

**Workarounds & Mitigations:**

- **For spatial requirements:** Document limitation clearly in results
- **For font styling:** Verify text content exactness (capitalization, spelling)
- **For font sizes:** Trust that submitted images show compliant labels
- **For formulas:** Provide informational note when formula-required products detected
- **For varietal percentages:** Add disclaimer that system verifies label text only, not production claims

**Future Enhancements:**
- Phase 2: Computer vision for spatial layout analysis
- Phase 3: Machine learning for label element detection and positioning
- Phase 4: Integration with TTB public data APIs (if available)

---

## 17. Appendix

### 17.1 Glossary
- **ABV:** Alcohol By Volume (percentage)
- **OCR:** Optical Character Recognition
- **TTB:** Alcohol and Tobacco Tax and Trade Bureau
- **CFR:** Code of Federal Regulations
- **Fuzzy Matching:** Approximate string matching (tolerates typos)
- **Bounding Box:** Rectangle coordinates around detected text

### 17.2 References
- [TTB Label Requirements](https://www.ttb.gov/media/66695/download?inline)
- [Google Cloud Vision API Docs](https://cloud.google.com/vision/docs)
- [Firebase Documentation](https://firebase.google.com/docs)
- [uv Python Package Manager](https://github.com/astral-sh/uv)

### 17.3 Sample Test Labels
*Include 5-10 sample label images in `/docs/sample-labels/` directory:*
- `bourbon-whiskey-sample.jpg`
- `beer-ipa-sample.png`
- `red-wine-sample.jpg`
- `vodka-sample.png`
- `mismatch-test-sample.jpg` (intentionally wrong data)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-24
**Author:** Product Team
**Status:** Approved for Development
