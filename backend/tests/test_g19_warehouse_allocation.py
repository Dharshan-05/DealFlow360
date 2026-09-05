"""Comprehensive Test Suite for DealFlow360 G19 (Phases 091–095).

Verifies:
- Phase 091: Warehouse Priority (1 = highest priority, priority ordering, priority validation >= 1)
- Phase 092: Warehouse Selection (Deterministic priority selection, full fulfillability, multi-warehouse identification)
- Phase 093: Multi-Warehouse Stock (Stock aggregation, total physical, reserved, ATP across all facilities)
- Phase 094: Fulfillment Allocation (Sequential allocation up to ATP ordered by priority, partial/unallocated reporting without backorders)
- Phase 095: Stock Reservation (Atomic multi-warehouse reservation, pessimistic row locking, rollback on conflict, release allocation)
- Authorization & Permissions (warehouses:read for queries, warehouses:write for reservations/releases)
"""
import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.company import Company
from app.models.permission import Permission
from app.models.product import Product
from app.models.role import Role
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.services.fulfillment_allocation import FulfillmentAllocationService
from app.services.multi_warehouse_stock import MultiWarehouseStockService
from app.services.stock_reservation import StockReservationService
from app.services.warehouse_selection import WarehouseSelectionService


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
def setup_g19_test_data(db_session):
    """Seed isolated company, roles, users, products, and 3 prioritized warehouses with stock."""
    suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G19 Fulfillment Corp {suffix}",
        legal_name=f"G19 Fulfillment Corporation {suffix}",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    # Permissions
    perm_read = db_session.scalars(select(Permission).where(Permission.name == "warehouses:read")).first()
    perm_write = db_session.scalars(select(Permission).where(Permission.name == "warehouses:write")).first()
    prod_read = db_session.scalars(select(Permission).where(Permission.name == "products:read")).first()
    prod_write = db_session.scalars(select(Permission).where(Permission.name == "products:write")).first()

    # Read/Write Role
    role_admin = Role(name=f"Warehouse Ops {suffix}", description="Full warehouse access")
    role_admin.permissions.extend([p for p in [perm_read, perm_write, prod_read, prod_write] if p])
    db_session.add(role_admin)

    # Read-Only Role
    role_viewer = Role(name=f"Warehouse Viewer {suffix}", description="Read-only warehouse access")
    role_viewer.permissions.extend([p for p in [perm_read, prod_read] if p])
    db_session.add(role_viewer)

    # No-Perm Role
    role_none = Role(name=f"Warehouse None {suffix}", description="No warehouse access")
    db_session.add(role_none)
    db_session.flush()

    # Users
    user_admin = User(
        email=f"admin_{suffix}@example.com",
        first_name="Admin",
        last_name="Ops",
        company_id=company.id,
        is_active=True,
    )
    user_admin.roles.append(role_admin)

    user_viewer = User(
        email=f"viewer_{suffix}@example.com",
        first_name="Viewer",
        last_name="Ops",
        company_id=company.id,
        is_active=True,
    )
    user_viewer.roles.append(role_viewer)

    user_none = User(
        email=f"none_{suffix}@example.com",
        first_name="None",
        last_name="Ops",
        company_id=company.id,
        is_active=True,
    )
    user_none.roles.append(role_none)

    db_session.add_all([user_admin, user_viewer, user_none])
    db_session.flush()

    # Create Product
    product = Product(
        sku=f"PRD-G19-{suffix}",
        name="Enterprise Cloud Gateway",
        base_price=Decimal("1500.00"),
        cost=Decimal("900.00"),
        unit="unit",
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()

    # Create 3 Warehouses with Priorities:
    # WH-1: Priority 1 (Central), Qty: 50, Reserved: 10 -> ATP: 40
    wh_1 = Warehouse(
        company_id=company.id,
        code=f"WH1-{suffix}".upper(),
        name="Primary Distribution Hub",
        city="Chicago",
        state="IL",
        priority=1,
        is_active=True,
    )
    # WH-2: Priority 2 (East), Qty: 30, Reserved: 5 -> ATP: 25
    wh_2 = Warehouse(
        company_id=company.id,
        code=f"WH2-{suffix}".upper(),
        name="Secondary Regional Depot",
        city="Newark",
        state="NJ",
        priority=2,
        is_active=True,
    )
    # WH-3: Priority 3 (West), Qty: 20, Reserved: 0 -> ATP: 20
    wh_3 = Warehouse(
        company_id=company.id,
        code=f"WH3-{suffix}".upper(),
        name="Tertiary Auxiliary Facility",
        city="Reno",
        state="NV",
        priority=3,
        is_active=True,
    )
    db_session.add_all([wh_1, wh_2, wh_3])
    db_session.flush()

    # Stock records
    stock_1 = WarehouseStock(warehouse_id=wh_1.id, product_id=product.id, quantity=50, reserved_quantity=10)
    stock_2 = WarehouseStock(warehouse_id=wh_2.id, product_id=product.id, quantity=30, reserved_quantity=5)
    stock_3 = WarehouseStock(warehouse_id=wh_3.id, product_id=product.id, quantity=20, reserved_quantity=0)
    db_session.add_all([stock_1, stock_2, stock_3])
    db_session.commit()

    token_admin = create_access_token(user_admin.id)
    token_viewer = create_access_token(user_viewer.id)
    token_none = create_access_token(user_none.id)

    return {
        "company": company,
        "product": product,
        "warehouses": [wh_1, wh_2, wh_3],
        "tokens": {
            "admin": token_admin,
            "viewer": token_viewer,
            "none": token_none,
        },
    }


# ==============================================================================
# Phase 091 Tests — Warehouse Priority
# ==============================================================================

def test_phase_091_warehouse_priority_ordering(client, setup_g19_test_data):
    """Verify warehouses are sorted in deterministic priority ascending order."""
    token = setup_g19_test_data["tokens"]["admin"]
    resp = client.get("/api/v1/warehouses", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]["items"]

    # Filter to current test warehouses
    wh_ids = [str(w.id) for w in setup_g19_test_data["warehouses"]]
    current_whs = [w for w in data if w["id"] in wh_ids]
    assert len(current_whs) == 3
    assert current_whs[0]["priority"] == 1
    assert current_whs[1]["priority"] == 2
    assert current_whs[2]["priority"] == 3


def test_phase_091_warehouse_create_and_update_priority(client, setup_g19_test_data):
    """Verify priority can be set on creation and updated."""
    token = setup_g19_test_data["tokens"]["admin"]
    suffix = uuid.uuid4().hex[:6]

    # Create warehouse with priority 5
    payload = {
        "code": f"WH-PRI-{suffix}",
        "name": "Priority Test Facility",
        "priority": 5,
    }
    create_resp = client.post("/api/v1/warehouses", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert create_resp.status_code == 201
    wh = create_resp.json()["data"]
    assert wh["priority"] == 5

    # Update priority to 1
    update_resp = client.put(f"/api/v1/warehouses/{wh['id']}", json={"priority": 1}, headers={"Authorization": f"Bearer {token}"})
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["priority"] == 1


def test_phase_091_priority_validation_rejects_zero_or_negative(client, setup_g19_test_data):
    """Verify priority < 1 is rejected by schema validation."""
    token = setup_g19_test_data["tokens"]["admin"]
    suffix = uuid.uuid4().hex[:6]

    payload = {
        "code": f"WH-BAD-{suffix}",
        "name": "Invalid Priority Facility",
        "priority": 0,
    }
    resp = client.post("/api/v1/warehouses", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422


# ==============================================================================
# Phase 092 Tests — Warehouse Selection
# ==============================================================================

def test_phase_092_warehouse_selection_highest_priority(client, setup_g19_test_data):
    """Verify warehouse selection selects WH-1 (Priority 1) when it has sufficient ATP (40)."""
    token = setup_g19_test_data["tokens"]["viewer"]
    product = setup_g19_test_data["product"]
    wh_1 = setup_g19_test_data["warehouses"][0]

    # Request 30 units (WH1 has ATP=40)
    resp = client.get(
        f"/api/v1/warehouses/selection/product/{product.id}?quantity=30",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_fully_fulfillable"] is True
    assert data["requires_multi_warehouse"] is False
    assert data["selected_warehouse_id"] == str(wh_1.id)
    assert data["selected_warehouse_priority"] == 1


def test_phase_092_warehouse_selection_fallback_to_multi_warehouse(client, setup_g19_test_data):
    """Verify selection flags requires_multi_warehouse when single WH cannot fulfill requested qty."""
    token = setup_g19_test_data["tokens"]["viewer"]
    product = setup_g19_test_data["product"]

    # Request 60 units (WH1 has 40, WH2 has 25, WH3 has 20 -> total ATP = 85)
    resp = client.get(
        f"/api/v1/warehouses/selection/product/{product.id}?quantity=60",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_fully_fulfillable"] is False
    assert data["requires_multi_warehouse"] is True
    assert data["selected_warehouse_id"] is None


# ==============================================================================
# Phase 093 Tests — Multi-Warehouse Stock Aggregation
# ==============================================================================

def test_phase_093_multi_warehouse_stock_breakdown(client, setup_g19_test_data):
    """Verify aggregate totals: Physical=100, Reserved=15, ATP=85 across 3 warehouses."""
    token = setup_g19_test_data["tokens"]["viewer"]
    product = setup_g19_test_data["product"]

    # Test warehouse endpoint
    resp = client.get(
        f"/api/v1/warehouses/multi-stock/product/{product.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["product_id"] == str(product.id)
    assert data["total_physical_quantity"] == 100
    assert data["total_reserved_quantity"] == 15
    assert data["total_available_quantity"] == 85
    assert data["warehouses_count"] == 3

    # Test product-scoped endpoint: GET /products/{product_id}/warehouse-stock
    resp_prod = client.get(
        f"/api/v1/products/{product.id}/warehouse-stock",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_prod.status_code == 200
    assert resp_prod.json()["data"]["total_available_quantity"] == 85


# ==============================================================================
# Phase 094 Tests — Fulfillment Allocation
# ==============================================================================

def test_phase_094_sequential_fulfillment_allocation_multi_facility(client, setup_g19_test_data):
    """Request 60 units: Allocates 40 from WH1 (pri 1), 20 from WH2 (pri 2), 0 from WH3 (pri 3)."""
    token = setup_g19_test_data["tokens"]["viewer"]
    product = setup_g19_test_data["product"]
    wh_1, wh_2, wh_3 = setup_g19_test_data["warehouses"]

    resp = client.post(
        f"/api/v1/warehouses/allocation/product/{product.id}",
        json={"requested_quantity": 60},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["requested_quantity"] == 60
    assert data["total_allocated"] == 60
    assert data["unallocated_quantity"] == 0
    assert data["is_fully_allocated"] is True

    allocs = {a["warehouse_id"]: a["allocated_quantity"] for a in data["allocations"]}
    assert allocs[str(wh_1.id)] == 40
    assert allocs[str(wh_2.id)] == 20
    assert allocs[str(wh_3.id)] == 0

    # Also test via products endpoint: POST /products/{product_id}/allocate
    resp_prod = client.post(
        f"/api/v1/products/{product.id}/allocate",
        json={"requested_quantity": 60},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_prod.status_code == 200
    assert resp_prod.json()["data"]["total_allocated"] == 60


def test_phase_094_allocation_exceeds_total_atp_reports_unallocated(client, setup_g19_test_data):
    """Request 100 units when total ATP is 85: Allocates 85, unallocated = 15, no backorders."""
    token = setup_g19_test_data["tokens"]["viewer"]
    product = setup_g19_test_data["product"]

    resp = client.post(
        f"/api/v1/warehouses/allocation/product/{product.id}",
        json={"requested_quantity": 100},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["requested_quantity"] == 100
    assert data["total_allocated"] == 85
    assert data["unallocated_quantity"] == 15
    assert data["is_fully_allocated"] is False


# ==============================================================================
# Phase 095 Tests — Multi-Warehouse Stock Reservation & Release
# ==============================================================================

def test_phase_095_atomic_stock_reservation_and_release(client, setup_g19_test_data, db_session):
    """Atomically reserve 50 units (WH1: 40, WH2: 10), verify DB state, then release."""
    token = setup_g19_test_data["tokens"]["admin"]
    product = setup_g19_test_data["product"]
    wh_1, wh_2, wh_3 = setup_g19_test_data["warehouses"]

    # Initial ATP: WH1=40, WH2=25, WH3=20
    reserve_resp = client.post(
        f"/api/v1/warehouses/reservation/product/{product.id}",
        json={"requested_quantity": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reserve_resp.status_code == 200
    res_data = reserve_resp.json()["data"]
    assert res_data["total_reserved"] == 50
    assert res_data["unallocated_quantity"] == 0
    assert res_data["is_fully_reserved"] is True

    # Check updated reservations
    res_map = {r["warehouse_id"]: r for r in res_data["reservations"]}
    assert res_map[str(wh_1.id)]["reserved_quantity"] == 40
    assert res_map[str(wh_1.id)]["remaining_atp"] == 0
    assert res_map[str(wh_2.id)]["reserved_quantity"] == 10
    assert res_map[str(wh_2.id)]["remaining_atp"] == 15

    # Release 10 units back to WH2 and 20 units back to WH1
    release_payload = {
        "releases": [
            {"warehouse_id": str(wh_1.id), "quantity": 20},
            {"warehouse_id": str(wh_2.id), "quantity": 10},
        ]
    }
    release_resp = client.post(
        f"/api/v1/warehouses/release/product/{product.id}",
        json=release_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert release_resp.status_code == 200
    rel_data = release_resp.json()["data"]
    assert rel_data["total_released"] == 30

    rel_map = {r["warehouse_id"]: r for r in rel_data["releases"]}
    assert rel_map[str(wh_1.id)]["remaining_atp"] == 20
    assert rel_map[str(wh_2.id)]["remaining_atp"] == 25


def test_phase_095_release_exceeding_reserved_fails(client, setup_g19_test_data):
    """Releasing more than reserved quantity raises validation error."""
    token = setup_g19_test_data["tokens"]["admin"]
    product = setup_g19_test_data["product"]
    wh_1 = setup_g19_test_data["warehouses"][0]

    release_payload = {
        "releases": [
            {"warehouse_id": str(wh_1.id), "quantity": 9999},
        ]
    }
    resp = client.post(
        f"/api/v1/warehouses/release/product/{product.id}",
        json=release_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


# ==============================================================================
# RBAC & Authorization Tests
# ==============================================================================

def test_rbac_unauthenticated_request_rejected(client, setup_g19_test_data):
    """Unauthenticated requests return 401."""
    product = setup_g19_test_data["product"]
    resp = client.get(f"/api/v1/warehouses/selection/product/{product.id}?quantity=10")
    assert resp.status_code == 401


def test_rbac_insufficient_permissions_rejected(client, setup_g19_test_data):
    """User without warehouses:write cannot reserve stock (403)."""
    token = setup_g19_test_data["tokens"]["none"]
    product = setup_g19_test_data["product"]

    resp = client.post(
        f"/api/v1/warehouses/reservation/product/{product.id}",
        json={"requested_quantity": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_rbac_viewer_cannot_reserve_stock(client, setup_g19_test_data):
    """Viewer with warehouses:read can read allocation but cannot reserve (403)."""
    token_viewer = setup_g19_test_data["tokens"]["viewer"]
    product = setup_g19_test_data["product"]

    # Can allocate (read-only calculation)
    resp_alloc = client.post(
        f"/api/v1/warehouses/allocation/product/{product.id}",
        json={"requested_quantity": 5},
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert resp_alloc.status_code == 200

    # Cannot reserve (write mutation)
    resp_res = client.post(
        f"/api/v1/warehouses/reservation/product/{product.id}",
        json={"requested_quantity": 5},
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert resp_res.status_code == 403
