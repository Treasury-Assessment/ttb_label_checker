/**
 * Type definitions for TTB Label Verification System
 */

// Product types supported by the system
export type ProductType = 'spirits' | 'wine' | 'beer';

// Verification status for each field
export type VerificationStatus = 'match' | 'mismatch' | 'not_found';

// Form data submitted by user
export interface LabelFormData {
  // Required fields
  brand_name: string;
  product_class: string;
  alcohol_content: number;

  // Optional fields
  net_contents?: string;
  bottler_name?: string;
  address?: string;
  country_of_origin?: string;
  is_imported?: boolean;
  age_statement?: string;
  contains_sulfites?: boolean;
  vintage_year?: number;
  style?: string;
}

// Bounding box for text location in image
export interface TextLocation {
  x: number;
  y: number;
  width: number;
  height: number;
}

// Individual field verification result
export interface FieldVerificationResult {
  field_name: string;
  status: VerificationStatus;
  expected: string;
  found: string | null;
  confidence: number;
  location?: TextLocation;
}

// Complete verification response from API
export interface VerificationResponse {
  status: 'success' | 'error';
  overall_match: boolean;
  confidence_score: number;
  results: FieldVerificationResult[];
  ocr_full_text: string;
  processing_time_ms: number;
}

// Error response from API
export interface ErrorResponse {
  status: 'error';
  error_code: 'INVALID_IMAGE' | 'OCR_FAILED' | 'INVALID_INPUT' | 'INTERNAL_ERROR';
  message: string;
  details?: any;
}

// Request payload for verification API
export interface VerificationRequest {
  product_type: ProductType;
  form_data: LabelFormData;
  image: string; // Base64 encoded
}

// File upload state
export interface UploadedFile {
  file: File;
  preview: string;
  base64?: string;
}
