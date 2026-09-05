/**
 * TypeScript Interfaces for G21 Discount Governance Foundation (Phases 101–105).
 * 
 * - Phase 101: Discount Configuration
 * - Phase 102: Customer Discount Ceiling
 * - Phase 103: Category Discount Ceiling
 * - Phase 104: Product Discount Ceiling
 * - Phase 105: Sales Rep Authority Limit
 */

// Phase 101: Discount Configuration
export interface DiscountConfiguration {
  id: string;
  company_id: string;
  name: string;
  description: string | null;
  default_discount_ceiling: number;
  is_active: boolean;
  effective_from: string;
  effective_until: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DiscountConfigurationCreateInput {
  name: string;
  description?: string | null;
  default_discount_ceiling: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface DiscountConfigurationUpdateInput {
  name?: string;
  description?: string | null;
  default_discount_ceiling?: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface DiscountConfigurationListResponse {
  items: DiscountConfiguration[];
  total: number;
}

// Phase 102: Customer Discount Ceiling
export interface CustomerDiscountCeiling {
  id: string;
  company_id: string;
  customer_id: string;
  max_discount_percentage: number;
  is_active: boolean;
  effective_from: string;
  effective_until: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerDiscountCeilingCreateInput {
  customer_id: string;
  max_discount_percentage: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface CustomerDiscountCeilingUpdateInput {
  max_discount_percentage?: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface CustomerDiscountCeilingListResponse {
  items: CustomerDiscountCeiling[];
  total: number;
}

// Phase 103: Category Discount Ceiling
export interface CategoryDiscountCeiling {
  id: string;
  company_id: string;
  category_id: string;
  max_discount_percentage: number;
  is_active: boolean;
  effective_from: string;
  effective_until: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CategoryDiscountCeilingCreateInput {
  category_id: string;
  max_discount_percentage: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface CategoryDiscountCeilingUpdateInput {
  max_discount_percentage?: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface CategoryDiscountCeilingListResponse {
  items: CategoryDiscountCeiling[];
  total: number;
}

// Phase 104: Product Discount Ceiling
export interface ProductDiscountCeiling {
  id: string;
  company_id: string;
  product_id: string;
  max_discount_percentage: number;
  is_active: boolean;
  effective_from: string;
  effective_until: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductDiscountCeilingCreateInput {
  product_id: string;
  max_discount_percentage: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface ProductDiscountCeilingUpdateInput {
  max_discount_percentage?: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface ProductDiscountCeilingListResponse {
  items: ProductDiscountCeiling[];
  total: number;
}

// Phase 105: Sales Rep Authority Limit
export interface SalesRepAuthorityLimit {
  id: string;
  company_id: string;
  user_id: string;
  max_authorized_discount: number;
  is_active: boolean;
  effective_from: string;
  effective_until: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface SalesRepAuthorityLimitCreateInput {
  user_id: string;
  max_authorized_discount: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface SalesRepAuthorityLimitUpdateInput {
  max_authorized_discount?: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface SalesRepAuthorityLimitListResponse {
  items: SalesRepAuthorityLimit[];
  total: number;
}

// Phase 106: Manager Authority Limit
export interface ManagerAuthorityLimit {
  id: string;
  company_id: string;
  user_id: string;
  max_authorized_discount: number;
  is_active: boolean;
  effective_from: string;
  effective_until: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ManagerAuthorityLimitCreateInput {
  user_id: string;
  max_authorized_discount: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface ManagerAuthorityLimitUpdateInput {
  max_authorized_discount?: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface ManagerAuthorityLimitListResponse {
  items: ManagerAuthorityLimit[];
  total: number;
}

// Phase 107: Finance Authority Limit
export interface FinanceAuthorityLimit {
  id: string;
  company_id: string;
  user_id: string;
  max_authorized_discount: number;
  is_active: boolean;
  effective_from: string;
  effective_until: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface FinanceAuthorityLimitCreateInput {
  user_id: string;
  max_authorized_discount: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface FinanceAuthorityLimitUpdateInput {
  max_authorized_discount?: number;
  is_active?: boolean;
  effective_from?: string;
  effective_until?: string | null;
}

export interface FinanceAuthorityLimitListResponse {
  items: FinanceAuthorityLimit[];
  total: number;
}

// Phases 108–110: Discount Policy Validation & Violation Detection
export interface DiscountViolation {
  type: string;
  source: string;
  limit: number;
  proposed: number;
  message: string;
  metadata: Record<string, any>;
}

export interface DiscountValidationRequest {
  customer_id: string;
  product_id: string;
  proposed_discount: number;
}

export interface DiscountPolicyEvaluationResponse {
  allowed: boolean;
  proposed_discount: number;
  effective_ceiling: number;
  actor_authority_limit: number | null;
  actor_role: string | null;
  violations: DiscountViolation[];
  evaluated_policies: Record<string, any>;
  evaluated_at: string;
}

