# Backend Unit Tests

Comprehensive test suite for TTB Label Verification System backend components.

## Overview

This test suite covers:
- **Data Models** (`test_models.py`) - Dataclass validation and serialization
- **OCR Processing** (`test_ocr.py`) - Image validation, Vision API integration (mocked)
- **Verification Logic** (`test_verification.py`) - Field matching, compliance scoring, TTB regulations

## Running Tests

### Prerequisites

```bash
# Navigate to functions directory
cd functions

# Activate virtual environment
source .venv/bin/activate  # Unix/Mac
.venv\Scripts\activate     # Windows

# Install test dependencies
uv pip install -e ".[dev]"
# OR
uv pip install pytest pytest-mock pytest-cov
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Models only
pytest tests/test_models.py

# OCR only
pytest tests/test_ocr.py

# Verification only
pytest tests/test_verification.py
```

### Run by Test Class

```bash
pytest tests/test_verification.py::TestVerifyBrandName
pytest tests/test_ocr.py::TestValidateAndDecodeImage
```

### Run Specific Test

```bash
pytest tests/test_verification.py::TestVerifyBrandName::test_exact_match
```

### Run with Coverage Report

```bash
# Terminal output with missing lines
pytest --cov=. --cov-report=term-missing

# HTML coverage report (opens in browser)
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Run Only Unit Tests (Fast)

```bash
pytest -m unit
```

### Skip Integration Tests

```bash
pytest -m "not integration"
```

### Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

### Show Print Statements

```bash
pytest -s
```

## Test Markers

Tests are marked with the following markers:

- **`@pytest.mark.unit`** - Fast unit tests, no external dependencies
- **`@pytest.mark.integration`** - Integration tests requiring Google Cloud Vision API
- **`@pytest.mark.slow`** - Tests taking > 1 second

Example usage:
```python
@pytest.mark.unit
def test_normalize_text():
    assert normalize_text("TEST") == "test"

@pytest.mark.integration
@pytest.mark.skip(reason="Requires Google Cloud credentials")
def test_real_vision_api():
    # Real Vision API call
    pass
```

## Test Structure

### test_models.py (350+ lines)

Tests all dataclass models:
- `ProductType` enum
- `VerificationStatus` enum
- `FormData` with all product-specific fields
- `FieldResult` with all statuses
- `VerificationResult` with scoring
- `OCRResult`, `BoundingBox`, `TextBlock`
- Serialization (`to_dict()` methods)

### test_ocr.py (400+ lines)

Tests OCR processing pipeline:
- **Image Validation:**
  - Valid formats (JPEG, PNG, WebP, HEIC)
  - Invalid formats (GIF, BMP)
  - Size constraints (< 100x100, > 10MB)
  - Dimension constraints (< 100x100, > 10000x10000)
  - Corrupted images
  - Base64 encoding/decoding

- **Vision API (Mocked):**
  - Successful text extraction
  - No text found
  - API errors
  - Bounding box extraction

- **Text Processing:**
  - Normalization (lowercase, whitespace, punctuation)
  - OCR error correction (0→O, 1→I, 5→S)

### test_verification.py (800+ lines)

Tests complete verification logic:

**Field Verification Functions:**
- `verify_brand_name()` - Fuzzy matching, case insensitive
- `verify_alcohol_content()` - Tolerance (±0.5%), format variations
- `verify_product_class()` - Partial matching
- `verify_government_warning()` - Exact text (95% fuzzy), keyword checks
- `verify_net_contents()` - Unit conversions, standards of fill
- `verify_age_statement()` - Conditional (whisky < 4 yrs, brandy < 2 yrs)
- `verify_proof()` - Calculation (ABV × 2), tolerance (±1)
- `verify_sulfites()` - Conditional (wine only, if ≥10 ppm)
- `verify_country_of_origin()` - Conditional (imported products)

**Compliance Scoring:**
- Perfect score (100%, Grade A)
- Missing critical fields (40 pts each)
- Missing important fields (20 pts each)
- Warning status (80% of points)
- Grade boundaries (A: 90-100%, B: 80-89%, C: 70-79%, D: 60-69%, F: <60%)

**Helper Functions:**
- `parse_net_contents()` - Unit conversion (mL, L, fl oz, gal)
- `is_standard_size()` - Standards of fill (spirits, wine, beer)

**Integration Tests:**
- Complete bourbon label verification
- Complete wine label verification
- ABV mismatch scenarios
- Missing government warning
- Optional fields handling

## Expected Coverage

Target code coverage: **>90%**

Current coverage (estimated):
- `models.py`: 100% (all dataclasses and methods tested)
- `ocr.py`: 85% (Vision API calls mocked, real calls skipped)
- `verification.py`: 95% (comprehensive field verification tests)

## Fixtures

### Global Fixtures (conftest.py)

- `government_warning_text` - Full 27 CFR Part 16 warning text
- `mock_vision_api_response` - Mocked Vision API response
- `sample_bourbon_label` - Complete bourbon test data
- `sample_wine_label` - Complete wine test data
- `sample_beer_label` - Complete beer test data
- `performance_timer` - Timer for performance testing

### Test-Specific Fixtures

- `bourbon_form_data` - Valid bourbon FormData
- `bourbon_ocr_text` - Matching bourbon OCR text
- `wine_form_data` - Valid wine FormData
- `wine_ocr_text` - Matching wine OCR text
- `valid_image` - 800x600 JPEG image
- `valid_base64_image` - Base64-encoded image with data URI
- `small_image` - 50x50 image (too small)
- `large_image` - >10MB image (too large)

## Continuous Integration

For CI/CD pipelines (GitHub Actions, etc.):

```yaml
# .github/workflows/test.yml
- name: Run Backend Tests
  run: |
    cd functions
    source .venv/bin/activate
    pytest --cov=. --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./functions/coverage.xml
