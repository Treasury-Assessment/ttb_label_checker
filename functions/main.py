"""
TTB Label Verification System - Firebase Cloud Functions
Main entry point for the verify_label function
"""

from firebase_functions import https_fn
from firebase_admin import initialize_app
import json

# Initialize Firebase Admin
initialize_app()


@https_fn.on_request(cors=https_fn.CorsOptions(
    cors_origins="*",
    cors_methods=["POST", "OPTIONS"]
))
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

        # TODO: Implement OCR processing (ocr.py)
        # TODO: Implement verification logic (verification.py)

        # Placeholder response
        response_data = {
            "status": "success",
            "overall_match": True,
            "confidence_score": 0.95,
            "results": [],
            "ocr_full_text": "Placeholder OCR text",
            "processing_time_ms": 0,
            "message": "Function initialized successfully - OCR and verification logic pending"
        }

        return https_fn.Response(
            json.dumps(response_data),
            status=200,
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": str(e)
            }),
            status=500,
            headers={"Content-Type": "application/json"}
        )
