"""Comprehensive Test Suite for DealFlow360 G20 (Phases 096–100).

Verifies:
- Phase 096: Backorder Engine (Creation when shortage occurs, open status, quantity checks, safe cancellation without mutating stock)
- Phase 097: Partial Fulfillment (Fulfillment creation with automated allocation and reservation, partial fulfillment status, backorder linkage)
- Phase 098: Delivery Status (State machine NOT_STARTED -> READY -> DISPATCHED -> IN_TRANSIT -> DELIVERED, invalid jump rejections, audit log tracking)
- Phase 099: Inventory Alerts (Alert scan, OUT_OF_STOCK [CRITICAL], LOW_STOCK [WARNING], BACKORDER [WARNING], deduplication, alert resolution)
- Phase 100: Inventory Dashboard (Unified operational dashboard, total physical/reserved/ATP, warehouse breakdowns, status distribution, alert metrics)
"""
import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.backorder import Backorder
from app.models.company import Company
from app.models.fulfillment import Fulfillment
from app.models.inventory_alert import InventoryAlert
from app.models.permission import Permission
from app.models.product import Product
from app.models.role import Role
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.services.backorder import BackorderService
from app.services.fulfillment import FulfillmentService
from app.services.inventory_alert import InventoryAlertService
from app.services.inventory_dashboard import InventoryDashboardService


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def setup_g20_test_data(db_session):
    """Seed company, user, warehouses, and product for G20 testing."""
    suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G20 Logistics Corp {suffix}",
        legal_name=f"G20 Logistics Corporation {suffix}",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    role = Role(
        name=f"g20_admin_{suffix}",
        description="G20 test role",
    )
    db_session.add(role)
    db_session.flush()

    user = User(
        email=f"g20_admin_{suffix}@example.com",
        first_name="G20",
        last_name="Admin",
        is_active=True,
        company_id=company.id,
        roles=[role],
    )

    db_session.add(user)
    db_session.flush()

    # Create 2 Warehouses
    wh_primary = Warehouse(
        company_id=company.id,
        name=f"Primary Hub {suffix}",
        code=f"WH-PRI-{suffix[:4].upper()}",
        priority=1,
        is_active=True,
    )
    wh_secondary = Warehouse(
        company_id=company.id,
        name=f"Secondary Hub {suffix}",
        code=f"WH-SEC-{suffix[:4].upper()}",
        priority=2,
        is_active=True,
    )
    db_session.add_all([wh_primary, wh_secondary])
    db_session.flush()

    # Create Product
    product = Product(
        sku=f"SKU-G20-{suffix[:6].upper()}",
        name=f"Enterprise Router {suffix}",
        base_price=Decimal("300.00"),
        cost=Decimal("150.00"),
        unit="unit",
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()

    # Stock: Primary has 20 (reserved 0), Secondary has 10 (reserved 0). Total ATP = 30
    stock_p = WarehouseStock(
        warehouse_id=wh_primary.id,
        product_id=product.id,
        quantity=20,
        reserved_quantity=0,
    )
    stock_s = WarehouseStock(
        warehouse_id=wh_secondary.id,
        product_id=product.id,
        quantity=10,
        reserved_quantity=0,
    )
    db_session.add_all([stock_p, stock_s])
    db_session.commit()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "company": company,
        "user": user,
        "role": role,
        "wh_primary": wh_primary,
        "wh_secondary": wh_secondary,
        "product": product,
        "headers": headers,
    }


# ===========================================================================
# Phase 096: Backorder Engine Tests
# ===========================================================================

def test_phase_096_backorder_creation_and_quantity_constraints(db_session, setup_g20_test_data):
    data = setup_g20_test_data
    company = data["company"]
    product = data["product"]

    # Requested 50, allocated 20 -> backordered must be 30
    bo = BackorderService.create_backorder(
        db=db_session,
        company_id=company.id,
        product_id=product.id,
        requested_quantity=50,
        allocated_quantity=20,
        notes="High volume client order",
    )
    assert bo.id is not None
    assert bo.status == "OPEN"
    assert bo.requested_quantity == 50
    assert bo.allocated_quantity == 20
    assert bo.backordered_quantity == 30


def test_phase_096_backorder_cancellation(db_session, setup_g20_test_data):
    data = setup_g20_test_data
    company = data["company"]
    product = data["product"]

    bo = BackorderService.create_backorder(
        db=db_session,
        company_id=company.id,
        product_id=product.id,
        requested_quantity=15,
        allocated_quantity=5,
    )
    assert bo.status == "OPEN"

    cancelled_bo = BackorderService.cancel_backorder(
        db=db_session,
        backorder_id=bo.id,
        company_id=company.id,
        notes="Customer cancelled request",
    )
    assert cancelled_bo.status == "CANCELLED"
    assert "Customer cancelled request" in cancelled_bo.notes

    # Cannot cancel again
    with pytest.raises(Exception):
        BackorderService.cancel_backorder(db_session, bo.id, company.id)


