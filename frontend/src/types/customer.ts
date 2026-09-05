/**
 * Customer entity and history types for DealFlow360 (Phases 056–060).
 */

export interface CustomerTier {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  discount_limit: number | string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: string;
  company_id: string;
  customer_code: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  postal_code?: string | null;
  tier_id?: string | null;
  tier?: CustomerTier | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreateInput {
  customer_code: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  tier_id?: string | null;
  is_active?: boolean;
}

export interface CustomerUpdateInput {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  tier_id?: string | null;
  is_active?: boolean;
}

export interface CustomerListResponse {
  items: Customer[];
  total: number;
  skip: number;
  limit: number;
}

export interface CustomerPurchaseHistory {
  id: string;
  customer_id: string;
  order_number: string;
  purchase_date: string;
  total_amount: number | string;
  status: string;
  item_count: number;
  notes?: string | null;
  created_at: string;
}

export interface PurchaseHistoryCreateInput {
  order_number: string;
  purchase_date?: string;
  total_amount: number | string;
  status?: string;
  item_count?: number;
  notes?: string;
}

export interface CustomerDealHistory {
  id: string;
  customer_id: string;
  deal_code: string;
  title: string;
  deal_value: number | string;
  status: string;
  sales_rep_name?: string | null;
  closed_date?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface DealHistoryCreateInput {
  deal_code: string;
  title: string;
  deal_value: number | string;
  status?: string;
  sales_rep_name?: string;
  closed_date?: string;
  notes?: string;
}

// Phase 061: Customer Discount History
export interface CustomerDiscountHistory {
  id: string;
  customer_id: string;
  discount_code: string;
  discount_percentage: number | string;
  discount_amount: number | string;
  deal_reference?: string | null;
  reason?: string | null;
  applied_at: string;
  created_at: string;
}

export interface DiscountHistoryCreateInput {
  discount_code: string;
  discount_percentage?: number | string;
  discount_amount?: number | string;
  deal_reference?: string;
  reason?: string;
  applied_at?: string;
}

// Phase 062: Customer Payment History
export interface CustomerPaymentHistory {
  id: string;
  customer_id: string;
  payment_reference: string;
  amount: number | string;
  status: string;
  payment_method?: string | null;
  transaction_reference?: string | null;
  payment_date: string;
  notes?: string | null;
  created_at: string;
}

export interface PaymentHistoryCreateInput {
  payment_reference: string;
  amount: number | string;
  status?: string;
  payment_method?: string;
  transaction_reference?: string;
  payment_date?: string;
  notes?: string;
}

// Phase 063: Customer LTV
export interface CustomerLtv {
  customer_id: string;
  ltv_amount: number | string;
  total_purchases_count: number;
  total_purchases_amount: number | string;
  total_settled_payments_amount: number | string;
  average_order_value: number | string;
  first_purchase_date?: string | null;
  latest_purchase_date?: string | null;
  calculated_at: string;
}

// Phase 064: Customer Discount Sensitivity
export type DiscountSensitivityLevel = "LOW" | "MODERATE" | "HIGH" | "INSUFFICIENT_DATA";

export interface DiscountSensitivity {
  customer_id: string;
  score: number;
  level: DiscountSensitivityLevel;
  average_discount_percent: number | string;
  discount_frequency_percent: number | string;
  total_orders_evaluated: number;
  discounted_orders_count: number;
  explanation: string;
  evaluated_at: string;
}

// Phase 065: Customer Risk Profile
export type CustomerRiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface CustomerRiskProfile {
  customer_id: string;
  score: number;
  risk_level: CustomerRiskLevel;
  failed_payment_ratio: number | string;
  payment_reliability_score: number;
  account_status: string;
  primary_factors: string[];
  explanation: string;
  evaluated_at: string;
}

// Consolidated Financial Intelligence Envelope
export interface CustomerFinancialIntelligence {
  customer_id: string;
  ltv: CustomerLtv;
  discount_sensitivity: DiscountSensitivity;
  risk_profile: CustomerRiskProfile;
}

