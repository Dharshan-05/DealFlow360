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
