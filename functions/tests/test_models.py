"""
Unit Tests for Data Models

Tests for dataclasses, enums, and model validation.
"""

import pytest
from models import (
    ProductType,
    VerificationStatus,
    FormData,
    FieldResult,
    VerificationResult,
    OCRResult,
    BoundingBox,
    TextBlock
)


class TestProductType:
    """Test ProductType enum."""

    def test_valid_product_types(self):
        """Test all valid product type values."""
        assert ProductType.SPIRITS.value == "spirits"
        assert ProductType.WINE.value == "wine"
        assert ProductType.BEER.value == "beer"

    def test_product_type_from_string(self):
        """Test creating ProductType from string."""
        assert ProductType("spirits") == ProductType.SPIRITS
        assert ProductType("wine") == ProductType.WINE
        assert ProductType("beer") == ProductType.BEER

    def test_invalid_product_type(self):
        """Test that invalid product type raises ValueError."""
        with pytest.raises(ValueError):
            ProductType("invalid")


class TestVerificationStatus:
    """Test VerificationStatus enum."""

    def test_valid_statuses(self):
        """Test all valid status values."""
        assert VerificationStatus.MATCH.value == "match"
        assert VerificationStatus.MISMATCH.value == "mismatch"
        assert VerificationStatus.NOT_FOUND.value == "not_found"
        assert VerificationStatus.WARNING.value == "warning"
        assert VerificationStatus.ERROR.value == "error"


class TestFormData:
    """Test FormData dataclass."""

    def test_required_fields_only(self):
        """Test FormData with only required fields."""
        form = FormData(
            brand_name="Test Brand",
            product_class="Bourbon Whiskey",
            alcohol_content=45.0
        )
        assert form.brand_name == "Test Brand"
        assert form.product_class == "Bourbon Whiskey"
        assert form.alcohol_content == 45.0
        assert form.net_contents is None
        assert form.bottler_name is None

    def test_all_fields_spirits(self):
        """Test FormData with all spirits-specific fields."""
        form = FormData(
            brand_name="Eagle Rare",
            product_class="Straight Bourbon Whiskey",
            alcohol_content=45.0,
            net_contents="750 mL",
            bottler_name="Buffalo Trace",
            address="Frankfort, KY",
            country_of_origin="United States",
            is_imported=False,
            age_statement="Aged 10 Years",
            proof=90.0,
            state_of_distillation="Kentucky",
            commodity_statement="Bourbon Whiskey"
        )
        assert form.age_statement == "Aged 10 Years"
        assert form.proof == 90.0
        assert form.state_of_distillation == "Kentucky"

    def test_all_fields_wine(self):
        """Test FormData with wine-specific fields."""
        form = FormData(
            brand_name="Napa Reserve",
            product_class="Cabernet Sauvignon",
            alcohol_content=13.5,
            vintage_year=2019,
            contains_sulfites=True,
            appellation="Napa Valley"
        )
        assert form.vintage_year == 2019
        assert form.contains_sulfites is True
        assert form.appellation == "Napa Valley"

    def test_all_fields_beer(self):
        """Test FormData with beer-specific fields."""
        form = FormData(
            brand_name="Hazy IPA",
            product_class="India Pale Ale",
            alcohol_content=6.5,
            style="New England IPA"
        )
        assert form.style == "New England IPA"

    def test_imported_product(self):
        """Test FormData for imported product."""
        form = FormData(
            brand_name="Scotch",
            product_class="Single Malt Whisky",
            alcohol_content=40.0,
            is_imported=True,
            country_of_origin="Scotland"
        )
        assert form.is_imported is True
        assert form.country_of_origin == "Scotland"

    def test_invalid_alcohol_content(self):
        """Test that negative alcohol content is allowed by dataclass but should fail validation."""
        # Dataclass allows it, validation happens in verification.py
        form = FormData(
            brand_name="Test",
            product_class="Test",
            alcohol_content=-5.0
        )
        assert form.alcohol_content == -5.0  # Dataclass accepts it

    def test_to_dict(self):
        """Test FormData.to_dict() method."""
        form = FormData(
            brand_name="Test",
            product_class="Bourbon",
            alcohol_content=45.0,
            net_contents="750 mL"
        )
        data = form.to_dict()
        assert data["brand_name"] == "Test"
        assert data["product_class"] == "Bourbon"
        assert data["alcohol_content"] == 45.0
        assert data["net_contents"] == "750 mL"
        assert isinstance(data, dict)


