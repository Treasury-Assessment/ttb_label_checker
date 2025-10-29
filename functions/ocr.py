"""
TTB Label Verification System - OCR Processing Module

This module handles all OCR (Optical Character Recognition) operations using
Google Cloud Vision API for text extraction from alcohol label images.

Features:
- Base64 image decoding and validation
- Google Cloud Vision API integration
- Text normalization and error correction
- Bounding box extraction for visual highlighting
- Optional Tesseract OCR fallback (future)

Author: TTB Label Verification System
Date: 2025-10-27
References:
    - Google Cloud Vision API: https://cloud.google.com/vision/docs
    - PIL/Pillow: https://pillow.readthedocs.io
"""

import base64
import io
import os
import re
import time

from PIL import Image

try:
    from google.cloud import vision
    VISION_API_AVAILABLE = True
except ImportError:
    VISION_API_AVAILABLE = False
    print("Warning: google-cloud-vision not installed. OCR will not work.")

from models import BoundingBox, OCRResult, TextBlock

# Configuration defaults
DEFAULT_SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "HEIC"}
DEFAULT_MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MIN_IMAGE_DIMENSION = 100  # Minimum width/height in pixels
MAX_IMAGE_DIMENSION = 10000  # Maximum width/height in pixels
DEFAULT_CONFIDENCE_THRESHOLD = 0.7

# Environment variables (with defaults)
SUPPORTED_FORMATS = set(
    os.getenv("SUPPORTED_FORMATS", "JPEG,PNG,WEBP,HEIC").upper().split(",")
) if os.getenv("SUPPORTED_FORMATS") else DEFAULT_SUPPORTED_FORMATS

MAX_IMAGE_SIZE = int(
    os.getenv("MAX_IMAGE_SIZE", str(DEFAULT_MAX_IMAGE_SIZE))
)

CONFIDENCE_THRESHOLD = float(
    os.getenv("OCR_CONFIDENCE_THRESHOLD", str(DEFAULT_CONFIDENCE_THRESHOLD))
)


class OCRError(Exception):
    """Base exception for OCR processing errors."""
    pass


class InvalidImageError(OCRError):
    """Raised when image is invalid, corrupt, or unsupported format."""
    pass


class OCRProcessingError(OCRError):
    """Raised when OCR processing fails."""
    pass


