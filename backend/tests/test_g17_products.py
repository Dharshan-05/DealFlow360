"""Comprehensive Test Suite for DealFlow360 G17 (Phases 081–085).

Verifies:
- Phase 081: Recurring Frequency (monthly, quarterly, yearly billing cycles, normalization, subscription coupling)
- Phase 082: Product Inventory (quantity >= 0, threshold >= 0, deterministic status: IN_STOCK, LOW_STOCK, OUT_OF_STOCK)
- Phase 083: Product Search (multi-field search across SKU, name, category with case-insensitivity)
- Phase 084: Product Filtering (composable category, active, subscription, and stock status filters)
- Phase 085: Product Dashboard (KPI metrics, inventory status distribution, category breakdown, subscription breakdown)
- RBAC and permission enforcement (products:read, products:write)
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
from app.models.product_category import ProductCategory
from app.models.role import Role
from app.models.user import User


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
def setup_g17_test_data(db_session):
    """Seed isolated company, roles, users, category, and products for G17 tests."""
    suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G17 Test Corp {suffix}",
        legal_name=f"G17 Test Corporation {suffix}",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    # Permissions
    perm_read = db_session.scalars(select(Permission).where(Permission.name == "products:read")).first()
    perm_write = db_session.scalars(select(Permission).where(Permission.name == "products:write")).first()

    # User with read + write
    role_admin = Role(name=f"g17_admin_{suffix}")
    role_admin.permissions.extend([p for p in [perm_read, perm_write] if p])
    db_session.add(role_admin)

    # User with read only
    role_viewer = Role(name=f"g17_viewer_{suffix}")
    role_viewer.permissions.extend([p for p in [perm_read] if p])
    db_session.add(role_viewer)
    db_session.flush()

    user_admin = User(
        email=f"g17admin_{suffix}@example.com",
        first_name="G17",
        last_name="Admin",
        company_id=company.id,
        is_active=True,
    )
    user_admin.roles.append(role_admin)
    db_session.add(user_admin)

    user_viewer = User(
        email=f"g17viewer_{suffix}@example.com",
        first_name="G17",
        last_name="Viewer",
        company_id=company.id,
        is_active=True,
    )
    user_viewer.roles.append(role_viewer)
    db_session.add(user_viewer)

    # Test Category
    cat_hw = ProductCategory(
        name=f"Hardware {suffix}",
        code=f"HW_{suffix.upper()}",
        description="Hardware Category",
        is_active=True,
    )
    cat_sw = ProductCategory(
        name=f"Software {suffix}",
        code=f"SW_{suffix.upper()}",
        description="Software Category",
        is_active=True,
    )
    db_session.add(cat_hw)
    db_session.add(cat_sw)
    db_session.commit()

    token_admin = create_access_token(str(user_admin.id))
    token_viewer = create_access_token(str(user_viewer.id))

    return {
        "admin_headers": {"Authorization": f"Bearer {token_admin}"},
        "viewer_headers": {"Authorization": f"Bearer {token_viewer}"},
        "cat_hw_id": str(cat_hw.id),
        "cat_sw_id": str(cat_sw.id),
        "suffix": suffix,
    }


# ===========================================================================
# Phase 081: Recurring Frequency Tests
# ===========================================================================

def test_create_subscription_product_with_recurring_frequency(client, setup_g17_test_data):
    """Phase 081: Subscription product successfully created with normalized recurring frequency."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    payload = {
        "sku": f"G17-SUB-M-{suffix}",
        "name": f"Monthly Subscription {suffix}",
        "cost": "50.00",
        "base_price": "150.00",
        "unit": "license",
        "tax_rate": "0.00",
        "is_subscription": True,
        "recurring_frequency": " monthly ",
        "inventory_quantity": 100,
        "low_stock_threshold": 10,
    }
    resp = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["is_subscription"] is True
    assert data["recurring_frequency"] == "monthly"


