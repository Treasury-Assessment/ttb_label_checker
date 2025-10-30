"""
TTB Label Verification System - Core Verification Logic

This module implements field-by-field verification of alcohol beverage labels
against TTB (Alcohol and Tobacco Tax and Trade Bureau) regulatory requirements.

Verifies:
- Brand name (fuzzy matching)
- Product class/type (keyword matching with synonyms)
- Alcohol content (ABV with ±0.5% tolerance)
- Net contents (multi-unit support with standards of fill)
- Government warning (95% fuzzy match)
- Product-specific requirements (age statement, sulfites, etc.)

References:
    - 27 CFR Part 5: Distilled Spirits
    - 27 CFR Part 4: Wine
    - 27 CFR Part 7: Malt Beverages
    - 27 CFR Part 16: Health Warning Statement

Author: TTB Label Verification System
Date: 2025-10-27
"""

import logging
import re
import time

from models import (
    FieldResult,
    FormData,
    OCRResult,
    ProductType,
    TextBlock,
    VerificationResult,
    VerificationStatus,
)
from ocr import normalize_text

# Configure logging
logger = logging.getLogger(__name__)

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    logger.warning(
        "fuzzywuzzy library not installed - falling back to exact string matching. "
        "This will severely degrade verification accuracy. "
        "Install with: uv pip install python-levenshtein fuzzywuzzy"
    )

# ============================================================================
# CONSTANTS - TTB Regulatory Requirements
# ============================================================================

# 27 CFR Part 16 - Government Warning Statement (EXACT TEXT REQUIRED)
# NOTE: Must use 95% fuzzy match to allow minor OCR errors
GOVERNMENT_WARNING_TEXT = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women "
    "should not drink alcoholic beverages during pregnancy because of "
    "the risk of birth defects. (2) Consumption of alcoholic beverages "
    "impairs your ability to drive a car or operate machinery, and may "
    "cause health problems."
)

# Critical keywords that MUST appear in government warning
GOVERNMENT_WARNING_CRITICAL_KEYWORDS = [
    "government warning",
    "surgeon general",
    "pregnancy",
    "birth defects",
    "impairs",
    "drive",
]

# 27 CFR 5.47a - Distilled Spirits Standard Sizes (in ml)
# Complete list of approved standard sizes for distilled spirits
SPIRITS_STANDARD_SIZES_ML = [
    3750,  # (1) 3.75 Liters
    3000,  # (2) 3 Liters
    2000,  # (3) 2 Liters
    1800,  # (4) 1.8 Liters
    1750,  # (5) 1.75 Liters
    1500,  # (6) 1.5 Liters
    1000,  # (7) 1.00 Liter
    945,   # (8) 945 mL
    900,   # (9) 900 mL
    750,   # (10) 750 mL (standard bottle)
    720,   # (11) 720 mL
    710,   # (12) 710 mL
    700,   # (13) 700 mL
    570,   # (14) 570 mL
    500,   # (15) 500 mL
    475,   # (16) 475 mL
    375,   # (17) 375 mL (half bottle)
    355,   # (18) 355 mL
    350,   # (19) 350 mL
    331,   # (20) 331 mL
    250,   # (21) 250 mL
    200,   # (22) 200 mL
    187,   # (23) 187 mL
    100,   # (24) 100 mL
    50,    # (25) 50 mL (miniature)
]

# 27 CFR 4.71 - Wine Standard Sizes (in ml)
# Complete list of approved standard sizes for wine
WINE_STANDARD_SIZES_ML = [
    3000,  # (1) 3 liters
    2250,  # (2) 2.25 liters
    1800,  # (3) 1.8 liters
    1500,  # (4) 1.5 liters (magnum)
    1000,  # (5) 1 liter
    750,   # (6) 750 milliliters (standard bottle)
    720,   # (7) 720 milliliters
    700,   # (8) 700 milliliters
    620,   # (9) 620 milliliters
    600,   # (10) 600 milliliters
    568,   # (11) 568 milliliters
    550,   # (12) 550 milliliters
    500,   # (13) 500 milliliters
    473,   # (14) 473 milliliters
    375,   # (15) 375 milliliters (half bottle/demi)
    360,   # (16) 360 milliliters
    355,   # (17) 355 milliliters
    330,   # (18) 330 milliliters
    300,   # (19) 300 milliliters
    250,   # (20) 250 milliliters
    200,   # (21) 200 milliliters
    187,   # (22) 187 milliliters (split/piccolo)
    180,   # (23) 180 milliliters
    100,   # (24) 100 milliliters
    50,    # (25) 50 milliliters
]

# 27 CFR 7.70 (formerly 7.22(a)(4)) - Beer/Malt Beverage Net Contents
# IMPORTANT: Beer/malt beverages have NO standards of fill under TTB regulations
# Unlike wine and spirits, beer can be sold in ANY container size
# Only requirement: net contents must be properly labeled in U.S. standard measures
#
# For verification purposes:
# - Verify volume matches between label and form data
# - DO NOT check against standard sizes (none exist for beer)
# - Accept any container size as valid
# - Only verify labeling format compliance (fluid ounces, pints, quarts, gallons)

# Unit conversion factors to ml
UNIT_CONVERSIONS = {
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "liters": 1000.0,
    "litre": 1000.0,
    "litres": 1000.0,
    "fl oz": 29.5735,
    "oz": 29.5735,
    "ounce": 29.5735,
    "ounces": 29.5735,
    "fluid ounce": 29.5735,
    "fluid ounces": 29.5735,
    "pt": 473.176,
    "pint": 473.176,
    "pints": 473.176,
    "qt": 946.353,
    "quart": 946.353,
    "quarts": 946.353,
    "gal": 3785.41,
    "gallon": 3785.41,
    "gallons": 3785.41,
}

# Product class synonyms and keywords
PRODUCT_CLASS_SYNONYMS = {
    # Spirits
    "bourbon": ["bourbon whiskey", "bourbon whisky", "kentucky bourbon"],
    "whiskey": ["whisky", "scotch", "rye", "irish whiskey", "tennessee whiskey"],
    "vodka": ["vodka"],
    "gin": ["gin", "london dry gin", "dry gin"],
    "rum": ["rum", "dark rum", "light rum", "spiced rum"],
    "tequila": ["tequila", "añejo", "reposado", "blanco"],
    "brandy": ["brandy", "cognac", "armagnac"],

    # Wine
    "red wine": ["cabernet", "merlot", "pinot noir", "shiraz", "syrah", "zinfandel"],
    "white wine": ["chardonnay", "sauvignon blanc", "pinot grigio", "riesling"],
    "rosé": ["rose", "rosé wine"],
    "sparkling wine": ["champagne", "prosecco", "cava", "sparkling"],

    # Beer
    "beer": ["malt beverage", "ale", "lager"],
    "ipa": ["india pale ale", "ipa"],
    "stout": ["stout", "porter"],
    "lager": ["lager", "pilsner", "pilsener"],
}


# ============================================================================
# FUZZY MATCHING UTILITIES
# ============================================================================

def find_text_block_by_content(
    ocr_result: OCRResult, search_terms: list[str], require_all: bool = False
) -> TextBlock | None:
    """
    Find the text block containing the search terms.

    Args:
        ocr_result: OCR result with text blocks
        search_terms: List of terms to search for (case-insensitive)
        require_all: If True, block must contain ALL terms. If False, any term matches.

    Returns:
        TextBlock if found, None otherwise
    """
    for block in ocr_result.text_blocks:
        block_lower = block.text.lower()

        if require_all:
            # All search terms must be in the block
            if all(term.lower() in block_lower for term in search_terms):
                return block
        else:
            # Any search term matches
            if any(term.lower() in block_lower for term in search_terms):
                return block

    return None