def validate_and_decode_image(base64_str: str) -> Image.Image:
    """
    Decode and validate base64-encoded image.

    Validates:
    - Base64 decoding succeeds
    - Image format is supported (JPEG, PNG, WebP, HEIC)
    - Image is not corrupt
    - Image size is within limits
    - Image dimensions are reasonable

    Args:
        base64_str: Base64-encoded image string (with or without data URI prefix)

    Returns:
        PIL Image object

    Raises:
        InvalidImageError: If image is invalid, corrupt, or unsupported

    Example:
        >>> image_data = "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
        >>> image = validate_and_decode_image(image_data)
        >>> print(image.format, image.size)
        JPEG (1200, 900)
    """
    try:
        # Remove data URI prefix if present
        if "," in base64_str and base64_str.startswith("data:"):
            base64_str = base64_str.split(",", 1)[1]

        # Decode base64
        try:
            image_bytes = base64.b64decode(base64_str)
        except Exception as e:
            raise InvalidImageError(f"Invalid base64 encoding: {str(e)}") from e

        # Check file size
        if len(image_bytes) > MAX_IMAGE_SIZE:
            size_mb = len(image_bytes) / (1024 * 1024)
            raise InvalidImageError(
                f"Image too large: {size_mb:.1f}MB (max {MAX_IMAGE_SIZE / (1024 * 1024)}MB)"
            )

        # Open image with PIL
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise InvalidImageError(f"Cannot open image: {str(e)}") from e

        # Validate format
        if image.format not in SUPPORTED_FORMATS:
            raise InvalidImageError(
                f"Unsupported format '{image.format}'. Supported: {', '.join(SUPPORTED_FORMATS)}"
            )

        # Validate dimensions
        width, height = image.size
        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            raise InvalidImageError(
                f"Image too small: {width}x{height}px (min {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}px)"
            )
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise InvalidImageError(
                f"Image too large: {width}x{height}px (max {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}px)"
            )

        # Convert to RGB if necessary (some formats like PNG can have RGBA)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        return image

    except InvalidImageError:
        raise
    except Exception as e:
        raise InvalidImageError(f"Image validation failed: {str(e)}") from e


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocess image for better OCR accuracy.

    Operations:
    - Resize if very large (to reduce processing time)
    - Enhance contrast (optional, can improve OCR)
    - Convert to grayscale (optional, can improve OCR)

    Args:
        image: PIL Image object

    Returns:
        Preprocessed PIL Image object

    Note:
        For MVP, minimal preprocessing. Can enhance later for better OCR accuracy.
    """
    # For MVP, just ensure reasonable size (don't send 20MP images to API)
    MAX_DIMENSION = 4000
    width, height = image.size

    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        # Calculate scale factor
        scale = MAX_DIMENSION / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Resize using high-quality resampling
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Future enhancements:
    # - Auto-rotate based on EXIF orientation
    # - Enhance contrast using PIL.ImageEnhance
    # - Denoise using PIL filters
    # - Convert to grayscale if needed

    return image


def extract_text_vision_api(image: Image.Image) -> OCRResult:
    """
    Extract text from image using Google Cloud Vision API.

    Uses TEXT_DETECTION feature which is optimized for dense text
    (like labels) compared to DOCUMENT_TEXT_DETECTION.

    Args:
        image: PIL Image object

    Returns:
        OCRResult with full text, text blocks, and metadata

    Raises:
        OCRProcessingError: If Vision API call fails or returns low confidence

    Example:
        >>> image = Image.open("label.jpg")
        >>> result = extract_text_vision_api(image)
        >>> print(result.full_text)
        Jack Daniel's Tennessee Whiskey
        40% ALC/VOL
        GOVERNMENT WARNING: ...
    """
    if not VISION_API_AVAILABLE:
        raise OCRProcessingError(
            "Google Cloud Vision API not available. Please install google-cloud-vision: uv pip install google-cloud-vision"
        )

    start_time = time.time()

    try:
        # Initialize Vision API client
        client = vision.ImageAnnotatorClient()

        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_byte_arr = img_byte_arr.getvalue()

        # Create Vision API image object
        vision_image = vision.Image(content=img_byte_arr)

        # Call TEXT_DETECTION
        response = client.text_detection(image=vision_image)

        # Check for API errors
        if response.error.message:
            raise OCRProcessingError(
                f"Vision API error: {response.error.message}"
            )

        # Extract text annotations
        texts = response.text_annotations

        if not texts:
            # No text detected
            processing_time = (time.time() - start_time) * 1000
            return OCRResult(
                full_text="",
                text_blocks=[],
                confidence=0.0,
                processing_time_ms=processing_time,
                image_width=image.size[0],
                image_height=image.size[1],
            )

        # First annotation is the full text
        full_text = texts[0].description

        # Subsequent annotations are individual text blocks
        text_blocks = []
        for annotation in texts[1:]:  # Skip first (full text)
            # Extract bounding box vertices
            vertices = annotation.bounding_poly.vertices
            if len(vertices) == 4:
                # Calculate bounding box from vertices
                xs = [v.x for v in vertices]
                ys = [v.y for v in vertices]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)

                bbox = BoundingBox(
                    x=x_min,
                    y=y_min,
                    width=x_max - x_min,
                    height=y_max - y_min,
                )

                # Vision API doesn't provide per-block confidence for TEXT_DETECTION
                # Use overall confidence from first annotation or default high confidence
                confidence = getattr(annotation, "confidence", 0.9)

                text_block = TextBlock(
                    text=annotation.description,
                    bounding_box=bbox,
                    confidence=confidence,
                )
                text_blocks.append(text_block)

        # Calculate overall confidence
        # Vision API doesn't always provide confidence, estimate from response
        overall_confidence = getattr(texts[0], "confidence", 0.85)

        # Warn if confidence too low
        if overall_confidence < CONFIDENCE_THRESHOLD:
            print(
                f"Warning: OCR confidence {overall_confidence:.2f} below threshold {CONFIDENCE_THRESHOLD}"
            )

        processing_time = (time.time() - start_time) * 1000

        return OCRResult(
            full_text=full_text,
            text_blocks=text_blocks,
            confidence=overall_confidence,
            processing_time_ms=processing_time,
            image_width=image.size[0],
            image_height=image.size[1],
        )

    except OCRProcessingError:
        raise
    except Exception as e:
        raise OCRProcessingError(f"OCR processing failed: {str(e)}") from e


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.

    Operations:
    - Convert to lowercase
    - Remove extra whitespace
    - Strip punctuation (except % for ABV)
    - Remove special characters

    Args:
        text: Raw text string

    Returns:
        Normalized text string

    Example:
        >>> normalize_text("  Jack Daniel's  Tennessee Whiskey  ")
        "jack daniels tennessee whiskey"
        >>> normalize_text("45.0% ALC/VOL")
        "45.0% alc/vol"
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Replace multiple spaces/newlines with single space
    text = re.sub(r"\s+", " ", text)

    # Remove most punctuation but keep % for ABV, . for decimals
    text = re.sub(r"[^\w\s.%/-]", "", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def correct_ocr_errors(text: str) -> str:
    """
    Correct common OCR character recognition errors.

    Common OCR mistakes:
    - 0 (zero) vs O (letter O)
    - 1 (one) vs l (lowercase L) vs I (uppercase i)
    - 5 (five) vs S (letter S)
    - 8 (eight) vs B (letter B)
    - 6 (six) vs G (letter G)

    Args:
        text: OCR text with potential errors

    Returns:
        Text with common OCR errors corrected

    Note:
        This is context-dependent and heuristic-based. May introduce
        errors if text legitimately contains these characters.
        Use cautiously and only where context is clear (e.g., ABV numbers).

    Example:
        >>> correct_ocr_errors("4O% ALC/VOL")  # O should be 0
        "40% ALC/VOL"
        >>> correct_ocr_errors("Aged l Years")  # l should be 1? No, it's "I"
        "Aged 1 Years"
    """
    # For MVP, minimal error correction to avoid false positives
    # Only correct in specific contexts where we're confident

    # Correct O to 0 in percentage context (e.g., "4O%" -> "40%")
    text = re.sub(r"(\d)O(%)", r"\g<1>0\g<2>", text)

    # Correct lowercase l to 1 in numeric context (e.g., "l.5" -> "1.5")
    text = re.sub(r"(?<=\s)l(?=\d)", "1", text)
    text = re.sub(r"(?<=\d)l(?=\.)", "1", text)

    # Future enhancements: Use context-aware ML model for smarter correction

    return text


def extract_text_from_image(base64_str: str) -> OCRResult:
    """
    High-level function to extract text from base64-encoded image.

    Combines all OCR steps:
    1. Validate and decode image
    2. Preprocess image
    3. Extract text via Vision API
    4. Normalize and correct text

    Args:
        base64_str: Base64-encoded image string

    Returns:
        OCRResult with extracted text and metadata

    Raises:
        InvalidImageError: If image is invalid
        OCRProcessingError: If OCR fails

    Example:
        >>> result = extract_text_from_image("data:image/jpeg;base64,/9j/...")
        >>> print(result.full_text)
        >>> print(f"Confidence: {result.confidence:.2%}")
        >>> print(f"Processed in {result.processing_time_ms:.0f}ms")
    """
    # Step 1: Validate and decode
    image = validate_and_decode_image(base64_str)

    # Step 2: Preprocess
    image = preprocess_image(image)

    # Step 3: Extract text
    ocr_result = extract_text_vision_api(image)

    # Step 4: Normalize text (for easier searching)
    # Note: We keep original text in text_blocks for display,
    # but normalized text can be used for searching
    ocr_result.full_text = correct_ocr_errors(ocr_result.full_text)

    return ocr_result


# Optional: Tesseract OCR fallback (future enhancement)
def extract_text_tesseract(image: Image.Image) -> OCRResult:
    """
    Extract text using Tesseract OCR (fallback if Vision API unavailable).

    Note: Not implemented in MVP. Requires pytesseract installation.

    Args:
        image: PIL Image object

    Returns:
        OCRResult with extracted text

    Raises:
        NotImplementedError: Not implemented in MVP
    """
    raise NotImplementedError(
        "Tesseract OCR fallback not implemented. Use Google Cloud Vision API."
    )


# Utility functions
def get_text_in_region(
    ocr_result: OCRResult, region: BoundingBox, tolerance: int = 20
) -> str:
    """
    Get all text found in a specific region of the image.

    Useful for targeted field extraction (e.g., finding ABV near "ALC/VOL").

    Args:
        ocr_result: OCR result to search
        region: Bounding box region to search
        tolerance: Pixels of tolerance for bounding box overlap

    Returns:
        Concatenated text from all blocks in region

    Example:
        >>> # Find text near top-left corner
        >>> region = BoundingBox(x=0, y=0, width=400, height=200)
        >>> brand_area_text = get_text_in_region(ocr_result, region)
    """
    texts = []
    for block in ocr_result.text_blocks:
        # Check if block overlaps with region
        if _boxes_overlap(block.bounding_box, region, tolerance):
            texts.append(block.text)

    return " ".join(texts)


def _boxes_overlap(box1: BoundingBox, box2: BoundingBox, tolerance: int) -> bool:
    """
    Check if two bounding boxes overlap (with tolerance).

    Args:
        box1: First bounding box
        box2: Second bounding box
        tolerance: Pixels of tolerance for overlap

    Returns:
        True if boxes overlap, False otherwise
    """
    # Expand boxes by tolerance
    x1_min = box1.x - tolerance
    y1_min = box1.y - tolerance
    x1_max = box1.x + box1.width + tolerance
    y1_max = box1.y + box1.height + tolerance

    x2_min = box2.x - tolerance
    y2_min = box2.y - tolerance
    x2_max = box2.x + box2.width + tolerance
    y2_max = box2.y + box2.height + tolerance

    # Check overlap
    return not (
        x1_max < x2_min or x2_max < x1_min or y1_max < y2_min or y2_max < y1_min
    )


def search_text_fuzzy(
    text: str, ocr_result: OCRResult, threshold: float = 0.8
) -> tuple[bool, TextBlock | None, float]:
    """
    Search for text in OCR result using fuzzy matching.

    Uses fuzzywuzzy library to find the best match across all text blocks,
    allowing for minor OCR errors and variations.

    Args:
        text: Text to search for
        ocr_result: OCR result to search in
        threshold: Fuzzy match threshold (0.0-1.0)

    Returns:
        Tuple of (found, text_block, similarity_score)

    Example:
        >>> found, block, score = search_text_fuzzy("Jack Daniel's", ocr_result, 0.85)
        >>> if found:
        ...     print(f"Found at {block.bounding_box} with score {score:.2f}")
    """
    try:
        from fuzzywuzzy import fuzz
    except ImportError:
        # Fallback to exact substring matching if fuzzywuzzy not available
        print("Warning: fuzzywuzzy not installed. Using exact matching. Install with: uv pip install python-levenshtein fuzzywuzzy")
        normalized_search = normalize_text(text)
        normalized_full = normalize_text(ocr_result.full_text)

        if normalized_search in normalized_full:
            # Try to find which block contains it
            for block in ocr_result.text_blocks:
                if normalized_search in normalize_text(block.text):
                    return True, block, 1.0
            return True, None, 1.0
        return False, None, 0.0

    # Normalize search text
    normalized_search = normalize_text(text)

    # Search through all text blocks and find best match
    best_match_block = None
    best_score = 0.0

    for block in ocr_result.text_blocks:
        normalized_block = normalize_text(block.text)

        # Use token_sort_ratio for fuzzy matching (handles word order differences)
        score = fuzz.token_sort_ratio(normalized_search, normalized_block) / 100.0

        if score > best_score:
            best_score = score
            best_match_block = block

    # Check if best match meets threshold
    if best_score >= threshold:
        return True, best_match_block, best_score

    return False, None, best_score
