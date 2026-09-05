/**
 * Product, Category, Units, Variants, and Attributes types for DealFlow360 (Phases 071–080).
 */

export interface ProductCategory {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCategoryCreateInput {
  name: string;
  code: string;
  description?: string | null;
  is_active?: boolean;
}

export interface ProductCategoryUpdateInput {
  name?: string;
  description?: string | null;
  is_active?: boolean;
}

// Phase 077: Product Unit
export interface ProductUnit {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductUnitCreateInput {
  code: string;
  name: string;
  description?: string | null;
  is_active?: boolean;
}

export interface ProductUnitUpdateInput {
  name?: string;
  description?: string | null;
  is_active?: boolean;
}

// Phase 079: Product Attribute & Values
export interface ProductAttributeValue {
  id: string;
  attribute_id: string;
  value: string;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface ProductAttributeValueCreateInput {
  value: string;
  display_order?: number;
}

export interface ProductAttribute {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  values: ProductAttributeValue[];
}

export interface ProductAttributeCreateInput {
  code: string;
  name: string;
  description?: string | null;
  is_active?: boolean;
}

export interface ProductAttributeUpdateInput {
  name?: string;
  description?: string | null;
  is_active?: boolean;
}

// Phase 078: Product Variant
export interface ProductVariant {
  id: string;
  product_id: string;
  sku: string;
  name: string;
  cost?: number | string | null;
  base_price?: number | string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  attribute_values: ProductAttributeValue[];
}

export interface ProductVariantCreateInput {
  sku: string;
  name: string;
  cost?: number | string | null;
  base_price?: number | string | null;
  is_active?: boolean;
  attribute_value_ids?: string[];
}

export interface ProductVariantUpdateInput {
  sku?: string;
  name?: string;
  cost?: number | string | null;
  base_price?: number | string | null;
  is_active?: boolean;
  attribute_value_ids?: string[];
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  description?: string | null;
  category_id?: string | null;
  category?: ProductCategory | null;
  cost: number | string;
  base_price: number | string;
  unit: string;
  tax_rate: number | string;
  is_subscription: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  variants?: ProductVariant[];

  // Computed Margin fields (Phase 075)
  margin_amount: number | string;
  margin_percentage: number | string | null;
}

export interface ProductCreateInput {
  sku: string;
  name: string;
  description?: string | null;
  category_id?: string | null;
  cost?: number | string;
  base_price?: number | string;
  unit?: string;
  tax_rate?: number | string;
  is_subscription?: boolean;
  is_active?: boolean;
}

export interface ProductUpdateInput {
  name?: string;
  description?: string | null;
  category_id?: string | null;
  cost?: number | string;
  base_price?: number | string;
  unit?: string;
  tax_rate?: number | string;
  is_subscription?: boolean;
  is_active?: boolean;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  skip: number;
  limit: number;
}