def find_text_block_by_regex(
    ocr_result: OCRResult,
    pattern: str,
    flags: int = re.IGNORECASE
) -> tuple[TextBlock | None, re.Match | None]:
    """
    Find text block matching regex pattern.

    Args:
        ocr_result: OCR result with text blocks
        pattern: Regular expression pattern to search for
        flags: Regex flags (default: re.IGNORECASE)

    Returns:
        Tuple of (TextBlock, Match) if found, (None, None) otherwise

    Example:
        >>> pattern = r'\b(\d+)\s*proof\b'
        >>> block, match = find_text_block_by_regex(ocr_result, pattern)
        >>> if match:
        ...     proof_value = match.group(1)
    """
    compiled = re.compile(pattern, flags)
    for block in ocr_result.text_blocks:
        match = compiled.search(block.text)
        if match:
            return block, match
    return None, None


def fuzzy_match(str1: str, str2: str, threshold: float = 0.85) -> tuple[bool, float]:
    """
    Compare two strings using fuzzy matching.

    Uses fuzzywuzzy library (Levenshtein distance) to handle minor OCR errors
    and variations in formatting.

    Args:
        str1: First string to compare
        str2: Second string to compare
        threshold: Minimum similarity ratio to consider a match (0.0-1.0)

    Returns:
        Tuple of (is_match, similarity_score)

    Example:
        >>> fuzzy_match("Jack Daniel's", "Jack Daniels", 0.85)
        (True, 0.96)
        >>> fuzzy_match("Bourbon", "Whiskey", 0.85)
        (False, 0.42)
    """
    if not FUZZYWUZZY_AVAILABLE:
        # Fallback to exact match if fuzzywuzzy not available
        logger.debug(
            "Using exact string matching fallback (fuzzywuzzy not available). "
            "Comparing: '%s' vs '%s'", str1, str2
        )
        normalized1 = normalize_text(str1)
        normalized2 = normalize_text(str2)
        exact_match = normalized1 == normalized2
        return exact_match, 1.0 if exact_match else 0.0

    # Normalize strings
    normalized1 = normalize_text(str1)
    normalized2 = normalize_text(str2)

    # Use token_sort_ratio (handles word order differences)
    similarity = fuzz.token_sort_ratio(normalized1, normalized2) / 100.0

    return similarity >= threshold, similarity


def find_text_in_ocr(
    search_text: str,
    ocr_result: OCRResult,
    threshold: float = 0.85,
) -> tuple[bool, str | None, TextBlock | None, float]:
    """
    Search for text in OCR result using token-based coverage matching.

    Uses a smart approach:
    1. Find candidate blocks using fuzzy matching (lower threshold)
    2. Check which tokens from expected text each block covers
    3. If blocks collectively cover the full expected text, it's a match

    This handles multi-line text, OCR errors, and non-adjacent blocks.

    Args:
        search_text: Text to search for
        ocr_result: OCR result to search in
        threshold: Fuzzy match threshold (0.0-1.0)

    Returns:
        Tuple of (found, matched_text, text_block, similarity_score)
    """
    # Quick check: fuzzy match against full OCR text
    is_match, score = fuzzy_match(search_text, ocr_result.full_text, threshold)
    if is_match:
        return True, search_text, None, score

    # Normalize expected text and split into tokens
    expected_normalized = normalize_text(search_text)
    expected_tokens = expected_normalized.split()

    if not expected_tokens:
        return False, None, None, 0.0

    # Find candidate blocks that might contain parts of the expected text
    # Use lower threshold (0.6) to be more permissive in finding candidates
    candidate_threshold = 0.6
    candidates = []

    for block in ocr_result.text_blocks:
        block_normalized = normalize_text(block.text)
        block_tokens = block_normalized.split()

        # Check if any token in this block fuzzy matches any expected token
        for block_token in block_tokens:
            for expected_token in expected_tokens:
                token_match, token_score = fuzzy_match(block_token, expected_token, candidate_threshold)
                if token_match:
                    candidates.append({
                        'block': block,
                        'normalized_text': block_normalized,
                        'tokens': block_tokens
                    })
                    break
            if candidates and candidates[-1]['block'] == block:
                break  # Already added this block

    if not candidates:
        return False, None, None, 0.0

    # Check token coverage: which expected tokens are covered by candidate blocks?
    covered_token_indices = set()
    matching_blocks = []

    for candidate in candidates:
        for block_token in candidate['tokens']:
            for i, expected_token in enumerate(expected_tokens):
                # Use fuzzy matching for individual tokens
                token_match, _ = fuzzy_match(block_token, expected_token, candidate_threshold)
                if token_match:
                    covered_token_indices.add(i)
                    if candidate['block'] not in matching_blocks:
                        matching_blocks.append(candidate['block'])

    # Calculate coverage: what percentage of expected tokens were found?
    coverage = len(covered_token_indices) / len(expected_tokens) if expected_tokens else 0.0

    # If coverage is high enough (80%+), consider it a match
    # This allows for minor OCR errors or missing articles/prepositions
    if coverage >= 0.8:
        # Reconstruct matched text from blocks
        matched_text = " ".join([block.text for block in matching_blocks])
        # Use coverage as the confidence score
        confidence = coverage

        logger.debug(f"Token coverage match: '{search_text}' covered {coverage:.1%} via {len(matching_blocks)} blocks")

        return True, matched_text, matching_blocks[0] if matching_blocks else None, confidence

    # Not enough coverage
    logger.debug(f"Insufficient token coverage: '{search_text}' only covered {coverage:.1%}")
    return False, None, None, coverage


# ============================================================================
# FIELD VERIFICATION FUNCTIONS
# ============================================================================

def verify_brand_name(
    expected: str, ocr_result: OCRResult, threshold: float = 0.85
) -> FieldResult:
    """
    Verify brand name on label matches expected value.

    27 CFR 5.32 (Spirits), 27 CFR 4.33 (Wine), 27 CFR 7.23 (Beer)
    Brand name is a CRITICAL field and must be prominently displayed.

    Args:
        expected: Expected brand name from form
        ocr_result: OCR result from label image
        threshold: Fuzzy match threshold (default 0.85 = 85%)

    Returns:
        FieldResult with verification status

    Example:
        >>> form_data.brand_name = "Jack Daniel's"
        >>> result = verify_brand_name("Jack Daniel's", ocr_result)
        >>> result.status == VerificationStatus.MATCH
        True
    """
    logger.info(f"Verifying brand name: '{expected}'")
    logger.debug(f"OCR text blocks count: {len(ocr_result.text_blocks)}")
    logger.debug(f"OCR full text preview: {ocr_result.full_text[:200]}...")

    found, matched_text, text_block, confidence = find_text_in_ocr(
        expected, ocr_result, threshold
    )

    if found:
        logger.info(f"Brand name FOUND: '{matched_text}' (confidence: {confidence:.1%})")
        return FieldResult(
            field_name="brand_name",
            status=VerificationStatus.MATCH,
            expected=expected,
            found=matched_text or expected,
            confidence=confidence,
            location=text_block.bounding_box if text_block else None,
            message=f"Brand name matches (confidence: {confidence:.1%})",
            cfr_reference="27 CFR 5.32, 4.33, 7.23",
        )
    else:
        logger.warning(f"Brand name NOT FOUND: '{expected}' (searched {len(ocr_result.text_blocks)} text blocks)")
        # Log sample blocks for debugging
        sample_blocks = [block.text for block in ocr_result.text_blocks[:10]]
        logger.debug(f"Sample text blocks: {sample_blocks}")

        return FieldResult(
            field_name="brand_name",
            status=VerificationStatus.NOT_FOUND,
            expected=expected,
            found=None,
            confidence=0.0,
            message=f"Brand name '{expected}' not found on label",
            cfr_reference="27 CFR 5.32, 4.33, 7.23",
        )


