/**
 * Product and Product Category types for DealFlow360 (Phases 071–075).
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
  is_active: boolean;
  created_at: string;
  updated_at: string;

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
  is_active?: boolean;
}

export interface ProductUpdateInput {
  name?: string;
  description?: string | null;
  category_id?: string | null;
  cost?: number | string;
  base_price?: number | string;
  is_active?: boolean;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  skip: number;
  limit: number;
}
