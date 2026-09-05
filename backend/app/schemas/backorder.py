from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class BackorderBase(BaseModel):
    product_id: UUID
    requested_quantity: int = Field(gt=0, description="Total requested items")
    allocated_quantity: int = Field(ge=0, default=0, description="Quantity immediately allocated")
    notes: Optional[str] = Field(default=None, max_length=500)


class BackorderCreate(BackorderBase):
    pass


class BackorderStatusUpdate(BaseModel):
    status: Optional[str] = Field(default="CANCELLED", pattern="^(OPEN|FULFILLED|CANCELLED)$")
    notes: Optional[str] = Field(default=None, max_length=500)


class BackorderCancelRequest(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=500)


class BackorderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    product_id: UUID
    requested_quantity: int
    allocated_quantity: int
    backordered_quantity: int
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BackorderListResponse(BaseModel):
    items: List[BackorderResponse]
    total: int
