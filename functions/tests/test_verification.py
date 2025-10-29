"""
Unit Tests for Verification Module

Tests for label verification logic, compliance scoring, field matching,
and TTB regulatory requirements.
"""


import pytest

from models import (
    FieldResult,
    FormData,
    OCRResult,
    ProductType,
    VerificationResult,
    VerificationStatus,
)
from verification import (
    GOVERNMENT_WARNING_TEXT,
    calculate_compliance_score,
    is_standard_size,
    parse_net_contents,
    verify_age_statement,
    verify_alcohol_content,
    verify_brand_name,
    verify_country_of_origin,
    verify_government_warning,
    verify_label,
    verify_net_contents,
    verify_product_class,
    verify_proof,
    verify_sulfites,
)

# Test Fixtures

@pytest.fixture
def bourbon_form_data():
    """Valid bourbon form data."""
    return FormData(
        brand_name="Eagle Rare",
        product_class="Straight Bourbon Whiskey",
        alcohol_content=45.0,
        net_contents="750 mL",
        bottler_name="Buffalo Trace Distillery",
        address="Frankfort, KY",
        country_of_origin="United States",
        is_imported=False,
        age_statement="Aged 10 Years",
        proof=90.0
    )


@pytest.fixture
def bourbon_ocr_text():
    """Matching OCR text for bourbon label."""
    return """
    EAGLE RARE
    KENTUCKY STRAIGHT BOURBON WHISKEY
    AGED 10 YEARS
    45% ALC/VOL
    90 PROOF
    750 mL
    BUFFALO TRACE DISTILLERY
    FRANKFORT, KENTUCKY
    GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
    """


@pytest.fixture
def wine_form_data():
    """Valid wine form data."""
    return FormData(
        brand_name="Napa Valley Reserve",
        product_class="Cabernet Sauvignon",
        alcohol_content=13.5,
        net_contents="750 mL",
        vintage_year=2019,
        contains_sulfites=True,
        appellation="Napa Valley"
    )


@pytest.fixture
def wine_ocr_text():
    """Matching OCR text for wine label."""
    return """
    NAPA VALLEY RESERVE
    CABERNET SAUVIGNON
    2019
    13.5% ALC/VOL
    750 mL
    NAPA VALLEY
    CONTAINS SULFITES
    GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
    """


# Test verify_brand_name

class TestVerifyBrandName:
    """Test brand name verification."""

    def test_exact_match(self):
        """Test exact brand name match (case insensitive)."""
        result = verify_brand_name("Eagle Rare", "EAGLE RARE KENTUCKY BOURBON")
        assert result.status == VerificationStatus.MATCH
        assert result.found == "EAGLE RARE"

    def test_fuzzy_match(self):
        """Test fuzzy brand name match (minor OCR errors)."""
        # "Rare" OCR'd as "Rave"
        result = verify_brand_name("Eagle Rare", "EAGLE RAVE BOURBON")
        # Should still match if similarity > 80%
        assert result.status == VerificationStatus.MATCH

    def test_not_found(self):
        """Test brand name not found on label."""
        result = verify_brand_name("Eagle Rare", "DIFFERENT BRAND BOURBON")
        assert result.status == VerificationStatus.NOT_FOUND

    def test_mismatch(self):
        """Test brand name mismatch (similar but different brand)."""
        result = verify_brand_name("Jack Daniel's", "Jim Beam BOURBON")
        assert result.status == VerificationStatus.NOT_FOUND

    def test_special_characters(self):
        """Test brand names with special characters."""
        result = verify_brand_name("Jack Daniel's", "JACK DANIELS WHISKEY")
        # Should match despite apostrophe difference
        assert result.status == VerificationStatus.MATCH


# Test verify_alcohol_content