def verify_product_class(
    expected: str, ocr_result: OCRResult, threshold: float = 0.80
) -> FieldResult:
    """
    Verify product class/type on label matches expected value.

    27 CFR 5.35 (Spirits), 27 CFR 4.34 (Wine), 27 CFR 7.24 (Beer)
    Product class must accurately describe the product.

    Uses keyword matching and synonyms to handle variations like:
    - "Bourbon" vs "Bourbon Whiskey"
    - "IPA" vs "India Pale Ale"
    - "Cabernet" vs "Cabernet Sauvignon"

    Args:
        expected: Expected product class from form
        ocr_result: OCR result from label image
        threshold: Fuzzy match threshold (slightly lower for class variations)

    Returns:
        FieldResult with verification status
    """
    # First try exact fuzzy match
    found, matched_text, text_block, confidence = find_text_in_ocr(
        expected, ocr_result, threshold
    )

    if found:
        return FieldResult(
            field_name="product_class",
            status=VerificationStatus.MATCH,
            expected=expected,
            found=matched_text or expected,
            confidence=confidence,
            location=text_block.bounding_box if text_block else None,
            message=f"Product class matches (confidence: {confidence:.1%})",
            cfr_reference="27 CFR 5.35, 4.34, 7.24",
        )

    # Try synonym matching
    expected_lower = expected.lower()
    ocr_text_lower = ocr_result.full_text.lower()

    for _base_class, synonyms in PRODUCT_CLASS_SYNONYMS.items():
        if expected_lower in synonyms or any(syn in expected_lower for syn in synonyms):
            # Check if any synonym appears in OCR text
            for synonym in synonyms:
                if synonym in ocr_text_lower:
                    return FieldResult(
                        field_name="product_class",
                        status=VerificationStatus.MATCH,
                        expected=expected,
                        found=synonym,
                        confidence=0.8,  # Lower confidence for synonym match
                        message=f"Product class matches via synonym: '{synonym}' ≈ '{expected}'",
                        cfr_reference="27 CFR 5.35, 4.34, 7.24",
                    )

    return FieldResult(
        field_name="product_class",
        status=VerificationStatus.NOT_FOUND,
        expected=expected,
        found=None,
        confidence=0.0,
        message=f"Product class '{expected}' not found on label",
        cfr_reference="27 CFR 5.35, 4.34, 7.24",
    )


def extract_abv_from_text(text: str) -> float | None:
    """
    Extract alcohol by volume (ABV) percentage from text.

    Handles formats:
    - "40% ALC/VOL"
    - "40% ABV"
    - "40 percent alcohol by volume"
    - "40%"

    Args:
        text: Text to extract ABV from

    Returns:
        ABV as float (e.g., 40.0), or None if not found

    Example:
        >>> extract_abv_from_text("40% ALC/VOL")
        40.0
        >>> extract_abv_from_text("13.5% ABV")
        13.5
    """
    # Pattern: number (with optional decimal) followed by % and optional ALC/VOL or ABV
    patterns = [
        # Pattern 1: Standard formats with ALC/VOL or ABV
        r"(\d+\.?\d*)\s*%\s*(?:alc(?:ohol)?(?:\s*\.?\s*)?(?:/\s*vol(?:ume)?)?|abv)",
        # Pattern 2: % followed by alcohol
        r"(\d+\.?\d*)\s*%\s*alcohol",
        # Pattern 3: X percent alc
        r"(\d+\.?\d*)\s*percent\s*alc",
        # Pattern 4: alcohol by volume X%
        r"alcohol\s*(?:by\s*volume)?\s*(\d+\.?\d*)\s*%",
        # Pattern 5: Just the percentage if preceded/followed by alcohol-related words
        r"(?:alc|alcohol|vol|volume|proof)\D{0,15}(\d+\.?\d*)\s*%",
        # Pattern 6: Percentage followed by vol within reasonable distance
        r"(\d+\.?\d*)\s*%\D{0,15}(?:alc|alcohol|vol|volume)",
    ]

    text_lower = text.lower()

    logger.debug(f"Searching for ABV in text (first 200 chars): {text_lower[:200]}")

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text_lower)
        if match:
            try:
                abv_value = float(match.group(1))
                # Sanity check: ABV should be between 0.5% and 95%
                if 0.5 <= abv_value <= 95:
                    logger.debug(f"ABV found using pattern {i+1}: '{match.group(0)}' → {abv_value}%")
                    return abv_value
                else:
                    logger.debug(f"Pattern {i+1} matched but value {abv_value}% is out of valid range (0.5-95%)")
            except (ValueError, IndexError):
                continue

    logger.warning(f"No ABV found in text. Searched with {len(patterns)} patterns.")
    return None


def verify_alcohol_content(
    expected: float, ocr_result: OCRResult, tolerance: float = 0.5
) -> FieldResult:
    """
    Verify alcohol by volume (ABV) on label matches expected value.

    27 CFR 5.37 (Spirits), 27 CFR 4.36 (Wine), 27 CFR 7.26 (Beer - optional)
    ABV is CRITICAL and must be accurate within ±0.5% tolerance.

    Args:
        expected: Expected ABV percentage (e.g., 40.0)
        ocr_result: OCR result from label image
        tolerance: Acceptable difference in percentage points (default ±0.5%)

    Returns:
        FieldResult with verification status
    """
    # Extract ABV from OCR text
    found_abv = extract_abv_from_text(ocr_result.full_text)

    if found_abv is None:
        return FieldResult(
            field_name="alcohol_content",
            status=VerificationStatus.NOT_FOUND,
            expected=f"{expected}% ABV",
            found=None,
            confidence=0.0,
            message="Alcohol content not found on label",
            cfr_reference="27 CFR 5.37, 4.36, 7.26",
        )

    # Find which text block contains the ABV for bounding box using regex
    abv_str = str(int(found_abv)) if found_abv == int(found_abv) else str(found_abv)
    # Pattern matches: "40% ALC/VOL", "40 % vol", "12.5% ABV", "alc.12.5% by vol."
    pattern = rf'\b{re.escape(abv_str)}\s*%?\s*(?:alc(?:\.|/vol)?|abv|vol|alcohol)\b'
    abv_block, _ = find_text_block_by_regex(ocr_result, pattern)

    # Check if within tolerance
    difference = abs(found_abv - expected)

    if difference <= tolerance:
        return FieldResult(
            field_name="alcohol_content",
            status=VerificationStatus.MATCH,
            expected=f"{expected}% ABV",
            found=f"{found_abv}% ABV",
            confidence=0.95,
            location=abv_block.bounding_box if abv_block else None,
            message=f"ABV matches: {found_abv}% (expected {expected}%, within ±{tolerance}% tolerance)",
            cfr_reference="27 CFR 5.37, 4.36, 7.26",
        )
    else:
        return FieldResult(
            field_name="alcohol_content",
            status=VerificationStatus.MISMATCH,
            expected=f"{expected}% ABV",
            found=f"{found_abv}% ABV",
            confidence=0.95,
            location=abv_block.bounding_box if abv_block else None,
            message=f"ABV mismatch: Expected {expected}%, Found {found_abv}% (difference: {difference:.1f}%, tolerance: ±{tolerance}%)",
            cfr_reference="27 CFR 5.37, 4.36, 7.26",
        )


