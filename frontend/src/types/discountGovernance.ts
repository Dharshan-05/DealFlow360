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

// ==============================================================================
// G23: Discount Intelligence Foundation (Phases 111–115)
// ==============================================================================

// Phase 113: Margin Protection
export interface MarginProtectionRequest {
  product_id: string;
  selling_price?: number;
  min_margin_percentage?: number;
}

export interface MarginProtectionResponse {
  product_id: string;
  selling_price: number;
  unit_cost: number;
  current_margin_percentage: number;
  protected_margin_percentage: number;
  max_discount_from_margin: number;
  is_margin_preserved: boolean;
  reason_code: string;
  reason_description: string;
}

// Phase 112: Maximum Safe Discount
export interface MaximumSafeDiscountRequest {
  customer_id: string;
  product_id: string;
  selling_price?: number;
  min_margin_percentage?: number;
}

export interface MaximumSafeDiscountResponse {
  customer_id: string;
  product_id: string;
  max_safe_discount: number;
  governed_ceiling: number;
  margin_ceiling: number;
  actor_authority_limit: number | null;
  limiting_factor: "MARGIN_LIMIT" | "GOVERNANCE_CEILING" | "ACTOR_AUTHORITY" | "NONE" | string;
  evaluation_breakdown: Record<string, any>;
  evaluated_at: string;
}

// Phase 114: Historical Discount Analysis
export interface HistoricalDiscountSummary {
  sample_size: number;
  average_discount: number | null;
  min_discount: number | null;
  max_discount: number | null;
  latest_discount: number | null;
  latest_applied_at: string | null;
  total_discount_amount: number;
}

export interface HistoricalDiscountAnalysisResponse {
  company_id: string;
  customer_id: string | null;
  product_id: string | null;
  summary: HistoricalDiscountSummary;
  has_history: boolean;
  evaluated_at: string;
}

// Phase 115: Customer Discount Analysis
export interface CustomerDiscountAnalysisResponse {
  customer_id: string;
  customer_name: string;
  customer_code: string;
  tier_name: string | null;
  active_customer_ceiling: number | null;
  history_summary: HistoricalDiscountSummary;
  compliance_rating: "COMPLIANT" | "HIGH_DISCOUNT_CUSTOMER" | "NO_HISTORY" | string;
  insight_summary: string;
  evaluated_at: string;
}

// Phase 111: Recommended Discount Engine
export interface DiscountRecommendationRequest {
  customer_id: string;
  product_id: string;
  selling_price?: number;
  min_margin_percentage?: number;
  benchmark_discount?: number;
}

export interface DiscountRecommendationResponse {
  customer_id: string;
  product_id: string;
  recommended_discount: number;
  max_safe_discount: number;
  governed_ceiling: number;
  margin_ceiling: number;
  customer_historical_avg: number | null;
  reason_code: "HISTORICAL_ALIGNMENT" | "MAX_SAFE_CLAMPED" | "MARGIN_CONSTRAINED" | "CEILING_CONSTRAINED" | "DEFAULT_BENCHMARK" | string;
  reason_summary: string;
  evaluation_details: Record<string, any>;
  evaluated_at: string;
}