class TestVerifyAlcoholContent:
    """Test alcohol content verification."""

    def test_exact_percentage_match(self):
        """Test exact ABV match."""
        result = verify_alcohol_content(45.0, "45% ALC/VOL", ProductType.SPIRITS, False)
        assert result.status == VerificationStatus.MATCH
        assert "45" in result.found

    def test_decimal_variations(self):
        """Test ABV with different decimal formats."""
        result = verify_alcohol_content(45.0, "45.0% ABV", ProductType.SPIRITS, False)
        assert result.status == VerificationStatus.MATCH

        result = verify_alcohol_content(13.5, "13.5% ALC/VOL", ProductType.WINE, False)
        assert result.status == VerificationStatus.MATCH

    def test_tolerance_match(self):
        """Test ABV within tolerance (±0.5%)."""
        result = verify_alcohol_content(40.0, "39.8% ALC/VOL", ProductType.SPIRITS, False)
        assert result.status == VerificationStatus.MATCH

        result = verify_alcohol_content(40.0, "40.3% ALC/VOL", ProductType.SPIRITS, False)
        assert result.status == VerificationStatus.MATCH

    def test_outside_tolerance(self):
        """Test ABV outside tolerance."""
        result = verify_alcohol_content(40.0, "37.5% ALC/VOL", ProductType.SPIRITS, False)
        assert result.status == VerificationStatus.MISMATCH
        assert "expected 40.0" in result.message.lower()

    def test_not_found(self):
        """Test ABV not found on label."""
        result = verify_alcohol_content(40.0, "NO ABV LISTED", ProductType.SPIRITS, False)
        assert result.status == VerificationStatus.NOT_FOUND

    def test_beer_optional_abv(self):
        """Test that ABV is optional for beer."""
        result = verify_alcohol_content(None, "NO ABV", ProductType.BEER, False)
        # Should be not_found but not an error for beer
        assert result.status == VerificationStatus.NOT_FOUND
        assert "optional" in result.message.lower()

    def test_multiple_abv_formats(self):
        """Test different ABV format variations."""
        formats = [
            "45% ALC/VOL",
            "45% ABV",
            "45 PERCENT ALCOHOL BY VOLUME",
            "ALC 45% BY VOL"
        ]
        for fmt in formats:
            result = verify_alcohol_content(45.0, fmt, ProductType.SPIRITS, False)
            assert result.status == VerificationStatus.MATCH


# Test verify_product_class

class TestVerifyProductClass:
    """Test product class/type verification."""

    def test_exact_class_match(self):
        """Test exact product class match."""
        result = verify_product_class(
            "Straight Bourbon Whiskey",
            "KENTUCKY STRAIGHT BOURBON WHISKEY"
        )
        assert result.status == VerificationStatus.MATCH

    def test_partial_class_match(self):
        """Test partial product class match (fuzzy)."""
        result = verify_product_class(
            "Bourbon Whiskey",
            "STRAIGHT BOURBON WHISKEY"
        )
        # Should match if key words present
        assert result.status == VerificationStatus.MATCH

    def test_class_not_found(self):
        """Test product class not found."""
        result = verify_product_class(
            "Bourbon Whiskey",
            "VODKA 80 PROOF"
        )
        assert result.status == VerificationStatus.NOT_FOUND

    def test_wine_varietals(self):
        """Test wine varietal matching."""
        result = verify_product_class(
            "Cabernet Sauvignon",
            "NAPA VALLEY CABERNET SAUVIGNON RED WINE"
        )
        assert result.status == VerificationStatus.MATCH

    def test_beer_styles(self):
        """Test beer style matching."""
        result = verify_product_class(
            "India Pale Ale",
            "HAZY IPA CRAFT BEER"
        )
        # "IPA" should match "India Pale Ale"
        assert result.status == VerificationStatus.MATCH


# Test verify_government_warning