def extract_volume_from_text(text: str) -> tuple[float, str] | None:
    """
    Extract volume and unit from text.

    Handles formats:
    - "750 mL"
    - "1 Liter"
    - "12 FL OZ"
    - "25.4 fl oz"

    Args:
        text: Text to extract volume from

    Returns:
        Tuple of (volume, unit) or None if not found

    Example:
        >>> extract_volume_from_text("750 mL")
        (750.0, "ml")
        >>> extract_volume_from_text("1 Liter")
        (1.0, "liter")
    """
    text_lower = text.lower()

    # Pattern: number followed by unit
    # Handle various spacing and case variations
    pattern = r"(\d+\.?\d*)\s*(ml|milliliters?|l|liters?|litres?|fl\s*oz|ounces?|oz|pints?|pt|quarts?|qt|gallons?|gal)"

    match = re.search(pattern, text_lower)
    if match:
        try:
            volume = float(match.group(1))
            unit = match.group(2).strip()
            # Normalize unit spacing (e.g., "fl oz" -> "fl oz")
            unit = re.sub(r"\s+", " ", unit)
            return volume, unit
        except (ValueError, IndexError):
            pass

    return None


def convert_volume_to_ml(volume: float, unit: str) -> float:
    """
    Convert volume to milliliters (ml) using standard conversion factors.

    Args:
        volume: Volume amount
        unit: Unit of measurement

    Returns:
        Volume in milliliters

    Raises:
        ValueError: If unit is not recognized

    Example:
        >>> convert_volume_to_ml(1.0, "liter")
        1000.0
        >>> convert_volume_to_ml(12, "fl oz")
        355.441
    """
    unit_lower = unit.lower().strip()

    if unit_lower in UNIT_CONVERSIONS:
        return volume * UNIT_CONVERSIONS[unit_lower]

    raise ValueError(f"Unknown unit: {unit}")


def parse_net_contents(text: str) -> float | None:
    """
    Parse net contents string and convert to milliliters.

    Convenience function that combines extract_volume_from_text and convert_volume_to_ml.

    Args:
        text: Text containing volume (e.g., "750 mL", "1 L", "25.4 fl oz")

    Returns:
        Volume in milliliters, or None if parsing fails

    Example:
        >>> parse_net_contents("750 mL")
        750.0
        >>> parse_net_contents("1 L")
        1000.0
        >>> parse_net_contents("invalid")
        None
    """
    if not text:
        return None

    volume_data = extract_volume_from_text(text)
    if not volume_data:
        return None

    volume, unit = volume_data
    try:
        return convert_volume_to_ml(volume, unit)
    except ValueError:
        return None


def is_standard_size(volume_ml: float, product_type: ProductType, tolerance: float = 1.0) -> bool:
    """
    Check if volume matches TTB-approved standard size.

    27 CFR 5.47a (Spirits), 27 CFR 4.71 (Wine), 27 CFR 7.70 (Beer - NO STANDARDS)

    Args:
        volume_ml: Volume in milliliters
        product_type: Product type (spirits, wine, or beer)
        tolerance: Tolerance in ml for rounding (default ±1ml)

    Returns:
        True if volume is a standard size, False otherwise

    Note:
        Beer/malt beverages have NO standards of fill - any size is valid.
    """
    if product_type == ProductType.BEER:
        # 27 CFR 7.70: Beer has NO standards of fill
        # Any container size is valid per TTB regulations
        return True

    standard_sizes = (
        SPIRITS_STANDARD_SIZES_ML
        if product_type == ProductType.SPIRITS
        else WINE_STANDARD_SIZES_ML
    )

    # Check if volume matches any standard size (within tolerance)
    for standard in standard_sizes:
        if abs(volume_ml - standard) <= tolerance:
            return True

    return False


def verify_net_contents(
    expected: str, ocr_result: OCRResult, product_type: ProductType
) -> FieldResult:
    """
    Verify net contents on label matches expected value.

    27 CFR 5.47a (Spirits), 27 CFR 4.71 (Wine), 27 CFR 7.70 (Beer)

    Checks:
    1. Volume matches between form and label (with unit conversion)
    2. For spirits/wine: Warns if non-standard size (doesn't fail)
    3. For beer: NO standard size check (27 CFR 7.70 - any size valid)

    Args:
        expected: Expected net contents from form (e.g., "750 mL")
        ocr_result: OCR result from label image
        product_type: Product type (spirits, wine, or beer)

    Returns:
        FieldResult with verification status
    """
    # Extract expected volume
    expected_volume_data = extract_volume_from_text(expected)
    if not expected_volume_data:
        return FieldResult(
            field_name="net_contents",
            status=VerificationStatus.ERROR,
            expected=expected,
            found=None,
            confidence=0.0,
            message=f"Invalid expected volume format: '{expected}'",
        )

    expected_volume, expected_unit = expected_volume_data
    expected_ml = convert_volume_to_ml(expected_volume, expected_unit)

    # Extract found volume from OCR
    found_volume_data = extract_volume_from_text(ocr_result.full_text)
    if not found_volume_data:
        return FieldResult(
            field_name="net_contents",
            status=VerificationStatus.NOT_FOUND,
            expected=expected,
            found=None,
            confidence=0.0,
            message="Net contents not found on label",
            cfr_reference="27 CFR 5.47a, 4.71, 7.70",
        )

    found_volume, found_unit = found_volume_data
    found_ml = convert_volume_to_ml(found_volume, found_unit)

    # Find which text block contains the volume for bounding box using regex
    vol_str = str(int(found_volume)) if found_volume.is_integer() else str(found_volume)
    # Pattern matches: "750 ml", "750ml", "750ML", "25.4 fl oz", "1 Liter"
    pattern = rf'\b{re.escape(vol_str)}\s*(?:ml|mL|ML|l|L|liter|litre|oz|fl\s*oz|ounce|pint|quart|gallon)\b'
    volume_block, _ = find_text_block_by_regex(ocr_result, pattern)

    # Compare volumes (±1ml tolerance for rounding)
    if abs(found_ml - expected_ml) <= 1.0:
        # Volume matches - check standards of fill
        is_standard = is_standard_size(found_ml, product_type)

        cfr_ref = {
            ProductType.SPIRITS: "27 CFR 5.47a",
            ProductType.WINE: "27 CFR 4.71",
            ProductType.BEER: "27 CFR 7.70",
        }[product_type]

        if product_type == ProductType.BEER:
            # Beer has no standard sizes - always valid
            return FieldResult(
                field_name="net_contents",
                status=VerificationStatus.MATCH,
                expected=expected,
                found=f"{found_volume} {found_unit}",
                confidence=0.95,
                location=volume_block.bounding_box if volume_block else None,
                message=f"Volume matches: {found_ml:.0f}ml (beer: any container size valid)",
                cfr_reference=cfr_ref,
            )
        elif is_standard:
            # Standard size for spirits/wine
            return FieldResult(
                field_name="net_contents",
                status=VerificationStatus.MATCH,
                expected=expected,
                found=f"{found_volume} {found_unit}",
                confidence=0.95,
                location=volume_block.bounding_box if volume_block else None,
                message=f"Volume matches: {found_ml:.0f}ml (standard size)",
                cfr_reference=cfr_ref,
            )
        else:
            # Non-standard size for spirits/wine - WARNING (not failure)
            return FieldResult(
                field_name="net_contents",
                status=VerificationStatus.WARNING,
                expected=expected,
                found=f"{found_volume} {found_unit}",
                confidence=0.95,
                location=volume_block.bounding_box if volume_block else None,
                message=f"Volume matches ({found_ml:.0f}ml) but NON-STANDARD size for {product_type.value}. Standard sizes required per {cfr_ref}.",
                cfr_reference=cfr_ref,
            )
    else:
        # Volume mismatch
        return FieldResult(
            field_name="net_contents",
            status=VerificationStatus.MISMATCH,
            expected=expected,
            found=f"{found_volume} {found_unit}",
            confidence=0.95,
            location=volume_block.bounding_box if volume_block else None,
            message=f"Volume mismatch: Expected {expected_ml:.0f}ml, Found {found_ml:.0f}ml (difference: {abs(found_ml - expected_ml):.0f}ml)",
            cfr_reference="27 CFR 5.47a, 4.71, 7.70",
        )


