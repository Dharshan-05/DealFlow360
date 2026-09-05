"""Inventory Alerts & Dashboard API Router (Phases 099 & 100)."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.inventory_alert import (
    InventoryAlertListResponse,
    InventoryAlertResolveRequest,
    InventoryAlertResponse,
    InventoryAlertScanResponse,
)
from app.schemas.inventory_dashboard import InventoryDashboardResponse
from app.services.inventory_alert import InventoryAlertService
from app.services.inventory_dashboard import InventoryDashboardService

router = APIRouter(prefix="/inventory", tags=["Inventory Operations"])


@router.get("/dashboard", response_model=InventoryDashboardResponse)
def get_inventory_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch complete aggregated inventory dashboard KPIs and warehouse breakdowns (Phase 100)."""
    return InventoryDashboardService.get_dashboard(
        db=db,
        company_id=current_user.company_id,
    )


@router.get("/alerts", response_model=InventoryAlertListResponse)
def list_inventory_alerts(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, WARNING, INFO)"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type (OUT_OF_STOCK, LOW_STOCK, BACKORDER)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List inventory alerts for company (Phase 099)."""
    return InventoryAlertService.list_alerts(
        db=db,
        company_id=current_user.company_id,
        is_active=is_active,
        severity=severity,
        alert_type=alert_type,
        skip=skip,
        limit=limit,
    )


@router.post("/alerts/scan", response_model=InventoryAlertScanResponse)
def scan_inventory_alerts(
    threshold: int = Query(10, ge=1, le=1000, description="Low stock threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger an on-demand scan of inventory to generate/resolve alerts."""
    return InventoryAlertService.scan_and_generate_alerts(
        db=db,
        company_id=current_user.company_id,
        low_stock_threshold=threshold,
    )


@router.post("/alerts/{alert_id}/resolve", response_model=InventoryAlertResponse)
def resolve_inventory_alert(
    alert_id: UUID,
    payload: Optional[InventoryAlertResolveRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually resolve an inventory alert."""
    return InventoryAlertService.resolve_alert(
        db=db,
        alert_id=alert_id,
        company_id=current_user.company_id,
    )
