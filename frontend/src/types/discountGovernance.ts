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
}

// ==============================================================================
// G24: Discount Intelligence -> Inventory / Deal / Risk / Decision / Automation
// Phases 116–120
// ==============================================================================

// Phase 116: Inventory-Aware Discount
export interface InventoryDiscountSignalRequest {
  product_id: string;
  base_target_discount: number;
}

export interface InventoryDiscountSignalResponse {
  product_id: string;
  total_physical_stock: number;
  total_reserved_stock: number;
  total_available_to_promise: number;
  open_backorders_count: number;
  inventory_signal: "EXCESS_AVAILABLE" | "HEALTHY_STOCK" | "LOW_STOCK" | "OUT_OF_STOCK" | "BACKORDERED" | string;
  adjustment_factor: number;
  suggested_discount: number;
  reason_code: string;
  explanation: string;
  evaluated_at: string;
}

// Phase 117: Deal-Value-Aware Discount
export interface DealValueDiscountSignalRequest {
  product_id: string;
  deal_value?: number;
  quantity?: number;
  selling_price_override?: number;
  base_target_discount: number;
}

export interface DealValueDiscountSignalResponse {
  product_id: string;
  effective_deal_value: number;
  value_tier: "LOW_VALUE" | "STANDARD_VALUE" | "HIGH_VALUE" | "ENTERPRISE_TIER" | string;
  value_incentive_multiplier: number;
  suggested_discount: number;
  reason_code: string;
  explanation: string;
  evaluated_at: string;
}

// Phase 118: Discount Risk Calculation
export interface RiskDimensionScore {
  dimension: string;
  score: number;
  weight: number;
  weighted_score: number;
  details: string;
}

export interface DiscountRiskCalculationRequest {
  customer_id: string;
  product_id: string;
  requested_discount: number;
  deal_value?: number;
  selling_price_override?: number;
  min_margin_percentage?: number;
}

export interface DiscountRiskCalculationResponse {
  customer_id: string;
  product_id: string;
  requested_discount: number;
  overall_risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  primary_risk_factors: string[];
  dimensions: RiskDimensionScore[];
  is_acceptable_risk: boolean;
  risk_summary: string;
  evaluated_at: string;
}

// Phase 119: Discount Decision Engine
export interface DiscountDecisionRequest {
  customer_id: string;
  product_id: string;
  requested_discount: number;
  deal_reference?: string;
  deal_value?: number;
  selling_price_override?: number;
  min_margin_percentage?: number;
}

export interface DiscountDecisionResponse {
  decision_id: string;
  customer_id: string;
  product_id: string;
  requested_discount: number;
  decision: "APPROVED" | "ADJUSTED" | "ESCALATION_REQUIRED" | "REJECTED" | string;
  permitted_discount: number;
  effective_ceiling: number;
  actor_authority_limit: number | null;
  margin_ceiling: number;
  max_safe_discount: number;
  inventory_signal: string;
  deal_value_tier: string;
  risk_level: string;
  limiting_factors: string[];
  is_executable: boolean;
  requires_escalation: boolean;
  escalation_role_needed: string | null;
  decision_summary: string;
  evaluated_at: string;
}

// Phase 120: Automated Discount Application
export interface ApplyDiscountRequest {
  customer_id: string;
  product_id: string;
  requested_discount: number;
  deal_reference: string;
  deal_value?: number;
  selling_price_override?: number;
  min_margin_percentage?: number;
  notes?: string;
}

export interface AppliedDiscountResponse {
  id: string;
  company_id: string;
  customer_id: string;
  product_id: string;
  user_id: string | null;
  deal_reference: string | null;
  decision_id: string | null;
  requested_discount: number;
  applied_discount: number;
  selling_price: number;
  discounted_price: number;
  unit_cost: number;
  margin_percentage: number;
  risk_level: string;
  reason_code: string;
  decision_summary: string | null;
  context_metadata?: Record<string, any>;
  applied_at: string;
  created_at: string;
}

export interface AppliedDiscountListResponse {
  items: AppliedDiscountResponse[];
  total: number;
}

// ==============================================================================
// B04: AI/ML Risk Engine Interfaces (Phases 136–145)
// ==============================================================================

export type ModelType = "XGBOOST" | "LIGHTGBM" | "RANDOM_FOREST";
export type RiskScoreCategory = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ModelEvaluationMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number | null;
  pr_auc: number | null;
  brier_score: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  sample_count: number;
}

export interface ModelArtifact {
  artifact_id: string;
  company_id: string;
  model_type: ModelType;
  feature_names: string[];
  hyperparameters: Record<string, any>;
  train_metrics: ModelEvaluationMetrics;
  val_metrics: ModelEvaluationMetrics | null;
  test_metrics: ModelEvaluationMetrics;
  feature_importances: Record<string, number>;
  random_seed: number;
  trained_at: string;
}

export interface CalibrationMetadata {
  calibration_id: string;
  method: "PLATT_SCALING" | "ISOTONIC" | "NONE";
  pre_calibration_brier: number;
  post_calibration_brier: number;
  brier_improvement_pct: number;
  sigmoid_a: number;
  sigmoid_b: number;
  validation_sample_count: number;
  calibrated_at: string;
}

export interface FeatureContribution {
  feature_name: string;
  feature_value: number;
  contribution: number;
  direction: "risk_increasing" | "risk_reducing";
  relative_impact_pct: number;
}

export interface RiskFactorDetail {
  feature_name: string;
  display_name: string;
  feature_value: number;
  contribution: number;
  direction: "risk_increasing" | "risk_reducing";
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "BENEFICIAL";
  description: string;
}

export interface RiskPredictionRequest {
  deal_value: number;
  requested_discount_pct: number;
  selling_price: number;
  unit_cost: number;
  customer_tenure_days?: number;
  customer_tier?: string;
  product_category?: string;
  inventory_signal?: string;
  lifetime_orders?: number;
  lifetime_revenue?: number;
  payment_default_ratio?: number;
  historical_avg_discount_pct?: number;
  historical_avg_margin_pct?: number;
  deal_reference?: string;
}

export interface RiskPredictionResponse {
  prediction_id: string;
  company_id: string;
  deal_reference: string | null;
  raw_probability: number;
  risk_probability: number;
  risk_score: number;
  risk_classification: RiskScoreCategory;
  model_type: ModelType;
  artifact_id: string;
  is_calibrated: boolean;
  top_risk_increasing_factors: RiskFactorDetail[];
  top_risk_reducing_factors: RiskFactorDetail[];
  feature_contributions: FeatureContribution[];
  evaluated_at: string;
}

export interface RiskDistributionBucket {
  score_range: string;
  count: number;
  percentage: number;
}

export interface AIRiskDashboardSummary {
  company_id: string;
  total_evaluated_deals: number;
  low_risk_count: number;
  medium_risk_count: number;
  high_risk_count: number;
  critical_risk_count: number;
  average_risk_score: number;
  risk_distribution: RiskDistributionBucket[];
  champion_model: ModelArtifact | null;
  calibration_status: CalibrationMetadata | null;
  recent_evaluated_deals: RiskPredictionResponse[];
  generated_at: string;
}




