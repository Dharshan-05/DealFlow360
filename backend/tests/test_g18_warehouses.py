"""Comprehensive Test Suite for DealFlow360 G18 (Phases 086–090).

Verifies:
- Phase 086: Warehouse CRUD (Create, List, Detail, Update, Soft Deactivation, Duplicate Code Rejection)
- Phase 087: Warehouse Stock (Quantity Management, Stock Listings, Non-Negative Constraints)
- Phase 088: Stock Availability API (Product Availability, Unknown Product/Warehouse, Out of Stock)
- Phase 089: Reserved Stock (Foundational Reserve and Release, Limits, Integrity Protection)
- Phase 090: Available-to-Promise (ATP) Calculation (Formula ATP = max(qty - res, 0), Endpoints)
- RBAC & Authorization (warehouses:read, warehouses:write, Unauthenticated 401, Unauthorized 403)
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
from app.services.atp import AvailableToPromiseService


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
def setup_g18_test_data(db_session):
    """Seed isolated company, roles, users, products, and warehouse with initial stock."""
    suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G18 Logistics Corp {suffix}",
        legal_name=f"G18 Logistics Corporation {suffix}",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    # Permissions
    perm_read = db_session.scalars(select(Permission).where(Permission.name == "warehouses:read")).first()
    perm_write = db_session.scalars(select(Permission).where(Permission.name == "warehouses:write")).first()

    # User with read + write (Admin / Operations)
    role_admin = Role(name=f"g18_admin_{suffix}")
    role_admin.permissions.extend([p for p in [perm_read, perm_write] if p])
    db_session.add(role_admin)

    # User with read only
    role_viewer = Role(name=f"g18_viewer_{suffix}")
    role_viewer.permissions.extend([p for p in [perm_read] if p])
    db_session.add(role_viewer)

    # User with no warehouse permissions
    role_unauth = Role(name=f"g18_unauth_{suffix}")
    db_session.add(role_unauth)
    db_session.flush()

    user_admin = User(
        email=f"g18admin_{suffix}@example.com",
        first_name="G18",
        last_name="Admin",
        company_id=company.id,
        is_active=True,
    )
    user_admin.roles.append(role_admin)
    db_session.add(user_admin)

    user_viewer = User(
        email=f"g18viewer_{suffix}@example.com",
        first_name="G18",
        last_name="Viewer",
        company_id=company.id,
        is_active=True,
    )
    user_viewer.roles.append(role_viewer)
    db_session.add(user_viewer)

    user_unauth = User(
        email=f"g18unauth_{suffix}@example.com",
        first_name="G18",
        last_name="Unauth",
        company_id=company.id,
        is_active=True,
    )
    user_unauth.roles.append(role_unauth)
    db_session.add(user_unauth)

    # Test Products
    prod_1 = Product(
        sku=f"G18-PRD-01-{suffix}",
        name=f"Enterprise Router {suffix}",
        cost=Decimal("1200.00"),
        base_price=Decimal("1900.00"),
        inventory_quantity=150,
        low_stock_threshold=10,
        is_active=True,
    )
    prod_2 = Product(
        sku=f"G18-PRD-02-{suffix}",
        name=f"Fiber Switch {suffix}",
        cost=Decimal("800.00"),
        base_price=Decimal("1400.00"),
        inventory_quantity=50,
        low_stock_threshold=5,
        is_active=True,
    )
    db_session.add(prod_1)
    db_session.add(prod_2)

    # Test Warehouse
    warehouse = Warehouse(
        company_id=company.id,
        code=f"WH-TEST-{suffix.upper()}",
        name=f"Test Warehouse {suffix}",
        city="Denver",
        state="CO",
        country="United States",
        is_active=True,
    )
    db_session.add(warehouse)
    db_session.flush()

    # Initial stock for prod_1: 100 physical, 20 reserved -> 80 ATP
    stock_1 = WarehouseStock(
        warehouse_id=warehouse.id,
        product_id=prod_1.id,
        quantity=100,
        reserved_quantity=20,
    )
    db_session.add(stock_1)
    db_session.commit()

    token_admin = create_access_token(str(user_admin.id))
    token_viewer = create_access_token(str(user_viewer.id))
    token_unauth = create_access_token(str(user_unauth.id))

    return {
        "company": company,
        "warehouse": warehouse,
        "prod_1": prod_1,
        "prod_2": prod_2,
        "stock_1": stock_1,
        "token_admin": token_admin,
        "token_viewer": token_viewer,
        "token_unauth": token_unauth,
        "suffix": suffix,
    }


# ==============================================================================
# Phase 086 — Warehouse CRUD Tests
# ==============================================================================

def test_create_warehouse_success(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    suffix = setup_g18_test_data["suffix"]

    payload = {
        "code": f"WH-NORTH-{suffix}",
        "name": f"North Regional Depot {suffix}",
        "city": "Seattle",
        "state": "WA",
        "country": "United States",
        "postal_code": "98101",
        "is_active": True,
    }
    response = client.post(
        "/api/v1/warehouses",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["code"] == f"WH-NORTH-{suffix.upper()}"
    assert data["data"]["city"] == "Seattle"


def test_create_warehouse_duplicate_code_fails(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    existing_code = setup_g18_test_data["warehouse"].code

    payload = {
        "code": existing_code,
        "name": "Duplicate Code Depot",
    }
    response = client.post(
        "/api/v1/warehouses",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    data = response.json()
    err_msg = data.get("error", {}).get("message") or data.get("detail", "")
    assert "already exists" in err_msg


def test_get_warehouse_by_id(client, setup_g18_test_data):
    token = setup_g18_test_data["token_viewer"]
    wh = setup_g18_test_data["warehouse"]

    response = client.get(
        f"/api/v1/warehouses/{wh.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == str(wh.id)
    assert data["code"] == wh.code
    assert data["total_physical_stock"] == 100
    assert data["total_reserved_stock"] == 20
    assert data["total_atp"] == 80


def test_get_warehouse_not_found(client, setup_g18_test_data):
    token = setup_g18_test_data["token_viewer"]
    random_id = uuid.uuid4()

    response = client.get(
        f"/api/v1/warehouses/{random_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_list_warehouses(client, setup_g18_test_data):
    token = setup_g18_test_data["token_viewer"]
    wh = setup_g18_test_data["warehouse"]

    response = client.get(
        "/api/v1/warehouses?limit=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1
    codes = [item["code"] for item in data["items"]]
    assert wh.code in codes


def test_update_warehouse_success(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]

    payload = {
        "name": f"Updated {wh.name}",
        "city": "Aurora",
    }
    response = client.put(
        f"/api/v1/warehouses/{wh.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == f"Updated {wh.name}"
    assert data["city"] == "Aurora"


def test_deactivate_warehouse_soft_delete(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]

    response = client.delete(
        f"/api/v1/warehouses/{wh.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["is_active"] is False

    # Verify still readable via GET
    get_res = client.get(
        f"/api/v1/warehouses/{wh.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["data"]["is_active"] is False


# ==============================================================================
# Phase 087 — Warehouse Stock Tests
# ==============================================================================

def test_set_and_list_warehouse_stock(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_2"]

    # Set stock for prod_2
    payload = {
        "product_id": str(prod.id),
        "quantity": 50,
        "reserved_quantity": 10,
    }
    response = client.post(
        f"/api/v1/warehouses/{wh.id}/stock",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["quantity"] == 50
    assert data["reserved_quantity"] == 10
    assert data["available_to_promise"] == 40
    assert data["is_available"] is True

    # List stock
    list_res = client.get(
        f"/api/v1/warehouses/{wh.id}/stock",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert list_data["total"] >= 2  # prod_1 + prod_2
    assert list_data["total_physical"] >= 150
    assert list_data["total_reserved"] >= 30
    assert list_data["total_atp"] >= 120


def test_update_warehouse_stock_quantity(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    # Update physical stock from 100 to 120 (reserved remains 20)
    response = client.put(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}",
        json={"quantity": 120},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["quantity"] == 120
    assert data["reserved_quantity"] == 20
    assert data["available_to_promise"] == 100  # 120 - 20 = 100


def test_update_stock_quantity_below_reserved_fails(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    # Current reserved is 20, attempting to set physical stock to 10 should fail
    response = client.put(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}",
        json={"quantity": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    data = response.json()
    err_msg = data.get("error", {}).get("message") or data.get("detail", "")
    assert "below currently reserved quantity" in err_msg


def test_negative_stock_quantity_rejected(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_2"]

    payload = {
        "product_id": str(prod.id),
        "quantity": -10,
        "reserved_quantity": 0,
    }
    response = client.post(
        f"/api/v1/warehouses/{wh.id}/stock",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


# ==============================================================================
# Phase 088 — Stock Availability API Tests
# ==============================================================================

def test_stock_availability_api(client, setup_g18_test_data):
    token = setup_g18_test_data["token_viewer"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    response = client.get(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/availability",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["product_id"] == str(prod.id)
    assert data["warehouse_id"] == str(wh.id)
    assert data["stock_quantity"] == 100
    assert data["reserved_quantity"] == 20
    assert data["available_quantity"] == 80
    assert data["is_available"] is True


def test_stock_availability_unknown_product(client, setup_g18_test_data):
    token = setup_g18_test_data["token_viewer"]
    wh = setup_g18_test_data["warehouse"]
    random_prod_id = uuid.uuid4()

    response = client.get(
        f"/api/v1/warehouses/{wh.id}/stock/{random_prod_id}/availability",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


# ==============================================================================
# Phase 089 — Reserved Stock Tests
# ==============================================================================

def test_reserve_stock_success(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    # Currently qty: 100, reserved: 20, ATP: 80
    # Reserve 30 units -> new reserved: 50, ATP: 50
    response = client.post(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/reserve",
        json={"quantity": 30},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["reserved_quantity"] == 50
    assert data["available_to_promise"] == 50


def test_reserve_stock_exceeding_physical_fails(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    # Currently qty: 100, reserved: 20, ATP: 80
    # Attempting to reserve 90 units should fail
    response = client.post(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/reserve",
        json={"quantity": 90},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    data = response.json()
    err_msg = data.get("error", {}).get("message") or data.get("detail", "")
    assert "Only 80 units available to promise" in err_msg


def test_release_stock_success(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    # Currently reserved: 20. Release 10 units -> new reserved: 10, ATP: 90
    response = client.post(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/release",
        json={"quantity": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["reserved_quantity"] == 10
    assert data["available_to_promise"] == 90


def test_release_stock_exceeding_reserved_fails(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    # Currently reserved: 20. Releasing 30 should fail
    response = client.post(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/release",
        json={"quantity": 30},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    data = response.json()
    err_msg = data.get("error", {}).get("message") or data.get("detail", "")
    assert "Current reserved quantity is only 20" in err_msg


def test_reserve_release_non_positive_amount_fails(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    res1 = client.post(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/reserve",
        json={"quantity": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 422

    res2 = client.post(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/release",
        json={"quantity": -5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 422


# ==============================================================================
# Phase 090 — Available-to-Promise (ATP) Tests
# ==============================================================================

def test_atp_service_deterministic_calculation():
    # 100 physical, 30 reserved => 70 ATP
    assert AvailableToPromiseService.calculate_atp(100, 30) == 70

    # 20 physical, 20 reserved => 0 ATP
    assert AvailableToPromiseService.calculate_atp(20, 20) == 0

    # 0 physical, 0 reserved => 0 ATP
    assert AvailableToPromiseService.calculate_atp(0, 0) == 0


def test_atp_service_invalid_states_rejected():
    with pytest.raises(Exception):
        AvailableToPromiseService.calculate_atp(-10, 0)

    with pytest.raises(Exception):
        AvailableToPromiseService.calculate_atp(50, -5)

    with pytest.raises(Exception):
        # Reserved greater than physical
        AvailableToPromiseService.calculate_atp(20, 25)


def test_atp_endpoint(client, setup_g18_test_data):
    token = setup_g18_test_data["token_viewer"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    # Current state: qty 100, reserved 20 => ATP 80
    response = client.get(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/atp",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["physical_stock"] == 100
    assert data["reserved_stock"] == 20
    assert data["available_to_promise"] == 80
    assert data["is_available"] is True


def test_atp_zero_when_fully_reserved(client, setup_g18_test_data):
    token = setup_g18_test_data["token_admin"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_2"]

    # Set 50 physical, 50 reserved => ATP 0
    client.post(
        f"/api/v1/warehouses/{wh.id}/stock",
        json={"product_id": str(prod.id), "quantity": 50, "reserved_quantity": 50},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/atp",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["physical_stock"] == 50
    assert data["reserved_stock"] == 50
    assert data["available_to_promise"] == 0
    assert data["is_available"] is False


# ==============================================================================
# Authorization & Security Tests
# ==============================================================================

def test_unauthenticated_request_fails(client, setup_g18_test_data):
    wh = setup_g18_test_data["warehouse"]
    response = client.get(f"/api/v1/warehouses/{wh.id}")
    assert response.status_code == 401


def test_unauthorized_user_lacks_permission(client, setup_g18_test_data):
    token = setup_g18_test_data["token_unauth"]
    wh = setup_g18_test_data["warehouse"]

    response = client.get(
        f"/api/v1/warehouses/{wh.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_viewer_cannot_mutate_stock(client, setup_g18_test_data):
    token = setup_g18_test_data["token_viewer"]
    wh = setup_g18_test_data["warehouse"]
    prod = setup_g18_test_data["prod_1"]

    response = client.post(
        f"/api/v1/warehouses/{wh.id}/stock/{prod.id}/reserve",
        json={"quantity": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