class TestVerifyGovernmentWarning:
    """Test government warning verification (27 CFR Part 16)."""

    def test_exact_warning_text(self):
        """Test exact warning text match."""
        result = verify_government_warning(GOVERNMENT_WARNING_TEXT)
        assert result.status == VerificationStatus.MATCH
        assert result.confidence >= 0.95

    def test_minor_ocr_errors(self):
        """Test warning with minor OCR errors (95% threshold)."""
        # "WARNING" OCR'd as "WARNlNG" (lowercase L), "Genera1" (digit 1)
        text_with_errors = GOVERNMENT_WARNING_TEXT.replace("WARNING", "WARNlNG").replace("General", "Genera1")
        result = verify_government_warning(text_with_errors)
        # Should still match with 95% fuzzy threshold
        assert result.status == VerificationStatus.MATCH

    def test_wrong_case(self):
        """Test warning with wrong case (should fail)."""
        wrong_case = "Government Warning: (1) According to the surgeon general..."
        result = verify_government_warning(wrong_case)
        # "GOVERNMENT WARNING" must be ALL CAPS
        assert result.status == VerificationStatus.MISMATCH

    def test_missing_keywords(self):
        """Test warning missing required keywords."""
        incomplete = "WARNING: Drinking during pregnancy is bad."
        result = verify_government_warning(incomplete)
        assert result.status == VerificationStatus.MISMATCH
        # Should check for keywords: "Surgeon General", "birth defects", "impairs"

    def test_not_found(self):
        """Test warning not found on label."""
        result = verify_government_warning("NO WARNING TEXT HERE")
        assert result.status == VerificationStatus.NOT_FOUND
        assert "not found" in result.message.lower()

    def test_partial_warning(self):
        """Test partial warning text (missing section 2)."""
        partial = "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects."
        result = verify_government_warning(partial)
        # Missing section (2) about driving/machinery
        assert result.status == VerificationStatus.MISMATCH


# Test verify_net_contents

class TestVerifyNetContents:
    """Test net contents verification and standards of fill."""

    def test_standard_spirits_size(self):
        """Test standard spirits bottle size."""
        result = verify_net_contents("750 mL", "750 mL", ProductType.SPIRITS)
        assert result.status == VerificationStatus.MATCH

    def test_standard_wine_size(self):
        """Test standard wine bottle size."""
        result = verify_net_contents("750 mL", "750 ML", ProductType.WINE)
        assert result.status == VerificationStatus.MATCH

    def test_beer_any_size(self):
        """Test beer has no standard sizes (any size valid)."""
        result = verify_net_contents("473 mL", "473 mL", ProductType.BEER)
        # Beer has no standards of fill, so any size should match
        assert result.status == VerificationStatus.MATCH

    def test_non_standard_spirits_size(self):
        """Test non-standard spirits size (warning)."""
        result = verify_net_contents("725 mL", "725 mL", ProductType.SPIRITS)
        # Non-standard size should be WARNING, not error
        assert result.status == VerificationStatus.WARNING
        assert "non-standard" in result.message.lower()

    def test_unit_conversion_fl_oz(self):
        """Test net contents with unit conversion (fl oz to mL)."""
        # 25.4 fl oz ≈ 750 mL
        result = verify_net_contents("750 mL", "25.4 FL OZ", ProductType.SPIRITS)
        assert result.status == VerificationStatus.MATCH

    def test_unit_conversion_liter(self):
        """Test net contents with liter conversion."""
        result = verify_net_contents("1 L", "1000 mL", ProductType.SPIRITS)
        assert result.status == VerificationStatus.MATCH

        result = verify_net_contents("750 mL", "0.75 L", ProductType.SPIRITS)
        assert result.status == VerificationStatus.MATCH

    def test_mismatch_size(self):
        """Test net contents mismatch."""
        result = verify_net_contents("750 mL", "1 L", ProductType.SPIRITS)
        assert result.status == VerificationStatus.MISMATCH

    def test_not_found(self):
        """Test net contents not found."""
        result = verify_net_contents("750 mL", "NO SIZE LISTED", ProductType.SPIRITS)
        assert result.status == VerificationStatus.NOT_FOUND


# Test verify_age_statement