def test_create_subscription_product_default_frequency(client, setup_g17_test_data):
    """Phase 081: Subscription product defaults to 'monthly' if recurring_frequency is omitted."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    payload = {
        "sku": f"G17-SUB-DEF-{suffix}",
        "name": f"Default Subscription {suffix}",
        "cost": "100.00",
        "base_price": "300.00",
        "is_subscription": True,
    }
    resp = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["recurring_frequency"] == "monthly"


def test_create_subscription_product_all_valid_frequencies(client, setup_g17_test_data):
    """Phase 081: Accepts all valid frequencies: monthly, quarterly, yearly."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    for freq in ["monthly", "quarterly", "yearly"]:
        payload = {
            "sku": f"G17-SUB-{freq.upper()}-{suffix}",
            "name": f"{freq.capitalize()} Sub {suffix}",
            "cost": "10.00",
            "base_price": "20.00",
            "is_subscription": True,
            "recurring_frequency": freq,
        }
        resp = client.post("/api/v1/products", json=payload, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["data"]["recurring_frequency"] == freq


def test_non_subscription_product_clears_frequency(client, setup_g17_test_data):
    """Phase 081: Non-subscription products cannot retain a recurring frequency."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    payload = {
        "sku": f"G17-STD-{suffix}",
        "name": f"Standard Non-Sub Product {suffix}",
        "cost": "10.00",
        "base_price": "20.00",
        "is_subscription": False,
        "recurring_frequency": "monthly",
    }
    resp = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["data"]["recurring_frequency"] is None


def test_invalid_recurring_frequency_rejected(client, setup_g17_test_data):
    """Phase 081: Invalid recurring frequency returns 422 validation error."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    payload = {
        "sku": f"G17-INV-FREQ-{suffix}",
        "name": f"Invalid Freq {suffix}",
        "cost": "10.00",
        "base_price": "20.00",
        "is_subscription": True,
        "recurring_frequency": "biweekly",
    }
    resp = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 422


def test_update_subscription_recurring_frequency(client, setup_g17_test_data):
    """Phase 081: Updating recurring frequency or switching between subscription and one-time."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    # Create monthly
    create_resp = client.post(
        "/api/v1/products",
        json={
            "sku": f"G17-UPD-SUB-{suffix}",
            "name": f"Update Sub {suffix}",
            "cost": "20.00",
            "base_price": "40.00",
            "is_subscription": True,
            "recurring_frequency": "monthly",
        },
        headers=headers,
    )
    product_id = create_resp.json()["data"]["id"]

    # Update to yearly
    upd_resp = client.put(
        f"/api/v1/products/{product_id}",
        json={"recurring_frequency": "yearly"},
        headers=headers,
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["data"]["recurring_frequency"] == "yearly"

    # Update to is_subscription=False -> frequency automatically cleared
    upd_resp2 = client.put(
        f"/api/v1/products/{product_id}",
        json={"is_subscription": False},
        headers=headers,
    )
    assert upd_resp2.status_code == 200
    assert upd_resp2.json()["data"]["recurring_frequency"] is None


# ===========================================================================
# Phase 082: Product Inventory Tests
# ===========================================================================

def test_product_inventory_status_in_stock(client, setup_g17_test_data):
    """Phase 082: Product with inventory_quantity > threshold derives IN_STOCK."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    payload = {
        "sku": f"G17-INV-INSTOCK-{suffix}",
        "name": f"In Stock Product {suffix}",
        "cost": "10.00",
        "base_price": "25.00",
        "inventory_quantity": 25,
        "low_stock_threshold": 10,
    }
    resp = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["inventory_quantity"] == 25
    assert data["low_stock_threshold"] == 10
    assert data["inventory_status"] == "IN_STOCK"


def test_product_inventory_status_low_stock(client, setup_g17_test_data):
    """Phase 082: Product with 0 < inventory_quantity <= threshold derives LOW_STOCK."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    payload = {
        "sku": f"G17-INV-LOWSTOCK-{suffix}",
        "name": f"Low Stock Product {suffix}",
        "cost": "15.00",
        "base_price": "30.00",
        "inventory_quantity": 5,
        "low_stock_threshold": 5,
    }
    resp = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["inventory_status"] == "LOW_STOCK"


def test_product_inventory_status_out_of_stock(client, setup_g17_test_data):
    """Phase 082: Product with inventory_quantity <= 0 derives OUT_OF_STOCK."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    payload = {
        "sku": f"G17-INV-OUTSTOCK-{suffix}",
        "name": f"Out Of Stock Product {suffix}",
        "cost": "10.00",
        "base_price": "20.00",
        "inventory_quantity": 0,
        "low_stock_threshold": 5,
    }
    resp = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["inventory_status"] == "OUT_OF_STOCK"