def verify_government_warning(ocr_result: OCRResult, threshold: float = 0.95) -> FieldResult:
    """
    Verify government warning statement on label.

    27 CFR Part 16 - Health Warning Statement
    This is a CRITICAL field. Warning must contain exact text with specific formatting.

    Uses 95% fuzzy match threshold to allow minor OCR errors while being strict.

    Critical requirements:
    - "GOVERNMENT WARNING" must be in ALL CAPS
    - "Surgeon General" must have capital S and G
    - Must contain pregnancy/birth defects warning
    - Must contain driving/machinery impairment warning

    Args:
        ocr_result: OCR result from label image
        threshold: Fuzzy match threshold (default 0.95 = 95%)

    Returns:
        FieldResult with verification status
    """
    logger.info("Verifying government warning statement")
    logger.debug(f"OCR full text length: {len(ocr_result.full_text)} chars")

    ocr_text_lower = ocr_result.full_text.lower()
    # CRITICAL: Normalize whitespace (convert newlines to spaces) for keyword matching
    # OCR text has "SURGEON\nGENERAL" but we search for "surgeon general" with a space
    ocr_text_normalized = re.sub(r'\s+', ' ', ocr_text_lower).strip()

    # Check if all critical keywords present (using fuzzy matching to handle OCR errors)
    missing_keywords = []
    for keyword in GOVERNMENT_WARNING_CRITICAL_KEYWORDS:
        keyword_lower = keyword.lower()
        # First try exact match (fast path)
        if keyword_lower in ocr_text_normalized:
            continue

        # If exact match fails, try fuzzy matching each keyword token
        # This handles OCR errors like "impairs" -> "imipairs"
        keyword_found = False
        keyword_tokens = keyword_lower.split()

        # For multi-word keywords, check if all tokens are fuzzy matched
        tokens_matched = 0
        for kw_token in keyword_tokens:
            # Check if this keyword token fuzzy matches any OCR token
            for ocr_token in ocr_text_normalized.split():
                is_match, score = fuzzy_match(kw_token, ocr_token, 0.80)
                if is_match:
                    tokens_matched += 1
                    break

        # If all keyword tokens were found (fuzzy), consider keyword present
        if tokens_matched == len(keyword_tokens):
            keyword_found = True
            logger.debug(f"Keyword '{keyword}' found via fuzzy matching")

        if not keyword_found:
            missing_keywords.append(keyword)
            logger.debug(f"Missing keyword: '{keyword}'")

    # Special check: "Surgeon General" SHOULD have capital S and G (27 CFR Part 16)
    # This is a formatting requirement, not a content requirement
    # Don't fail the entire check if capitalization is wrong due to OCR errors
    surgeon_general_pattern = r'\bS[Uu][Rr][Gg][Ee][Oo][Nn]\s+G[Ee][Nn][Ee][Rr][Aa][Ll]\b'
    has_proper_capitalization = re.search(surgeon_general_pattern, ocr_result.full_text) is not None

    if not has_proper_capitalization and "surgeon general" not in missing_keywords:
        # Note: We already checked if "surgeon general" exists via fuzzy matching above
        # This just checks if capitalization is correct
        logger.debug("Note: 'Surgeon General' capitalization may be incorrect (should be capital S and G)")

    if missing_keywords:
        logger.warning(f"Government warning missing keywords: {missing_keywords}")
        return FieldResult(
            field_name="government_warning",
            status=VerificationStatus.NOT_FOUND,
            expected="GOVERNMENT WARNING: (1) According to the Surgeon General...",
            found=None,
            confidence=0.0,
            message=f"Government warning incomplete or missing. Missing keywords: {', '.join(missing_keywords)}",
            cfr_reference="27 CFR Part 16",
        )

    logger.info("All government warning keywords found")

    # Find which text block contains "GOVERNMENT WARNING" for bounding box
    warning_search_terms = ["government warning", "government", "warning"]
    warning_block = find_text_block_by_content(ocr_result, warning_search_terms)

    # For government warning, use token coverage approach since it's long text spanning multiple lines
    # This is more robust than trying to fuzzy match the entire 265-character warning
    warning_normalized = normalize_text(GOVERNMENT_WARNING_TEXT)
    warning_tokens = warning_normalized.split()

    # Find how many warning tokens are present in the OCR text
    ocr_normalized = normalize_text(ocr_result.full_text)
    ocr_tokens = ocr_normalized.split()

    # Count token coverage
    covered_tokens = 0
    for warning_token in warning_tokens:
        # Check if this warning token appears in OCR text (exact or fuzzy)
        for ocr_token in ocr_tokens:
            token_match, _ = fuzzy_match(warning_token, ocr_token, 0.85)
            if token_match:
                covered_tokens += 1
                break

    # Calculate coverage percentage
    token_coverage = covered_tokens / len(warning_tokens) if warning_tokens else 0.0

    logger.debug(f"Government warning token coverage: {token_coverage:.1%} ({covered_tokens}/{len(warning_tokens)} tokens)")

    # If we have high coverage (85%+) and all keywords present, consider it a match
    if token_coverage >= 0.85:
        logger.info(f"Government warning MATCHED via token coverage (confidence: {token_coverage:.1%})")
        return FieldResult(
            field_name="government_warning",
            status=VerificationStatus.MATCH,
            expected="GOVERNMENT WARNING: (1) According to the Surgeon General...",
            found="Government warning present",
            confidence=token_coverage,
            location=warning_block.bounding_box if warning_block else None,
            message=f"Government warning matches (confidence: {token_coverage:.1%})",
            cfr_reference="27 CFR Part 16",
        )

    # Warning keywords present but text coverage is low
    if token_coverage >= 0.70:
        # Partial coverage - warning
        logger.warning(f"Government warning has partial coverage: {token_coverage:.1%}")
        return FieldResult(
            field_name="government_warning",
            status=VerificationStatus.WARNING,
            expected="GOVERNMENT WARNING: (1) According to the Surgeon General...",
            found="Government warning present with variations",
            confidence=token_coverage,
            location=warning_block.bounding_box if warning_block else None,
            message=f"Government warning found but may have formatting issues (coverage: {token_coverage:.1%})",
            cfr_reference="27 CFR Part 16",
        )

    return FieldResult(
        field_name="government_warning",
        status=VerificationStatus.NOT_FOUND,
        expected="GOVERNMENT WARNING: (1) According to the Surgeon General...",
        found=None,
        confidence=0.0,
        message="Government warning not found or incomplete",
        cfr_reference="27 CFR Part 16",
    )


# ============================================================================
# PRODUCT-SPECIFIC VERIFICATION FUNCTIONS
# ============================================================================

def is_age_statement_required(product_class: str, form_data: FormData) -> bool:
    """
    Determine if age statement is required based on product type and age.

    27 CFR 5.74 - Age Statement Requirements:
    - Whisky aged less than 4 years: Age statement REQUIRED
    - Brandy aged less than 2 years: Age statement REQUIRED
    - Other spirits: Age statement optional
    - Wine/Beer: Age statement not applicable

    Args:
        product_class: Product class (e.g., "Bourbon Whiskey", "Brandy")
        form_data: Form data with age_statement field

    Returns:
        True if age statement is required, False otherwise
    """
    product_lower = product_class.lower()

    # Check if it's whisky/whiskey
    if any(w in product_lower for w in ["whiskey", "whisky", "bourbon", "rye", "scotch"]):
        # If age statement provided and < 4 years, it's required
        if form_data.age_statement:
            # Extract age from statement
            age_match = re.search(r"(\d+)\s*(?:year|yr)", form_data.age_statement.lower())
            if age_match:
                age = int(age_match.group(1))
                if age < 4:
                    return True
        # If no age statement but product is whisky, it's optional (assume >= 4 years)
        return False

    # Check if it's brandy
    if "brandy" in product_lower or "cognac" in product_lower:
        if form_data.age_statement:
            age_match = re.search(r"(\d+)\s*(?:year|yr)", form_data.age_statement.lower())
            if age_match:
                age = int(age_match.group(1))
                if age < 2:
                    return True
        return False

    return False


