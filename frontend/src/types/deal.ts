export type DealStage =
  | "NEW"
  | "QUALIFIED"
  | "PROPOSAL"
  | "NEGOTIATION"
  | "CLOSED_WON"
  | "CLOSED_LOST";

export type DealActivityType =
  | "NOTE"
  | "CALL"
  | "EMAIL"
  | "MEETING"
  | "TASK"
  | "FOLLOW_UP"
  | "STAGE_CHANGE"
  | "APPROVAL"
  | "QUOTE_SENT"
  | "QUOTE_ACCEPTED"
  | "QUOTE_REJECTED";

export type DealMarginRisk = "HEALTHY" | "MODERATE" | "THIN" | "CRITICAL";

export interface DealProduct {
  id: string;
  deal_id: string;
  product_id: string;
  product_name?: string | null;
  product_sku?: string | null;
  quotation_line_item_id?: string | null;
  quantity: number | string;
  unit_price: number | string;
  unit_cost: number | string;
  discount_percent: number | string;
  tax_rate: number | string;
  subtotal: number | string;
  discount_amount: number | string;
  taxable_amount: number | string;
  tax_amount: number | string;
  total_amount: number | string;
  total_cost: number | string;
  gross_profit: number | string;
  margin_percentage: number | string;
  notes?: string | null;
  created_at: string;
}

export interface DealProductCreateInput {
  product_id: string;
  quantity: number;
  unit_price?: number;
  discount_percent?: number;
  tax_rate?: number;
  notes?: string;
}

export interface DealMarginResponse {
  deal_id: string;
  deal_code: string;
  total_revenue: number | string;
  total_cost: number | string;
  gross_profit: number | string;
  gross_margin_percentage: number | string;
  discounted_margin_percentage: number | string;
  margin_risk: DealMarginRisk;
  is_negative_margin: boolean;
}

export interface DealProbabilityFactor {
  factor: string;
  impact_pct: number;
  description: string;
}

export interface DealProbabilityResponse {
  deal_id: string;
  probability: number;
  stage: string;
  factors: DealProbabilityFactor[];
  explanation: string;
}

export interface DealForecastResponse {
  deal_id: string;
  deal_code: string;
  deal_value: number | string;
  probability: number;
  weighted_value: number | string;
  stage: string;
  status: string;
}

export interface StageForecastItem {
  stage: string;
  deal_count: number;
  total_value: number | string;
  weighted_value: number | string;
}

export interface PipelineForecastSummary {
  total_deals_count: number;
  open_deals_count: number;
  won_deals_count: number;
  lost_deals_count: number;
  pipeline_value: number | string;
  weighted_pipeline_value: number | string;
  expected_revenue: number | string;
  won_revenue: number | string;
  lost_value: number | string;
  stages: StageForecastItem[];
}

export interface DealActivity {
  id: string;
  deal_id: string;
  activity_type: string;
  title: string;
  description?: string | null;
  actor_id?: string | null;
  actor_name?: string | null;
  activity_metadata?: Record<string, any> | null;
  created_at: string;
}

export interface DealActivityCreateInput {
  activity_type: DealActivityType;
  title: string;
  description?: string;
  activity_metadata?: Record<string, any>;
}

export interface DealTimelineEvent {
  event_id: string;
  source: string;
  event_type: string;
  title: string;
  description?: string | null;
  actor_name?: string | null;
  timestamp: string;
  metadata?: Record<string, any> | null;
}

export interface DealSummary {
  id: string;
  company_id: string;
  customer_id: string;
  customer_name?: string | null;
  deal_code: string;
  title: string;
  deal_value: number | string;
  status: string;
  stage: string;
  sales_rep_name?: string | null;
  owner_id?: string | null;
  quotation_id?: string | null;
  quotation_number?: string | null;
  quotation_version?: number | null;
  probability: number;
  expected_revenue: number | string;
  gross_profit: number | string;
  margin_percentage: number | string;
  closed_date?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DealDetail extends DealSummary {
  subtotal: number | string;
  discount_amount: number | string;
  discount_percent: number | string;
  tax_amount: number | string;
  total_cost: number | string;
  notes?: string | null;
  products: DealProduct[];
  recent_activities: DealActivity[];
}

export interface DealDashboardResponse {
  total_deals: number;
  open_deals: number;
  won_deals: number;
  lost_deals: number;
  pipeline_value: number | string;
  weighted_pipeline: number | string;
  expected_revenue: number | string;
  average_deal_value: number | string;
  win_rate: number;
  deals_by_stage: StageForecastItem[];
  recent_activities: DealActivity[];
  top_deals: DealSummary[];
}
