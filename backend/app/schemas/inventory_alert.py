from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class InventoryAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    product_id: UUID
    warehouse_id: Optional[UUID] = None
    alert_type: str
    severity: str
    message: str
    is_active: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None


class InventoryAlertListResponse(BaseModel):
    items: List[InventoryAlertResponse]
    total: int


class InventoryAlertResolveRequest(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=500)


class InventoryAlertScanResponse(BaseModel):
    alerts_generated: int
    alerts_resolved: int
    total_active: int
