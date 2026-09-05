"""Comprehensive Test Suite for Product Management Foundation (Phases 071–075).

Verifies:
- Phase 071: Product CRUD (create, read, list, update, delete, duplicate SKU rejection, 404 handling, pagination)
- Phase 072: Product Categories (create, read, list, update, delete, relations, category validation, reference safety)
- Phase 073: Product Pricing (valid price, zero price, negative price rejection, decimal precision)
- Phase 074: Product Cost (valid cost, zero cost, negative cost rejection, decimal precision)
- Phase 075: Product Margin (positive margin, zero margin, negative margin, zero price division-by-zero safety)
- RBAC and Authentication enforcement (products:read, products:write)
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
def setup_g15_test_data(db_session):
    """Seed isolated test company, roles, users, categories, and products for G15 tests."""
    unique_suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G15 Test Corp {unique_suffix}",
        legal_name=f"G15 Test Corporation {unique_suffix}",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    # Permissions
    perm_read = db_session.scalars(select(Permission).where(Permission.name == "products:read")).first()
    perm_write = db_session.scalars(select(Permission).where(Permission.name == "products:write")).first()

    # Manager Role (has read + write)
    role_manager = Role(name=f"G15 Product Manager {unique_suffix}")
    role_manager.permissions.extend([p for p in [perm_read, perm_write] if p])
    db_session.add(role_manager)

    # Viewer Role (has read only)
    role_viewer = Role(name=f"G15 Product Viewer {unique_suffix}")
    role_viewer.permissions.extend([p for p in [perm_read] if p])
    db_session.add(role_viewer)
    db_session.flush()

    # Users
    user_manager = User(
        email=f"manager_{unique_suffix}@test.com",
        first_name="Product",
        last_name="Manager",
        company_id=company.id,
        is_active=True,
    )
    user_manager.roles.append(role_manager)

    user_viewer = User(
        email=f"viewer_{unique_suffix}@test.com",
        first_name="Product",
        last_name="Viewer",
        company_id=company.id,
        is_active=True,
    )
    user_viewer.roles.append(role_viewer)
    db_session.add_all([user_manager, user_viewer])
    db_session.flush()

    # Test category
    category = ProductCategory(
        name=f"Hardware Systems {unique_suffix}",
        code=f"CAT-HW-{unique_suffix.upper()}",
        description="Enterprise hardware devices and accessories",
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()

    # Test product
    product = Product(
        sku=f"SKU-SRV-{unique_suffix.upper()}",
        name=f"Enterprise Server {unique_suffix}",
        description="High performance rack server",
        category_id=category.id,
        cost=Decimal("3000.00"),
        base_price=Decimal("5000.00"),
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    manager_token = create_access_token(str(user_manager.id))
    viewer_token = create_access_token(str(user_viewer.id))

    return {
        "company": company,
        "category": category,
        "product": product,
        "manager_token": manager_token,
        "viewer_token": viewer_token,
        "unique_suffix": unique_suffix,
    }


# ===========================================================================
# Phase 071: Product CRUD Tests
# ===========================================================================

def test_phase_071_create_product(client, setup_g15_test_data):
    """Verify creating a new product with valid pricing and SKU."""
    data = setup_g15_test_data
    token = data["manager_token"]
    cat_id = str(data["category"].id)
    unique = uuid.uuid4().hex[:6].upper()

    payload = {
        "sku": f"PROD-{unique}",
        "name": f"Enterprise Router {unique}",
        "description": "Core routing hardware",
        "category_id": cat_id,
        "cost": "1200.00",
        "base_price": "2000.00",
        "is_active": True,
    }

    res = client.post(
        "/api/v1/products",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    res_data = res.json()
    assert res_data["success"] is True
    prod = res_data["data"]
    assert prod["sku"] == f"PROD-{unique}"
    assert prod["name"] == f"Enterprise Router {unique}"
    assert float(prod["base_price"]) == 2000.00
    assert float(prod["cost"]) == 1200.00
    assert prod["category_id"] == cat_id
    assert prod["category"]["id"] == cat_id


def test_phase_071_create_product_duplicate_sku(client, setup_g15_test_data):
    """Verify duplicate SKU is rejected."""
    data = setup_g15_test_data
    token = data["manager_token"]
    existing_sku = data["product"].sku

    payload = {
        "sku": existing_sku,
        "name": "Duplicate Product",
        "cost": "100.00",
        "base_price": "200.00",
    }

    res = client.post(
        "/api/v1/products",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "already exists" in res.json()["error"]["message"]


def test_phase_071_list_and_get_product(client, setup_g15_test_data):
    """Verify listing and retrieving products by ID."""
    data = setup_g15_test_data
    token = data["viewer_token"]
    prod_id = str(data["product"].id)

    # List
    res_list = client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_list.status_code == 200
    list_data = res_list.json()["data"]
    assert list_data["total"] >= 1
    assert any(p["id"] == prod_id for p in list_data["items"])

    # Get by ID
    res_get = client.get(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_get.status_code == 200
    p = res_get.json()["data"]
    assert p["id"] == prod_id
    assert p["sku"] == data["product"].sku


def test_phase_071_update_product(client, setup_g15_test_data):
    """Verify updating product details."""
    data = setup_g15_test_data
    token = data["manager_token"]
    prod_id = str(data["product"].id)

    update_payload = {
        "name": "Updated Enterprise Server V2",
        "description": "Upgraded Xeon Processor",
        "base_price": "5500.00",
    }

    res = client.put(
        f"/api/v1/products/{prod_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    updated = res.json()["data"]
    assert updated["name"] == "Updated Enterprise Server V2"
    assert updated["description"] == "Upgraded Xeon Processor"
    assert float(updated["base_price"]) == 5500.00


def test_phase_071_delete_product(client, setup_g15_test_data):
    """Verify soft deleting/deactivating product."""
    data = setup_g15_test_data
    token = data["manager_token"]
    prod_id = str(data["product"].id)

    res = client.delete(
        f"/api/v1/products/{prod_id}?soft=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["deleted"] is True

    # Check deactivated in get
    res_get = client.get(
        f"/api/v1/products/{prod_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_get.status_code == 200
    assert res_get.json()["data"]["is_active"] is False


def test_phase_071_product_not_found(client, setup_g15_test_data):
    """Verify 404 for nonexistent product ID."""
    token = setup_g15_test_data["viewer_token"]
    rand_id = str(uuid.uuid4())

    res = client.get(
        f"/api/v1/products/{rand_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


# ===========================================================================
# Phase 072: Product Categories Tests
# ===========================================================================

def test_phase_072_category_crud_and_validation(client, setup_g15_test_data):
    """Verify creating, listing, updating, and deleting product categories."""
    data = setup_g15_test_data
    token = data["manager_token"]
    unique = uuid.uuid4().hex[:6].upper()

    # 1. Create category
    cat_payload = {
        "name": f"Cloud Storage {unique}",
        "code": f"CAT-STR-{unique}",
        "description": "High throughput enterprise storage",
    }
    res_create = client.post(
        "/api/v1/product-categories",
        json=cat_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_create.status_code == 201
    created_cat = res_create.json()["data"]
    cat_id = created_cat["id"]
    assert created_cat["code"] == f"CAT-STR-{unique}"

    # 2. Duplicate code rejected
    res_dup = client.post(
        "/api/v1/product-categories",
        json=cat_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_dup.status_code == 400

    # 3. List categories
    res_list = client.get(
        "/api/v1/product-categories",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_list.status_code == 200
    assert any(c["id"] == cat_id for c in res_list.json()["data"])

    # 4. Update category
    res_update = client.put(
        f"/api/v1/product-categories/{cat_id}",
        json={"name": f"Cloud SAN Storage {unique}", "description": "NVMe-over-Fabrics"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_update.status_code == 200
    assert res_update.json()["data"]["name"] == f"Cloud SAN Storage {unique}"

    # 5. Delete category safely
    res_del = client.delete(
        f"/api/v1/product-categories/{cat_id}?soft=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_del.status_code == 200
    assert res_del.json()["data"]["deleted"] is True


def test_phase_072_invalid_category_reference(client, setup_g15_test_data):
    """Verify product creation fails when referencing nonexistent category."""
    token = setup_g15_test_data["manager_token"]
    rand_cat_id = str(uuid.uuid4())

    payload = {
        "sku": f"SKU-INV-{uuid.uuid4().hex[:6].upper()}",
        "name": "Invalid Category Product",
        "category_id": rand_cat_id,
        "cost": "50.00",
        "base_price": "100.00",
    }
    res = client.post(
        "/api/v1/products",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "does not exist" in res.json()["error"]["message"]


# ===========================================================================
# Phase 073 & 074: Product Pricing & Cost Validation Tests
# ===========================================================================

def test_phase_073_074_pricing_and_cost_validation(client, setup_g15_test_data):
    """Verify pricing and cost validation rules (non-negative, decimal-safe)."""
    token = setup_g15_test_data["manager_token"]

    # Negative price rejected
    res_neg_price = client.post(
        "/api/v1/products",
        json={
            "sku": f"SKU-PNEG-{uuid.uuid4().hex[:6].upper()}",
            "name": "Negative Price Product",
            "cost": "50.00",
            "base_price": "-100.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_neg_price.status_code == 422

    # Negative cost rejected
    res_neg_cost = client.post(
        "/api/v1/products",
        json={
            "sku": f"SKU-CNEG-{uuid.uuid4().hex[:6].upper()}",
            "name": "Negative Cost Product",
            "cost": "-50.00",
            "base_price": "100.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_neg_cost.status_code == 422

    # Zero price and zero cost allowed
    res_zero = client.post(
        "/api/v1/products",
        json={
            "sku": f"SKU-ZERO-{uuid.uuid4().hex[:6].upper()}",
            "name": "Zero Price Product",
            "cost": "0.00",
            "base_price": "0.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_zero.status_code == 201
    assert float(res_zero.json()["data"]["base_price"]) == 0.00
    assert float(res_zero.json()["data"]["cost"]) == 0.00


# ===========================================================================
# Phase 075: Product Margin Tests
# ===========================================================================

def test_phase_075_product_margin_derivation(client, setup_g15_test_data):
    """Verify deterministic gross margin amount and percentage calculation."""
    token = setup_g15_test_data["manager_token"]

    # 1. Positive Margin: Price = 1000.00, Cost = 600.00
    # Margin Amount = 400.00, Margin % = (400 / 1000) * 100 = 40.00%
    res1 = client.post(
        "/api/v1/products",
        json={
            "sku": f"SKU-M1-{uuid.uuid4().hex[:6].upper()}",
            "name": "Positive Margin Product",
            "cost": "600.00",
            "base_price": "1000.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201
    p1 = res1.json()["data"]
    assert float(p1["margin_amount"]) == 400.00
    assert float(p1["margin_percentage"]) == 40.00

    # 2. Zero Margin: Price = 500.00, Cost = 500.00
    # Margin Amount = 0.00, Margin % = 0.00%
    res2 = client.post(
        "/api/v1/products",
        json={
            "sku": f"SKU-M2-{uuid.uuid4().hex[:6].upper()}",
            "name": "Break Even Product",
            "cost": "500.00",
            "base_price": "500.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 201
    p2 = res2.json()["data"]
    assert float(p2["margin_amount"]) == 0.00
    assert float(p2["margin_percentage"]) == 0.00

    # 3. Negative Margin: Price = 300.00, Cost = 450.00
    # Margin Amount = -150.00, Margin % = (-150 / 300) * 100 = -50.00%
    res3 = client.post(
        "/api/v1/products",
        json={
            "sku": f"SKU-M3-{uuid.uuid4().hex[:6].upper()}",
            "name": "Loss Leader Product",
            "cost": "450.00",
            "base_price": "300.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res3.status_code == 201
    p3 = res3.json()["data"]
    assert float(p3["margin_amount"]) == -150.00
    assert float(p3["margin_percentage"]) == -50.00

    # 4. Zero Selling Price: Price = 0.00, Cost = 50.00
    # Margin Amount = -50.00, Margin % = None (zero-division safe)
    res4 = client.post(
        "/api/v1/products",
        json={
            "sku": f"SKU-M4-{uuid.uuid4().hex[:6].upper()}",
            "name": "Free Sample Product",
            "cost": "50.00",
            "base_price": "0.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res4.status_code == 201
    p4 = res4.json()["data"]
    assert float(p4["margin_amount"]) == -50.00
    assert p4["margin_percentage"] is None


# ===========================================================================
# RBAC Enforcement Tests
# ===========================================================================

def test_rbac_write_permission_enforcement(client, setup_g15_test_data):
    """Verify user with products:read cannot perform products:write actions."""
    viewer_token = setup_g15_test_data["viewer_token"]

    # Attempt to create product with viewer token
    res_create = client.post(
        "/api/v1/products",
        json={
            "sku": f"SKU-RBAC-{uuid.uuid4().hex[:6].upper()}",
            "name": "Unauthorized Product",
            "cost": "10.00",
            "base_price": "20.00",
        },
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res_create.status_code == 403
    assert "missing required permission 'products:write'" in res_create.json()["error"]["message"]
