"""
Pytest Configuration and Shared Fixtures

Global test configuration, fixtures, and helpers for all test modules.
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to Python path so tests can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


# Pytest configuration

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (>1 second)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (fast, no external dependencies)"
    )


# Global Fixtures

@pytest.fixture(scope="session")
def government_warning_text():
    """Full government warning text (27 CFR Part 16)."""
    return """GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."""


@pytest.fixture
def mock_vision_api_response():
    """Mock Google Cloud Vision API response."""
    from unittest.mock import Mock

    # Create mock text annotation
    mock_annotation = Mock()
    mock_annotation.description = "SAMPLE LABEL TEXT\nBOURBON WHISKEY\n45% ALC/VOL"

    # Create mock bounding box vertices
    def create_vertex(x, y):
        vertex = Mock()
        vertex.x = x
        vertex.y = y
        return vertex

    mock_text_block = Mock()
    mock_text_block.description = "BOURBON WHISKEY"
    mock_text_block.bounding_poly.vertices = [
        create_vertex(100, 50),
        create_vertex(300, 50),
        create_vertex(300, 80),
        create_vertex(100, 80)
    ]

    # Create mock response
    mock_response = Mock()
    mock_response.text_annotations = [mock_annotation, mock_text_block]
    mock_response.error.message = ""

    return mock_response


@pytest.fixture
def sample_bourbon_label():
    """Sample bourbon label data for testing."""
    return {
        "form_data": {
            "brand_name": "Eagle Rare",
            "product_class": "Straight Bourbon Whiskey",
            "alcohol_content": 45.0,
            "net_contents": "750 mL",
            "bottler_name": "Buffalo Trace Distillery",
            "address": "Frankfort, KY",
            "age_statement": "Aged 10 Years",
            "proof": 90.0,
            "is_imported": False
        },
        "ocr_text": """
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
    }


@pytest.fixture
def sample_wine_label():
    """Sample wine label data for testing."""
    return {
        "form_data": {
            "brand_name": "Napa Valley Reserve",
            "product_class": "Cabernet Sauvignon",
            "alcohol_content": 13.5,
            "net_contents": "750 mL",
            "vintage_year": 2019,
            "contains_sulfites": True,
            "appellation": "Napa Valley"
        },
        "ocr_text": """
            NAPA VALLEY RESERVE
            CABERNET SAUVIGNON
            2019
            13.5% ALC/VOL
            750 mL
            NAPA VALLEY
            CONTAINS SULFITES
            GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
        """
    }


@pytest.fixture
def sample_beer_label():
    """Sample beer label data for testing."""
    return {
        "form_data": {
            "brand_name": "Hazy Days IPA",
            "product_class": "India Pale Ale",
            "alcohol_content": 6.5,
            "net_contents": "12 fl oz",
            "style": "New England IPA"
        },
        "ocr_text": """
            HAZY DAYS IPA
            NEW ENGLAND INDIA PALE ALE
            6.5% ALC/VOL
            12 FL OZ
            GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
        """
    }


# Helper Functions

def assert_field_result(field_result, expected_status, expected_field_name=None):
    """
    Helper to assert FieldResult properties.

    Args:
        field_result: FieldResult object to check
        expected_status: Expected VerificationStatus
        expected_field_name: Optional expected field name
    """

    assert field_result.status == expected_status

    if expected_field_name:
        assert field_result.field_name == expected_field_name


def assert_compliance_grade(score, expected_grade):
    """
    Helper to assert compliance grade matches expected.

    Args:
        score: Compliance score (0-100)
        expected_grade: Expected grade (A-F)
    """
    if score >= 90:
        assert expected_grade == "A", f"Score {score} should be grade A"
    elif score >= 80:
        assert expected_grade == "B", f"Score {score} should be grade B"
    elif score >= 70:
        assert expected_grade == "C", f"Score {score} should be grade C"
    elif score >= 60:
        assert expected_grade == "D", f"Score {score} should be grade D"
    else:
        assert expected_grade == "F", f"Score {score} should be grade F"


# Mock Environment Variables

@pytest.fixture(scope="session", autouse=True)
def set_test_env_vars(monkeypatch_session):
    """Set test environment variables for all tests."""

    test_env_vars = {
        "GOOGLE_CLOUD_PROJECT_ID": "test-project",
        "OCR_CONFIDENCE_THRESHOLD": "0.7",
        "FIREBASE_STORAGE_BUCKET": "test-bucket.appspot.com"
    }

    for key, value in test_env_vars.items():
        monkeypatch_session.setenv(key, value)


@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch."""
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()


# Performance Testing Helpers

@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return None

    return Timer()


# Custom Assertions

def pytest_assertrepr_compare(op, left, right):
    """Custom assertion representation for better error messages."""
    if isinstance(left, dict) and isinstance(right, dict) and op == "==":
        return [
            "Comparing dicts:",
            f"Left keys: {sorted(left.keys())}",
            f"Right keys: {sorted(right.keys())}",
            "Differences:"
        ] + [
            f"  {key}: {left.get(key)} != {right.get(key)}"
            for key in set(left.keys()) | set(right.keys())
            if left.get(key) != right.get(key)
        ]
