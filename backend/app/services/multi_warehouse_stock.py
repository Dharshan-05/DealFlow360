"""Multi-Warehouse Stock Aggregation Service (Phase 093).

Provides aggregated product stock visibility across all warehouse facilities for a company:
- Total physical quantity
- Total reserved quantity
- Total available-to-promise quantity across all warehouses
- Per-warehouse breakdown with facility metadata and priority ordering
"""
import uuid
from typing import List
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.warehouse import (
    MultiWarehouseStockResponse,
    WarehouseStockDetailItem,
)
from app.services.atp import AvailableToPromiseService


class MultiWarehouseStockService:
    """Service providing multi-warehouse stock visibility and aggregation."""

    @classmethod
    def get_product_multi_warehouse_stock(
        cls,
        db: Session,
        product_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> MultiWarehouseStockResponse:
        """Calculate and return aggregate and per-warehouse inventory breakdown for a product."""
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

        detail_items: List[WarehouseStockDetailItem] = []
        total_physical = 0
        total_reserved = 0
        total_atp = 0

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

            total_physical += physical
            total_reserved += reserved
            total_atp += atp

            detail_items.append(
                WarehouseStockDetailItem(
                    warehouse_id=wh.id,
                    warehouse_code=wh.code,
                    warehouse_name=wh.name,
                    priority=wh.priority,
                    physical_quantity=physical,
                    reserved_quantity=reserved,
                    available_to_promise=atp,
                    is_available=atp > 0,
                )
            )

        return MultiWarehouseStockResponse(
            product_id=product.id,
            product_sku=product.sku,
            product_name=product.name,
            total_physical_quantity=total_physical,
            total_reserved_quantity=total_reserved,
            total_available_quantity=total_atp,
            warehouses_count=len(detail_items),
            warehouses=detail_items,
        )
