'use client';

import { useState } from 'react';
import type { ProductType, LabelFormData, VerificationResponse, UploadedFile } from '@/types';
import { verifyLabel, APIError } from '@/lib/api';
import LabelForm from '@/components/LabelForm';
import ImageUpload from '@/components/ImageUpload';
import VerificationResults from '@/components/VerificationResults';

export default function Home() {
  const [productType, setProductType] = useState<ProductType>('spirits');
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleImageSelect = (file: File | null) => {
    if (!file) {
      setUploadedFile(null);
      return;
    }

    // Create preview URL
    const preview = URL.createObjectURL(file);
    setUploadedFile({ file, preview });
    setError(null);
  };

  const handleVerify = async (formData: LabelFormData) => {
    if (!uploadedFile) {
      setError('Please upload a label image');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await verifyLabel(productType, formData, uploadedFile.file);
      setResults(response);

      // Scroll to results
      setTimeout(() => {
        document.getElementById('results')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.getUserMessage());
      } else {
        setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      }
      console.error('Verification error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResults(null);
    setError(null);
    setUploadedFile(null);
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            TTB Label Verification System
          </h1>
          <p className="text-gray-600 mt-1">
            AI-powered compliance checking for alcohol beverage labels
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Product Type Selector */}
        {!results && (
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Select Product Type
            </label>
            <div className="grid grid-cols-3 gap-4">
              {(['spirits', 'wine', 'beer'] as ProductType[]).map((type) => (
                <button
                  key={type}
                  onClick={() => setProductType(type)}
                  disabled={isLoading}
                  className={`
                    py-3 px-4 rounded-lg border-2 font-medium capitalize transition-all
                    ${productType === type
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                    }
                    ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  {type === 'spirits' && '🥃'}
                  {type === 'wine' && '🍷'}
                  {type === 'beer' && '🍺'}
                  {' '}
                  {type}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Main Content */}
        {!results ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Column - Form */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Product Information
              </h2>
              <LabelForm
                productType={productType}
                onSubmit={handleVerify}
                isLoading={isLoading}
              />
            </div>

            {/* Right Column - Image Upload */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Label Image
              </h2>
              <ImageUpload
                onImageSelect={handleImageSelect}
                uploadedFile={uploadedFile}
                disabled={isLoading}
              />
            </div>
          </div>
        ) : (
          /* Results View */
          <div id="results" className="bg-white rounded-lg shadow-lg p-6">
            <VerificationResults
              results={results}
              imageUrl={uploadedFile?.preview}
              onReVerify={handleReset}
            />
          </div>
        )}

        {/* Error Message */}
        {error && !results && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <svg className="w-5 h-5 text-red-600 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div>
                <h3 className="text-sm font-medium text-red-800">Verification Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 max-w-sm mx-4 text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Verifying Label...
              </h3>
              <p className="text-sm text-gray-600">
                Extracting text and checking compliance
              </p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-gray-500 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="font-medium text-yellow-800 mb-1">
            ⚠️ Important Disclaimer
          </p>
          <p>
            This is a simplified compliance pre-check tool for development purposes.
            <br />
            <strong>NOT an official TTB certification.</strong> Always consult TTB directly for official label approval.
          </p>
        </div>
      </div>
    </main>
  );
}
