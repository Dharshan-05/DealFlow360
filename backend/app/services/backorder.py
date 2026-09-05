"""Backorder Service (Phase 096).

Manages lifecycle and operations for inventory shortages when requested quantity
exceeds allocated quantity:
- Creates Backorder records with OPEN status
- Fulfills Backorder when stock becomes available
- Cancels Backorder with clean status transition without mutating stock
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.backorder import Backorder
from app.models.product import Product
from app.schemas.backorder import BackorderCreate, BackorderListResponse, BackorderResponse


class BackorderService:
    @classmethod
    def create_backorder(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        requested_quantity: int,
        allocated_quantity: int,
        notes: Optional[str] = None,
    ) -> Backorder:
        """Create a new Backorder record."""
        if requested_quantity <= 0:
            raise ValidationError("Requested quantity must be strictly greater than 0.")
        if allocated_quantity < 0:
            raise ValidationError("Allocated quantity cannot be negative.")
        if allocated_quantity >= requested_quantity:
            raise ValidationError("Allocated quantity must be strictly less than requested quantity to create a backorder.")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        backordered_quantity = requested_quantity - allocated_quantity

        backorder = Backorder(
            company_id=company_id,
            product_id=product_id,
            requested_quantity=requested_quantity,
            allocated_quantity=allocated_quantity,
            backordered_quantity=backordered_quantity,
            status="OPEN",
            notes=notes,
        )
        db.add(backorder)
        db.commit()
        db.refresh(backorder)
        return backorder

    @classmethod
    def get_backorder(cls, db: Session, backorder_id: uuid.UUID, company_id: uuid.UUID) -> Backorder:
        """Fetch a specific backorder by ID within company scope."""
        backorder = (
            db.query(Backorder)
            .filter(Backorder.id == backorder_id, Backorder.company_id == company_id)
            .first()
        )
        if not backorder:
            raise NotFoundError(f"Backorder with id {backorder_id} not found.")
        return backorder

    @classmethod
    def list_backorders(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> BackorderListResponse:
        """List company backorders with optional status or product filters."""
        query = db.query(Backorder).filter(Backorder.company_id == company_id)
        if product_id:
            query = query.filter(Backorder.product_id == product_id)
        if status:
            query = query.filter(Backorder.status == status)

        total = query.count()
        items = query.order_by(Backorder.created_at.desc()).offset(skip).limit(limit).all()

        return BackorderListResponse(
            items=[BackorderResponse.model_validate(item) for item in items],
            total=total,
        )

    @classmethod
    def cancel_backorder(
        cls,
        db: Session,
        backorder_id: uuid.UUID,
        company_id: uuid.UUID,
        notes: Optional[str] = None,
    ) -> Backorder:
        """Cancel an open backorder."""
        backorder = cls.get_backorder(db, backorder_id, company_id)
        if backorder.status != "OPEN":
            raise ConflictError(f"Cannot cancel backorder in '{backorder.status}' state. Only OPEN backorders can be cancelled.")

        backorder.status = "CANCELLED"
        if notes:
            backorder.notes = f"{backorder.notes or ''}\nCancelled: {notes}".strip()

        db.commit()
        db.refresh(backorder)
        return backorder

    @classmethod
    def fulfill_backorder(
        cls,
        db: Session,
        backorder_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Backorder:
        """Mark an open backorder as fulfilled."""
        backorder = cls.get_backorder(db, backorder_id, company_id)
        if backorder.status != "OPEN":
            raise ConflictError(f"Cannot fulfill backorder in '{backorder.status}' state. Only OPEN backorders can be fulfilled.")

        backorder.status = "FULFILLED"
        db.commit()
        db.refresh(backorder)
        return backorder
