"""Fulfillment Allocation Service (Phase 094).

Deterministically allocates requested quantity across multiple warehouses ordered strictly by priority (priority ascending):
1. Loops through active warehouses in priority order.
2. Allocates available stock up to Available-to-Promise (ATP = quantity - reserved_quantity).
3. Continues allocating until the requested quantity is met or all warehouse ATP is exhausted.
4. Reports total allocated quantity and unallocated remaining quantity without creating backorders (Phase 096+).
"""
import uuid
from typing import List
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.warehouse import AllocationItem, AllocationResponse
from app.services.atp import AvailableToPromiseService


class FulfillmentAllocationService:
    """Service to compute sequential fulfillment allocation across priority-ordered warehouses."""

    @classmethod
    def calculate_allocation(
        cls,
        db: Session,
        product_id: uuid.UUID,
        requested_quantity: int,
        company_id: uuid.UUID,
    ) -> AllocationResponse:
        """Deterministically allocate requested quantity across warehouses by priority order."""
        if requested_quantity <= 0:
            raise ValidationError("Requested quantity must be strictly greater than 0.")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        warehouses = (
            db.query(Warehouse)
            .filter(
                Warehouse.company_id == company_id,
                Warehouse.is_active == True,
            )
            .order_by(Warehouse.priority.asc(), Warehouse.code.asc())
            .all()
        )

        remaining_needed = requested_quantity
        total_allocated = 0
        allocations: List[AllocationItem] = []

        for wh in warehouses:
            stock = (
                db.query(WarehouseStock)
                .filter(
                    WarehouseStock.warehouse_id == wh.id,
                    WarehouseStock.product_id == product_id,
                )
                .first()
            )
            physical = stock.quantity if stock else 0
            reserved = stock.reserved_quantity if stock else 0
            atp = AvailableToPromiseService.calculate_atp(physical, reserved)

            allocated_for_wh = 0
            if remaining_needed > 0 and atp > 0:
                allocated_for_wh = min(remaining_needed, atp)
                remaining_needed -= allocated_for_wh
                total_allocated += allocated_for_wh

            allocations.append(
                AllocationItem(
                    warehouse_id=wh.id,
                    warehouse_code=wh.code,
                    warehouse_name=wh.name,
                    priority=wh.priority,
                    available_to_promise=atp,
                    allocated_quantity=allocated_for_wh,
                )
            )

        unallocated = requested_quantity - total_allocated
        is_fully_allocated = unallocated == 0

        return AllocationResponse(
            product_id=product.id,
            requested_quantity=requested_quantity,
            total_allocated=total_allocated,
            unallocated_quantity=unallocated,
            is_fully_allocated=is_fully_allocated,
            allocations=allocations,
        )
