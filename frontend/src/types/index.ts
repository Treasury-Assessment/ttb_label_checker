/**
 * Type definitions for TTB Label Verification System
 */

// Product types supported by the system
export type ProductType = 'spirits' | 'wine' | 'beer';

// Verification status for each field
export type VerificationStatus = 'match' | 'mismatch' | 'not_found' | 'warning' | 'error';

// Form data submitted by user
export interface LabelFormData {
  // Required fields
  brand_name: string;
  product_class: string;
  alcohol_content: number;

  // Optional common fields
  net_contents?: string;
  bottler_name?: string;
  address?: string;
  country_of_origin?: string;
  is_imported?: boolean;

  // Spirits-specific fields
  age_statement?: string;
  proof?: number;
  state_of_distillation?: string;
  commodity_statement?: string;

  // Wine-specific fields
  vintage_year?: number;
  contains_sulfites?: boolean;
  appellation?: string;

  // Beer-specific fields
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
  message?: string;
  cfr_reference?: string;
}

// Complete verification response from API
export interface VerificationResponse {
  status: 'success' | 'error';
  overall_match: boolean;
  confidence_score: number;
  compliance_score?: number;
  compliance_grade?: string;
  field_results: FieldVerificationResult[];
  ocr_full_text: string;
  processing_time_ms: number;
  warnings?: string[];
  errors?: string[];
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
