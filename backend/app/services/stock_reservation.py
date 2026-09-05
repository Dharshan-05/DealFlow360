"""Multi-Warehouse Stock Reservation Service (Phase 095).

Safe, transaction-locked atomic stock reservation across warehouses:
1. Calculates sequential allocation across priority-ordered warehouses using Phase 094 logic.
2. Obtains pessimistic row-level locks (with_for_update()) on affected WarehouseStock rows.
3. Verifies ATP remains strictly sufficient under transaction lock.
4. Atomically increments reserved_quantity for each allocated warehouse stock.
5. Records structured AuditLog entries.
6. Provides atomic multi-warehouse release capabilities.
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.product import Product
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.warehouse import (
    MultiWarehouseReleaseRequest,
    MultiWarehouseReleaseResponse,
    MultiWarehouseReservationResponse,
    WarehouseReservationItem,
)
from app.services.atp import AvailableToPromiseService
from app.services.fulfillment_allocation import FulfillmentAllocationService


class StockReservationService:
    """Atomic multi-warehouse stock reservation and release service."""

    @classmethod
    def reserve_allocation(
        cls,
        db: Session,
        product_id: uuid.UUID,
        requested_quantity: int,
        company_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> MultiWarehouseReservationResponse:
        """Atomically reserve requested quantity across priority warehouses with row locks."""
        if requested_quantity <= 0:
            raise ValidationError("Requested quantity must be strictly greater than 0.")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        # Compute deterministic priority allocation
        allocation = FulfillmentAllocationService.calculate_allocation(
            db=db,
            product_id=product_id,
            requested_quantity=requested_quantity,
            company_id=company_id,
        )

        active_allocations = [a for a in allocation.allocations if a.allocated_quantity > 0]
        if not active_allocations:
            raise ValidationError(
                f"Cannot reserve: no available ATP found for product '{product.sku}' across company warehouses."
            )

        reservation_results: List[WarehouseReservationItem] = []

        # Pessimistic row locking on warehouse stock rows
        for alloc in active_allocations:
            wh_stock = (
                db.query(WarehouseStock)
                .filter(
                    WarehouseStock.warehouse_id == alloc.warehouse_id,
                    WarehouseStock.product_id == product_id,
                )
                .with_for_update()
                .first()
            )

            if not wh_stock:
                raise NotFoundError(
                    f"Warehouse stock record for warehouse {alloc.warehouse_code} not found during reservation lock."
                )

            current_atp = AvailableToPromiseService.calculate_atp(wh_stock.quantity, wh_stock.reserved_quantity)
            if current_atp < alloc.allocated_quantity:
                raise ConflictError(
                    f"Concurrency conflict: ATP for warehouse {alloc.warehouse_code} changed from "
                    f"{alloc.available_to_promise} to {current_atp}, cannot fulfill allocation of {alloc.allocated_quantity}."
                )

            # Atomically increment reserved_quantity
            wh_stock.reserved_quantity += alloc.allocated_quantity
            remaining_atp = AvailableToPromiseService.calculate_atp(wh_stock.quantity, wh_stock.reserved_quantity)

            reservation_results.append(
                WarehouseReservationItem(
                    warehouse_id=alloc.warehouse_id,
                    warehouse_code=alloc.warehouse_code,
                    reserved_quantity=alloc.allocated_quantity,
                    remaining_atp=remaining_atp,
                )
            )

            if current_user:
                audit = AuditLog(
                    action="MULTI_WAREHOUSE_RESERVE",
                    resource_type="warehouse_stock",
                    resource_id=wh_stock.id,
                    user_id=current_user.id,
                    company_id=company_id,
                    context_metadata={
                        "product_sku": product.sku,
                        "warehouse_code": alloc.warehouse_code,
                        "reserved_amount": alloc.allocated_quantity,
                        "remaining_atp": remaining_atp,
                    },
                )
                db.add(audit)

        db.commit()

        total_reserved = sum(r.reserved_quantity for r in reservation_results)
        unallocated = requested_quantity - total_reserved

        return MultiWarehouseReservationResponse(
            product_id=product.id,
            requested_quantity=requested_quantity,
            total_reserved=total_reserved,
            unallocated_quantity=unallocated,
            is_fully_reserved=unallocated == 0,
            reservations=reservation_results,
        )

    @classmethod
    def release_allocation(
        cls,
        db: Session,
        product_id: uuid.UUID,
        release_req: MultiWarehouseReleaseRequest,
        company_id: uuid.UUID,
        current_user: Optional[User] = None,
    ) -> MultiWarehouseReleaseResponse:
        """Atomically release specified reserved quantities across warehouses."""
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        released_results: List[WarehouseReservationItem] = []
        total_released = 0

        for rel in release_req.releases:
            if rel.quantity <= 0:
                raise ValidationError("Release quantity must be strictly greater than 0.")

            wh = (
                db.query(Warehouse)
                .filter(Warehouse.id == rel.warehouse_id, Warehouse.company_id == company_id)
                .first()
            )
            if not wh:
                raise NotFoundError(f"Warehouse with id {rel.warehouse_id} not found for this company.")

            wh_stock = (
                db.query(WarehouseStock)
                .filter(
                    WarehouseStock.warehouse_id == rel.warehouse_id,
                    WarehouseStock.product_id == product_id,
                )
                .with_for_update()
                .first()
            )

            if not wh_stock:
                raise NotFoundError(
                    f"Warehouse stock record for warehouse {wh.code} not found."
                )

            if wh_stock.reserved_quantity < rel.quantity:
                raise ValidationError(
                    f"Cannot release {rel.quantity} units from warehouse {wh.code}: "
                    f"only {wh_stock.reserved_quantity} units are currently reserved."
                )

            wh_stock.reserved_quantity -= rel.quantity
            total_released += rel.quantity
            remaining_atp = AvailableToPromiseService.calculate_atp(wh_stock.quantity, wh_stock.reserved_quantity)

            released_results.append(
                WarehouseReservationItem(
                    warehouse_id=wh.id,
                    warehouse_code=wh.code,
                    reserved_quantity=rel.quantity,
                    remaining_atp=remaining_atp,
                )
            )

            if current_user:
                audit = AuditLog(
                    action="MULTI_WAREHOUSE_RELEASE",
                    resource_type="warehouse_stock",
                    resource_id=wh_stock.id,
                    user_id=current_user.id,
                    company_id=company_id,
                    context_metadata={
                        "product_sku": product.sku,
                        "warehouse_code": wh.code,
                        "released_amount": rel.quantity,
                        "remaining_atp": remaining_atp,
                    },
                )
                db.add(audit)

        db.commit()

        return MultiWarehouseReleaseResponse(
            product_id=product.id,
            total_released=total_released,
            releases=released_results,
        )
