/**
 * TypeScript Interfaces for G20 (Phases 096–100):
 * - Backorders (Phase 096)
 * - Partial Fulfillment (Phase 097)
 * - Delivery Status (Phase 098)
 * - Inventory Alerts (Phase 099)
 * - Inventory Dashboard (Phase 100)
 */

export interface Backorder {
  id: string;
  company_id: string;
  product_id: string;
  requested_quantity: number;
  allocated_quantity: number;
  backordered_quantity: number;
  status: 'OPEN' | 'FULFILLED' | 'CANCELLED';
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackorderListResponse {
  items: Backorder[];
  total: number;
}

export interface BackorderCreateInput {
  product_id: string;
  requested_quantity: number;
  allocated_quantity?: number;
  notes?: string | null;
}

export interface Fulfillment {
  id: string;
  company_id: string;
  product_id: string;
  requested_quantity: number;
  fulfilled_quantity: number;
  remaining_quantity: number;
  status: 'PENDING' | 'PARTIALLY_FULFILLED' | 'FULFILLED';
  delivery_status: 'NOT_STARTED' | 'READY' | 'DISPATCHED' | 'IN_TRANSIT' | 'DELIVERED' | 'CANCELLED';
  backorder_id: string | null;
  tracking_number: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface FulfillmentListResponse {
  items: Fulfillment[];
  total: number;
}

export interface FulfillmentCreateInput {
  product_id: string;
  requested_quantity: number;
  preferred_warehouse_id?: string | null;
  customer_tier?: string | null;
  notes?: string | null;
}

export interface FulfillmentDeliveryStatusUpdateInput {
  delivery_status: 'NOT_STARTED' | 'READY' | 'DISPATCHED' | 'IN_TRANSIT' | 'DELIVERED' | 'CANCELLED';
  tracking_number?: string | null;
  notes?: string | null;
}

export interface InventoryAlert {
  id: string;
  company_id: string;
  product_id: string;
  warehouse_id: string | null;
  alert_type: 'OUT_OF_STOCK' | 'LOW_STOCK' | 'BACKORDER';
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  message: string;
  is_active: boolean;
  created_at: string;
  resolved_at: string | null;
}

export interface InventoryAlertListResponse {
  items: InventoryAlert[];
  total: number;
}

export interface InventoryAlertScanResponse {
  alerts_generated: number;
  alerts_resolved: number;
  total_active: number;
}

export interface InventoryKPISummary {
  total_physical_stock: number;
  total_reserved_stock: number;
  total_atp_stock: number;
  out_of_stock_count: number;
  low_stock_count: number;
  open_backorders_count: number;
  partial_fulfillments_count: number;
  total_fulfillments_count: number;
}

export interface WarehouseStockBreakdown {
  warehouse_id: string;
  warehouse_name: string;
  warehouse_code: string;
  is_active: boolean;
  priority: number;
  total_quantity: number;
  total_reserved: number;
  total_atp: number;
  sku_count: number;
}

export interface InventoryDashboardResponse {
  kpis: InventoryKPISummary;
  delivery_status_distribution: Record<string, number>;
  fulfillment_status_distribution: Record<string, number>;
  warehouse_breakdown: WarehouseStockBreakdown[];
  recent_alerts: InventoryAlert[];
}
