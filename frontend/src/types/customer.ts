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