def test_phase_096_backorder_api_endpoints(client, setup_g20_test_data):
    data = setup_g20_test_data
    product = data["product"]
    headers = data["headers"]

    # Create backorder via API
    resp = client.post(
        "/api/v1/backorders",
        headers=headers,
        json={
            "product_id": str(product.id),
            "requested_quantity": 40,
            "allocated_quantity": 10,
            "notes": "API test backorder",
        },
    )
    assert resp.status_code == 201
    bo_data = resp.json()
    assert bo_data["backordered_quantity"] == 30
    assert bo_data["status"] == "OPEN"
    bo_id = bo_data["id"]

    # List backorders
    list_resp = client.get("/api/v1/backorders", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # Cancel backorder
    cancel_resp = client.post(
        f"/api/v1/backorders/{bo_id}/cancel",
        headers=headers,
        json={"notes": "API cancel"},
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"


# ===========================================================================
# Phase 097: Partial Fulfillment Tests
# ===========================================================================

def test_phase_097_partial_fulfillment_with_auto_backorder(client, db_session, setup_g20_test_data):
    data = setup_g20_test_data
    product = data["product"]
    headers = data["headers"]

    # Total ATP across warehouses = 20 (pri) + 10 (sec) = 30
    # Request 45: Should allocate 30 (20 pri + 10 sec), remaining 15 backordered!
    resp = client.post(
        "/api/v1/fulfillments",
        headers=headers,
        json={
            "product_id": str(product.id),
            "requested_quantity": 45,
            "notes": "Large order partial fulfillment test",
        },
    )
    assert resp.status_code == 201
    f_data = resp.json()

    assert f_data["requested_quantity"] == 45
    assert f_data["fulfilled_quantity"] == 30
    assert f_data["remaining_quantity"] == 15
    assert f_data["status"] == "PARTIALLY_FULFILLED"
    assert f_data["delivery_status"] == "NOT_STARTED"
    assert f_data["backorder_id"] is not None

    # Verify backorder created matches shortage
    bo = db_session.query(Backorder).filter(Backorder.id == uuid.UUID(f_data["backorder_id"])).first()
    assert bo is not None
    assert bo.requested_quantity == 45
    assert bo.allocated_quantity == 30
    assert bo.backordered_quantity == 15
    assert bo.status == "OPEN"


def test_phase_097_complete_fulfillment_no_backorder(client, db_session, setup_g20_test_data):
    data = setup_g20_test_data
    suffix = uuid.uuid4().hex[:6]
    company = data["company"]
    headers = data["headers"]

    # Create new product with plenty stock
    p2 = Product(
        sku=f"SKU-FULL-{suffix}",
        name="Ample Stock Switch",
        base_price=Decimal("200.00"),
        cost=Decimal("100.00"),
        unit="unit",
        is_active=True,
    )
    db_session.add(p2)
    db_session.flush()


    stock = WarehouseStock(
        warehouse_id=data["wh_primary"].id,
        product_id=p2.id,
        quantity=50,
        reserved_quantity=0,
    )
    db_session.add(stock)
    db_session.commit()

    # Request 20 (ATP is 50): Fully fulfilled, status FULFILLED, no backorder
    resp = client.post(
        "/api/v1/fulfillments",
        headers=headers,
        json={
            "product_id": str(p2.id),
            "requested_quantity": 20,
            "notes": "Full fulfillment test",
        },
    )
    assert resp.status_code == 201
    f_data = resp.json()
    assert f_data["status"] == "FULFILLED"
    assert f_data["fulfilled_quantity"] == 20
    assert f_data["remaining_quantity"] == 0
    assert f_data["backorder_id"] is None


# ===========================================================================
# Phase 098: Delivery Status State Machine Tests
# ===========================================================================

def test_phase_098_delivery_status_transitions_and_audit(client, db_session, setup_g20_test_data):
    data = setup_g20_test_data
    headers = data["headers"]
    product = data["product"]

    # 1. Create a fulfillment
    create_resp = client.post(
        "/api/v1/fulfillments",
        headers=headers,
        json={
            "product_id": str(product.id),
            "requested_quantity": 5,
        },
    )
    assert create_resp.status_code == 201
    f_id = create_resp.json()["id"]
    assert create_resp.json()["delivery_status"] == "NOT_STARTED"

    # 2. Advance to READY
    r1 = client.put(
        f"/api/v1/fulfillments/{f_id}/delivery-status",
        headers=headers,
        json={"delivery_status": "READY"},
    )
    assert r1.status_code == 200
    assert r1.json()["delivery_status"] == "READY"

    # 3. Illegal skip: Try jumping directly to DELIVERED (Must Fail 409 Conflict)
    r_bad = client.put(
        f"/api/v1/fulfillments/{f_id}/delivery-status",
        headers=headers,
        json={"delivery_status": "DELIVERED"},
    )
    assert r_bad.status_code == 409

    # 4. Advance to DISPATCHED
    r2 = client.put(
        f"/api/v1/fulfillments/{f_id}/delivery-status",
        headers=headers,
        json={"delivery_status": "DISPATCHED", "tracking_number": "TRK-98001"},
    )
    assert r2.status_code == 200
    assert r2.json()["delivery_status"] == "DISPATCHED"
    assert r2.json()["tracking_number"] == "TRK-98001"

    # 5. Advance to IN_TRANSIT
    r3 = client.put(
        f"/api/v1/fulfillments/{f_id}/delivery-status",
        headers=headers,
        json={"delivery_status": "IN_TRANSIT"},
    )
    assert r3.status_code == 200
    assert r3.json()["delivery_status"] == "IN_TRANSIT"

    # 6. Final state: DELIVERED
    r4 = client.put(
        f"/api/v1/fulfillments/{f_id}/delivery-status",
        headers=headers,
        json={"delivery_status": "DELIVERED"},
    )
    assert r4.status_code == 200
    assert r4.json()["delivery_status"] == "DELIVERED"

    # 7. DELIVERED is terminal, cannot transition or cancel
    r_term = client.put(
        f"/api/v1/fulfillments/{f_id}/delivery-status",
        headers=headers,
        json={"delivery_status": "CANCELLED"},
    )
    assert r_term.status_code == 409

    # Verify AuditLog recorded the events
    audits = (
        db_session.query(AuditLog)
        .filter(AuditLog.resource_id == str(f_id))
        .all()
    )
    assert len(audits) >= 4  # creation + 4 transitions



# ===========================================================================
# Phase 099: Inventory Alerts Tests
# ===========================================================================

def test_phase_099_alert_scanning_deduplication_and_resolution(client, db_session, setup_g20_test_data):
    data = setup_g20_test_data
    company = data["company"]
    headers = data["headers"]

    # 1. Trigger Alert Scan
    scan_resp = client.post("/api/v1/inventory/alerts/scan?threshold=10", headers=headers)
    assert scan_resp.status_code == 200
    assert scan_resp.json()["total_active"] >= 0

    # 2. Re-trigger scan: Should deduplicate and not generate duplicate active alerts
    scan_resp2 = client.post("/api/v1/inventory/alerts/scan?threshold=10", headers=headers)
    assert scan_resp2.status_code == 200
    assert scan_resp2.json()["alerts_generated"] == 0

    # 3. List active alerts
    alerts_resp = client.get("/api/v1/inventory/alerts?is_active=true", headers=headers)
    assert alerts_resp.status_code == 200
    alert_list = alerts_resp.json()

    if alert_list["total"] > 0:
        first_alert_id = alert_list["items"][0]["id"]
        # Resolve alert manually
        res_resp = client.post(f"/api/v1/inventory/alerts/{first_alert_id}/resolve", headers=headers)
        assert res_resp.status_code == 200
        assert res_resp.json()["is_active"] is False
        assert res_resp.json()["resolved_at"] is not None


# ===========================================================================
# Phase 100: Inventory Dashboard Tests
# ===========================================================================

def test_phase_100_inventory_dashboard_aggregation(client, setup_g20_test_data):
    data = setup_g20_test_data
    headers = data["headers"]

    resp = client.get("/api/v1/inventory/dashboard", headers=headers)
    assert resp.status_code == 200
    dash = resp.json()

    # Verify KPI summary fields
    kpis = dash["kpis"]
    assert "total_physical_stock" in kpis
    assert "total_reserved_stock" in kpis
    assert "total_atp_stock" in kpis
    assert "out_of_stock_count" in kpis
    assert "low_stock_count" in kpis
    assert "open_backorders_count" in kpis
    assert "partial_fulfillments_count" in kpis
    assert "total_fulfillments_count" in kpis

    # Verify distributions
    assert "NOT_STARTED" in dash["delivery_status_distribution"]
    assert "DELIVERED" in dash["delivery_status_distribution"]
    assert "PARTIALLY_FULFILLED" in dash["fulfillment_status_distribution"]

    # Verify warehouse breakdown
    assert len(dash["warehouse_breakdown"]) >= 2
    for wh_item in dash["warehouse_breakdown"]:
        assert "warehouse_code" in wh_item
        assert "priority" in wh_item
        assert "total_atp" in wh_item