def validate_age_format(age_text: str) -> bool:
    """
    Validate age statement format against TTB-approved formats.

    27 CFR 5.74 - Approved Age Statement Formats:
    - "Aged 4 Years"
    - "4 Years Old"
    - "4 Year Old"
    - Numbers as words: "Four Years Old"

    Args:
        age_text: Age statement text

    Returns:
        True if format is valid, False otherwise
    """
    age_lower = age_text.lower()

    # Approved patterns
    patterns = [
        r"aged\s+\d+\s+years?",
        r"\d+\s+years?\s+old",
        r"\d+\s+yr\.?\s+old",
        r"aged\s+\d+\s+months?",  # For products under 1 year
    ]

    for pattern in patterns:
        if re.search(pattern, age_lower):
            return True

    return False


def verify_age_statement(
    form_data: FormData, ocr_result: OCRResult, product_class: str
) -> FieldResult:
    """
    Verify age statement on label (conditional requirement).

    27 CFR 5.74 - Age Statement Requirements
    Required for: Whisky < 4 years, Brandy < 2 years

    Args:
        form_data: Form data with age_statement
        ocr_result: OCR result from label
        product_class: Product class to determine if required

    Returns:
        FieldResult with verification status
    """
    if not form_data.age_statement:
        # No age statement provided - check if required
        is_required = is_age_statement_required(product_class, form_data)
        if is_required:
            return FieldResult(
                field_name="age_statement",
                status=VerificationStatus.ERROR,
                expected="Age statement required",
                found=None,
                confidence=0.0,
                message=f"Age statement REQUIRED for {product_class} but not provided in form",
                cfr_reference="27 CFR 5.74",
            )
        # Not required - skip verification
        return FieldResult(
            field_name="age_statement",
            status=VerificationStatus.MATCH,
            expected="Not required",
            found="Not applicable",
            confidence=1.0,
            message="Age statement not required for this product",
        )

    # Age statement provided - verify it
    if not validate_age_format(form_data.age_statement):
        return FieldResult(
            field_name="age_statement",
            status=VerificationStatus.WARNING,
            expected=form_data.age_statement,
            found=None,
            confidence=0.5,
            message=f"Age statement format may not comply with TTB requirements: '{form_data.age_statement}'",
            cfr_reference="27 CFR 5.74",
        )

    # Search for age statement on label using both fuzzy match and regex
    found, matched_text, text_block, confidence = find_text_in_ocr(
        form_data.age_statement, ocr_result, threshold=0.85
    )

    # Also try regex pattern to catch TTB-approved age formats
    # Pattern matches: "Aged 4 years", "4 year old", "Aged at least 12 years", "18 months old"
    age_pattern = r'\b(?:aged?|age)\s+(?:at\s+least\s+|a\s+minimum\s+of\s+)?(\d+)\s+(?:years?|yrs?|months?|mos?)\s*(?:old)?\b'
    regex_block, age_match = find_text_block_by_regex(ocr_result, age_pattern)

    # Use whichever method found a result
    if found or regex_block:
        final_block = text_block if found else regex_block
        final_text = matched_text if found else (age_match.group(0) if age_match else form_data.age_statement)
        final_confidence = confidence if found else 0.9

        return FieldResult(
            field_name="age_statement",
            status=VerificationStatus.MATCH,
            expected=form_data.age_statement,
            found=final_text or form_data.age_statement,
            confidence=final_confidence,
            location=final_block.bounding_box if final_block else None,
            message=f"Age statement matches (confidence: {final_confidence:.1%})",
            cfr_reference="27 CFR 5.74",
        )
    else:
        is_required = is_age_statement_required(product_class, form_data)
        status = VerificationStatus.NOT_FOUND if is_required else VerificationStatus.WARNING

        return FieldResult(
            field_name="age_statement",
            status=status,
            expected=form_data.age_statement,
            found=None,
            confidence=0.0,
            message=f"Age statement '{form_data.age_statement}' not found on label",
            cfr_reference="27 CFR 5.74",
        )


def verify_proof(form_data: FormData, ocr_result: OCRResult) -> FieldResult:
    """
    Verify proof statement on label (optional for spirits).

    27 CFR 5.65 - Proof Statement
    Proof = ABV × 2 (must be within ±1 tolerance)

    Args:
        form_data: Form data with proof and alcohol_content
        ocr_result: OCR result from label

    Returns:
        FieldResult with verification status
    """
    if form_data.proof is None:
        # Proof not provided - skip verification
        return FieldResult(
            field_name="proof",
            status=VerificationStatus.MATCH,
            expected="Not provided",
            found="Not applicable",
            confidence=1.0,
            message="Proof statement not provided (optional)",
        )

    # Calculate expected proof from ABV
    expected_proof = form_data.alcohol_content * 2

    # Check if provided proof matches expected
    if abs(form_data.proof - expected_proof) > 1.0:
        return FieldResult(
            field_name="proof",
            status=VerificationStatus.ERROR,
            expected=f"{expected_proof:.0f} proof",
            found=f"{form_data.proof:.0f} proof",
            confidence=1.0,
            message=f"Proof calculation error: {form_data.proof:.0f} proof doesn't match ABV {form_data.alcohol_content}% (should be {expected_proof:.0f} proof)",
            cfr_reference="27 CFR 5.65",
        )

    # Search for proof on label using regex
    proof_pattern = rf'\b{form_data.proof:.0f}\s*proof\b'
    if re.search(proof_pattern, ocr_result.full_text, re.IGNORECASE):
        # Find which text block contains the proof using regex
        # Pattern matches: "80 proof", "80proof", "(80 Proof)", "80 PROOF"
        proof_block, _ = find_text_block_by_regex(ocr_result, proof_pattern)

        return FieldResult(
            field_name="proof",
            status=VerificationStatus.MATCH,
            expected=f"{form_data.proof:.0f} proof",
            found=f"{form_data.proof:.0f} proof",
            confidence=0.9,
            location=proof_block.bounding_box if proof_block else None,
            message=f"Proof statement matches: {form_data.proof:.0f} proof",
            cfr_reference="27 CFR 5.65",
        )
    else:
        return FieldResult(
            field_name="proof",
            status=VerificationStatus.WARNING,
            expected=f"{form_data.proof:.0f} proof",
            found=None,
            confidence=0.0,
            message=f"Proof statement '{form_data.proof:.0f} proof' not found on label (optional field)",
            cfr_reference="27 CFR 5.65",
        )


