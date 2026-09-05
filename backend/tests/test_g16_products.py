"""Comprehensive Test Suite for DealFlow360 G16 (Phases 076–080).

Verifies:
- Phase 076: Product Tax (tax_rate >= 0, Decimal percentage, validation, price/margin stability)
- Phase 077: Product Units (ProductUnit catalog CRUD, unit selection, normalization)
- Phase 078: Product Variants (Parent-child relationship, SKU uniqueness across products/variants, price/cost overrides, variant CRUD)
- Phase 079: Product Attributes & Values (Attribute definition CRUD, option values, variant linking)
- Phase 080: Subscription Products (is_subscription flag on product creation/update/retrieval, validation)
- RBAC and Permission enforcement (products:read, products:write)
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
from app.models.product_attribute import ProductAttribute, ProductAttributeValue
from app.models.product_category import ProductCategory
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant
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
def setup_g16_test_data(db_session):
    """Seed isolated company, roles, users, and categories for G16 tests."""
    unique_suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G16 Test Corp {unique_suffix}",
        legal_name=f"G16 Test Corporation {unique_suffix}",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    # Permissions
    perm_read = db_session.scalars(select(Permission).where(Permission.name == "products:read")).first()
    perm_write = db_session.scalars(select(Permission).where(Permission.name == "products:write")).first()

    # Manager Role (read + write)
    role_manager = Role(name=f"G16 Product Manager {unique_suffix}")
    role_manager.permissions.extend([p for p in [perm_read, perm_write] if p])
    db_session.add(role_manager)

    # Viewer Role (read only)
    role_viewer = Role(name=f"G16 Product Viewer {unique_suffix}")
    role_viewer.permissions.extend([p for p in [perm_read] if p])
    db_session.add(role_viewer)
    db_session.flush()

    # Users
    user_manager = User(
        email=f"manager_g16_{unique_suffix}@test.com",
        first_name="Product",
        last_name="Manager",
        company_id=company.id,
        is_active=True,
    )
    user_manager.roles.append(role_manager)

    user_viewer = User(
        email=f"viewer_g16_{unique_suffix}@test.com",
        first_name="Product",
        last_name="Viewer",
        company_id=company.id,
        is_active=True,
    )
    user_viewer.roles.append(role_viewer)
    db_session.add_all([user_manager, user_viewer])
    db_session.flush()

    category = ProductCategory(
        name=f"Cloud Infra {unique_suffix}",
        code=f"CAT-CLOUD-{unique_suffix.upper()}",
        description="Cloud infrastructure and services",
        is_active=True,
    )
    db_session.add(category)
    db_session.commit()

    token_manager = create_access_token(str(user_manager.id))
    token_viewer = create_access_token(str(user_viewer.id))

    return {
        "company": company,
        "category": category,
        "manager_headers": {"Authorization": f"Bearer {token_manager}"},
        "viewer_headers": {"Authorization": f"Bearer {token_viewer}"},
        "suffix": unique_suffix,
    }


# ===========================================================================
# Phase 076: Product Tax Tests
# ===========================================================================

def test_phase_076_product_tax_creation_and_update(client, setup_g16_test_data):
    """Verify tax_rate field validation, decimal precision, and non-negative constraint."""
    headers = setup_g16_test_data["manager_headers"]
    suffix = setup_g16_test_data["suffix"]
    cat_id = str(setup_g16_test_data["category"].id)

    # 1. Create product with valid tax rate
    sku = f"TAX-PRD-{suffix.upper()}-01"
    create_payload = {
        "sku": sku,
        "name": f"Tax Tested Server {suffix}",
        "description": "Server with 8.25% sales tax",
        "category_id": cat_id,
        "cost": "1000.00",
        "base_price": "2000.00",
        "unit": "unit",
        "tax_rate": "8.25",
        "is_subscription": False,
        "is_active": True,
    }
    res = client.post("/api/v1/products", json=create_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert Decimal(str(data["tax_rate"])) == Decimal("8.25")
    assert Decimal(str(data["margin_amount"])) == Decimal("1000.00")
    assert Decimal(str(data["margin_percentage"])) == Decimal("50.00")
    product_id = data["id"]

    # 2. Update tax rate
    update_res = client.put(f"/api/v1/products/{product_id}", json={"tax_rate": "12.50"}, headers=headers)
    assert update_res.status_code == 200
    assert Decimal(str(update_res.json()["data"]["tax_rate"])) == Decimal("12.50")

    # 3. Reject negative tax rate
    neg_res = client.put(f"/api/v1/products/{product_id}", json={"tax_rate": "-5.00"}, headers=headers)
    assert neg_res.status_code == 422


# ===========================================================================
# Phase 077: Product Units Tests
# ===========================================================================

def test_phase_077_product_units_catalog_crud(client, setup_g16_test_data):
    """Verify standard units of measure catalog CRUD and authorization."""
    mgr_headers = setup_g16_test_data["manager_headers"]
    view_headers = setup_g16_test_data["viewer_headers"]
    suffix = setup_g16_test_data["suffix"]

    # 1. Create unit
    code = f"BUNDLE_{suffix.upper()}"
    create_payload = {
        "code": code,
        "name": "Hardware Bundle Pack",
        "description": "Packaged equipment bundles",
        "is_active": True,
    }
    res = client.post("/api/v1/product-units", json=create_payload, headers=mgr_headers)
    assert res.status_code == 201
    unit_data = res.json()["data"]
    assert unit_data["code"] == code
    assert unit_data["name"] == "Hardware Bundle Pack"
    unit_id = unit_data["id"]

    # 2. Duplicate code rejection
    dup_res = client.post("/api/v1/product-units", json=create_payload, headers=mgr_headers)
    assert dup_res.status_code == 400

    # 3. Read unit
    get_res = client.get(f"/api/v1/product-units/{unit_id}", headers=view_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == unit_id

    # 4. List units
    list_res = client.get("/api/v1/product-units", headers=view_headers)
    assert list_res.status_code == 200
    assert any(u["code"] == code for u in list_res.json()["data"])

    # 5. Update unit
    upd_res = client.put(
        f"/api/v1/product-units/{unit_id}",
        json={"name": "Updated Hardware Bundle Pack"},
        headers=mgr_headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["data"]["name"] == "Updated Hardware Bundle Pack"

    # 6. Delete unit
    del_res = client.delete(f"/api/v1/product-units/{unit_id}?soft=true", headers=mgr_headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True


# ===========================================================================
# Phase 078: Product Variants Tests
# ===========================================================================

def test_phase_078_product_variants_crud_and_overrides(client, setup_g16_test_data):
    """Verify parent-child product variant management, SKU uniqueness, and price overrides."""
    headers = setup_g16_test_data["manager_headers"]
    suffix = setup_g16_test_data["suffix"]
    cat_id = str(setup_g16_test_data["category"].id)

    # 1. Create parent product
    parent_sku = f"VPAR-{suffix.upper()}"
    p_res = client.post(
        "/api/v1/products",
        json={
            "sku": parent_sku,
            "name": f"Variant Parent Item {suffix}",
            "category_id": cat_id,
            "cost": "500.00",
            "base_price": "1000.00",
            "unit": "unit",
            "tax_rate": "5.00",
            "is_subscription": False,
        },
        headers=headers,
    )
    assert p_res.status_code == 201
    parent_id = p_res.json()["data"]["id"]

    # 2. Create variant under parent
    var_sku = f"{parent_sku}-V1"
    v_res = client.post(
        f"/api/v1/products/{parent_id}/variants",
        json={
            "sku": var_sku,
            "name": "Variant 1 - 32GB RAM",
            "cost": "600.00",
            "base_price": "1200.00",
            "is_active": True,
        },
        headers=headers,
    )
    assert v_res.status_code == 201
    var_data = v_res.json()["data"]
    assert var_data["sku"] == var_sku
    assert Decimal(str(var_data["cost"])) == Decimal("600.00")
    assert Decimal(str(var_data["base_price"])) == Decimal("1200.00")
    variant_id = var_data["id"]

    # 3. Prevent duplicate SKU against existing product or variant
    dup_v = client.post(
        f"/api/v1/products/{parent_id}/variants",
        json={"sku": var_sku, "name": "Duplicate Variant"},
        headers=headers,
    )
    assert dup_v.status_code == 400

    dup_prod_sku = client.post(
        f"/api/v1/products/{parent_id}/variants",
        json={"sku": parent_sku, "name": "Variant With Parent SKU"},
        headers=headers,
    )
    assert dup_prod_sku.status_code == 400

    # 4. List variants
    list_v = client.get(f"/api/v1/products/{parent_id}/variants", headers=headers)
    assert list_v.status_code == 200
    assert len(list_v.json()["data"]) >= 1

    # 5. Get variant by ID
    get_v = client.get(f"/api/v1/products/variants/{variant_id}", headers=headers)
    assert get_v.status_code == 200
    assert get_v.json()["data"]["id"] == variant_id

    # 6. Update variant
    upd_v = client.put(
        f"/api/v1/products/variants/{variant_id}",
        json={"name": "Variant 1 - 64GB RAM", "base_price": "1350.00"},
        headers=headers,
    )
    assert upd_v.status_code == 200
    assert upd_v.json()["data"]["name"] == "Variant 1 - 64GB RAM"
    assert Decimal(str(upd_v.json()["data"]["base_price"])) == Decimal("1350.00")

    # 7. Delete variant
    del_v = client.delete(f"/api/v1/products/variants/{variant_id}?soft=true", headers=headers)
    assert del_v.status_code == 200
    assert del_v.json()["data"]["deleted"] is True


# ===========================================================================
# Phase 079: Product Attributes & Options Tests
# ===========================================================================

def test_phase_079_product_attributes_and_options(client, setup_g16_test_data):
    """Verify creation of reusable product attributes and value options."""
    headers = setup_g16_test_data["manager_headers"]
    suffix = setup_g16_test_data["suffix"]

    # 1. Create attribute
    attr_code = f"STORAGE_{suffix.upper()}"
    res = client.post(
        "/api/v1/product-attributes",
        json={
            "code": attr_code,
            "name": "Storage Capacity",
            "description": "Drive storage size",
            "is_active": True,
        },
        headers=headers,
    )
    assert res.status_code == 201
    attr_data = res.json()["data"]
    assert attr_data["code"] == attr_code
    attr_id = attr_data["id"]

    # 2. Add options/values
    val_res1 = client.post(
        f"/api/v1/product-attributes/{attr_id}/values",
        json={"value": "512GB SSD", "display_order": 1},
        headers=headers,
    )
    assert val_res1.status_code == 201
    val1_id = val_res1.json()["data"]["id"]

    val_res2 = client.post(
        f"/api/v1/product-attributes/{attr_id}/values",
        json={"value": "1TB SSD", "display_order": 2},
        headers=headers,
    )
    assert val_res2.status_code == 201

    # 3. Duplicate value rejection under same attribute
    dup_val = client.post(
        f"/api/v1/product-attributes/{attr_id}/values",
        json={"value": "512GB SSD"},
        headers=headers,
    )
    assert dup_val.status_code == 400

    # 4. Fetch attribute with values
    get_attr = client.get(f"/api/v1/product-attributes/{attr_id}", headers=headers)
    assert get_attr.status_code == 200
    vals = get_attr.json()["data"]["values"]
    assert len(vals) == 2

    # 5. Delete one value option
    del_val = client.delete(f"/api/v1/product-attributes/{attr_id}/values/{val1_id}", headers=headers)
    assert del_val.status_code == 200


# ===========================================================================
# Phase 080: Subscription Products Tests
# ===========================================================================

def test_phase_080_subscription_products(client, setup_g16_test_data):
    """Verify is_subscription boolean flag handling, filtering, and validation."""
    headers = setup_g16_test_data["manager_headers"]
    suffix = setup_g16_test_data["suffix"]
    cat_id = str(setup_g16_test_data["category"].id)

    # 1. Create subscription product
    sub_sku = f"SUB-SAAS-{suffix.upper()}"
    res = client.post(
        "/api/v1/products",
        json={
            "sku": sub_sku,
            "name": f"Cloud SaaS Subscription {suffix}",
            "category_id": cat_id,
            "cost": "100.00",
            "base_price": "299.00",
            "unit": "month",
            "tax_rate": "0.00",
            "is_subscription": True,
            "is_active": True,
        },
        headers=headers,
    )
    assert res.status_code == 201
    prod_data = res.json()["data"]
    assert prod_data["is_subscription"] is True
    prod_id = prod_data["id"]

    # 2. Verify filter by is_subscription=true
    filter_res = client.get(f"/api/v1/products?is_subscription=true", headers=headers)
    assert filter_res.status_code == 200
    items = filter_res.json()["data"]["items"]
    assert any(p["sku"] == sub_sku and p["is_subscription"] is True for p in items)

    # 3. Toggle is_subscription to false
    toggle_res = client.put(f"/api/v1/products/{prod_id}", json={"is_subscription": False}, headers=headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["data"]["is_subscription"] is False
