'use client';

/**
 * Verification Results Component
 *
 * Displays field-by-field verification results with compliance score,
 * visual indicators, and image highlighting
 */

import { useState } from 'react';
import type { VerificationResponse, FieldVerificationResult, VerificationStatus } from '@/types';

interface VerificationResultsProps {
  results: VerificationResponse;
  imageUrl?: string;
  onReVerify?: () => void;
}

export default function VerificationResults({ results, imageUrl, onReVerify }: VerificationResultsProps) {
  const [expandedFields, setExpandedFields] = useState<Set<string>>(new Set());

  const toggleField = (fieldName: string) => {
    const newExpanded = new Set(expandedFields);
    if (newExpanded.has(fieldName)) {
      newExpanded.delete(fieldName);
    } else {
      newExpanded.add(fieldName);
    }
    setExpandedFields(newExpanded);
  };

  // Get status icon and color
  const getStatusInfo = (status: VerificationStatus) => {
    switch (status) {
      case 'match':
        return { icon: '✅', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200' };
      case 'mismatch':
        return { icon: '❌', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' };
      case 'not_found':
        return { icon: '🔍', color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200' };
      case 'warning':
        return { icon: '⚠️', color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200' };
      case 'error':
        return { icon: '💥', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' };
      default:
        return { icon: '❓', color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200' };
    }
  };

  // Get compliance grade color
  const getGradeColor = (grade?: string) => {
    switch (grade) {
      case 'A': return 'text-green-600 bg-green-100';
      case 'B': return 'text-blue-600 bg-blue-100';
      case 'C': return 'text-yellow-600 bg-yellow-100';
      case 'D': return 'text-orange-600 bg-orange-100';
      case 'F': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <div className={`rounded-lg border-2 p-6 ${results.overall_match ? 'bg-green-50 border-green-500' : 'bg-red-50 border-red-500'}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`text-4xl ${results.overall_match ? 'text-green-600' : 'text-red-600'}`}>
              {results.overall_match ? '✅' : '❌'}
            </div>
            <div>
              <h2 className={`text-2xl font-bold ${results.overall_match ? 'text-green-900' : 'text-red-900'}`}>
                {results.overall_match ? 'PASSED' : 'FAILED'}
              </h2>
              <p className={`text-sm ${results.overall_match ? 'text-green-700' : 'text-red-700'}`}>
                {results.overall_match ? 'Label meets TTB requirements' : 'Label has critical compliance issues'}
              </p>
            </div>
          </div>

          {/* Compliance Score & Grade */}
          {results.compliance_score !== undefined && (
            <div className="text-right">
              <div className="flex items-center space-x-2 justify-end">
                <span className={`text-3xl font-bold px-4 py-2 rounded-lg ${getGradeColor(results.compliance_grade)}`}>
                  {results.compliance_grade}
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Score: {results.compliance_score}/100
              </p>
              <p className="text-xs text-gray-500">
                Confidence: {(results.confidence_score * 100).toFixed(0)}%
              </p>
            </div>
          )}
        </div>

        {/* Errors */}
        {results.errors && results.errors.length > 0 && (
          <div className="mt-4 space-y-1">
            {results.errors.map((error, idx) => (
              <p key={idx} className="text-sm text-red-800 flex items-start">
                <span className="mr-2">•</span>
                <span>{error}</span>
              </p>
            ))}
          </div>
        )}

        {/* Warnings */}
        {results.warnings && results.warnings.length > 0 && (
          <div className="mt-4 space-y-1">
            {results.warnings.map((warning, idx) => (
              <p key={idx} className="text-sm text-yellow-800 flex items-start">
                <span className="mr-2">⚠️</span>
                <span>{warning}</span>
              </p>
            ))}
          </div>
        )}
      </div>

      {/* Processing Info */}
      <div className="flex items-center justify-between text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
        <span>Processing time: {results.processing_time_ms.toFixed(0)}ms</span>
        {onReVerify && (
          <button
            onClick={onReVerify}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Verify Another Label →
          </button>
        )}
      </div>

      {/* Field Results */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-900">Field-by-Field Results</h3>

        {results.field_results.map((field, idx) => {
          const statusInfo = getStatusInfo(field.status);
          const isExpanded = expandedFields.has(field.field_name);

          return (
            <div
              key={idx}
              className={`border rounded-lg overflow-hidden ${statusInfo.border} ${statusInfo.bg}`}
            >
              {/* Field Header */}
              <button
                onClick={() => toggleField(field.field_name)}
                className="w-full flex items-center justify-between p-4 hover:opacity-80 transition-opacity"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{statusInfo.icon}</span>
                  <div className="text-left">
                    <h4 className="font-medium text-gray-900 capitalize">
                      {field.field_name.replace(/_/g, ' ')}
                    </h4>
                    <p className={`text-sm ${statusInfo.color}`}>
                      {field.status.toUpperCase()}
                      {field.confidence > 0 && ` • ${(field.confidence * 100).toFixed(0)}% confidence`}
                    </p>
                  </div>
                </div>

                <svg
                  className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Field Details (Expanded) */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-2 border-t border-gray-200">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600 font-medium">Expected:</p>
                      <p className="text-gray-900">{field.expected || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-gray-600 font-medium">Found:</p>
                      <p className="text-gray-900">{field.found || 'Not found'}</p>
                    </div>
                  </div>

                  {field.message && (
                    <div className="mt-2">
                      <p className="text-sm text-gray-700">{field.message}</p>
                    </div>
                  )}

                  {field.cfr_reference && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-500">
                        Reference: {field.cfr_reference}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* OCR Preview (Collapsible) */}
      <details className="border border-gray-300 rounded-lg">
        <summary className="cursor-pointer p-4 hover:bg-gray-50 font-medium text-gray-900">
          View Full OCR Text
        </summary>
        <div className="p-4 bg-gray-50 border-t border-gray-300">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap break-words font-mono">
            {results.ocr_full_text}
          </pre>
        </div>
      </details>
    </div>
  );
}
