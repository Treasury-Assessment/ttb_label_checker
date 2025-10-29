/**
 * API Client for TTB Label Verification
 *
 * Handles communication with Cloud Functions backend
 */

import type {
  ProductType,
  LabelFormData,
  VerificationRequest,
  VerificationResponse,
  ErrorResponse,
} from '@/types';

// Get API URL from environment variable
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001/ttb-label-checker/us-east4';

/**
 * Convert File to base64 string
 */
export async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      // Return full data URI (includes mime type)
      resolve(result);
    };
    reader.onerror = (error) => reject(error);
  });
}

/**
 * Verify label against TTB requirements
 *
 * @param productType - Type of alcohol product (spirits, wine, beer)
 * @param formData - User-submitted product information
 * @param imageFile - Label image file
 * @returns Verification results or throws error
 */
export async function verifyLabel(
  productType: ProductType,
  formData: LabelFormData,
  imageFile: File
): Promise<VerificationResponse> {
  try {
    // Convert image to base64
    const imageBase64 = await fileToBase64(imageFile);

    // Construct request
    const request: VerificationRequest = {
      product_type: productType,
      form_data: formData,
      image: imageBase64,
    };

    // Make API call
    const response = await fetch(`${API_URL}/verify_label`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const data = await response.json();

    // Handle error responses
    if (!response.ok || data.status === 'error') {
      const error = data as ErrorResponse;
      throw new APIError(
        error.message || 'Verification failed',
        error.error_code || 'UNKNOWN_ERROR',
        response.status,
        error.details
      );
    }

    return data as VerificationResponse;
  } catch (error) {
    // Re-throw APIError as-is
    if (error instanceof APIError) {
      throw error;
    }

    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new APIError(
        'Network error - could not connect to server',
        'NETWORK_ERROR',
        0
      );
    }

    // Handle other errors
    throw new APIError(
      error instanceof Error ? error.message : 'Unknown error occurred',
      'UNKNOWN_ERROR',
      0
    );
  }
}

/**
 * Custom API Error class with additional context
 */
export class APIError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(): string {
    switch (this.code) {
      case 'INVALID_IMAGE':
        return 'Invalid image format. Please upload a JPEG, PNG, or WebP image.';
      case 'OCR_FAILED':
        return 'Could not read text from image. Please ensure the label has clear, readable text with good lighting.';
      case 'INVALID_INPUT':
        return 'Invalid form data. Please check all required fields.';
      case 'NETWORK_ERROR':
        return 'Connection error. Please check your internet connection and try again.';
      case 'TIMEOUT':
        return 'Request timed out. Please try again with a smaller image.';
      default:
        return this.message || 'An unexpected error occurred. Please try again.';
    }
  }
}

/**
 * Validate image file before upload
 *
 * @param file - Image file to validate
 * @throws Error if file is invalid
 */
export function validateImageFile(file: File): void {
  const MAX_SIZE = 10 * 1024 * 1024; // 10MB
  const SUPPORTED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic'];

  // Check file size
  if (file.size > MAX_SIZE) {
    throw new Error(`Image too large. Maximum size is 10MB (yours: ${(file.size / 1024 / 1024).toFixed(1)}MB)`);
  }

  // Check file type
  if (!SUPPORTED_TYPES.includes(file.type)) {
    throw new Error(`Unsupported format: ${file.type}. Please use JPEG, PNG, or WebP.`);
  }
}
