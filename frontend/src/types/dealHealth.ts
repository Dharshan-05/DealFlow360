export type DealHealthClassification = "HEALTHY" | "WATCH" | "AT_RISK" | "CRITICAL";

export interface DealHealthSummaryCard {
  total_active_deals: number;
  healthy_deals_count: number;
  watch_deals_count: number;
  at_risk_deals_count: number;
  critical_deals_count: number;
  avg_health_score: number;
  avg_conversion_probability: number;
  avg_stall_probability: number;
  avg_delay_probability: number;
  total_anomalies_count: number;
  open_alerts_count: number;
  unresolved_critical_alerts_count: number;
  pending_nudges_count: number;
  pending_escalations_count: number;
}

export interface RankedDealHealthItem {
  deal_id: string;
  deal_code: string;
  title: string;
  customer_name: string;
  customer_tier: string;
  sales_rep_name?: string;
  deal_value: number;
  stage: string;
  health_score: number;
  classification: string;
  conversion_pct: number;
  stall_pct: number;
  delay_pct: number;
  primary_risk: string;
  created_at: string;
}

export interface DealHealthAlertResponse {
  id: string;
  company_id: string;
  deal_id: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  health_score: number;
  anomaly_score?: number;
  recommended_action?: string;
  status: string;
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

export interface DealHealthRecommendationResponse {
  id: string;
  company_id: string;
  deal_id: string;
  recommendation_type: string;
  priority: string;
  title: string;
  explanation: string;
  triggering_signal: string;
  suggested_action: string;
  status: string;
  created_at: string;
}

export interface DealHealthDashboardResponse {
  summary: DealHealthSummaryCard;
  health_distribution: Record<string, number>;
  trend_series: Array<{ date: string; avg_score: number }>;
  critical_deals: RankedDealHealthItem[];
  at_risk_deals: RankedDealHealthItem[];
  stalled_deals: RankedDealHealthItem[];
  discount_anomalies: RankedDealHealthItem[];
  approval_bottlenecks: RankedDealHealthItem[];
  delivery_risks: RankedDealHealthItem[];
  recommendations: DealHealthRecommendationResponse[];
  open_alerts: DealHealthAlertResponse[];
}

export interface DealHealthPredictionResponse {
  deal_id: string;
  health_score: number;
  classification: DealHealthClassification;
  conversion_probability: number;
  conversion_percentage: number;
  stall_probability: number;
  stall_percentage: number;
  stall_risk_level: string;
  delay_probability: number;
  delay_percentage: number;
  delay_risk_level: string;
  anomaly_detected: boolean;
  anomaly_score: number;
  primary_risk_factors: string[];
  positive_factors: string[];
  model_version: string;
}

