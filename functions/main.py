"""
TTB Label Verification System - Firebase Cloud Functions

Main entry point for the verify_label Cloud Function.
Integrates OCR processing and TTB compliance verification.

Author: TTB Label Verification System
Date: 2025-10-27
"""

import json
import traceback

from firebase_admin import initialize_app
from firebase_functions import https_fn, options
from pydantic import BaseModel, Field, ValidationError, field_validator

# Initialize Firebase Admin
initialize_app()

# Import our modules (after Firebase init to ensure proper setup)
# ruff: noqa: E402
from models import (
    ErrorResponse,
    FormData,
    ProductType,
)
from ocr import (
    InvalidImageError,
    OCRProcessingError,
    extract_text_from_image,
)
from verification import verify_label as verify_label_logic

# ============================================================================
# PYDANTIC REQUEST MODELS
# ============================================================================

class FormDataRequest(BaseModel):
    """Pydantic model for form data validation."""
    brand_name: str = Field(..., min_length=1, description="Brand or trade name")
    product_class: str = Field(..., min_length=1, description="Product class/type")
    alcohol_content: float = Field(..., ge=0.0, le=100.0, description="Alcohol by volume percentage")

    # Common optional fields
    net_contents: str | None = Field(None, description="Volume with unit")
    bottler_name: str | None = None
    address: str | None = None
    country_of_origin: str | None = None
    is_imported: bool = False

    # Spirits-specific fields
    age_statement: str | None = None
    proof: float | None = Field(None, ge=0.0, description="Alcohol proof")
    state_of_distillation: str | None = None
    commodity_statement: str | None = None

    # Wine-specific fields
    vintage_year: int | None = Field(None, ge=1800, le=2100, description="4-digit year")
    contains_sulfites: bool = False
    appellation: str | None = None

    # Beer-specific fields
    style: str | None = None


class VerificationRequest(BaseModel):
    """Pydantic model for the complete verification request."""
    product_type: str = Field(..., description="Product type: spirits, wine, or beer")
    form_data: FormDataRequest
    image: str = Field(..., min_length=10, description="Base64 encoded image")

    @field_validator('product_type')
    @classmethod
    def validate_product_type(cls, v: str) -> str:
        """Validate product type is one of the allowed values."""
        allowed = ['spirits', 'wine', 'beer']
        if v.lower() not in allowed:
            raise ValueError(f"product_type must be one of: {', '.join(allowed)}")
        return v.lower()


