"""Warehouse Selection Service (Phase 092).

Determines the preferred warehouse for a requested product quantity:
1. Evaluates all active warehouses for the company ordered by priority (priority ascending).
2. Calculates ATP for each warehouse.
3. If a warehouse has sufficient ATP to fulfill the entire requested quantity, selects the highest-priority one.
4. If no single warehouse can fulfill the entire quantity, identifies whether multi-warehouse allocation is required.
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.warehouse import (
    WarehouseSelectionCandidate,
    WarehouseSelectionResponse,
)
from app.services.atp import AvailableToPromiseService


class WarehouseSelectionService:
    """Service to determine preferred warehouse for fulfilling a requested product quantity."""

    @classmethod
    def select_warehouse(
        cls,
        db: Session,
        product_id: uuid.UUID,
        requested_quantity: int,
        company_id: uuid.UUID,
    ) -> WarehouseSelectionResponse:
        """Select preferred warehouse for product quantity based on deterministic priority & ATP."""
        if requested_quantity <= 0:
            raise ValidationError("Requested quantity must be strictly greater than 0.")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        # Query all active warehouses for the company ordered by priority ASC, code ASC
        warehouses = (
            db.query(Warehouse)
            .filter(
                Warehouse.company_id == company_id,
                Warehouse.is_active == True,
            )
            .order_by(Warehouse.priority.asc(), Warehouse.code.asc())
            .all()
        )

        candidates: List[WarehouseSelectionCandidate] = []
        selected_wh: Optional[Warehouse] = None
        selected_wh_priority: Optional[int] = None

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
            can_fulfill = atp >= requested_quantity

            candidates.append(
                WarehouseSelectionCandidate(
                    warehouse_id=wh.id,
                    warehouse_code=wh.code,
                    warehouse_name=wh.name,
                    priority=wh.priority,
                    physical_quantity=physical,
                    reserved_quantity=reserved,
                    available_to_promise=atp,
                    can_fulfill_full=can_fulfill,
                )
            )

            # Select first (highest-priority) warehouse with sufficient ATP
            if can_fulfill and selected_wh is None:
                selected_wh = wh
                selected_wh_priority = wh.priority

        total_available = sum(c.available_to_promise for c in candidates)
        is_fully_fulfillable = selected_wh is not None
        requires_multi_warehouse = not is_fully_fulfillable and (total_available >= requested_quantity)

        return WarehouseSelectionResponse(
            product_id=product.id,
            requested_quantity=requested_quantity,
            selected_warehouse_id=selected_wh.id if selected_wh else None,
            selected_warehouse_code=selected_wh.code if selected_wh else None,
            selected_warehouse_name=selected_wh.name if selected_wh else None,
            selected_warehouse_priority=selected_wh_priority,
            is_fully_fulfillable=is_fully_fulfillable,
            requires_multi_warehouse=requires_multi_warehouse,
            candidates=candidates,
        )