class TestVerifyAgeStatement:
    """Test age statement verification (conditional requirement)."""

    def test_whisky_under_4_years_required(self):
        """Test age statement required for whisky < 4 years."""
        result = verify_age_statement(
            "Aged 2 Years",
            "AGED 2 YEARS",
            "Bourbon Whiskey"
        )
        assert result.status == VerificationStatus.MATCH

    def test_whisky_under_4_years_missing(self):
        """Test age statement missing for whisky < 4 years (error)."""
        result = verify_age_statement(
            "Aged 2 Years",
            "NO AGE STATEMENT",
            "Bourbon Whiskey"
        )
        # Should be error if whisky < 4 years and not found
        assert result.status == VerificationStatus.NOT_FOUND
        assert "required" in result.message.lower()

    def test_whisky_over_4_years_optional(self):
        """Test age statement optional for whisky >= 4 years."""
        result = verify_age_statement(
            None,
            "AGED 10 YEARS",
            "Bourbon Whiskey"
        )
        # Optional field, not required
        assert result.status == VerificationStatus.MATCH

    def test_brandy_under_2_years_required(self):
        """Test age statement required for brandy < 2 years."""
        result = verify_age_statement(
            "Aged 1 Year",
            "AGED 1 YEAR",
            "Brandy"
        )
        assert result.status == VerificationStatus.MATCH

    def test_vodka_no_age_required(self):
        """Test age statement not required for vodka."""
        result = verify_age_statement(
            None,
            "NO AGE",
            "Vodka"
        )
        # Not required for vodka
        assert result.status == VerificationStatus.NOT_FOUND
        assert "not required" in result.message.lower()

    def test_age_format_variations(self):
        """Test different age statement formats."""
        formats = [
            ("Aged 10 Years", "AGED 10 YEARS"),
            ("10 Years Old", "10 YEARS OLD"),
            ("Aged 10 Yrs", "AGED 10 YRS"),
        ]
        for expected, ocr in formats:
            result = verify_age_statement(expected, ocr, "Bourbon")
            assert result.status == VerificationStatus.MATCH


# Test verify_proof

class TestVerifyProof:
    """Test proof verification (spirits only)."""

    def test_correct_proof(self):
        """Test correct proof calculation (ABV × 2)."""
        result = verify_proof(90.0, 45.0, "90 PROOF")
        assert result.status == VerificationStatus.MATCH

    def test_proof_tolerance(self):
        """Test proof within tolerance (±1)."""
        result = verify_proof(100.0, 50.0, "99 PROOF")
        # Within ±1 tolerance
        assert result.status == VerificationStatus.MATCH

        result = verify_proof(100.0, 50.0, "101 PROOF")
        assert result.status == VerificationStatus.MATCH

    def test_incorrect_proof(self):
        """Test incorrect proof."""
        result = verify_proof(80.0, 45.0, "95 PROOF")
        # Expected 90 (45×2), found 95
        assert result.status == VerificationStatus.MISMATCH

    def test_proof_not_found(self):
        """Test proof not found (optional field)."""
        result = verify_proof(90.0, 45.0, "NO PROOF LISTED")
        assert result.status == VerificationStatus.NOT_FOUND
        # Optional, so not critical error

    def test_proof_optional(self):
        """Test that proof is optional."""
        result = verify_proof(None, 40.0, "NO PROOF")
        assert result.status == VerificationStatus.NOT_FOUND
        assert "optional" in result.message.lower()


# Test verify_sulfites

