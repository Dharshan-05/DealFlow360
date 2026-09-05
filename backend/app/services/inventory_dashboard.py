"""Inventory Dashboard Service (Phase 100).

Aggregates operational metrics across all company warehouses, fulfillments,
backorders, and stock levels into a unified dashboard representation:
- Physical Stock, Reserved Stock, ATP Stock
- Out-of-Stock and Low-Stock SKU counts
- Open Backorders and Partial Fulfillments
- Delivery status distribution breakdown
- Fulfillment status distribution breakdown
- Warehouse-by-warehouse stock breakdown
- Recent active alerts
"""
import uuid
from typing import Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.backorder import Backorder
from app.models.fulfillment import Fulfillment
from app.models.inventory_alert import InventoryAlert
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.inventory_alert import InventoryAlertResponse
from app.schemas.inventory_dashboard import (
    InventoryDashboardResponse,
    InventoryKPISummary,
    WarehouseStockBreakdown,
)
from app.services.atp import AvailableToPromiseService


class InventoryDashboardService:
    @classmethod
    def get_dashboard(cls, db: Session, company_id: uuid.UUID) -> InventoryDashboardResponse:
        """Compute comprehensive operational dashboard for company inventory."""

        # 1. Active Warehouses
        warehouses = (
            db.query(Warehouse)
            .filter(Warehouse.company_id == company_id, Warehouse.is_active == True)
            .order_by(Warehouse.priority.asc(), Warehouse.code.asc())
            .all()
        )

        total_physical = 0
        total_reserved = 0
        warehouse_breakdowns: List[WarehouseStockBreakdown] = []

        for wh in warehouses:
            stocks = db.query(WarehouseStock).filter(WarehouseStock.warehouse_id == wh.id).all()
            wh_qty = sum(s.quantity for s in stocks)
            wh_res = sum(s.reserved_quantity for s in stocks)
            wh_atp = AvailableToPromiseService.calculate_atp(wh_qty, wh_res)
            sku_count = len(stocks)

            total_physical += wh_qty
            total_reserved += wh_res

            warehouse_breakdowns.append(
                WarehouseStockBreakdown(
                    warehouse_id=wh.id,
                    warehouse_name=wh.name,
                    warehouse_code=wh.code,
                    is_active=wh.is_active,
                    priority=wh.priority,
                    total_quantity=wh_qty,
                    total_reserved=wh_res,
                    total_atp=wh_atp,
                    sku_count=sku_count,
                )
            )

        total_atp = AvailableToPromiseService.calculate_atp(total_physical, total_reserved)

        # 2. Product stock levels across company
        products = db.query(Product).filter(Product.is_active == True).all()
        out_of_stock_count = 0
        low_stock_count = 0


        for prod in products:
            prod_stocks = (
                db.query(WarehouseStock)
                .join(Warehouse, Warehouse.id == WarehouseStock.warehouse_id)
                .filter(
                    WarehouseStock.product_id == prod.id,
                    Warehouse.company_id == company_id,
                    Warehouse.is_active == True,
                )
                .all()
            )
            prod_qty = sum(s.quantity for s in prod_stocks)
            prod_res = sum(s.reserved_quantity for s in prod_stocks)
            prod_atp = AvailableToPromiseService.calculate_atp(prod_qty, prod_res)

            if prod_atp == 0:
                out_of_stock_count += 1
            elif 0 < prod_atp <= 10:
                low_stock_count += 1

        # 3. Backorders KPIs
        open_backorders_count = (
            db.query(Backorder)
            .filter(Backorder.company_id == company_id, Backorder.status == "OPEN")
            .count()
        )

        # 4. Fulfillments KPIs & distributions
        all_fulfillments = db.query(Fulfillment).filter(Fulfillment.company_id == company_id).all()
        total_fulfillments_count = len(all_fulfillments)
        partial_fulfillments_count = sum(1 for f in all_fulfillments if f.status == "PARTIALLY_FULFILLED")

        delivery_distribution: Dict[str, int] = {
            "NOT_STARTED": 0,
            "READY": 0,
            "DISPATCHED": 0,
            "IN_TRANSIT": 0,
            "DELIVERED": 0,
            "CANCELLED": 0,
        }
        for f in all_fulfillments:
            if f.delivery_status in delivery_distribution:
                delivery_distribution[f.delivery_status] += 1
            else:
                delivery_distribution[f.delivery_status] = 1

        fulfillment_distribution: Dict[str, int] = {
            "PENDING": 0,
            "PARTIALLY_FULFILLED": 0,
            "FULFILLED": 0,
        }
        for f in all_fulfillments:
            if f.status in fulfillment_distribution:
                fulfillment_distribution[f.status] += 1
            else:
                fulfillment_distribution[f.status] = 1

        # 5. Recent Active Alerts
        active_alerts = (
            db.query(InventoryAlert)
            .filter(InventoryAlert.company_id == company_id, InventoryAlert.is_active == True)
            .order_by(InventoryAlert.created_at.desc())
            .limit(10)
            .all()
        )

        return InventoryDashboardResponse(
            kpis=InventoryKPISummary(
                total_physical_stock=total_physical,
                total_reserved_stock=total_reserved,
                total_atp_stock=total_atp,
                out_of_stock_count=out_of_stock_count,
                low_stock_count=low_stock_count,
                open_backorders_count=open_backorders_count,
                partial_fulfillments_count=partial_fulfillments_count,
                total_fulfillments_count=total_fulfillments_count,
            ),
            delivery_status_distribution=delivery_distribution,
            fulfillment_status_distribution=fulfillment_distribution,
            warehouse_breakdown=warehouse_breakdowns,
            recent_alerts=[InventoryAlertResponse.model_validate(a) for a in active_alerts],
        )