class TestFieldResult:
    """Test FieldResult dataclass."""

    def test_match_result(self):
        """Test FieldResult with match status."""
        result = FieldResult(
            field_name="brand_name",
            status=VerificationStatus.MATCH,
            expected="Eagle Rare",
            found="EAGLE RARE",
            confidence=0.98,
            message="Brand name verified"
        )
        assert result.field_name == "brand_name"
        assert result.status == VerificationStatus.MATCH
        assert result.expected == "Eagle Rare"
        assert result.found == "EAGLE RARE"
        assert result.confidence == 0.98

    def test_mismatch_result(self):
        """Test FieldResult with mismatch status."""
        result = FieldResult(
            field_name="alcohol_content",
            status=VerificationStatus.MISMATCH,
            expected="40.0",
            found="37.5",
            confidence=0.95,
            message="ABV mismatch",
            cfr_reference="27 CFR 5.37"
        )
        assert result.status == VerificationStatus.MISMATCH
        assert result.cfr_reference == "27 CFR 5.37"

    def test_not_found_result(self):
        """Test FieldResult with not_found status."""
        result = FieldResult(
            field_name="age_statement",
            status=VerificationStatus.NOT_FOUND,
            expected="Aged 10 Years",
            found=None,
            confidence=0.0,
            message="Age statement not found on label"
        )
        assert result.found is None
        assert result.confidence == 0.0

    def test_with_location(self):
        """Test FieldResult with bounding box location."""
        bbox = BoundingBox(x=100, y=200, width=300, height=50)
        result = FieldResult(
            field_name="brand_name",
            status=VerificationStatus.MATCH,
            expected="Test",
            found="TEST",
            confidence=0.95,
            location=bbox
        )
        assert result.location is not None
        assert result.location.x == 100
        assert result.location.width == 300

    def test_to_dict(self):
        """Test FieldResult.to_dict() serialization."""
        result = FieldResult(
            field_name="brand_name",
            status=VerificationStatus.MATCH,
            expected="Test",
            found="TEST",
            confidence=0.95
        )
        data = result.to_dict()
        assert data["field_name"] == "brand_name"
        assert data["status"] == "match"
        assert data["expected"] == "Test"
        assert data["found"] == "TEST"


class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_successful_verification(self):
        """Test VerificationResult for successful verification."""
        field_results = [
            FieldResult("brand_name", VerificationStatus.MATCH, "Test", "TEST", 0.95),
            FieldResult("alcohol_content", VerificationStatus.MATCH, "40", "40% ABV", 0.93)
        ]

        result = VerificationResult(
            overall_match=True,
            confidence_score=0.94,
            field_results=field_results,
            ocr_full_text="TEST\n40% ABV\n...",
            processing_time_ms=1200.5,
            compliance_score=100,
            compliance_grade="A"
        )

        assert result.overall_match is True
        assert result.compliance_score == 100
        assert result.compliance_grade == "A"
        assert len(result.field_results) == 2
        assert result.processing_time_ms == 1200.5

    def test_failed_verification(self):
        """Test VerificationResult for failed verification."""
        field_results = [
            FieldResult("brand_name", VerificationStatus.MATCH, "Test", "TEST", 0.95),
            FieldResult("alcohol_content", VerificationStatus.MISMATCH, "40", "37.5", 0.93)
        ]

        result = VerificationResult(
            overall_match=False,
            confidence_score=0.94,
            field_results=field_results,
            ocr_full_text="TEST\n37.5% ABV",
            processing_time_ms=1300.0,
            compliance_score=60,
            compliance_grade="D",
            errors=["Alcohol content mismatch"],
            warnings=[]
        )

        assert result.overall_match is False
        assert result.compliance_grade == "D"
        assert len(result.errors) == 1
        assert result.errors[0] == "Alcohol content mismatch"

    def test_with_warnings(self):
        """Test VerificationResult with warnings."""
        field_results = [
            FieldResult("net_contents", VerificationStatus.WARNING, "725 mL", "725 mL", 0.90)
        ]

        result = VerificationResult(
            overall_match=True,
            confidence_score=0.90,
            field_results=field_results,
            ocr_full_text="725 mL",
            processing_time_ms=1100.0,
            compliance_score=85,
            compliance_grade="B",
            warnings=["Non-standard bottle size"]
        )

        assert len(result.warnings) == 1
        assert result.compliance_grade == "B"

    def test_to_dict(self):
        """Test VerificationResult.to_dict() serialization."""
        field_results = [
            FieldResult("brand_name", VerificationStatus.MATCH, "Test", "TEST", 0.95)
        ]

        result = VerificationResult(
            overall_match=True,
            confidence_score=0.95,
            field_results=field_results,
            ocr_full_text="TEST",
            processing_time_ms=1200.0,
            compliance_score=100,
            compliance_grade="A"
        )

        data = result.to_dict()
        assert data["overall_match"] is True
        assert data["compliance_score"] == 100
        assert data["compliance_grade"] == "A"
        assert len(data["field_results"]) == 1
        assert isinstance(data, dict)