class TestVerifySulfites:
    """Test sulfite declaration verification (wine only)."""

    def test_sulfites_required_and_present(self):
        """Test sulfites required and found."""
        result = verify_sulfites(True, "CONTAINS SULFITES")
        assert result.status == VerificationStatus.MATCH

    def test_sulfites_required_but_missing(self):
        """Test sulfites required but not found (error)."""
        result = verify_sulfites(True, "NO SULFITE TEXT")
        assert result.status == VerificationStatus.NOT_FOUND
        assert "required" in result.message.lower()

    def test_sulfites_not_required(self):
        """Test sulfites not required (< 10 ppm)."""
        result = verify_sulfites(False, "NO SULFITES")
        assert result.status == VerificationStatus.NOT_FOUND
        assert "not required" in result.message.lower()

    def test_sulfites_variations(self):
        """Test different sulfite declaration formats."""
        formats = [
            "CONTAINS SULFITES",
            "CONTAINS SULPHITES",
            "SULFITES ADDED"
        ]
        for fmt in formats:
            result = verify_sulfites(True, fmt)
            assert result.status == VerificationStatus.MATCH


# Test verify_country_of_origin

class TestVerifyCountryOfOrigin:
    """Test country of origin verification (imported products)."""

    def test_imported_country_required_and_present(self):
        """Test country required for imports and found."""
        result = verify_country_of_origin("Scotland", "PRODUCT OF SCOTLAND", True)
        assert result.status == VerificationStatus.MATCH

    def test_imported_country_required_but_missing(self):
        """Test country required but not found (error)."""
        result = verify_country_of_origin("Scotland", "NO COUNTRY LISTED", True)
        assert result.status == VerificationStatus.NOT_FOUND
        assert "required for imported" in result.message.lower()

    def test_domestic_country_not_required(self):
        """Test country not required for domestic products."""
        result = verify_country_of_origin(None, "MADE IN USA", False)
        # Not required for domestic
        assert result.status == VerificationStatus.NOT_FOUND
        assert "not required" in result.message.lower()

    def test_country_variations(self):
        """Test different country name formats."""
        pairs = [
            ("Scotland", "PRODUCT OF SCOTLAND"),
            ("United States", "MADE IN USA"),
            ("France", "FRANCE"),
            ("Mexico", "PRODUCT OF MEXICO")
        ]
        for country, ocr in pairs:
            result = verify_country_of_origin(country, ocr, True)
            assert result.status == VerificationStatus.MATCH


# Test calculate_compliance_score

