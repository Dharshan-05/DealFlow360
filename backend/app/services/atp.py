import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.warehouse import ATPResponse, StockAvailabilityResponse


class AvailableToPromiseService:
    """Service providing deterministic Available-to-Promise (ATP) calculations
    and stock availability evaluations (Phases 088, 090).
    """

    @staticmethod
    def calculate_atp(physical_stock: int, reserved_stock: int) -> int:
        """Deterministic formula: ATP = max(physical_stock - reserved_stock, 0).
        Enforces that reserved stock cannot cause negative ATP.
        """
        if physical_stock < 0:
            raise ValidationError("Physical stock cannot be negative.")
        if reserved_stock < 0:
            raise ValidationError("Reserved stock cannot be negative.")
        if reserved_stock > physical_stock:
            raise ValidationError(
                f"Data inconsistency: reserved stock ({reserved_stock}) exceeds physical stock ({physical_stock})."
            )
        return max(physical_stock - reserved_stock, 0)

    @classmethod
    def get_atp(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> ATPResponse:
        """Calculate and return ATP for a given warehouse and product pairing (Phase 090)."""
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        stock = (
            db.query(WarehouseStock)
            .filter(
                WarehouseStock.warehouse_id == warehouse_id,
                WarehouseStock.product_id == product_id,
            )
            .first()
        )

        physical_stock = stock.quantity if stock else 0
        reserved_stock = stock.reserved_quantity if stock else 0
        atp = cls.calculate_atp(physical_stock, reserved_stock)

        return ATPResponse(
            product_id=product_id,
            warehouse_id=warehouse_id,
            physical_stock=physical_stock,
            reserved_stock=reserved_stock,
            available_to_promise=atp,
            is_available=atp > 0,
        )

    @classmethod
    def check_availability(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> StockAvailabilityResponse:
        """Evaluate stock availability for a given warehouse and product pairing (Phase 088)."""
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        stock = (
            db.query(WarehouseStock)
            .filter(
                WarehouseStock.warehouse_id == warehouse_id,
                WarehouseStock.product_id == product_id,
            )
            .first()
        )

        physical_stock = stock.quantity if stock else 0
        reserved_stock = stock.reserved_quantity if stock else 0
        available_qty = cls.calculate_atp(physical_stock, reserved_stock)

        return StockAvailabilityResponse(
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            warehouse_id=warehouse.id,
            warehouse_name=warehouse.name,
            warehouse_code=warehouse.code,
            stock_quantity=physical_stock,
            reserved_quantity=reserved_stock,
            available_quantity=available_qty,
            is_available=available_qty > 0,
        )
