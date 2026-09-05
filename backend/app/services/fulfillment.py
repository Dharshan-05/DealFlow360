"""Fulfillment Service (Phases 097 & 098).

Handles:
- Phase 097: Partial Fulfillment creation, stock allocation and reservation across warehouses,
  and automated backorder linkage when stock is partially allocated or unavailable.
- Phase 098: Strict Delivery Status State Machine:
  NOT_STARTED -> READY -> DISPATCHED -> IN_TRANSIT -> DELIVERED (or CANCELLED prior to DELIVERED).
  Logs status changes in AuditLog.
"""
import uuid
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.fulfillment import Fulfillment
from app.models.product import Product
from app.models.user import User
from app.schemas.fulfillment import (
    FulfillmentCreate,
    FulfillmentDeliveryStatusUpdate,
    FulfillmentListResponse,
    FulfillmentResponse,
)
from app.services.backorder import BackorderService
from app.services.fulfillment_allocation import FulfillmentAllocationService
from app.services.stock_reservation import StockReservationService


class FulfillmentService:
    # Allowed transitions for Phase 098 Delivery State Machine
    VALID_DELIVERY_TRANSITIONS: Dict[str, Set[str]] = {
        "NOT_STARTED": {"READY", "CANCELLED"},
        "READY": {"DISPATCHED", "CANCELLED"},
        "DISPATCHED": {"IN_TRANSIT", "CANCELLED"},
        "IN_TRANSIT": {"DELIVERED"},
        "DELIVERED": set(),  # Terminal state
        "CANCELLED": set(),  # Terminal state
    }

    @classmethod
    def create_fulfillment(
        cls,
        db: Session,
        company_id: uuid.UUID,
        payload: FulfillmentCreate,
        current_user: Optional[User] = None,
    ) -> Fulfillment:
        """Create fulfillment record, allocate stock, reserve allocated stock, and create backorder for shortages."""
        if payload.requested_quantity <= 0:
            raise ValidationError("Requested quantity must be strictly greater than 0.")

        product = db.query(Product).filter(Product.id == payload.product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {payload.product_id} not found.")

        # Compute sequential priority allocation across warehouses
        allocation = FulfillmentAllocationService.calculate_allocation(
            db=db,
            product_id=payload.product_id,
            requested_quantity=payload.requested_quantity,
            company_id=company_id,
        )

        fulfilled_qty = allocation.total_allocated
        unallocated_qty = allocation.unallocated_quantity
        remaining_qty = payload.requested_quantity - fulfilled_qty

        # Reserve allocated stock if any was allocated
        if fulfilled_qty > 0:
            StockReservationService.reserve_allocation(
                db=db,
                product_id=payload.product_id,
                requested_quantity=fulfilled_qty,
                company_id=company_id,
                current_user=current_user,
            )

        # Handle backorder if shortage exists
        backorder_id = None
        if unallocated_qty > 0:
            backorder = BackorderService.create_backorder(
                db=db,
                company_id=company_id,
                product_id=payload.product_id,
                requested_quantity=payload.requested_quantity,
                allocated_quantity=fulfilled_qty,
                notes=payload.notes,
            )
            backorder_id = backorder.id

        # Determine fulfillment status (Phase 097)
        if fulfilled_qty == payload.requested_quantity:
            status = "FULFILLED"
        elif fulfilled_qty > 0:
            status = "PARTIALLY_FULFILLED"
        else:
            status = "PENDING"

        # Initial delivery status
        delivery_status = "NOT_STARTED"

        fulfillment = Fulfillment(
            company_id=company_id,
            product_id=payload.product_id,
            requested_quantity=payload.requested_quantity,
            fulfilled_quantity=fulfilled_qty,
            remaining_quantity=remaining_qty,
            status=status,
            delivery_status=delivery_status,
            backorder_id=backorder_id,
            notes=payload.notes,
        )
        db.add(fulfillment)
        db.commit()
        db.refresh(fulfillment)

        # Audit log creation
        if current_user:
            audit = AuditLog(
                action="FULFILLMENT_CREATED",
                resource_type="fulfillment",
                resource_id=fulfillment.id,
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "status": status,
                    "requested_quantity": payload.requested_quantity,
                    "fulfilled_quantity": fulfilled_qty,
                    "remaining_quantity": remaining_qty,
                    "backorder_id": str(backorder_id) if backorder_id else None,
                },
            )
            db.add(audit)
            db.commit()

        return fulfillment

    @classmethod
    def get_fulfillment(cls, db: Session, fulfillment_id: uuid.UUID, company_id: uuid.UUID) -> Fulfillment:
        """Get fulfillment by ID."""
        fulfillment = (
            db.query(Fulfillment)
            .filter(Fulfillment.id == fulfillment_id, Fulfillment.company_id == company_id)
            .first()
        )
        if not fulfillment:
            raise NotFoundError(f"Fulfillment with id {fulfillment_id} not found.")
        return fulfillment

    @classmethod
    def list_fulfillments(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        delivery_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> FulfillmentListResponse:
        """List company fulfillments with optional filters."""
        query = db.query(Fulfillment).filter(Fulfillment.company_id == company_id)
        if product_id:
            query = query.filter(Fulfillment.product_id == product_id)
        if status:
            query = query.filter(Fulfillment.status == status)
        if delivery_status:
            query = query.filter(Fulfillment.delivery_status == delivery_status)

        total = query.count()
        items = query.order_by(Fulfillment.created_at.desc()).offset(skip).limit(limit).all()

        return FulfillmentListResponse(
            items=[FulfillmentResponse.model_validate(item) for item in items],
            total=total,
        )

    @classmethod
    def update_delivery_status(
        cls,
        db: Session,
        fulfillment_id: uuid.UUID,
        company_id: uuid.UUID,
        payload: FulfillmentDeliveryStatusUpdate,
        current_user: Optional[User] = None,
    ) -> Fulfillment:
        """Validate and transition delivery status (Phase 098 State Machine)."""
        fulfillment = cls.get_fulfillment(db, fulfillment_id, company_id)
        current_status = fulfillment.delivery_status
        next_status = payload.delivery_status

        # Validate legal state transition
        valid_next_states = cls.VALID_DELIVERY_TRANSITIONS.get(current_status, set())
        if next_status not in valid_next_states:
            raise ConflictError(
                f"Invalid delivery status transition from '{current_status}' to '{next_status}'. "
                f"Allowed transitions: {sorted(list(valid_next_states)) if valid_next_states else 'None (Terminal state)'}."
            )

        fulfillment.delivery_status = next_status
        if payload.tracking_number:
            fulfillment.tracking_number = payload.tracking_number
        if payload.notes:
            fulfillment.notes = f"{fulfillment.notes or ''}\nDelivery Update: {payload.notes}".strip()

        db.commit()
        db.refresh(fulfillment)

        # Audit log delivery status transition
        if current_user:
            audit = AuditLog(
                action="DELIVERY_STATUS_UPDATED",
                resource_type="fulfillment",
                resource_id=fulfillment.id,
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={
                    "previous_status": current_status,
                    "new_status": next_status,
                    "tracking_number": payload.tracking_number,
                },
            )
            db.add(audit)
            db.commit()

        return fulfillment