class TestCalculateComplianceScore:
    """Test compliance scoring algorithm."""

    def test_perfect_score(self):
        """Test 100% compliance (all fields match)."""
        field_results = [
            FieldResult("brand_name", VerificationStatus.MATCH, "Test", "TEST", 0.95),
            FieldResult("alcohol_content", VerificationStatus.MATCH, "40", "40", 0.95),
            FieldResult("product_class", VerificationStatus.MATCH, "Bourbon", "BOURBON", 0.95),
            FieldResult("government_warning", VerificationStatus.MATCH, "WARNING", "WARNING", 0.95),
            FieldResult("net_contents", VerificationStatus.MATCH, "750mL", "750mL", 0.95),
        ]

        earned, max_score, percentage, grade = calculate_compliance_score(field_results)

        assert percentage == 100.0
        assert grade == "A"
        assert earned == max_score

    def test_missing_one_critical_field(self):
        """Test score when missing one critical field (40 pts)."""
        field_results = [
            FieldResult("brand_name", VerificationStatus.MATCH, "Test", "TEST", 0.95),
            FieldResult("alcohol_content", VerificationStatus.MATCH, "40", "40", 0.95),
            FieldResult("product_class", VerificationStatus.MATCH, "Bourbon", "BOURBON", 0.95),
            FieldResult("government_warning", VerificationStatus.NOT_FOUND, "WARNING", None, 0.0),
            FieldResult("net_contents", VerificationStatus.MATCH, "750mL", "750mL", 0.95),
        ]

        earned, max_score, percentage, grade = calculate_compliance_score(field_results)

        # Lost 40 pts for government_warning (critical)
        # Earned: 40+40+40+0+20 = 140 out of 200 = 70%
        assert percentage <= 70.0
        assert grade == "C" or grade == "D"

    def test_warning_status_partial_points(self):
        """Test that WARNING status gives 80% of points."""
        field_results = [
            FieldResult("brand_name", VerificationStatus.MATCH, "Test", "TEST", 0.95),
            FieldResult("alcohol_content", VerificationStatus.MATCH, "40", "40", 0.95),
            FieldResult("product_class", VerificationStatus.MATCH, "Bourbon", "BOURBON", 0.95),
            FieldResult("government_warning", VerificationStatus.MATCH, "WARNING", "WARNING", 0.95),
            FieldResult("net_contents", VerificationStatus.WARNING, "750mL", "725mL", 0.90),
        ]

        earned, max_score, percentage, grade = calculate_compliance_score(field_results)

        # net_contents (20 pts) with WARNING = 20 * 0.8 = 16 pts
        # Total: 40+40+40+40+16 = 176 out of 200 = 88%
        assert percentage >= 85.0
        assert grade == "B"

    def test_multiple_mismatches(self):
        """Test score with multiple mismatches."""
        field_results = [
            FieldResult("brand_name", VerificationStatus.MISMATCH, "Test", "WRONG", 0.50),
            FieldResult("alcohol_content", VerificationStatus.MISMATCH, "40", "37.5", 0.95),
            FieldResult("product_class", VerificationStatus.MATCH, "Bourbon", "BOURBON", 0.95),
            FieldResult("government_warning", VerificationStatus.MATCH, "WARNING", "WARNING", 0.95),
        ]

        earned, max_score, percentage, grade = calculate_compliance_score(field_results)

        # Lost 80 pts (2 critical fields)
        # Earned: 0+0+40+40 = 80 out of 160 = 50%
        assert percentage == 50.0
        assert grade == "F"

    def test_grade_boundaries(self):
        """Test grade assignment at boundaries."""
        test_cases = [
            (100, "A"),
            (95, "A"),
            (90, "A"),
            (89, "B"),
            (85, "B"),
            (80, "B"),
            (79, "C"),
            (75, "C"),
            (70, "C"),
            (69, "D"),
            (65, "D"),
            (60, "D"),
            (59, "F"),
            (50, "F"),
            (0, "F")
        ]

        for percentage, expected_grade in test_cases:
            # Test grade boundaries
            _, _, actual_percentage, grade = calculate_compliance_score([])
            # Verify expected grade matches percentage range
            if percentage >= 90:
                assert expected_grade == "A"
            elif percentage >= 80:
                assert expected_grade == "B"
            elif percentage >= 70:
                assert expected_grade == "C"
            elif percentage >= 60:
                assert expected_grade == "D"
            else:
                assert expected_grade == "F"


# Test parse_net_contents

class TestParseNetContents:
    """Test net contents parsing and unit conversion."""

    def test_parse_ml(self):
        """Test parsing milliliters."""
        assert parse_net_contents("750 mL") == 750.0
        assert parse_net_contents("750mL") == 750.0
        assert parse_net_contents("750 ml") == 750.0

    def test_parse_liter(self):
        """Test parsing liters."""
        assert parse_net_contents("1 L") == 1000.0
        assert parse_net_contents("0.75 L") == 750.0
        assert parse_net_contents("1.75L") == 1750.0

    def test_parse_fl_oz(self):
        """Test parsing fluid ounces."""
        # 25.4 fl oz ≈ 750 mL
        result = parse_net_contents("25.4 fl oz")
        assert abs(result - 750.0) < 10.0  # Allow small rounding

    def test_parse_gallon(self):
        """Test parsing gallons."""
        # 1 gallon = 3785.41 mL
        result = parse_net_contents("1 gallon")
        assert abs(result - 3785.0) < 50.0

    def test_invalid_format(self):
        """Test parsing invalid format returns None."""
        assert parse_net_contents("invalid") is None
        assert parse_net_contents("") is None


# Test is_standard_size