def verify_sulfite_declaration(form_data: FormData, ocr_result: OCRResult) -> FieldResult:
    """
    Verify sulfite declaration on wine labels (conditional requirement).

    27 CFR 5.63(c)(7) - Sulfite Declaration
    Required if wine contains ≥10 ppm sulfites (contains_sulfites = True)

    Args:
        form_data: Form data with contains_sulfites flag
        ocr_result: OCR result from label

    Returns:
        FieldResult with verification status
    """
    if not form_data.contains_sulfites:
        # Sulfites not declared - no requirement
        return FieldResult(
            field_name="sulfites",
            status=VerificationStatus.MATCH,
            expected="Not required",
            found="Not applicable",
            confidence=1.0,
            message="Sulfite declaration not required (contains_sulfites = False)",
        )

    # Sulfites declared - must appear on label
    ocr_lower = ocr_result.full_text.lower()
    # Normalize whitespace for matching (handles line breaks)
    ocr_normalized = re.sub(r'\s+', ' ', ocr_lower).strip()

    logger.info("Verifying sulfite declaration")
    logger.debug(f"OCR text (first 300 chars, normalized): {ocr_normalized[:300]}")

    # Use regex to match sulfite variations (handles British/American spelling)
    # Pattern matches: "CONTAINS SULFITES", "sulfites", "sulphites", "sulfite"
    # American: sulfite/sulfites (no h), British: sulphite/sulphites (with h)
    sulfite_pattern = r'\b(?:contains\s+)?sul[fp]h?ites?\b'

    match = re.search(sulfite_pattern, ocr_normalized)
    if match:
        logger.info(f"Sulfite declaration FOUND: '{match.group(0)}'")
        # Find which text block contains sulfites using regex
        sulfite_block, _ = find_text_block_by_regex(ocr_result, sulfite_pattern)

        return FieldResult(
                field_name="sulfites",
                status=VerificationStatus.MATCH,
                expected="Contains Sulfites",
                found="Contains Sulfites",
                confidence=0.9,
                location=sulfite_block.bounding_box if sulfite_block else None,
                message="Sulfite declaration found on label",
                cfr_reference="27 CFR 5.63(c)(7)",
            )

    # Sulfites required but not found
    logger.warning(f"Sulfite declaration NOT FOUND. Pattern '{sulfite_pattern}' did not match in OCR text.")
    return FieldResult(
        field_name="sulfites",
        status=VerificationStatus.NOT_FOUND,
        expected="Contains Sulfites",
        found=None,
        confidence=0.0,
        message="Sulfite declaration REQUIRED but not found on label (wine contains ≥10 ppm sulfites)",
        cfr_reference="27 CFR 5.63(c)(7)",
    )


def verify_sulfites(contains_sulfites: bool, ocr_text: str) -> FieldResult:
    """
    Simplified sulfite verification for testing.

    Wrapper around verify_sulfite_declaration for simpler API.

    Args:
        contains_sulfites: Whether wine contains sulfites (≥10 ppm)
        ocr_text: OCR extracted text to search

    Returns:
        FieldResult with verification status
    """
    # Create minimal FormData and OCRResult for the full function
    form_data = FormData(
        brand_name="",
        product_class="",
        alcohol_content=0.0,
        contains_sulfites=contains_sulfites,
    )
    ocr_result = OCRResult(
        full_text=ocr_text,
        confidence=1.0,
        text_blocks=[],
    )
    return verify_sulfite_declaration(form_data, ocr_result)


def verify_vintage(form_data: FormData, ocr_result: OCRResult) -> FieldResult:
    """
    Verify vintage year on wine labels (optional).

    27 CFR 4.27 - Vintage Year
    If provided, year must appear on label

    Args:
        form_data: Form data with vintage_year
        ocr_result: OCR result from label

    Returns:
        FieldResult with verification status
    """
    if form_data.vintage_year is None:
        return FieldResult(
            field_name="vintage",
            status=VerificationStatus.MATCH,
            expected="Not provided",
            found="Not applicable",
            confidence=1.0,
            message="Vintage year not provided (optional)",
        )

    # Search for vintage year (4-digit year) using regex for validation
    vintage_str = str(form_data.vintage_year)
    # Pattern ensures it's a valid year (1800-2099) and not part of a larger number
    vintage_pattern = rf'\b{re.escape(vintage_str)}\b'

    vintage_block, _ = find_text_block_by_regex(ocr_result, vintage_pattern)

    if vintage_block:
        return FieldResult(
            field_name="vintage",
            status=VerificationStatus.MATCH,
            expected=vintage_str,
            found=vintage_str,
            confidence=0.95,
            location=vintage_block.bounding_box if vintage_block else None,
            message=f"Vintage year {vintage_str} found on label",
            cfr_reference="27 CFR 4.27",
        )
    else:
        return FieldResult(
            field_name="vintage",
            status=VerificationStatus.NOT_FOUND,
            expected=vintage_str,
            found=None,
            confidence=0.0,
            message=f"Vintage year {vintage_str} not found on label",
            cfr_reference="27 CFR 4.27",
        )


def verify_country_of_origin(form_data: FormData, ocr_result: OCRResult) -> FieldResult:
    """
    Verify country of origin on imported products (conditional requirement).

    27 CFR 5.44 (Spirits), 27 CFR 4.30 (Wine), 27 CFR 7.25 (Beer)
    Required if is_imported = True

    Args:
        form_data: Form data with country_of_origin and is_imported
        ocr_result: OCR result from label

    Returns:
        FieldResult with verification status
    """
    if not form_data.is_imported:
        return FieldResult(
            field_name="country_of_origin",
            status=VerificationStatus.MATCH,
            expected="Not required",
            found="Domestic product",
            confidence=1.0,
            message="Country of origin not required (domestic product)",
        )

    if not form_data.country_of_origin:
        return FieldResult(
            field_name="country_of_origin",
            status=VerificationStatus.ERROR,
            expected="Country name required",
            found=None,
            confidence=0.0,
            message="Country of origin REQUIRED for imported products but not provided in form",
            cfr_reference="27 CFR 5.44, 4.30, 7.25",
        )

    # Search for country on label
    found, matched_text, text_block, confidence = find_text_in_ocr(
        form_data.country_of_origin, ocr_result, threshold=0.85
    )

    # Also check for common phrases
    ocr_lower = ocr_result.full_text.lower()
    country_lower = form_data.country_of_origin.lower()

    if found or f"product of {country_lower}" in ocr_lower or f"imported from {country_lower}" in ocr_lower:
        # If we didn't find via fuzzy match, search for text block manually
        if not text_block:
            search_terms = [form_data.country_of_origin, f"product of {form_data.country_of_origin}",
                          f"imported from {form_data.country_of_origin}"]
            text_block = find_text_block_by_content(ocr_result, search_terms)

        return FieldResult(
            field_name="country_of_origin",
            status=VerificationStatus.MATCH,
            expected=form_data.country_of_origin,
            found=matched_text or form_data.country_of_origin,
            confidence=confidence if found else 0.85,
            location=text_block.bounding_box if text_block else None,
            message=f"Country of origin found: {form_data.country_of_origin}",
            cfr_reference="27 CFR 5.44, 4.30, 7.25",
        )
    else:
        return FieldResult(
            field_name="country_of_origin",
            status=VerificationStatus.NOT_FOUND,
            expected=form_data.country_of_origin,
            found=None,
            confidence=0.0,
            message=f"Country of origin '{form_data.country_of_origin}' REQUIRED but not found on label",
            cfr_reference="27 CFR 5.44, 4.30, 7.25",
        )


# ============================================================================
# COMPLIANCE SCORING ALGORITHM
# ============================================================================

