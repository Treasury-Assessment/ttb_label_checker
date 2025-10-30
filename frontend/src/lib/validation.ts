/**
 * Form Validation Schemas using Zod
 *
 * Provides type-safe form validation with product-specific rules
 */

import { z } from 'zod';
import type { ProductType } from '@/types';

// Base schema with common fields (all product types)
const baseFormSchema = z.object({
  brand_name: z.string()
    .min(2, 'Brand name must be at least 2 characters')
    .max(100, 'Brand name must be less than 100 characters'),

  product_class: z.string()
    .min(2, 'Product class/type is required')
    .max(100, 'Product class must be less than 100 characters'),

  alcohol_content: z.number()
    .min(0, 'ABV must be at least 0%')
    .max(100, 'ABV must be at most 100%'),

  // Optional common fields
  net_contents: z.string().optional(),
  bottler_name: z.string().optional(),
  address: z.string().optional(),
  country_of_origin: z.string().optional(),
  is_imported: z.boolean().optional(),
});

// Spirits-specific schema
export const spiritsFormSchema = baseFormSchema.extend({
  age_statement: z.string().optional(),
  proof: z.number().min(0).max(200).optional(),
  state_of_distillation: z.string().optional(),
  commodity_statement: z.string().optional(),
});

// Wine-specific schema
export const wineFormSchema = baseFormSchema.extend({
  vintage_year: z.union([
    z.number()
      .min(1800, 'Vintage year must be valid')
      .max(new Date().getFullYear(), 'Vintage year cannot be in the future'),
    z.nan(),
    z.undefined(),
  ]).optional(),
  contains_sulfites: z.boolean().optional(),
  appellation: z.string().optional(),
});

// Beer-specific schema
export const beerFormSchema = baseFormSchema.extend({
  alcohol_content: z.union([
    z.number()
      .min(0, 'ABV must be at least 0%')
      .max(100, 'ABV must be at most 100%'),
    z.nan(),
    z.undefined(),
  ]).optional(),
  style: z.string().optional(),
});

// Export type-inferred schemas
export type SpiritsFormData = z.infer<typeof spiritsFormSchema>;
export type WineFormData = z.infer<typeof wineFormSchema>;
export type BeerFormData = z.infer<typeof beerFormSchema>;

/**
 * Get appropriate schema based on product type
 */
export function getFormSchema(productType: ProductType) {
  switch (productType) {
    case 'spirits':
      return spiritsFormSchema;
    case 'wine':
      return wineFormSchema;
    case 'beer':
      return beerFormSchema;
    default:
      return baseFormSchema;
  }
}