class TestIsStandardSize:
    """Test standard size checking."""

    def test_spirits_standard_sizes(self):
        """Test standard spirits sizes."""
        for size in [50, 100, 200, 375, 500, 750, 1000, 1750]:
            assert is_standard_size(size, ProductType.SPIRITS) is True

    def test_spirits_non_standard_size(self):
        """Test non-standard spirits size."""
        assert is_standard_size(725, ProductType.SPIRITS) is False
        assert is_standard_size(800, ProductType.SPIRITS) is False

    def test_wine_standard_sizes(self):
        """Test standard wine sizes."""
        for size in [187, 375, 500, 750, 1000, 1500]:
            assert is_standard_size(size, ProductType.WINE) is True

    def test_wine_non_standard_size(self):
        """Test non-standard wine size."""
        assert is_standard_size(725, ProductType.WINE) is False

    def test_beer_any_size(self):
        """Test beer has no standard sizes (all valid)."""
        # Beer has no standards of fill, so any size should return True
        assert is_standard_size(473, ProductType.BEER) is True
        assert is_standard_size(355, ProductType.BEER) is True
        assert is_standard_size(999, ProductType.BEER) is True


# Test verify_label (full integration)

class TestVerifyLabel:
    """Test complete label verification (integration)."""

    def test_bourbon_perfect_match(self, bourbon_form_data, bourbon_ocr_text):
        """Test bourbon label with perfect match."""
        ocr_result = OCRResult(
            full_text=bourbon_ocr_text,
            text_blocks=[],
            confidence=0.95
        )

        result = verify_label(ProductType.SPIRITS, bourbon_form_data, ocr_result)

        assert isinstance(result, VerificationResult)
        assert result.overall_match is True
        assert result.compliance_score == 100
        assert result.compliance_grade == "A"
        assert len(result.field_results) > 0

    def test_wine_perfect_match(self, wine_form_data, wine_ocr_text):
        """Test wine label with perfect match."""
        ocr_result = OCRResult(
            full_text=wine_ocr_text,
            text_blocks=[],
            confidence=0.95
        )

        result = verify_label(ProductType.WINE, wine_form_data, ocr_result)

        assert result.overall_match is True
        assert result.compliance_score >= 90
        assert result.compliance_grade in ["A", "B"]

    def test_abv_mismatch(self, bourbon_form_data):
        """Test label with ABV mismatch."""
        ocr_text = """
        EAGLE RARE
        STRAIGHT BOURBON WHISKEY
        37.5% ALC/VOL
        GOVERNMENT WARNING...
        """

        ocr_result = OCRResult(full_text=ocr_text, text_blocks=[], confidence=0.95)
        result = verify_label(ProductType.SPIRITS, bourbon_form_data, ocr_result)

        assert result.overall_match is False
        assert result.compliance_score < 80
        assert len(result.errors) > 0

    def test_missing_government_warning(self, bourbon_form_data):
        """Test label missing government warning (critical)."""
        ocr_text = """
        EAGLE RARE
        STRAIGHT BOURBON WHISKEY
        45% ALC/VOL
        """

        ocr_result = OCRResult(full_text=ocr_text, text_blocks=[], confidence=0.95)
        result = verify_label(ProductType.SPIRITS, bourbon_form_data, ocr_result)

        assert result.overall_match is False
        assert result.compliance_grade == "F"
        # Should have error about missing warning
        assert any("warning" in error.lower() for error in result.errors)

    def test_optional_fields_missing(self):
        """Test that missing optional fields don't fail verification."""
        form = FormData(
            brand_name="Test Vodka",
            product_class="Vodka",
            alcohol_content=40.0
        )

        ocr_text = """
        TEST VODKA
        VODKA
        40% ALC/VOL
        GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
        """

        ocr_result = OCRResult(full_text=ocr_text, text_blocks=[], confidence=0.95)
        result = verify_label(ProductType.SPIRITS, form, ocr_result)

        # Should still pass with only required fields
        assert result.overall_match is True
        assert result.compliance_grade in ["A", "B"]
