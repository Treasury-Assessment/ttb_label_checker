"""
TTB Label Verification System - Data Models

This module defines all data structures used throughout the backend verification system.
Uses Python dataclasses with type hints for type safety and clarity.

Author: TTB Label Verification System
Date: 2025-10-27
"""

from dataclasses import dataclass, field, asdict
from enum import Enum


class ProductType(Enum):
    """
    Alcohol beverage product type categories.

    These categories determine which TTB regulations apply:
    - SPIRITS: 27 CFR Part 5 (Distilled Spirits)
    - WINE: 27 CFR Part 4 (Wine)
    - BEER: 27 CFR Part 7 (Malt Beverages)
    """

    SPIRITS = "spirits"
    WINE = "wine"
    BEER = "beer"

    def __str__(self) -> str:
        return self.value


class VerificationStatus(Enum):
    """
    Status of individual field verification.

    - MATCH: Field value on label matches expected value
    - MISMATCH: Field value found but doesn't match expected
    - NOT_FOUND: Field not detected on label
    - WARNING: Field matches but has compliance warning (e.g., non-standard size)
    - ERROR: Verification failed due to processing error
    """

    MATCH = "match"
    MISMATCH = "mismatch"
    NOT_FOUND = "not_found"
    WARNING = "warning"
    ERROR = "error"

    def __str__(self) -> str:
        return self.value


@dataclass
class BoundingBox:
    """
    Rectangular bounding box coordinates for text location on label image.

    Coordinates represent the region where OCR detected text, used for
    visual highlighting in the frontend.

    Attributes:
        x: X-coordinate of top-left corner (pixels)
        y: Y-coordinate of top-left corner (pixels)
        width: Width of bounding box (pixels)
        height: Height of bounding box (pixels)
    """

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        """Validate bounding box coordinates."""
        if self.width < 0 or self.height < 0:
            raise ValueError("Width and height must be non-negative")
        if self.x < 0 or self.y < 0:
            raise ValueError("Coordinates must be non-negative")


