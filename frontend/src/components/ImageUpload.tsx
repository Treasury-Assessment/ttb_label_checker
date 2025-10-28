'use client';

/**
 * Image Upload Component
 *
 * Drag-and-drop image upload with preview and validation
 */

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { validateImageFile } from '@/lib/api';
import type { UploadedFile } from '@/types';

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  uploadedFile?: UploadedFile | null;
  disabled?: boolean;
}

export default function ImageUpload({ onImageSelect, uploadedFile, disabled = false }: ImageUploadProps) {
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);

    if (acceptedFiles.length === 0) {
      setError('No file selected');
      return;
    }

    const file = acceptedFiles[0];

    // Validate file
    try {
      validateImageFile(file);
      onImageSelect(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid file');
    }
  }, [onImageSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp'],
      'image/heic': ['.heic'],
    },
    maxFiles: 1,
    disabled,
  });

  const clearImage = () => {
    setError(null);
    onImageSelect(null as any); // Clear selection
  };

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      {!uploadedFile && (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />

          <div className="space-y-3">
            {/* Upload Icon */}
            <div className="mx-auto w-16 h-16 flex items-center justify-center rounded-full bg-gray-100">
              <svg
                className="w-8 h-8 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>

            {/* Instructions */}
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop image here' : 'Drag & drop label image'}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                or click to browse
              </p>
            </div>

            {/* Supported Formats */}
            <p className="text-xs text-gray-500">
              JPEG, PNG, WebP • Max 10MB
            </p>
          </div>
        </div>
      )}

      {/* Preview */}
      {uploadedFile && (
        <div className="space-y-3">
          <div className="relative rounded-lg border border-gray-300 overflow-hidden bg-gray-50">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={uploadedFile.preview}
              alt="Label preview"
              className="w-full h-auto max-h-96 object-contain"
            />

            {/* Remove button overlay */}
            <button
              onClick={clearImage}
              disabled={disabled}
              className="absolute top-2 right-2 bg-red-600 text-white p-2 rounded-full hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg"
              title="Remove image"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* File Info */}
          <div className="flex items-center justify-between text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span className="font-medium truncate">{uploadedFile.file.name}</span>
            </div>
            <span className="text-gray-500 whitespace-nowrap ml-4">
              {(uploadedFile.file.size / 1024 / 1024).toFixed(1)} MB
            </span>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <svg className="w-5 h-5 text-red-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-red-800">Upload Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tips */}
      {!uploadedFile && !error && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Tips for best results:</h4>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li>Use good lighting - avoid shadows and glare</li>
            <li>Ensure text is in focus and readable</li>
            <li>Capture the entire label</li>
            <li>Minimum resolution: 800x600px</li>
          </ul>
        </div>
      )}
    </div>
  );
}
