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

// Phase 081: Recurring Frequency
export type RecurringFrequency = "monthly" | "quarterly" | "yearly";

// Phase 082: Inventory Status
export type InventoryStatus = "IN_STOCK" | "LOW_STOCK" | "OUT_OF_STOCK";

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
  recurring_frequency?: RecurringFrequency | null;
  inventory_quantity: number;
  low_stock_threshold: number;
  inventory_status: InventoryStatus;
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
  recurring_frequency?: RecurringFrequency | string | null;
  inventory_quantity?: number;
  low_stock_threshold?: number;
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
  recurring_frequency?: RecurringFrequency | string | null;
  inventory_quantity?: number;
  low_stock_threshold?: number;
  is_active?: boolean;
}

export interface ProductListResponse {
  items: Product[];
  total: number;
  skip: number;
  limit: number;
}

// Phase 085: Product Dashboard Analytics
export interface CategoryDistributionItem {
  category_id?: string | null;
  category_name: string;
  count: number;
}

export interface ProductDashboardData {
  total_products: number;
  active_products: number;
  subscription_products: number;
  out_of_stock_products: number;
  low_stock_products: number;
  in_stock_products: number;
  inventory_distribution: Record<string, number>;
  category_distribution: CategoryDistributionItem[];
  subscription_distribution: Record<string, number>;
  frequency_distribution: Record<string, number>;
}