@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins="*",
        cors_methods=["GET", "POST", "OPTIONS"],
    ),
    region="us-east4"
)
def verify_label(req: https_fn.Request) -> https_fn.Response:
    """
    Cloud Function to verify alcohol label against TTB requirements.

    Expected POST body:
    {
        "product_type": "spirits" | "wine" | "beer",
        "form_data": {
            "brand_name": str,
            "product_class": str,
            "alcohol_content": float,
            ...
        },
        "image": str  # Base64 encoded image
    }

    Returns:
    {
        "status": "success" | "error",
        "overall_match": bool,
        "confidence_score": float,
        "results": [...],
        ...
    }
    """

    # Handle CORS preflight
    if req.method == "OPTIONS":
        return https_fn.Response(status=204)

    # Only accept POST requests
    if req.method != "POST":
        return https_fn.Response(
            json.dumps({"status": "error", "message": "Method not allowed"}),
            status=405,
            headers={"Content-Type": "application/json"}
        )

    try:
        # Parse and validate request body with Pydantic
        request_json = req.get_json(silent=True)

        if not request_json:
            error_response = ErrorResponse(
                error_code="INVALID_INPUT",
                message="Request body must be valid JSON"
            )
            return https_fn.Response(
                json.dumps(error_response.to_dict()),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # Validate request with Pydantic
        try:
            verification_request = VerificationRequest(**request_json)
        except ValidationError as e:
            # Format validation errors
            error_details = []
            for error in e.errors():
                field_path = " -> ".join(str(x) for x in error["loc"])
                error_details.append(f"{field_path}: {error['msg']}")

            error_response = ErrorResponse(
                error_code="INVALID_INPUT",
                message="Request validation failed",
                details={"errors": error_details}
            )
            return https_fn.Response(
                json.dumps(error_response.to_dict()),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # Convert Pydantic models to internal dataclasses
        product_type = ProductType(verification_request.product_type)

        form_data = FormData(
            brand_name=verification_request.form_data.brand_name,
            product_class=verification_request.form_data.product_class,
            alcohol_content=verification_request.form_data.alcohol_content,
            net_contents=verification_request.form_data.net_contents,
            bottler_name=verification_request.form_data.bottler_name,
            address=verification_request.form_data.address,
            country_of_origin=verification_request.form_data.country_of_origin,
            is_imported=verification_request.form_data.is_imported,
            age_statement=verification_request.form_data.age_statement,
            proof=verification_request.form_data.proof,
            state_of_distillation=verification_request.form_data.state_of_distillation,
            commodity_statement=verification_request.form_data.commodity_statement,
            vintage_year=verification_request.form_data.vintage_year,
            contains_sulfites=verification_request.form_data.contains_sulfites,
            appellation=verification_request.form_data.appellation,
            style=verification_request.form_data.style,
        )

        image_base64 = verification_request.image

        # STEP 1: OCR Processing
        try:
            ocr_result = extract_text_from_image(image_base64)
        except InvalidImageError as e:
            error_response = ErrorResponse(
                error_code="INVALID_IMAGE",
                message=str(e),
                details={"suggestion": "Please upload a clear JPEG, PNG, or WebP image"}
            )
            return https_fn.Response(
                json.dumps(error_response.to_dict()),
                status=400,
                headers={"Content-Type": "application/json"}
            )
        except OCRProcessingError as e:
            error_response = ErrorResponse(
                error_code="OCR_FAILED",
                message=f"OCR processing failed: {str(e)}",
                details={"suggestion": "Ensure image has clear, readable text"}
            )
            return https_fn.Response(
                json.dumps(error_response.to_dict()),
                status=500,
                headers={"Content-Type": "application/json"}
            )

        # Check if OCR extracted any text
        if not ocr_result.full_text or len(ocr_result.full_text.strip()) < 10:
            error_response = ErrorResponse(
                error_code="OCR_FAILED",
                message="No text detected on label",
                details={
                    "suggestion": "Ensure label image has clear, readable text with good lighting",
                    "ocr_confidence": ocr_result.confidence
                }
            )
            return https_fn.Response(
                json.dumps(error_response.to_dict()),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # STEP 2: Label Verification
        try:
            verification_result = verify_label_logic(form_data, ocr_result, product_type)
        except Exception as e:
            error_response = ErrorResponse(
                error_code="VERIFICATION_ERROR",
                message=f"Verification failed: {str(e)}",
                details={"traceback": traceback.format_exc()}
            )
            return https_fn.Response(
                json.dumps(error_response.to_dict()),
                status=500,
                headers={"Content-Type": "application/json"}
            )

        # STEP 3: Return results
        response_data = verification_result.to_dict()

        return https_fn.Response(
            json.dumps(response_data),
            status=200,
            headers={"Content-Type": "application/json"}
        )

    except InvalidImageError as e:
        # Image validation errors
        error_response = ErrorResponse(
            error_code="INVALID_IMAGE",
            message=str(e)
        )
        return https_fn.Response(
            json.dumps(error_response.to_dict()),
            status=400,
            headers={"Content-Type": "application/json"}
        )

    except OCRProcessingError as e:
        # OCR processing errors
        error_response = ErrorResponse(
            error_code="OCR_FAILED",
            message=str(e)
        )
        return https_fn.Response(
            json.dumps(error_response.to_dict()),
            status=500,
            headers={"Content-Type": "application/json"}
        )

    except ValueError as e:
        # Input validation errors
        error_response = ErrorResponse(
            error_code="INVALID_INPUT",
            message=str(e)
        )
        return https_fn.Response(
            json.dumps(error_response.to_dict()),
            status=400,
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        # Unexpected errors
        error_response = ErrorResponse(
            error_code="INTERNAL_ERROR",
            message=f"Unexpected error: {str(e)}",
            details={"traceback": traceback.format_exc()}
        )
        return https_fn.Response(
            json.dumps(error_response.to_dict()),
            status=500,
            headers={"Content-Type": "application/json"}
        )
