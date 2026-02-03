'use client';

/**
 * Label Form Component
 *
 * Dynamic form that adapts fields based on product type (spirits, wine, beer)
 * Handles validation, conditional fields, and form state
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { ProductType, LabelFormData } from '@/types';
import { getFormSchema } from '@/lib/validation';

interface LabelFormProps {
  productType: ProductType;
  onSubmit: (data: LabelFormData) => void;
  isLoading?: boolean;
}

export default function LabelForm({ productType, onSubmit, isLoading = false }: LabelFormProps) {
  const schema = getFormSchema(productType);
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<LabelFormData>({
    resolver: zodResolver(schema) as any,
  });

  const isImported = watch('is_imported');
  const alcoholContent = watch('alcohol_content');

  // Reset form when product type changes
  useEffect(() => {
    reset();
  }, [productType, reset]);

  // Auto-calculate proof from ABV for spirits
  const calculatedProof = alcoholContent ? Math.round(alcoholContent * 2) : undefined;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Required Fields */}
      <div className="space-y-4">
        <h3 className="font-semibold text-lg text-gray-900">Required Information</h3>

        {/* Brand Name */}
        <div>
          <label htmlFor="brand_name" className="block text-sm font-medium text-gray-700 mb-1">
            Brand Name *
          </label>
          <input
            {...register('brand_name')}
            type="text"
            id="brand_name"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Jack Daniel's"
            disabled={isLoading}
          />
          {errors.brand_name && (
            <p className="mt-1 text-sm text-red-600">{errors.brand_name.message}</p>
          )}
        </div>

        {/* Product Class */}
        <div>
          <label htmlFor="product_class" className="block text-sm font-medium text-gray-700 mb-1">
            Product Class/Type *
          </label>
          <input
            {...register('product_class')}
            type="text"
            id="product_class"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder={
              productType === 'spirits' ? 'e.g., Bourbon Whiskey' :
                productType === 'wine' ? 'e.g., Cabernet Sauvignon' :
                  'e.g., India Pale Ale'
            }
            disabled={isLoading}
          />
          {errors.product_class && (
            <p className="mt-1 text-sm text-red-600">{errors.product_class.message}</p>
          )}
        </div>

        {/* Alcohol Content */}
        <div>
          <label htmlFor="alcohol_content" className="block text-sm font-medium text-gray-700 mb-1">
            Alcohol Content (ABV) {productType !== 'beer' && '*'} {productType === 'beer' && '(optional)'}
          </label>
          <div className="relative">
            <input
              {...register('alcohol_content', { valueAsNumber: true })}
              type="number"
              step="0.1"
              min="0"
              max="100"
              id="alcohol_content"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., 40.0"
              disabled={isLoading}
            />
            <span className="absolute right-3 top-2 text-gray-500">%</span>
          </div>
          {errors.alcohol_content && (
            <p className="mt-1 text-sm text-red-600">{errors.alcohol_content.message}</p>
          )}
        </div>
      </div>

      {/* Optional Common Fields */}
      <div className="space-y-4 pt-4 border-t">
        <h3 className="font-semibold text-lg text-gray-900">Optional Information</h3>

        {/* Net Contents */}
        <div>
          <label htmlFor="net_contents" className="block text-sm font-medium text-gray-700 mb-1">
            Net Contents
          </label>
          <input
            {...register('net_contents')}
            type="text"
            id="net_contents"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., 750 mL"
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Examples: 750 mL, 1 L, 12 fl oz
          </p>
        </div>

        {/* Imported checkbox */}
        <div className="flex items-center">
          <input
            {...register('is_imported')}
            type="checkbox"
            id="is_imported"
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            disabled={isLoading}
          />
          <label htmlFor="is_imported" className="ml-2 block text-sm text-gray-700">
            Imported product
          </label>
        </div>

        {/* Country of Origin (conditional) */}
        {isImported && (
          <div>
            <label htmlFor="country_of_origin" className="block text-sm font-medium text-gray-700 mb-1">
              Country of Origin * (required for imports)
            </label>
            <input
              {...register('country_of_origin')}
              type="text"
              id="country_of_origin"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., Scotland"
              disabled={isLoading}
            />
            {errors.country_of_origin && (
              <p className="mt-1 text-sm text-red-600">{errors.country_of_origin.message}</p>
            )}
          </div>
        )}
      </div>

      {/* Product-Specific Fields */}
      {productType === 'spirits' && (
        <div className="space-y-4 pt-4 border-t">
          <h3 className="font-semibold text-lg text-gray-900">Spirits-Specific</h3>

          {/* Age Statement */}
          <div>
            <label htmlFor="age_statement" className="block text-sm font-medium text-gray-700 mb-1">
              Age Statement
            </label>
            <input
              {...register('age_statement')}
              type="text"
              id="age_statement"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., Aged 4 Years"
              disabled={isLoading}
            />
            <p className="mt-1 text-xs text-gray-500">
              Required for whisky &lt;4 years, brandy &lt;2 years
            </p>
          </div>

          {/* Proof */}
          <div>
            <label htmlFor="proof" className="block text-sm font-medium text-gray-700 mb-1">
              Proof {calculatedProof && `(calculated: ${calculatedProof})`}
            </label>
            <input
              {...register('proof', { valueAsNumber: true })}
              type="number"
              step="0.1"
              min="0"
              max="200"
              id="proof"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder={calculatedProof ? String(calculatedProof) : "e.g., 80"}
              disabled={isLoading}
            />
            <p className="mt-1 text-xs text-gray-500">
              Proof = ABV × 2
            </p>
          </div>
        </div>
      )}

      {productType === 'wine' && (
        <div className="space-y-4 pt-4 border-t">
          <h3 className="font-semibold text-lg text-gray-900">Wine-Specific</h3>

          {/* Vintage Year */}
          <div>
            <label htmlFor="vintage_year" className="block text-sm font-medium text-gray-700 mb-1">
              Vintage Year
            </label>
            <input
              {...register('vintage_year', { valueAsNumber: true })}
              type="number"
              min="1800"
              max={new Date().getFullYear()}
              id="vintage_year"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., 2020"
              disabled={isLoading}
            />
            {errors.vintage_year && (
              <p className="mt-1 text-sm text-red-600">{errors.vintage_year.message}</p>
            )}
          </div>

          {/* Contains Sulfites */}
          <div className="flex items-center">
            <input
              {...register('contains_sulfites')}
              type="checkbox"
              id="contains_sulfites"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={isLoading}
            />
            <label htmlFor="contains_sulfites" className="ml-2 block text-sm text-gray-700">
              Contains sulfites (≥10 ppm)
            </label>
          </div>

          {/* Appellation */}
          <div>
            <label htmlFor="appellation" className="block text-sm font-medium text-gray-700 mb-1">
              Appellation
            </label>
            <input
              {...register('appellation')}
              type="text"
              id="appellation"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., Napa Valley"
              disabled={isLoading}
            />
          </div>
        </div>
      )}

      {productType === 'beer' && (
        <div className="space-y-4 pt-4 border-t">
          <h3 className="font-semibold text-lg text-gray-900">Beer-Specific</h3>

          {/* Style */}
          <div>
            <label htmlFor="style" className="block text-sm font-medium text-gray-700 mb-1">
              Beer Style
            </label>
            <input
              {...register('style')}
              type="text"
              id="style"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., IPA, Lager, Stout"
              disabled={isLoading}
            />
          </div>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full bg-blue-600 text-white py-3 px-4 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? 'Verifying...' : 'Verify Label'}
      </button>
    </form>
  );
}