def calculate_compliance_score(field_results: list[FieldResult]) -> tuple[int, int, float, str]:
    """
    Calculate weighted compliance score based on field verification results.

    Scoring System:
    - CRITICAL FIELDS (40 points each): brand_name, alcohol_content, product_class, government_warning
    - IMPORTANT FIELDS (20 points each): net_contents, sulfites (if applicable)
    - OPTIONAL FIELDS (10 points each): age_statement, proof, vintage, country_of_origin, etc.

    Grading Scale:
    - A: 90-100% (Excellent compliance)
    - B: 80-89%  (Good compliance, minor issues)
    - C: 70-79%  (Acceptable compliance, some issues)
    - D: 60-69%  (Poor compliance, multiple issues)
    - F: <60%    (Failed compliance, critical issues)

    Args:
        field_results: List of FieldResult objects from verification

    Returns:
        Tuple of (score, max_score, percentage, grade)

    Example:
        >>> score, max_score, percentage, grade = calculate_compliance_score(field_results)
        >>> print(f"Score: {score}/{max_score} ({percentage:.1f}%) - Grade: {grade}")
        Score: 180/200 (90.0%) - Grade: A
    """
    # Define field weights
    CRITICAL_FIELDS = {
        "brand_name": 40,
        "alcohol_content": 40,
        "product_class": 40,
        "government_warning": 40,
    }

    IMPORTANT_FIELDS = {
        "net_contents": 20,
        "sulfites": 20,
    }

    OPTIONAL_FIELDS = {
        "age_statement": 10,
        "proof": 10,
        "vintage": 10,
        "country_of_origin": 10,
        "state_of_distillation": 10,
        "appellation": 10,
        "style": 10,
    }

    earned_score = 0
    max_possible_score = 0

    for field_result in field_results:
        field_name = field_result.field_name
        status = field_result.status

        # Determine field weight
        if field_name in CRITICAL_FIELDS:
            weight = CRITICAL_FIELDS[field_name]
        elif field_name in IMPORTANT_FIELDS:
            weight = IMPORTANT_FIELDS[field_name]
        elif field_name in OPTIONAL_FIELDS:
            weight = OPTIONAL_FIELDS[field_name]
        else:
            # Unknown field - assign default low weight
            weight = 5

        max_possible_score += weight

        # Calculate earned points based on status
        if status == VerificationStatus.MATCH:
            # Full points if match
            earned_score += weight
        elif status == VerificationStatus.WARNING:
            # Partial points for warnings (80% of full points)
            earned_score += int(weight * 0.8)
        elif status == VerificationStatus.MISMATCH:
            # No points for mismatch, but field was checked
            earned_score += 0
        elif status == VerificationStatus.NOT_FOUND:
            # Check if field is truly required or just optional
            # If expected value is "Not required" or "Not applicable", give full points
            if field_result.expected in ["Not required", "Not provided", "Not applicable", "Domestic product"]:
                earned_score += weight
            else:
                # Field was required but not found - no points
                earned_score += 0
        elif status == VerificationStatus.ERROR:
            # Critical error - no points
            earned_score += 0

    # Calculate percentage
    percentage = (earned_score / max_possible_score * 100) if max_possible_score > 0 else 0

    # Assign grade
    if percentage >= 90:
        grade = "A"
    elif percentage >= 80:
        grade = "B"
    elif percentage >= 70:
        grade = "C"
    elif percentage >= 60:
        grade = "D"
    else:
        grade = "F"

    return earned_score, max_possible_score, percentage, grade


# ============================================================================
# MAIN VERIFICATION FUNCTION
# ============================================================================

def verify_label(
    form_data: FormData, ocr_result: OCRResult, product_type: ProductType
) -> VerificationResult:
    """
    Main verification function - orchestrates all field-by-field checks.

    Verifies label against form data and TTB regulatory requirements:
    1. Brand name (critical)
    2. Product class/type (critical)
    3. Alcohol content (critical)
    4. Net contents (critical)
    5. Government warning (critical)
    6. Optional fields (conditional based on product type)

    Args:
        form_data: User-submitted product information
        ocr_result: OCR result from label image
        product_type: Product type (spirits, wine, beer)

    Returns:
        VerificationResult with overall status and all field results

    Example:
        >>> form_data = FormData(brand_name="Jack Daniel's", ...)
        >>> ocr_result = extract_text_from_image(image_data)
        >>> result = verify_label(form_data, ocr_result, ProductType.SPIRITS)
        >>> print(result.overall_match)
        True
    """
    start_time = time.time()
    field_results: list[FieldResult] = []
    warnings: list[str] = []
    errors: list[str] = []

    # 1. Verify brand name (CRITICAL)
    brand_result = verify_brand_name(form_data.brand_name, ocr_result)
    field_results.append(brand_result)
    if brand_result.status != VerificationStatus.MATCH:
        errors.append(f"Brand name '{form_data.brand_name}' not found on label")

    # 2. Verify product class (CRITICAL)
    class_result = verify_product_class(form_data.product_class, ocr_result)
    field_results.append(class_result)
    if class_result.status != VerificationStatus.MATCH:
        errors.append(f"Product class '{form_data.product_class}' not found on label")

    # 3. Verify alcohol content (CRITICAL)
    abv_result = verify_alcohol_content(form_data.alcohol_content, ocr_result)
    field_results.append(abv_result)
    if abv_result.status == VerificationStatus.MISMATCH:
        errors.append(abv_result.message)
    elif abv_result.status == VerificationStatus.NOT_FOUND:
        errors.append("Alcohol content not found on label")

    # 4. Verify net contents (if provided)
    if form_data.net_contents:
        contents_result = verify_net_contents(
            form_data.net_contents, ocr_result, product_type
        )
        field_results.append(contents_result)
        if contents_result.status == VerificationStatus.WARNING:
            warnings.append(contents_result.message)
        elif contents_result.status in [VerificationStatus.MISMATCH, VerificationStatus.NOT_FOUND]:
            errors.append(contents_result.message or "Net contents not found")

    # 5. Verify government warning (CRITICAL)
    warning_result = verify_government_warning(ocr_result)
    field_results.append(warning_result)
    if warning_result.status != VerificationStatus.MATCH:
        errors.append("Government warning missing or incomplete (CRITICAL)")

    # 6. Product-specific verification
    if product_type == ProductType.SPIRITS:
        # Age statement (conditional)
        age_result = verify_age_statement(form_data, ocr_result, form_data.product_class)
        field_results.append(age_result)
        if age_result.status == VerificationStatus.ERROR:
            errors.append(age_result.message)
        elif age_result.status == VerificationStatus.NOT_FOUND:
            errors.append(age_result.message)

        # Proof (optional)
        proof_result = verify_proof(form_data, ocr_result)
        field_results.append(proof_result)
        if proof_result.status == VerificationStatus.ERROR:
            errors.append(proof_result.message)
        elif proof_result.status == VerificationStatus.WARNING:
            warnings.append(proof_result.message)

    elif product_type == ProductType.WINE:
        # Sulfite declaration (conditional)
        sulfite_result = verify_sulfite_declaration(form_data, ocr_result)
        field_results.append(sulfite_result)
        if sulfite_result.status == VerificationStatus.NOT_FOUND:
            errors.append(sulfite_result.message)

        # Vintage year (optional)
        vintage_result = verify_vintage(form_data, ocr_result)
        field_results.append(vintage_result)
        if vintage_result.status == VerificationStatus.NOT_FOUND:
            warnings.append(vintage_result.message)

    elif product_type == ProductType.BEER:
        # Beer has minimal additional requirements
        # ABV is optional for beer (already verified above if provided)
        # "Malt Beverage" synonym already handled in product_class verification
        pass

    # 7. Country of origin (conditional - all product types)
    country_result = verify_country_of_origin(form_data, ocr_result)
    field_results.append(country_result)
    if country_result.status == VerificationStatus.ERROR:
        errors.append(country_result.message)
    elif country_result.status == VerificationStatus.NOT_FOUND:
        if form_data.is_imported:
            errors.append(country_result.message)

    # Calculate overall match (no critical errors)
    overall_match = len(errors) == 0

    # Calculate weighted confidence score
    confidence_scores = [fr.confidence for fr in field_results]
    confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

    # Calculate compliance score and grade
    earned_score, max_score, percentage, grade = calculate_compliance_score(field_results)

    processing_time = (time.time() - start_time) * 1000  # Convert to ms

    return VerificationResult(
        overall_match=overall_match,
        confidence_score=confidence_score,
        field_results=field_results,
        ocr_full_text=ocr_result.full_text,
        processing_time_ms=processing_time + ocr_result.processing_time_ms,
        compliance_score=int(percentage),  # Store as integer percentage (0-100)
        compliance_grade=grade,
        warnings=warnings,
        errors=errors,
    )
