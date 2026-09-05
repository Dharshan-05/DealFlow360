from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class FulfillmentCreate(BaseModel):
    product_id: UUID
    requested_quantity: int = Field(gt=0, description="Quantity requested to fulfill")
    preferred_warehouse_id: Optional[UUID] = None
    customer_tier: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=500)


class FulfillmentDeliveryStatusUpdate(BaseModel):
    delivery_status: str = Field(
        pattern="^(NOT_STARTED|READY|DISPATCHED|IN_TRANSIT|DELIVERED|CANCELLED)$",
        description="Next delivery status in state machine",
    )
    tracking_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)


class FulfillmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    product_id: UUID
    requested_quantity: int
    fulfilled_quantity: int
    remaining_quantity: int
    status: str
    delivery_status: str
    backorder_id: Optional[UUID] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FulfillmentListResponse(BaseModel):
    items: List[FulfillmentResponse]
    total: int
