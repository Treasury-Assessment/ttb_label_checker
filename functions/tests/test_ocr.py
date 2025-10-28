"""
Unit Tests for OCR Module

Tests for image validation, OCR processing, text normalization, and error correction.
Uses mocked Google Cloud Vision API.
"""

import base64
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image

from models import BoundingBox, OCRResult, TextBlock
from ocr import (
    correct_ocr_errors,
    extract_text_from_image,
    extract_text_vision_api,
    normalize_text,
    validate_and_decode_image,
)

# Test Fixtures

@pytest.fixture
def valid_image():
    """Create a valid test image (800x600 JPEG)."""
    img = Image.new('RGB', (800, 600), color='white')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def valid_base64_image(valid_image):
    """Create a valid base64-encoded image with data URI."""
    b64_data = base64.b64encode(valid_image).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_data}"


@pytest.fixture
def small_image():
    """Create an image that's too small (50x50)."""
    img = Image.new('RGB', (50, 50), color='white')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def large_image():
    """Create an image that's too large (>10MB)."""
    # Create a large image
    img = Image.new('RGB', (5000, 5000), color='white')
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=100)
    buffer.seek(0)
    return buffer.getvalue()


# Test validate_and_decode_image

class TestValidateAndDecodeImage:
    """Test image validation and decoding."""

    def test_valid_jpeg_with_data_uri(self, valid_base64_image):
        """Test decoding valid JPEG with data URI prefix."""
        img = validate_and_decode_image(valid_base64_image)
        assert isinstance(img, Image.Image)
        assert img.size == (800, 600)

    def test_valid_jpeg_without_data_uri(self, valid_image):
        """Test decoding valid JPEG without data URI prefix."""
        b64_data = base64.b64encode(valid_image).decode('utf-8')
        img = validate_and_decode_image(b64_data)
        assert isinstance(img, Image.Image)
        assert img.size == (800, 600)

    def test_valid_png(self):
        """Test decoding valid PNG image."""
        img = Image.new('RGB', (800, 600), color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        decoded = validate_and_decode_image(f"data:image/png;base64,{b64_data}")
        assert isinstance(decoded, Image.Image)

    def test_invalid_base64(self):
        """Test that invalid base64 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid base64 encoding"):
            validate_and_decode_image("not-valid-base64!!!")

    def test_image_too_small(self, small_image):
        """Test that image < 100x100 raises ValueError."""
        b64_data = base64.b64encode(small_image).decode('utf-8')
        with pytest.raises(ValueError, match="Image dimensions too small"):
            validate_and_decode_image(b64_data)

    def test_image_too_large_dimensions(self):
        """Test that image > 10000x10000 raises ValueError."""
        # Create image with large dimensions
        img = Image.new('RGB', (11000, 11000), color='white')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        with pytest.raises(ValueError, match="Image dimensions too large"):
            validate_and_decode_image(b64_data)

    def test_image_too_large_file_size(self, large_image):
        """Test that image > 10MB raises ValueError."""
        b64_data = base64.b64encode(large_image).decode('utf-8')
        with pytest.raises(ValueError, match="Image size too large"):
            validate_and_decode_image(b64_data)

    def test_unsupported_format(self):
        """Test that unsupported format raises ValueError."""
        # Create a GIF (unsupported)
        img = Image.new('RGB', (800, 600), color='white')
        buffer = BytesIO()
        img.save(buffer, format='GIF')
        buffer.seek(0)
        b64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        with pytest.raises(ValueError, match="Unsupported image format"):
            validate_and_decode_image(f"data:image/gif;base64,{b64_data}")

    def test_corrupted_image_data(self):
        """Test that corrupted image data raises ValueError."""
        # Valid base64 but not a valid image
        invalid_data = base64.b64encode(b"not an image").decode('utf-8')
        with pytest.raises(ValueError, match="Could not decode image"):
            validate_and_decode_image(invalid_data)


# Test extract_text_vision_api

class TestExtractTextVisionAPI:
    """Test Google Cloud Vision API text extraction (mocked)."""

    @patch('ocr.vision.ImageAnnotatorClient')
    def test_successful_text_extraction(self, mock_vision_client):
        """Test successful OCR with Vision API."""
        # Create mock response
        mock_annotation = Mock()
        mock_annotation.description = "EAGLE RARE\nKENTUCKY STRAIGHT BOURBON WHISKEY\n45% ALC/VOL"

        mock_text_annotation = Mock()
        mock_text_annotation.description = "EAGLE RARE"
        mock_vertex1 = Mock()
        mock_vertex1.x = 100
        mock_vertex1.y = 50
        mock_vertex2 = Mock()
        mock_vertex2.x = 300
        mock_vertex2.y = 50
        mock_vertex3 = Mock()
        mock_vertex3.x = 300
        mock_vertex3.y = 80
        mock_vertex4 = Mock()
        mock_vertex4.x = 100
        mock_vertex4.y = 80
        mock_text_annotation.bounding_poly.vertices = [
            mock_vertex1, mock_vertex2, mock_vertex3, mock_vertex4
        ]

        mock_response = Mock()
        mock_response.text_annotations = [mock_annotation, mock_text_annotation]
        mock_response.error.message = ""

        mock_client_instance = MagicMock()
        mock_client_instance.text_detection.return_value = mock_response
        mock_vision_client.return_value = mock_client_instance

        # Test
        img = Image.new('RGB', (800, 600), color='white')
        result = extract_text_vision_api(img)

        assert isinstance(result, OCRResult)
        assert "EAGLE RARE" in result.full_text
        assert len(result.text_blocks) > 0
        assert result.confidence > 0.0

    @patch('ocr.vision.ImageAnnotatorClient')
    def test_no_text_found(self, mock_vision_client):
        """Test when no text is found on label."""
        mock_response = Mock()
        mock_response.text_annotations = []
        mock_response.error.message = ""

        mock_client_instance = MagicMock()
        mock_client_instance.text_detection.return_value = mock_response
        mock_vision_client.return_value = mock_client_instance

        img = Image.new('RGB', (800, 600), color='white')
        result = extract_text_vision_api(img)

        assert result.full_text == ""
        assert len(result.text_blocks) == 0
        assert result.confidence == 0.0

    @patch('ocr.vision.ImageAnnotatorClient')
    def test_vision_api_error(self, mock_vision_client):
        """Test handling of Vision API error."""
        mock_response = Mock()
        mock_response.text_annotations = []
        mock_response.error.message = "API Error: Invalid image"

        mock_client_instance = MagicMock()
        mock_client_instance.text_detection.return_value = mock_response
        mock_vision_client.return_value = mock_client_instance

        img = Image.new('RGB', (800, 600), color='white')

        with pytest.raises(ValueError, match="OCR failed"):
            extract_text_vision_api(img)

    @patch('ocr.vision.ImageAnnotatorClient')
    def test_bounding_box_extraction(self, mock_vision_client):
        """Test that bounding boxes are correctly extracted."""
        mock_text_annotation = Mock()
        mock_text_annotation.description = "TEST"
        mock_vertex1 = Mock()
        mock_vertex1.x = 100
        mock_vertex1.y = 200
        mock_vertex2 = Mock()
        mock_vertex2.x = 400
        mock_vertex2.y = 200
        mock_vertex3 = Mock()
        mock_vertex3.x = 400
        mock_vertex3.y = 250
        mock_vertex4 = Mock()
        mock_vertex4.x = 100
        mock_vertex4.y = 250
        mock_text_annotation.bounding_poly.vertices = [
            mock_vertex1, mock_vertex2, mock_vertex3, mock_vertex4
        ]

        mock_full_annotation = Mock()
        mock_full_annotation.description = "TEST"

        mock_response = Mock()
        mock_response.text_annotations = [mock_full_annotation, mock_text_annotation]
        mock_response.error.message = ""

        mock_client_instance = MagicMock()
        mock_client_instance.text_detection.return_value = mock_response
        mock_vision_client.return_value = mock_client_instance

        img = Image.new('RGB', (800, 600), color='white')
        result = extract_text_vision_api(img)

        assert len(result.text_blocks) > 0
        bbox = result.text_blocks[0].bounding_box
        assert bbox.x == 100
        assert bbox.y == 200
        assert bbox.width == 300  # 400 - 100
        assert bbox.height == 50  # 250 - 200


# Test normalize_text

class TestNormalizeText:
    """Test text normalization."""

    def test_lowercase_conversion(self):
        """Test that text is converted to lowercase."""
        assert normalize_text("EAGLE RARE") == "eagle rare"
        assert normalize_text("Mixed Case Text") == "mixed case text"

    def test_whitespace_normalization(self):
        """Test that extra whitespace is removed."""
        assert normalize_text("  extra   spaces  ") == "extra spaces"
        assert normalize_text("tab\t\ttext") == "tab text"
        assert normalize_text("newline\n\ntext") == "newline text"

    def test_punctuation_removal(self):
        """Test that punctuation is removed."""
        assert normalize_text("test, text!") == "test text"
        assert normalize_text("brand-name") == "brandname"
        assert normalize_text("40% alc/vol") == "40 alcvol"

    def test_empty_string(self):
        """Test normalization of empty string."""
        assert normalize_text("") == ""

    def test_only_punctuation(self):
        """Test string with only punctuation."""
        assert normalize_text("!!!???") == ""

    def test_preserve_numbers(self):
        """Test that numbers are preserved."""
        assert normalize_text("45.0% ABV") == "450 abv"
        assert normalize_text("Aged 10 Years") == "aged 10 years"


# Test correct_ocr_errors

class TestCorrectOCRErrors:
    """Test OCR error correction."""

    def test_zero_to_o_correction(self):
        """Test correction of 0 to O."""
        assert correct_ocr_errors("G0VERNMENT") == "GOVERNMENT"
        assert correct_ocr_errors("B0URBON") == "BOURBON"

    def test_one_to_i_correction(self):
        """Test correction of 1 to I."""
        assert correct_ocr_errors("WARN1NG") == "WARNING"
        assert correct_ocr_errors("SP1RITS") == "SPIRITS"

    def test_five_to_s_correction(self):
        """Test correction of 5 to S."""
        assert correct_ocr_errors("5URGEON") == "SURGEON"
        assert correct_ocr_errors("5COTCH") == "SCOTCH"

    def test_multiple_corrections(self):
        """Test multiple corrections in one string."""
        assert correct_ocr_errors("G0VERNMENT WARN1NG") == "GOVERNMENT WARNING"
        assert correct_ocr_errors("5URGEON GENERA1") == "SURGEON GENERAL"

    def test_preserve_valid_numbers(self):
        """Test that valid numbers are preserved."""
        # Should NOT correct numbers in contexts where they're valid
        text = "45% ALC/VOL"
        corrected = correct_ocr_errors(text)
        assert "45" in corrected  # Number should remain

    def test_empty_string(self):
        """Test correction of empty string."""
        assert correct_ocr_errors("") == ""

    def test_no_errors(self):
        """Test string with no OCR errors."""
        text = "GOVERNMENT WARNING"
        assert correct_ocr_errors(text) == text


# Test extract_text_from_image (full pipeline)

class TestExtractTextFromImage:
    """Test complete OCR extraction pipeline."""

    @patch('ocr.extract_text_vision_api')
    def test_full_extraction_pipeline(self, mock_vision_ocr, valid_base64_image):
        """Test complete OCR pipeline from base64 to OCRResult."""
        # Mock Vision API response
        mock_ocr_result = OCRResult(
            full_text="EAGLE RARE\nBOURBON WHISKEY\n45% ALC/VOL",
            text_blocks=[
                TextBlock("EAGLE RARE", 0.98, BoundingBox(100, 50, 200, 30)),
                TextBlock("BOURBON WHISKEY", 0.96, BoundingBox(100, 100, 250, 30)),
                TextBlock("45% ALC/VOL", 0.95, BoundingBox(100, 150, 150, 25))
            ],
            confidence=0.96
        )
        mock_vision_ocr.return_value = mock_ocr_result

        # Test
        result = extract_text_from_image(valid_base64_image)

        assert isinstance(result, OCRResult)
        assert "EAGLE RARE" in result.full_text
        assert len(result.text_blocks) == 3
        assert result.confidence == 0.96

    @patch('ocr.extract_text_vision_api')
    def test_invalid_image_raises_error(self, mock_vision_ocr):
        """Test that invalid base64 image raises ValueError."""
        with pytest.raises(ValueError, match="Invalid base64 encoding"):
            extract_text_from_image("invalid-base64")

    @patch('ocr.extract_text_vision_api')
    def test_error_handling(self, mock_vision_ocr, valid_base64_image):
        """Test error handling when Vision API fails."""
        mock_vision_ocr.side_effect = ValueError("OCR failed: API error")

        with pytest.raises(ValueError, match="OCR failed"):
            extract_text_from_image(valid_base64_image)


# Integration Tests

class TestOCRIntegration:
    """Integration tests for OCR module (if Vision API credentials available)."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires Google Cloud Vision API credentials")
    def test_real_vision_api_call(self):
        """Test actual Vision API call (skipped by default)."""
        # This test would require real credentials and a test image
        # Skip by default to avoid API costs during regular testing
        pass

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires Google Cloud Vision API credentials")
    def test_real_label_image(self):
        """Test OCR on actual label image (skipped by default)."""
        # This would test with a real bourbon label image
        # Skip by default
        pass