class TestOCRResult:
    """Test OCRResult dataclass."""

    def test_ocr_result_creation(self):
        """Test creating OCRResult."""
        text_blocks = [
            TextBlock(
                text="EAGLE RARE",
                confidence=0.98,
                bounding_box=BoundingBox(100, 50, 200, 30)
            ),
            TextBlock(
                text="45% ALC/VOL",
                confidence=0.95,
                bounding_box=BoundingBox(100, 100, 150, 25)
            )
        ]

        ocr = OCRResult(
            full_text="EAGLE RARE\n45% ALC/VOL",
            text_blocks=text_blocks,
            confidence=0.96
        )

        assert ocr.full_text == "EAGLE RARE\n45% ALC/VOL"
        assert len(ocr.text_blocks) == 2
        assert ocr.confidence == 0.96

    def test_empty_ocr_result(self):
        """Test OCRResult with no text found."""
        ocr = OCRResult(
            full_text="",
            text_blocks=[],
            confidence=0.0
        )

        assert ocr.full_text == ""
        assert len(ocr.text_blocks) == 0
        assert ocr.confidence == 0.0


class TestBoundingBox:
    """Test BoundingBox dataclass."""

    def test_bounding_box_creation(self):
        """Test creating BoundingBox."""
        bbox = BoundingBox(x=100, y=200, width=300, height=50)
        assert bbox.x == 100
        assert bbox.y == 200
        assert bbox.width == 300
        assert bbox.height == 50

    def test_bounding_box_to_dict(self):
        """Test BoundingBox.to_dict() serialization."""
        bbox = BoundingBox(x=100, y=200, width=300, height=50)
        data = bbox.to_dict()
        assert data["x"] == 100
        assert data["y"] == 200
        assert data["width"] == 300
        assert data["height"] == 50


class TestTextBlock:
    """Test TextBlock dataclass."""

    def test_text_block_creation(self):
        """Test creating TextBlock."""
        bbox = BoundingBox(100, 200, 300, 50)
        block = TextBlock(
            text="EAGLE RARE",
            confidence=0.98,
            bounding_box=bbox
        )

        assert block.text == "EAGLE RARE"
        assert block.confidence == 0.98
        assert block.bounding_box.x == 100

    def test_text_block_to_dict(self):
        """Test TextBlock.to_dict() serialization."""
        bbox = BoundingBox(100, 200, 300, 50)
        block = TextBlock(
            text="EAGLE RARE",
            confidence=0.98,
            bounding_box=bbox
        )

        data = block.to_dict()
        assert data["text"] == "EAGLE RARE"
        assert data["confidence"] == 0.98
        assert "bounding_box" in data
        assert data["bounding_box"]["x"] == 100
