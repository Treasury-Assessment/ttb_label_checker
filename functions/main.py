"""
TTB Label Verification System - Firebase Cloud Functions

Main entry point for the verify_label Cloud Function.
Integrates OCR processing and TTB compliance verification.

Author: TTB Label Verification System
Date: 2025-10-27
"""

from firebase_functions import https_fn
from firebase_admin import initialize_app
import json
import traceback

# Initialize Firebase Admin
initialize_app()

# Import our modules
from models import (
    FormData,
    ProductType,
    ErrorResponse,
    VerificationStatus,
)
from ocr import (
    extract_text_from_image,
    InvalidImageError,
    OCRProcessingError,
)
from verification import verify_label


@https_fn.on_request(cors=True, region="us-east4")
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
        # Parse request body
        request_json = req.get_json(silent=True)

        if not request_json:
            return https_fn.Response(
                json.dumps({
                    "status": "error",
                    "error_code": "INVALID_INPUT",
                    "message": "Request body must be valid JSON"
                }),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # Validate required fields
        required_fields = ["product_type", "form_data", "image"]
        missing_fields = [field for field in required_fields if field not in request_json]

        if missing_fields:
            return https_fn.Response(
                json.dumps({
                    "status": "error",
                    "error_code": "INVALID_INPUT",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # Extract and validate product_type
        product_type_str = request_json.get("product_type", "").lower()
        try:
            product_type = ProductType(product_type_str)
        except ValueError:
            return https_fn.Response(
                json.dumps({
                    "status": "error",
                    "error_code": "INVALID_INPUT",
                    "message": f"Invalid product_type: '{product_type_str}'. Must be 'spirits', 'wine', or 'beer'"
                }),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # Parse form data into FormData model
        form_data_dict = request_json.get("form_data", {})
        try:
            form_data = FormData(
                brand_name=form_data_dict.get("brand_name", ""),
                product_class=form_data_dict.get("product_class", ""),
                alcohol_content=float(form_data_dict.get("alcohol_content", 0)),
                net_contents=form_data_dict.get("net_contents"),
                bottler_name=form_data_dict.get("bottler_name"),
                address=form_data_dict.get("address"),
                country_of_origin=form_data_dict.get("country_of_origin"),
                is_imported=form_data_dict.get("is_imported", False),
                age_statement=form_data_dict.get("age_statement"),
                proof=float(form_data_dict.get("proof")) if form_data_dict.get("proof") is not None else None,
                state_of_distillation=form_data_dict.get("state_of_distillation"),
                commodity_statement=form_data_dict.get("commodity_statement"),
                vintage_year=int(form_data_dict.get("vintage_year")) if form_data_dict.get("vintage_year") else None,
                contains_sulfites=form_data_dict.get("contains_sulfites", False),
                appellation=form_data_dict.get("appellation"),
                style=form_data_dict.get("style"),
            )
        except (ValueError, KeyError) as e:
            return https_fn.Response(
                json.dumps({
                    "status": "error",
                    "error_code": "INVALID_INPUT",
                    "message": f"Invalid form data: {str(e)}"
                }),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # Extract image
        image_base64 = request_json.get("image", "")
        if not image_base64:
            return https_fn.Response(
                json.dumps({
                    "status": "error",
                    "error_code": "INVALID_INPUT",
                    "message": "Image data is required"
                }),
                status=400,
                headers={"Content-Type": "application/json"}
            )

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
            verification_result = verify_label(form_data, ocr_result, product_type)
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