def test_product_inventory_negative_rejected(client, setup_g17_test_data):
    """Phase 082: Negative inventory quantity or threshold is rejected with 422."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    payload = {
        "sku": f"G17-INV-NEG-{suffix}",
        "name": f"Negative Stock Product {suffix}",
        "cost": "10.00",
        "base_price": "20.00",
        "inventory_quantity": -5,
    }
    resp = client.post("/api/v1/products", json=payload, headers=headers)
    assert resp.status_code == 422


def test_update_inventory_recalculates_status(client, setup_g17_test_data):
    """Phase 082: Updating inventory quantity dynamically recalculates inventory_status."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]

    # Start with 0 (OUT_OF_STOCK)
    create_resp = client.post(
        "/api/v1/products",
        json={
            "sku": f"G17-INV-RECALC-{suffix}",
            "name": f"Dynamic Inventory {suffix}",
            "cost": "10.00",
            "base_price": "20.00",
            "inventory_quantity": 0,
            "low_stock_threshold": 5,
        },
        headers=headers,
    )
    product_id = create_resp.json()["data"]["id"]
    assert create_resp.json()["data"]["inventory_status"] == "OUT_OF_STOCK"

    # Update to 3 (LOW_STOCK)
    upd1 = client.put(
        f"/api/v1/products/{product_id}",
        json={"inventory_quantity": 3},
        headers=headers,
    )
    assert upd1.status_code == 200
    assert upd1.json()["data"]["inventory_status"] == "LOW_STOCK"

    # Update to 20 (IN_STOCK)
    upd2 = client.put(
        f"/api/v1/products/{product_id}",
        json={"inventory_quantity": 20},
        headers=headers,
    )
    assert upd2.status_code == 200
    assert upd2.json()["data"]["inventory_status"] == "IN_STOCK"


# ===========================================================================
# Phase 083: Product Search Tests
# ===========================================================================

def test_search_by_sku(client, setup_g17_test_data):
    """Phase 083: Search products by exact or partial SKU case-insensitively."""
    admin_headers = setup_g17_test_data["admin_headers"]
    viewer_headers = setup_g17_test_data["viewer_headers"]
    suffix = setup_g17_test_data["suffix"].upper()

    sku = f"G17-SRCH-SKU-{suffix}"
    client.post(
        "/api/v1/products",
        json={
            "sku": sku,
            "name": f"Searchable SKU Product {suffix}",
            "cost": "10.00",
            "base_price": "25.00",
        },
        headers=admin_headers,
    )

    # Search by partial lowercase SKU
    resp = client.get(f"/api/v1/products?search=srch-sku-{suffix.lower()}", headers=viewer_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) >= 1
    assert any(p["sku"] == sku for p in items)


