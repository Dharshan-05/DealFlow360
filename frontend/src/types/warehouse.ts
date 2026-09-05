/**
 * TypeScript Interfaces for Warehouse & Inventory (G18: Phases 086–090).
 */

export interface Warehouse {
  id: string;
  company_id: string;
  code: string;
  name: string;
  description: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  postal_code: string | null;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
  total_stock_items: number;
  total_physical_stock: number;
  total_reserved_stock: number;
  total_atp: number;
}

export interface WarehouseCreateInput {
  code: string;
  name: string;
  description?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  postal_code?: string | null;
  is_active?: boolean;
  priority?: number;
}

export interface WarehouseUpdateInput {
  name?: string;
  description?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  postal_code?: string | null;
  is_active?: boolean;
  priority?: number;
}

export interface WarehouseListResponse {
  items: Warehouse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface WarehouseStock {
  id: string;
  warehouse_id: string;
  product_id: string;
  quantity: number;
  reserved_quantity: number;
  available_to_promise: number;
  is_available: boolean;
  product_sku: string | null;
  product_name: string | null;
  product_unit: string | null;
  category_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface WarehouseStockListResponse {
  warehouse_id: string;
  warehouse_code: string;
  warehouse_name: string;
  items: WarehouseStock[];
  total: number;
  total_physical: number;
  total_reserved: number;
  total_atp: number;
}

export interface WarehouseStockCreateInput {
  product_id: string;
  quantity: number;
  reserved_quantity?: number;
}

export interface WarehouseStockUpdateInput {
  quantity: number;
}

export interface StockReserveReleaseInput {
  quantity: number;
}

export interface StockAvailability {
  product_id: string;
  product_name: string;
  product_sku: string;
  warehouse_id: string;
  warehouse_name: string;
  warehouse_code: string;
  stock_quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  is_available: boolean;
}

export interface ATPData {
  product_id: string;
  warehouse_id: string;
  physical_stock: number;
  reserved_stock: number;
  available_to_promise: number;
  is_available: boolean;
}

// ==============================================================================
// Phase 092 — Warehouse Selection Types
// ==============================================================================

export interface WarehouseSelectionCandidate {
  warehouse_id: string;
  warehouse_code: string;
  warehouse_name: string;
  priority: number;
  physical_quantity: number;
  reserved_quantity: number;
  available_to_promise: number;
  can_fulfill_full: boolean;
}

export interface WarehouseSelectionResponse {
  product_id: string;
  requested_quantity: number;
  selected_warehouse_id: string | null;
  selected_warehouse_code: string | null;
  selected_warehouse_name: string | null;
  selected_warehouse_priority: number | null;
  is_fully_fulfillable: boolean;
  requires_multi_warehouse: boolean;
  candidates: WarehouseSelectionCandidate[];
}

// ==============================================================================
// Phase 093 — Multi-Warehouse Stock Types
// ==============================================================================

export interface WarehouseStockDetailItem {
  warehouse_id: string;
  warehouse_code: string;
  warehouse_name: string;
  priority: number;
  physical_quantity: number;
  reserved_quantity: number;
  available_to_promise: number;
  is_available: boolean;
}

export interface MultiWarehouseStockResponse {
  product_id: string;
  product_sku: string;
  product_name: string;
  total_physical_quantity: number;
  total_reserved_quantity: number;
  total_available_quantity: number;
  warehouses_count: number;
  warehouses: WarehouseStockDetailItem[];
}

// ==============================================================================
// Phase 094 — Fulfillment Allocation Types
// ==============================================================================

export interface AllocationItem {
  warehouse_id: string;
  warehouse_code: string;
  warehouse_name: string;
  priority: number;
  available_to_promise: number;
  allocated_quantity: number;
}

export interface AllocationResponse {
  product_id: string;
  requested_quantity: number;
  total_allocated: number;
  unallocated_quantity: number;
  is_fully_allocated: boolean;
  allocations: AllocationItem[];
}

// ==============================================================================
// Phase 095 — Multi-Warehouse Stock Reservation Types
// ==============================================================================

export interface WarehouseReservationItem {
  warehouse_id: string;
  warehouse_code: string;
  reserved_quantity: number;
  remaining_atp: number;
}

export interface MultiWarehouseReservationResponse {
  product_id: string;
  requested_quantity: number;
  total_reserved: number;
  unallocated_quantity: number;
  is_fully_reserved: boolean;
  reservations: WarehouseReservationItem[];
}

export interface WarehouseReleaseItem {
  warehouse_id: string;
  quantity: number;
}

export interface MultiWarehouseReleaseResponse {
  product_id: string;
  total_released: number;
  releases: WarehouseReservationItem[];
}