@dataclass
class TextBlock:
    """
    OCR-detected text block with location and confidence.

    Represents a single piece of text extracted from the label image,
    including its location and OCR confidence score.

    Attributes:
        text: Extracted text content
        bounding_box: Location of text on image
        confidence: OCR confidence score (0.0-1.0)
    """

    text: str
    bounding_box: BoundingBox
    confidence: float

    def __post_init__(self):
        """Validate text block data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class FormData:
    """
    User-submitted product information for label verification.

    Contains all fields the user claims are on the label. Product-specific
    fields are optional and only validated if product type requires them.

    Required Fields (All Products):
        brand_name: Brand or trade name (e.g., "Jack Daniel's")
        product_class: Product class/type (e.g., "Bourbon Whiskey", "Cabernet Sauvignon", "IPA")
        alcohol_content: Alcohol by volume percentage (0-100)

    Common Optional Fields:
        net_contents: Volume with unit (e.g., "750 mL", "12 fl oz")
        bottler_name: Bottler, producer, or importer name
        address: Bottler/producer address (city, state)
        country_of_origin: Country name for imported products (required if is_imported=True)
        is_imported: Whether product is imported (triggers country_of_origin requirement)

    Spirits-Specific Fields:
        age_statement: Age declaration (e.g., "Aged 4 Years")
                      Required if: whisky <4 years OR brandy <2 years (27 CFR 5.74)
        proof: Alcohol proof (proof = ABV × 2), optional but verified if present
        state_of_distillation: U.S. state where distilled (optional)
        commodity_statement: Neutral spirits statement (optional, conditional)

    Wine-Specific Fields:
        vintage_year: Year grapes were harvested (4-digit year)
        contains_sulfites: Whether wine contains ≥10 ppm sulfites (requires "Contains Sulfites" declaration)
        appellation: Geographic wine region (e.g., "Napa Valley")

    Beer-Specific Fields:
        style: Beer style (e.g., "IPA", "Lager", "Stout")

    References:
        - 27 CFR Part 5: Distilled Spirits
        - 27 CFR Part 4: Wine
        - 27 CFR Part 7: Malt Beverages
    """

    # Required fields (all products)
    brand_name: str
    product_class: str
    alcohol_content: float

    # Common optional fields
    net_contents: str | None = None
    bottler_name: str | None = None
    address: str | None = None
    country_of_origin: str | None = None
    is_imported: bool | None = False

    # Spirits-specific fields
    age_statement: str | None = None
    proof: float | None = None
    state_of_distillation: str | None = None
    commodity_statement: str | None = None

    # Wine-specific fields
    vintage_year: int | None = None
    contains_sulfites: bool | None = False
    appellation: str | None = None

    # Beer-specific fields
    style: str | None = None

    def __post_init__(self):
        """Validate form data fields."""
        if not self.brand_name or len(self.brand_name.strip()) == 0:
            raise ValueError("brand_name cannot be empty")

        if not self.product_class or len(self.product_class.strip()) == 0:
            raise ValueError("product_class cannot be empty")

        if not 0.0 <= self.alcohol_content <= 100.0:
            raise ValueError("alcohol_content must be between 0 and 100")

        if self.proof is not None and self.proof < 0:
            raise ValueError("proof must be non-negative")

        if self.vintage_year is not None:
            if not 1800 <= self.vintage_year <= 2100:
                raise ValueError("vintage_year must be a valid 4-digit year")

    def to_dict(self) -> dict:
        """
        Convert FormData to dictionary representation.

        Returns:
            Dictionary with all non-None fields
        """
        # Use asdict and filter out None values
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None and v is not False}


@dataclass
class FieldResult:
    """
    Verification result for a single label field.

    Contains the comparison result between expected (form data) and found (OCR) values
    for one field, including confidence score and text location.

    Attributes:
        field_name: Name of the field being verified (e.g., "brand_name", "alcohol_content")
        status: Verification status (match, mismatch, not_found, warning, error)
        expected: Expected value from form data (as string)
        found: Actual value found on label via OCR (None if not found)
        confidence: Confidence score for this verification (0.0-1.0)
        location: Bounding box where text was found (None if not found)
        message: Human-readable explanation of result
        cfr_reference: Reference to applicable TTB regulation (e.g., "27 CFR 5.74")

    Examples:
        Match:
            FieldResult(
                field_name="brand_name",
                status=VerificationStatus.MATCH,
                expected="Jack Daniel's",
                found="Jack Daniel's",
                confidence=0.98,
                message="Brand name matches"
            )

        Mismatch:
            FieldResult(
                field_name="alcohol_content",
                status=VerificationStatus.MISMATCH,
                expected="45.0% ABV",
                found="40.0% ABV",
                confidence=0.95,
                message="ABV mismatch: Expected 45.0%, Found 40.0%"
            )

        Not Found:
            FieldResult(
                field_name="age_statement",
                status=VerificationStatus.NOT_FOUND,
                expected="Aged 4 Years",
                found=None,
                confidence=0.0,
                message="Age statement not detected on label"
            )

        Warning:
            FieldResult(
                field_name="net_contents",
                status=VerificationStatus.WARNING,
                expected="355 mL",
                found="355 mL",
                confidence=0.92,
                message="Volume matches (355mL) but non-standard size for spirits",
                cfr_reference="27 CFR 5.47a"
            )
    """

    field_name: str
    status: VerificationStatus
    expected: str
    found: str | None
    confidence: float
    location: BoundingBox | None = None
    message: str = ""
    cfr_reference: str | None = None

    def __post_init__(self):
        """Validate field result data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict:
        """
        Convert FieldResult to dictionary representation.

        Returns:
            Dictionary with all field result data
        """
        data = asdict(self)
        # Convert status enum to string
        data["status"] = str(self.status)
        # Convert location BoundingBox to dict if present
        if self.location:
            data["location"] = asdict(self.location)
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class OCRResult:
    """
    Complete OCR processing result from label image.

    Contains all text extracted from the label image, including individual
    text blocks with locations and overall processing metadata.

    Attributes:
        full_text: Complete extracted text (all blocks concatenated)
        text_blocks: List of individual text blocks with locations
        confidence: Overall OCR confidence score (0.0-1.0)
        processing_time_ms: Time taken for OCR processing (milliseconds)
        image_width: Original image width (pixels)
        image_height: Original image height (pixels)
    """

    full_text: str
    text_blocks: list[TextBlock]
    confidence: float
    processing_time_ms: float
    image_width: int
    image_height: int

    def __post_init__(self):
        """Validate OCR result data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.processing_time_ms < 0:
            raise ValueError("Processing time must be non-negative")
        if self.image_width <= 0 or self.image_height <= 0:
            raise ValueError("Image dimensions must be positive")


@dataclass
class VerificationResult:
    """
    Complete label verification result.

    Contains overall verification status, all field-by-field results,
    OCR data, and processing metadata. This is the final response
    returned by the verification API.

    Attributes:
        overall_match: Whether label passes verification (all critical fields match)
        confidence_score: Overall confidence score (0.0-1.0, weighted average)
        field_results: List of individual field verification results
        ocr_full_text: Complete text extracted from label (for debugging)
        processing_time_ms: Total processing time including OCR and verification
        compliance_score: Optional compliance score (0-100)
        compliance_grade: Optional compliance grade (A/B/C/D/F)
        warnings: List of non-critical warnings
        errors: List of critical errors (if any)

    Example:
        VerificationResult(
            overall_match=True,
            confidence_score=0.92,
            field_results=[...],
            ocr_full_text="Jack Daniel's Tennessee Whiskey...",
            processing_time_ms=2847.5,
            compliance_score=95,
            compliance_grade="A",
            warnings=["Non-standard bottle size for spirits"],
            errors=[]
        )
    """

    overall_match: bool
    confidence_score: float
    field_results: list[FieldResult]
    ocr_full_text: str
    processing_time_ms: float
    compliance_score: int | None = None
    compliance_grade: str | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate verification result data."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        if self.processing_time_ms < 0:
            raise ValueError("Processing time must be non-negative")
        if self.compliance_score is not None:
            if not 0 <= self.compliance_score <= 100:
                raise ValueError("Compliance score must be between 0 and 100")
        if self.compliance_grade is not None:
            if self.compliance_grade not in ["A", "B", "C", "D", "F"]:
                raise ValueError("Compliance grade must be A, B, C, D, or F")

    def to_dict(self) -> dict:
        """
        Convert VerificationResult to dictionary representation for API response.

        Returns:
            Dictionary with all verification result data
        """
        data = asdict(self)
        # Add status field
        data["status"] = "success"
        # Convert nested FieldResult objects to dicts
        data["field_results"] = [fr.to_dict() for fr in self.field_results]
        # Filter out None values except for lists (warnings/errors can be empty)
        return {
            k: v for k, v in data.items()
            if v is not None or k in ["warnings", "errors"]
        }

    def has_critical_errors(self) -> bool:
        """
        Check if verification has any critical errors.

        Critical errors include:
        - Missing government warning
        - Missing required fields (brand, ABV, class)
        - OCR confidence too low

        Returns:
            True if critical errors exist, False otherwise
        """
        return len(self.errors) > 0

    def get_failed_fields(self) -> list[FieldResult]:
        """
        Get list of fields that failed verification (mismatch or not found).

        Returns:
            List of FieldResult objects with status MISMATCH or NOT_FOUND
        """
        return [
            fr
            for fr in self.field_results
            if fr.status in [VerificationStatus.MISMATCH, VerificationStatus.NOT_FOUND]
        ]

    def get_warnings(self) -> list[FieldResult]:
        """
        Get list of fields with warnings (non-critical issues).

        Returns:
            List of FieldResult objects with status WARNING
        """
        return [fr for fr in self.field_results if fr.status == VerificationStatus.WARNING]


@dataclass
class ErrorResponse:
    """
    Error response for failed verification attempts.

    Used when verification cannot complete due to invalid input,
    OCR failure, or other processing errors.

    Attributes:
        status: Always "error"
        error_code: Machine-readable error code (e.g., "INVALID_IMAGE", "OCR_FAILED")
        message: Human-readable error message
        details: Optional additional error details (dict)

    Error Codes:
        INVALID_IMAGE: Unsupported format, corrupt file, or invalid image
        OCR_FAILED: Google Cloud Vision API error or low confidence
        INVALID_INPUT: Missing or invalid form fields
        INTERNAL_ERROR: Unexpected server error
        TIMEOUT: Processing exceeded time limit

    Example:
        ErrorResponse(
            status="error",
            error_code="INVALID_IMAGE",
            message="Image format not supported. Please use JPEG, PNG, or WebP.",
            details={"format_detected": "BMP", "supported_formats": ["JPEG", "PNG", "WebP"]}
        )
    """

    status: str = "error"
    error_code: str = ""
    message: str = ""
    details: dict | None = None

    def to_dict(self) -> dict:
        """
        Convert ErrorResponse to dictionary representation for API response.

        Returns:
            Dictionary with error data
        """
        data = asdict(self)
        # Filter out None values
        return {k: v for k, v in data.items() if v is not None}