def test_search_by_name_partial(client, setup_g17_test_data):
    """Phase 083: Search products by partial name."""
    admin_headers = setup_g17_test_data["admin_headers"]
    viewer_headers = setup_g17_test_data["viewer_headers"]
    suffix = setup_g17_test_data["suffix"]

    client.post(
        "/api/v1/products",
        json={
            "sku": f"G17-SRCH-NAME-{suffix}",
            "name": f"Ultra Dynamic Inventory {suffix}",
            "cost": "10.00",
            "base_price": "25.00",
        },
        headers=admin_headers,
    )

    resp = client.get(f"/api/v1/products?search=Dynamic%20Inventory", headers=viewer_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert any(f"Ultra Dynamic Inventory {suffix}" in p["name"] for p in items)


def test_search_by_category_name(client, setup_g17_test_data):
    """Phase 083: Search matches category name."""
    headers = setup_g17_test_data["admin_headers"]
    suffix = setup_g17_test_data["suffix"]
    cat_id = setup_g17_test_data["cat_hw_id"]

    # Create product linked to hardware category
    sku = f"G17-CAT-SEARCH-{suffix.upper()}"
    client.post(
        "/api/v1/products",
        json={
            "sku": sku,
            "name": f"Rack Mount Server Unit {suffix}",
            "category_id": cat_id,
            "cost": "500.00",
            "base_price": "800.00",
        },
        headers=headers,
    )

    # Search for "Hardware" category
    resp = client.get(f"/api/v1/products?search=Hardware%20{suffix}", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert any(p["sku"] == sku for p in items)


def test_search_no_results(client, setup_g17_test_data):
    """Phase 083: Search with nonexistent query returns empty array."""
    headers = setup_g17_test_data["viewer_headers"]
    resp = client.get("/api/v1/products?search=NONEXISTENT_QUERY_XYZ_99999", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 0
    assert len(resp.json()["data"]["items"]) == 0


# ===========================================================================
# Phase 084: Product Filtering Tests
# ===========================================================================

def test_filter_by_category(client, setup_g17_test_data):
    """Phase 084: Filter products by category_id."""
    headers = setup_g17_test_data["viewer_headers"]
    cat_hw_id = setup_g17_test_data["cat_hw_id"]

    resp = client.get(f"/api/v1/products?category_id={cat_hw_id}", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    for item in items:
        assert item["category_id"] == cat_hw_id


def test_filter_by_subscription(client, setup_g17_test_data):
    """Phase 084: Filter products by is_subscription flag."""
    headers = setup_g17_test_data["viewer_headers"]

    resp = client.get("/api/v1/products?is_subscription=true", headers=headers)
    assert resp.status_code == 200
    for item in resp.json()["data"]["items"]:
        assert item["is_subscription"] is True


def test_filter_by_inventory_status(client, setup_g17_test_data):
    """Phase 084: Filter products by deterministic inventory_status."""
    headers = setup_g17_test_data["viewer_headers"]

    # Filter OUT_OF_STOCK
    resp_out = client.get("/api/v1/products?inventory_status=OUT_OF_STOCK", headers=headers)
    assert resp_out.status_code == 200
    for item in resp_out.json()["data"]["items"]:
        assert item["inventory_status"] == "OUT_OF_STOCK"
        assert item["inventory_quantity"] <= 0

    # Filter LOW_STOCK
    resp_low = client.get("/api/v1/products?inventory_status=LOW_STOCK", headers=headers)
    assert resp_low.status_code == 200
    for item in resp_low.json()["data"]["items"]:
        assert item["inventory_status"] == "LOW_STOCK"
        assert 0 < item["inventory_quantity"] <= item["low_stock_threshold"]

    # Filter IN_STOCK
    resp_in = client.get("/api/v1/products?inventory_status=IN_STOCK", headers=headers)
    assert resp_in.status_code == 200
    for item in resp_in.json()["data"]["items"]:
        assert item["inventory_status"] == "IN_STOCK"
        assert item["inventory_quantity"] > item["low_stock_threshold"]


def test_composite_filtering(client, setup_g17_test_data):
    """Phase 084: Composable filters working in conjunction."""
    headers = setup_g17_test_data["viewer_headers"]
    suffix = setup_g17_test_data["suffix"]

    resp = client.get(
        f"/api/v1/products?search={suffix}&is_subscription=true&inventory_status=IN_STOCK",
        headers=headers,
    )
    assert resp.status_code == 200
    for item in resp.json()["data"]["items"]:
        assert item["is_subscription"] is True
        assert item["inventory_status"] == "IN_STOCK"


# ===========================================================================
# Phase 085: Product Dashboard Analytics Tests
# ===========================================================================

def test_product_dashboard_metrics(client, setup_g17_test_data):
    """Phase 085: Product dashboard endpoint returns aggregated KPIs and distributions."""
    headers = setup_g17_test_data["viewer_headers"]

    resp = client.get("/api/v1/products/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]

    # Verify KPI counts
    assert "total_products" in data
    assert "active_products" in data
    assert "subscription_products" in data
    assert "out_of_stock_products" in data
    assert "low_stock_products" in data
    assert "in_stock_products" in data

    assert data["total_products"] >= data["active_products"]
    assert data["total_products"] >= data["subscription_products"]

    # Verify inventory distribution
    inv_dist = data["inventory_distribution"]
    assert "IN_STOCK" in inv_dist
    assert "LOW_STOCK" in inv_dist
    assert "OUT_OF_STOCK" in inv_dist
    assert inv_dist["IN_STOCK"] + inv_dist["LOW_STOCK"] + inv_dist["OUT_OF_STOCK"] == data["total_products"]

    # Verify category distribution
    assert "category_distribution" in data
    assert isinstance(data["category_distribution"], list)

    # Verify subscription distribution
    sub_dist = data["subscription_distribution"]
    assert sub_dist["subscription"] + sub_dist["standard"] == data["total_products"]

    # Verify frequency distribution
    freq_dist = data["frequency_distribution"]
    assert "monthly" in freq_dist
    assert "quarterly" in freq_dist
    assert "yearly" in freq_dist
    assert sum(freq_dist.values()) == data["subscription_products"]


def test_product_dashboard_unauthorized(client):
    """Phase 085: Dashboard endpoint requires authentication."""
    resp = client.get("/api/v1/products/dashboard")
    assert resp.status_code in (401, 403)
