from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.inventory_alert import InventoryAlertResponse


class InventoryKPISummary(BaseModel):
    total_physical_stock: int
    total_reserved_stock: int
    total_atp_stock: int
    out_of_stock_count: int
    low_stock_count: int
    open_backorders_count: int
    partial_fulfillments_count: int
    total_fulfillments_count: int


class WarehouseStockBreakdown(BaseModel):
    warehouse_id: UUID
    warehouse_name: str
    warehouse_code: str
    is_active: bool
    priority: int
    total_quantity: int
    total_reserved: int
    total_atp: int
    sku_count: int


class InventoryDashboardResponse(BaseModel):
    kpis: InventoryKPISummary
    delivery_status_distribution: Dict[str, int]
    fulfillment_status_distribution: Dict[str, int]
    warehouse_breakdown: List[WarehouseStockBreakdown]
    recent_alerts: List[InventoryAlertResponse]
