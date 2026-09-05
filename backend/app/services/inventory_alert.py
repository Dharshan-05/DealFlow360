"""Inventory Alert Service (Phase 099).

Detects, records, and resolves inventory warnings/critical events:
- OUT_OF_STOCK (CRITICAL): ATP == 0 across all active warehouses or in a specific warehouse
- LOW_STOCK (WARNING): ATP <= threshold (default <= 10 or custom threshold)
- BACKORDER (WARNING): Open backorders pending for product
- Deduplication: Avoids duplicate alerts for the same active condition
- Resolves alerts when conditions normalize or manually acknowledged
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.backorder import Backorder
from app.models.inventory_alert import InventoryAlert
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.inventory_alert import (
    InventoryAlertListResponse,
    InventoryAlertResponse,
    InventoryAlertScanResponse,
)
from app.services.atp import AvailableToPromiseService


class InventoryAlertService:
    LOW_STOCK_THRESHOLD = 10

    @classmethod
    def scan_and_generate_alerts(
        cls,
        db: Session,
        company_id: uuid.UUID,
        low_stock_threshold: int = LOW_STOCK_THRESHOLD,
    ) -> InventoryAlertScanResponse:
        """Scan product warehouse stocks and backorders to generate active alerts without duplication."""
        alerts_generated = 0
        alerts_resolved = 0

        # 1. Inspect all active products
        products = db.query(Product).filter(Product.is_active == True).all()

        for product in products:
            stocks = (
                db.query(WarehouseStock)
                .join(Warehouse, Warehouse.id == WarehouseStock.warehouse_id)
                .filter(
                    WarehouseStock.product_id == product.id,
                    Warehouse.company_id == company_id,
                    Warehouse.is_active == True,
                )
                .all()
            )

            total_qty = sum(s.quantity for s in stocks)
            total_reserved = sum(s.reserved_quantity for s in stocks)
            total_atp = AvailableToPromiseService.calculate_atp(total_qty, total_reserved)

            # Check OUT_OF_STOCK (CRITICAL)
            if total_atp == 0:
                created = cls._ensure_alert(
                    db=db,
                    company_id=company_id,
                    product_id=product.id,
                    warehouse_id=None,
                    alert_type="OUT_OF_STOCK",
                    severity="CRITICAL",
                    message=f"Product '{product.sku}' is completely OUT OF STOCK (ATP: 0 across all warehouses).",
                )
                if created:
                    alerts_generated += 1
            else:
                # If product now has stock, auto-resolve previous active OUT_OF_STOCK alert
                resolved = cls._resolve_existing_alert(db, company_id, product.id, None, "OUT_OF_STOCK")
                if resolved:
                    alerts_resolved += 1

            # Check LOW_STOCK (WARNING)
            if 0 < total_atp <= low_stock_threshold:
                created = cls._ensure_alert(
                    db=db,
                    company_id=company_id,
                    product_id=product.id,
                    warehouse_id=None,
                    alert_type="LOW_STOCK",
                    severity="WARNING",
                    message=f"Product '{product.sku}' is running LOW ON STOCK (Total ATP: {total_atp}, threshold: {low_stock_threshold}).",
                )
                if created:
                    alerts_generated += 1
            elif total_atp > low_stock_threshold:
                resolved = cls._resolve_existing_alert(db, company_id, product.id, None, "LOW_STOCK")
                if resolved:
                    alerts_resolved += 1

            # Check open backorders
            open_backorders = (
                db.query(Backorder)
                .filter(
                    Backorder.company_id == company_id,
                    Backorder.product_id == product.id,
                    Backorder.status == "OPEN",
                )
                .all()
            )
            total_backordered = sum(b.backordered_quantity for b in open_backorders)

            if total_backordered > 0:
                created = cls._ensure_alert(
                    db=db,
                    company_id=company_id,
                    product_id=product.id,
                    warehouse_id=None,
                    alert_type="BACKORDER",
                    severity="WARNING",
                    message=f"Product '{product.sku}' has {len(open_backorders)} open backorder(s) totaling {total_backordered} units.",
                )
                if created:
                    alerts_generated += 1
            else:
                resolved = cls._resolve_existing_alert(db, company_id, product.id, None, "BACKORDER")
                if resolved:
                    alerts_resolved += 1

        db.commit()

        total_active = (
            db.query(InventoryAlert)
            .filter(InventoryAlert.company_id == company_id, InventoryAlert.is_active == True)
            .count()
        )

        return InventoryAlertScanResponse(
            alerts_generated=alerts_generated,
            alerts_resolved=alerts_resolved,
            total_active=total_active,
        )

    @classmethod
    def _ensure_alert(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        warehouse_id: Optional[uuid.UUID],
        alert_type: str,
        severity: str,
        message: str,
    ) -> bool:
        """Create alert if active alert does not already exist (deduplication)."""
        existing = (
            db.query(InventoryAlert)
            .filter(
                InventoryAlert.company_id == company_id,
                InventoryAlert.product_id == product_id,
                InventoryAlert.warehouse_id == warehouse_id,
                InventoryAlert.alert_type == alert_type,
                InventoryAlert.is_active == True,
            )
            .first()
        )
        if existing:
            return False

        alert = InventoryAlert(
            company_id=company_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            is_active=True,
        )
        db.add(alert)
        return True

    @classmethod
    def _resolve_existing_alert(
        cls,
        db: Session,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        warehouse_id: Optional[uuid.UUID],
        alert_type: str,
    ) -> bool:
        """Resolve active alert if exists."""
        alert = (
            db.query(InventoryAlert)
            .filter(
                InventoryAlert.company_id == company_id,
                InventoryAlert.product_id == product_id,
                InventoryAlert.warehouse_id == warehouse_id,
                InventoryAlert.alert_type == alert_type,
                InventoryAlert.is_active == True,
            )
            .first()
        )
        if alert:
            alert.is_active = False
            alert.resolved_at = datetime.now(timezone.utc)
            return True
        return False

    @classmethod
    def resolve_alert(cls, db: Session, alert_id: uuid.UUID, company_id: uuid.UUID) -> InventoryAlert:
        """Manually resolve an active alert."""
        alert = (
            db.query(InventoryAlert)
            .filter(InventoryAlert.id == alert_id, InventoryAlert.company_id == company_id)
            .first()
        )
        if not alert:
            raise NotFoundError(f"Inventory alert with id {alert_id} not found.")

        alert.is_active = False
        alert.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
        return alert

    @classmethod
    def list_alerts(
        cls,
        db: Session,
        company_id: uuid.UUID,
        is_active: Optional[bool] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> InventoryAlertListResponse:
        """List alerts with filtering options."""
        query = db.query(InventoryAlert).filter(InventoryAlert.company_id == company_id)
        if is_active is not None:
            query = query.filter(InventoryAlert.is_active == is_active)
        if severity:
            query = query.filter(InventoryAlert.severity == severity)
        if alert_type:
            query = query.filter(InventoryAlert.alert_type == alert_type)

        total = query.count()
        items = query.order_by(InventoryAlert.created_at.desc()).offset(skip).limit(limit).all()

        return InventoryAlertListResponse(
            items=[InventoryAlertResponse.model_validate(item) for item in items],
            total=total,
        )
