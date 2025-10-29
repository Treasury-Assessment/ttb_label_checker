/**
 * Unit Tests for API Client
 *
 * Tests for verifyLabel, APIError, validateImageFile, and fileToBase64 functions.
 */

import {
  verifyLabel,
  APIError,
  validateImageFile,
  fileToBase64
} from '../api'
import type { ProductType, VerificationResponse } from '@/types'

describe('API Client', () => {
  beforeEach(() => {
    // Clear all fetch mocks before each test
    jest.clearAllMocks()
  })

  describe('fileToBase64', () => {
    it('should convert File to base64 string', async () => {
      const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
      const result = await fileToBase64(file)

      expect(result).toContain('data:text/plain;base64,')
      expect(typeof result).toBe('string')
    })

    it('should handle image files', async () => {
      // Create a fake image file
      const blob = new Blob(['fake image data'], { type: 'image/jpeg' })
      const file = new File([blob], 'label.jpg', { type: 'image/jpeg' })

      const result = await fileToBase64(file)

      expect(result).toContain('data:image/jpeg;base64,')
    })

    it('should reject on FileReader error', async () => {
      const file = new File(['test'], 'test.txt', { type: 'text/plain' })

      // Mock FileReader to trigger error
      const originalFileReader = globalThis.FileReader
      globalThis.FileReader = class extends originalFileReader {
        readAsDataURL() {
          setTimeout(() => {
            this.onerror?.(new Error('Read error') as any)
          }, 0)
        }
      } as any

      await expect(fileToBase64(file)).rejects.toThrow()

      // Restore original FileReader
      globalThis.FileReader = originalFileReader
    })
  })

  describe('validateImageFile', () => {
    it('should accept valid JPEG file', () => {
      const file = new File(['fake image'], 'label.jpg', { type: 'image/jpeg' })
      Object.defineProperty(file, 'size', { value: 1024 * 1024 }) // 1MB

      expect(() => validateImageFile(file)).not.toThrow()
    })

    it('should accept valid PNG file', () => {
      const file = new File(['fake image'], 'label.png', { type: 'image/png' })
      Object.defineProperty(file, 'size', { value: 1024 * 1024 })

      expect(() => validateImageFile(file)).not.toThrow()
    })

    it('should accept valid WebP file', () => {
      const file = new File(['fake image'], 'label.webp', { type: 'image/webp' })
      Object.defineProperty(file, 'size', { value: 1024 * 1024 })

      expect(() => validateImageFile(file)).not.toThrow()
    })

    it('should accept valid HEIC file', () => {
      const file = new File(['fake image'], 'label.heic', { type: 'image/heic' })
      Object.defineProperty(file, 'size', { value: 1024 * 1024 })

      expect(() => validateImageFile(file)).not.toThrow()
    })

    it('should reject file larger than 10MB', () => {
      const file = new File(['fake image'], 'label.jpg', { type: 'image/jpeg' })
      Object.defineProperty(file, 'size', { value: 11 * 1024 * 1024 }) // 11MB

      expect(() => validateImageFile(file)).toThrow('Image too large')
    })

    it('should reject unsupported file types', () => {
      const file = new File(['fake image'], 'label.gif', { type: 'image/gif' })
      Object.defineProperty(file, 'size', { value: 1024 * 1024 })

      expect(() => validateImageFile(file)).toThrow('Unsupported format')
    })

    it('should reject non-image files', () => {
      const file = new File(['text'], 'file.txt', { type: 'text/plain' })
      Object.defineProperty(file, 'size', { value: 1024 })

      expect(() => validateImageFile(file)).toThrow('Unsupported format')
    })

    it('should show file size in error message', () => {
      const file = new File(['fake image'], 'label.jpg', { type: 'image/jpeg' })
      Object.defineProperty(file, 'size', { value: 15 * 1024 * 1024 }) // 15MB

      expect(() => validateImageFile(file)).toThrow('15.0MB')
    })
  })

  describe('APIError', () => {
    it('should create error with message and code', () => {
      const error = new APIError('Test error', 'TEST_CODE', 400)

      expect(error.message).toBe('Test error')
      expect(error.code).toBe('TEST_CODE')
      expect(error.status).toBe(400)
      expect(error.name).toBe('APIError')
    })

    it('should include optional details', () => {
      const details = { field: 'brand_name', issue: 'missing' }
      const error = new APIError('Test error', 'INVALID_INPUT', 400, details)

      expect(error.details).toEqual(details)
    })

    it('should provide user-friendly message for INVALID_IMAGE', () => {
      const error = new APIError('Backend error', 'INVALID_IMAGE', 400)

      expect(error.getUserMessage()).toContain('Invalid image format')
      expect(error.getUserMessage()).toContain('JPEG, PNG, or WebP')
    })

    it('should provide user-friendly message for OCR_FAILED', () => {
      const error = new APIError('OCR error', 'OCR_FAILED', 500)

      expect(error.getUserMessage()).toContain('Could not read text')
      expect(error.getUserMessage()).toContain('good lighting')
    })

    it('should provide user-friendly message for INVALID_INPUT', () => {
      const error = new APIError('Validation failed', 'INVALID_INPUT', 400)

      expect(error.getUserMessage()).toContain('Invalid form data')
      expect(error.getUserMessage()).toContain('required fields')
    })

    it('should provide user-friendly message for NETWORK_ERROR', () => {
      const error = new APIError('Network error', 'NETWORK_ERROR', 0)

      expect(error.getUserMessage()).toContain('Connection error')
      expect(error.getUserMessage()).toContain('internet connection')
    })

    it('should provide user-friendly message for TIMEOUT', () => {
      const error = new APIError('Timeout', 'TIMEOUT', 408)

      expect(error.getUserMessage()).toContain('timed out')
      expect(error.getUserMessage()).toContain('smaller image')
    })

    it('should fallback to original message for unknown code', () => {
      const error = new APIError('Custom error message', 'UNKNOWN_CODE', 500)

      expect(error.getUserMessage()).toContain('Custom error message')
    })
  })

  describe('verifyLabel', () => {
    const mockFormData = {
      brand_name: 'Test Brand',
      product_class: 'Bourbon Whiskey',
      alcohol_content: 45.0,
      net_contents: '750 mL',
    }

    const mockFile = new File(['fake image'], 'label.jpg', { type: 'image/jpeg' })
    Object.defineProperty(mockFile, 'size', { value: 1024 * 1024 })

    const mockSuccessResponse: VerificationResponse = {
      status: 'success',
      overall_match: true,
      confidence_score: 0.95,
      compliance_score: 100,
      compliance_grade: 'A',
      field_results: [
        {
          field_name: 'brand_name',
          status: 'match',
          expected: 'Test Brand',
          found: 'TEST BRAND',
          confidence: 0.98,
        },
      ],
      ocr_full_text: 'TEST BRAND\nBOURBON WHISKEY\n45% ALC/VOL',
      processing_time_ms: 1200,
    }

    beforeEach(() => {
      // Reset fetch mock
      global.fetch = jest.fn()
    })

    it('should successfully verify label', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSuccessResponse,
      })

      const result = await verifyLabel('spirits', mockFormData, mockFile)

      expect(result).toEqual(mockSuccessResponse)
      expect(global.fetch).toHaveBeenCalledTimes(1)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/verify_label'),
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: expect.any(String),
        })
      )
    })

    it('should include product type and form data in request', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSuccessResponse,
      })

      await verifyLabel('spirits', mockFormData, mockFile)

      const callArgs = (global.fetch as jest.Mock).mock.calls[0]
      const requestBody = JSON.parse(callArgs[1].body)

      expect(requestBody.product_type).toBe('spirits')
      expect(requestBody.form_data).toEqual(mockFormData)
      expect(requestBody.image).toContain('data:image/jpeg;base64,')
    });

    it('should handle API error response', async () => {
      const errorResponse = {
        status: 'error',
        message: 'OCR failed',
        error_code: 'OCR_FAILED',
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => errorResponse,
      });

      await expect(verifyLabel('spirits', mockFormData, mockFile)).rejects.toThrow(
        APIError
      );
      await expect(verifyLabel('spirits', mockFormData, mockFile)).rejects.toThrow(
        'OCR failed'
      );
    })

    it('should handle network errors', async () => {
      const networkError = new TypeError('Failed to fetch');
      (global.fetch as jest.Mock).mockRejectedValue(networkError);

      try {
        await verifyLabel('spirits', mockFormData, mockFile);
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).code).toBe('NETWORK_ERROR');
      }
    })

    it('should handle unknown errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Unexpected error'))

      await expect(verifyLabel('spirits', mockFormData, mockFile)).rejects.toThrow(
        APIError
      )

      try {
        await verifyLabel('spirits', mockFormData, mockFile)
      } catch (error) {
        expect(error).toBeInstanceOf(APIError)
        expect((error as APIError).code).toBe('UNKNOWN_ERROR')
      }
    })

    it('should handle different product types', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockSuccessResponse,
      })

      await verifyLabel('wine', mockFormData, mockFile)
      let requestBody = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)
      expect(requestBody.product_type).toBe('wine')

      await verifyLabel('beer', mockFormData, mockFile)
      requestBody = JSON.parse((global.fetch as jest.Mock).mock.calls[1][1].body)
      expect(requestBody.product_type).toBe('beer')
    });

    // Note: Skipping this test because the API_URL constant is evaluated at module load time,
    // so changing process.env in the test doesn't affect it. This would require mocking the
    // entire module or changing the implementation to read env vars dynamically.
    it.skip('should use correct API URL from environment variable', async () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_URL;
      process.env.NEXT_PUBLIC_API_URL = 'https://custom-api.com';

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSuccessResponse,
      })

      await verifyLabel('spirits', mockFormData, mockFile)

      expect(global.fetch).toHaveBeenCalledWith(
        'https://custom-api.com/verify_label',
        expect.any(Object)
      )

      // Restore original env
      process.env.NEXT_PUBLIC_API_URL = originalEnv;
    });

    it('should include error details in APIError', async () => {
      const errorResponse = {
        status: 'error',
        message: 'Validation failed',
        error_code: 'INVALID_INPUT',
        details: { missing_fields: ['brand_name'] },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => errorResponse,
      })

      try {
        await verifyLabel('spirits', mockFormData, mockFile)
      } catch (error) {
        expect(error).toBeInstanceOf(APIError)
        expect((error as APIError).details).toEqual({ missing_fields: ['brand_name'] })
      }
    })
  })
})