```

## Troubleshooting

### Import Errors

If you get import errors:
```bash
# Ensure you're in the functions directory
cd functions

# Install in editable mode
uv pip install -e .
```

### Google Cloud Credentials

Integration tests are skipped by default. To run them:

1. Set up service account credentials
2. Export environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
   ```
3. Run integration tests:
   ```bash
   pytest -m integration
   ```

### Coverage Report Not Generated

```bash
# Explicitly specify coverage options
pytest --cov=. --cov-report=html --cov-report=term

# Check that htmlcov/ directory was created
ls -la htmlcov/
```

## Writing New Tests

### Example Test Structure

```python
import pytest
from models import FormData, ProductType
from verification import verify_brand_name

class TestMyFeature:
    """Test description."""

    def test_basic_case(self):
        """Test basic functionality."""
        result = verify_brand_name("Test", "TEST BRAND")
        assert result.status == VerificationStatus.MATCH

    def test_edge_case(self):
        """Test edge case."""
        result = verify_brand_name("", "TEXT")
        assert result.status == VerificationStatus.NOT_FOUND

    @pytest.mark.parametrize("input,expected", [
        ("Test", "match"),
        ("Another", "not_found"),
    ])
    def test_multiple_cases(self, input, expected):
        """Test multiple cases with parametrize."""
        result = verify_brand_name(input, "TEST BRAND")
        assert result.status.value == expected
```

## Best Practices

1. **Use Fixtures**: Reuse common test data from fixtures
2. **Parametrize**: Use `@pytest.mark.parametrize` for multiple similar tests
3. **Mock External Calls**: Always mock Google Cloud Vision API calls
4. **Descriptive Names**: Test names should describe what they test
5. **Docstrings**: Add docstrings to test classes and methods
6. **Assertions**: Use specific assertions (`assert x == y`, not `assert x`)
7. **Coverage**: Aim for >90% code coverage
8. **Fast Tests**: Keep unit tests fast (<100ms each)

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Google Cloud Vision API Docs](https://cloud.google.com/vision/docs)
- [TTB Regulations (27 CFR)](https://www.ecfr.gov/current/title-27)

---

**Last Updated:** 2024-10-27
**Test Suite Version:** 1.0
**Total Test Count:** 100+ tests
**Estimated Run Time:** <5 seconds (unit tests only)
