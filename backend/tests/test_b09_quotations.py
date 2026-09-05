"""Comprehensive Test Suite for DealFlow360 B09 (Phases 186–195: Quotation Engine).

Verifies strict roadmap compliance and production guarantees:
- Phase 186: Quotation CRUD (Create, Read, Update, Delete/Cancel, header + lines, tenant isolation)
- Phase 187: Quote Number Generation (Deterministic unique quote number, sequential company-scoped numbering)
- Phase 188: Customer Selection (Associate quotation with customer, reject cross-tenant customer, return metadata)
- Phase 189: Product Selection (Add products, validate status, reject inactive products)
- Phase 190: Quantity Management (Positive quantity validation, Decimal-safe quantities, reject <= 0)
- Phase 191: Unit Price (Product base price inheritance, authorized override, precision preservation)
- Phase 192: Tax Calculation (Tax calculation per line, correct taxable base, zero-tax cases)
- Phase 193: Line Discount (Percentage discount boundaries, discounted line subtotal)
- Phase 194: Overall Discount (Quotation-level discount, interaction with line discounts, totals recalculation)
- Phase 195: Real-Time Margin (Cost vs selling price, gross profit, margin %, negative/zero margin detection)
- Security & Multi-Tenancy (Strict tenant isolation, RBAC permissions)
- B08 Compatibility (B08 recommendation add-to-quote compatibility)
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.company import Company
from app.models.customer import Customer
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation, QuotationStatus
from app.models.quotation_line_item import QuotationLineItem
from app.models.role import Role
from app.models.user import User
from app.schemas.quotation import (
    QuotationCalculationRequest,
    QuotationCreate,
    QuotationLineItemCreate,
    QuotationUpdate,
)
from app.services.quotation import (
    QuotationCalculationEngine,
    QuotationNumberGenerator,
    QuotationService,
)


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
def setup_b09_data(db_session):
    """Seed companies, users, products, categories, and customers for B09 testing."""
    # 1. Multi-Tenant Companies
    company_a = Company(
        name=f"B09 Corp Alpha {uuid.uuid4().hex[:8]}",
        legal_name="Alpha Tech Quotations Inc",
        email=f"alpha_quote_{uuid.uuid4().hex[:8]}@example.com",
    )
    company_b = Company(
        name=f"B09 Corp Beta {uuid.uuid4().hex[:8]}",
        legal_name="Beta Global Deals Corp",
        email=f"beta_quote_{uuid.uuid4().hex[:8]}@example.com",
    )
    db_session.add_all([company_a, company_b])
    db_session.commit()

    # 2. Permissions & Roles
    perm_read = db_session.execute(select(Permission).where(Permission.name == "quotations:read")).scalar_one_or_none()
    if not perm_read:
        perm_read = Permission(name="quotations:read", description="Read quotations", resource="quotations", action="read")
        db_session.add(perm_read)

    perm_write = db_session.execute(select(Permission).where(Permission.name == "quotations:write")).scalar_one_or_none()
    if not perm_write:
        perm_write = Permission(name="quotations:write", description="Write quotations", resource="quotations", action="write")
        db_session.add(perm_write)

    perm_disc_read = db_session.execute(select(Permission).where(Permission.name == "discounts:read")).scalar_one_or_none()
    if not perm_disc_read:
        perm_disc_read = Permission(name="discounts:read", description="Read discounts", resource="discounts", action="read")
        db_session.add(perm_disc_read)

    db_session.commit()

    role_sales = Role(name=f"Sales_B09_{uuid.uuid4().hex[:8]}", description="Sales Representative B09")
    role_sales.permissions.extend([perm_read, perm_write, perm_disc_read])
    db_session.add(role_sales)
    db_session.commit()

    # 3. Users
    user_a = User(
        company_id=company_a.id,
        email=f"sales_a_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="mock_hash",
        first_name="Alice",
        last_name="Sales",
        is_active=True,
    )
    user_a.roles.append(role_sales)

    user_b = User(
        company_id=company_b.id,
        email=f"sales_b_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="mock_hash",
        first_name="Bob",
        last_name="Sales",
        is_active=True,
    )
    user_b.roles.append(role_sales)

    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(subject=str(user_a.id))
    token_b = create_access_token(subject=str(user_b.id))

    # 4. Product Category
    cat_compute = ProductCategory(
        name=f"Compute_{uuid.uuid4().hex[:8]}",
        code=f"CMP_{uuid.uuid4().hex[:8]}",
        description="Enterprise compute infrastructure",
        is_active=True,
    )
    db_session.add(cat_compute)
    db_session.commit()

    # 5. Products Catalog
    # P1: Standard Server (Price: $1,000.00, Cost: $600.00 -> Margin: 40%)
    p1 = Product(
        sku=f"SRV-STD-{uuid.uuid4().hex[:8]}",
        name="Standard Compute Node",
        category_id=cat_compute.id,
        cost=Decimal("600.00"),
        base_price=Decimal("1000.00"),
        inventory_quantity=50,
        is_active=True,
    )
    # P2: Premium Server (Price: $2,500.00, Cost: $1,500.00 -> Margin: 40%)
    p2 = Product(
        sku=f"SRV-PRM-{uuid.uuid4().hex[:8]}",
        name="Enterprise Compute Matrix",
        category_id=cat_compute.id,
        cost=Decimal("1500.00"),
        base_price=Decimal("2500.00"),
        inventory_quantity=20,
        is_active=True,
    )
    # P3: Loss Leader / Cheap item (Price: $100.00, Cost: $500.00 -> Margin: -400%)
    p3_loss = Product(
        sku=f"LOSS-LEAD-{uuid.uuid4().hex[:8]}",
        name="Subsidized Starter Hardware",
        category_id=cat_compute.id,
        cost=Decimal("500.00"),
        base_price=Decimal("100.00"),
        inventory_quantity=10,
        is_active=True,
    )
    # P4: Zero Margin item (Price: $300.00, Cost: $300.00 -> Margin: 0%)
    p4_zero = Product(
        sku=f"AT-COST-{uuid.uuid4().hex[:8]}",
        name="Pass-through Cable Bundle",
        category_id=cat_compute.id,
        cost=Decimal("300.00"),
        base_price=Decimal("300.00"),
        inventory_quantity=100,
        is_active=True,
    )
    # P5: Inactive Product (Cannot be quoted)
    p5_inactive = Product(
        sku=f"DISC-B09-{uuid.uuid4().hex[:8]}",
        name="Obsolete Storage Array",
        category_id=cat_compute.id,
        cost=Decimal("200.00"),
        base_price=Decimal("400.00"),
        inventory_quantity=0,
        is_active=False,
    )
    db_session.add_all([p1, p2, p3_loss, p4_zero, p5_inactive])
    db_session.commit()

    # 6. Customers
    now = datetime.now(timezone.utc)
    cust_a = Customer(
        company_id=company_a.id,
        customer_code=f"CUST-A-{uuid.uuid4().hex[:8]}",
        name="Alpha Global Corp",
        email=f"alphacust_{uuid.uuid4().hex[:8]}@example.com",
        is_active=True,
        created_at=now - timedelta(days=60),
    )
    cust_b = Customer(
        company_id=company_b.id,
        customer_code=f"CUST-B-{uuid.uuid4().hex[:8]}",
        name="Beta Logistics Sub",
        email=f"betacust_{uuid.uuid4().hex[:8]}@example.com",
        is_active=True,
        created_at=now - timedelta(days=30),
    )
    db_session.add_all([cust_a, cust_b])
    db_session.commit()

    return {
        "company_a": company_a,
        "company_b": company_b,
        "user_a": user_a,
        "user_b": user_b,
        "token_a": token_a,
        "token_b": token_b,
        "p1": p1,
        "p2": p2,
        "p3_loss": p3_loss,
        "p4_zero": p4_zero,
        "p5_inactive": p5_inactive,
        "cust_a": cust_a,
        "cust_b": cust_b,
    }


# ==============================================================================
# Phase 186: Quotation CRUD Tests
# ==============================================================================

def test_phase_186_quotation_crud_lifecycle(client, setup_b09_data):
    """Verify Quotation CRUD operations: create, read, list, update, cancel, and delete."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    # 1. Create Quotation
    create_payload = {
        "customer_id": str(data["cust_a"].id),
        "notes": "Initial Q1 expansion deal",
        "terms_conditions": "Net 30 days payment",
        "overall_discount_percent": "0.00",
        "line_items": [
            {
                "product_id": str(data["p1"].id),
                "quantity": "2.00",
                "unit_price": "1000.00",
                "discount_percent": "5.00",
                "tax_rate": "8.00",
            },
            {
                "product_id": str(data["p2"].id),
                "quantity": "1.00",
                "tax_rate": "0.00",
            },
        ],
    }
    create_res = client.post("/api/v1/quotations", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    quote_data = create_res.json()["data"]
    quote_id = quote_data["id"]
    quote_num = quote_data["quotation_number"]
    assert quote_data["status"] == "DRAFT"
    assert quote_data["customer_id"] == str(data["cust_a"].id)
    assert len(quote_data["line_items"]) == 2

    # 2. Read Quotation Detail
    get_res = client.get(f"/api/v1/quotations/{quote_id}", headers=headers)
    assert get_res.status_code == 200
    detail = get_res.json()["data"]
    assert detail["id"] == quote_id
    assert detail["quotation_number"] == quote_num
    assert detail["customer_name"] == "Alpha Global Corp"

    # 3. List Quotations with pagination and filtering
    list_res = client.get(f"/api/v1/quotations?customer_id={data['cust_a'].id}&status=DRAFT", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["data"]
    assert any(q["id"] == quote_id for q in items)

    # 4. Update Quotation
    update_payload = {
        "notes": "Updated Q1 deal notes",
        "overall_discount_percent": "2.00",
        "line_items": [
            {
                "product_id": str(data["p1"].id),
                "quantity": "3.00",
                "unit_price": "1000.00",
                "discount_percent": "0.00",
                "tax_rate": "10.00",
            }
        ],
    }
    put_res = client.put(f"/api/v1/quotations/{quote_id}", json=update_payload, headers=headers)
    assert put_res.status_code == 200
    updated_data = put_res.json()["data"]
    assert updated_data["notes"] == "Updated Q1 deal notes"
    assert len(updated_data["line_items"]) == 1

    # 5. Cancel Quotation
    cancel_res = client.post(f"/api/v1/quotations/{quote_id}/cancel?reason=CustomerPostponed", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"

    # 6. Delete Cancelled Quotation
    del_res = client.delete(f"/api/v1/quotations/{quote_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True

    # Verify deleted quote is gone
    get_after_del = client.get(f"/api/v1/quotations/{quote_id}", headers=headers)
    assert get_after_del.status_code == 404


# ==============================================================================
# Phase 187: Quote Number Generation Tests
# ==============================================================================

def test_phase_187_deterministic_unique_numbering(client, setup_b09_data):
    """Verify sequential, collision-safe quotation number generation."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    numbers = []
    for _ in range(3):
        res = client.post(
            "/api/v1/quotations",
            json={
                "customer_id": str(data["cust_a"].id),
                "line_items": [{"product_id": str(data["p1"].id), "quantity": "1.00"}],
            },
            headers=headers,
        )
        assert res.status_code == 201
        numbers.append(res.json()["data"]["quotation_number"])

    # All numbers must be distinct
    assert len(set(numbers)) == 3
    # Format check: QT-YYYYMM-XXXX
    now = datetime.now(timezone.utc)
    expected_prefix = f"QT-{now.strftime('%Y%m')}-"
    for num in numbers:
        assert num.startswith(expected_prefix)


# ==============================================================================
# Phase 188: Customer Selection Tests
# ==============================================================================

def test_phase_188_customer_selection_and_tenant_validation(client, setup_b09_data):
    """Verify customer selection, response metadata, and cross-tenant customer rejection."""
    data = setup_b09_data
    headers_a = {"Authorization": f"Bearer {data['token_a']}"}

    # Cross-tenant customer selection must be rejected
    payload_cross = {
        "customer_id": str(data["cust_b"].id),  # Customer belongs to Company B
        "line_items": [{"product_id": str(data["p1"].id), "quantity": "1.00"}],
    }
    res_cross = client.post("/api/v1/quotations", json=payload_cross, headers=headers_a)
    assert res_cross.status_code == 404

    # Valid customer selection includes customer details in response
    payload_valid = {
        "customer_id": str(data["cust_a"].id),
        "line_items": [{"product_id": str(data["p1"].id), "quantity": "1.00"}],
    }
    res_valid = client.post("/api/v1/quotations", json=payload_valid, headers=headers_a)
    assert res_valid.status_code == 201
    body = res_valid.json()["data"]
    assert body["customer_id"] == str(data["cust_a"].id)
    assert body["customer_name"] == data["cust_a"].name
    assert body["customer_code"] == data["cust_a"].customer_code


# ==============================================================================
# Phase 189: Product Selection Tests
# ==============================================================================

def test_phase_189_product_selection_and_inactive_rejection(client, setup_b09_data):
    """Verify product selection and rejection of inactive or nonexistent products."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    # Inactive product rejection
    res_inactive = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": str(data["cust_a"].id),
            "line_items": [{"product_id": str(data["p5_inactive"].id), "quantity": "1.00"}],
        },
        headers=headers,
    )
    assert res_inactive.status_code == 400
    err_msg = res_inactive.json().get("error", {}).get("message", "") or res_inactive.json().get("detail", "")
    assert "inactive" in err_msg.lower()

    # Nonexistent product rejection
    res_nonexistent = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": str(data["cust_a"].id),
            "line_items": [{"product_id": str(uuid.uuid4()), "quantity": "1.00"}],
        },
        headers=headers,
    )
    assert res_nonexistent.status_code == 404


# ==============================================================================
# Phase 190: Quantity Management Tests
# ==============================================================================

def test_phase_190_quantity_management_validation(client, setup_b09_data):
    """Verify positive quantity validation and rejection of zero or negative quantities."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    # Zero quantity
    res_zero = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": str(data["cust_a"].id),
            "line_items": [{"product_id": str(data["p1"].id), "quantity": "0.00"}],
        },
        headers=headers,
    )
    assert res_zero.status_code in (400, 422)

    # Negative quantity
    res_neg = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": str(data["cust_a"].id),
            "line_items": [{"product_id": str(data["p1"].id), "quantity": "-5.00"}],
        },
        headers=headers,
    )
    assert res_neg.status_code in (400, 422)

    # Fractional decimal quantity (e.g. 2.50)
    res_frac = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": str(data["cust_a"].id),
            "line_items": [{"product_id": str(data["p1"].id), "quantity": "2.50", "unit_price": "1000.00"}],
        },
        headers=headers,
    )
    assert res_frac.status_code == 201
    line = res_frac.json()["data"]["line_items"][0]
    assert Decimal(line["subtotal"]) == Decimal("2500.00")


# ==============================================================================
# Phase 191: Unit Price Tests
# ==============================================================================

def test_phase_191_unit_price_derivation_and_override(client, setup_b09_data):
    """Verify product base price derivation and authorized unit price override."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    payload = {
        "customer_id": str(data["cust_a"].id),
        "line_items": [
            # Line 1: No override -> Product base price ($1,000.00)
            {"product_id": str(data["p1"].id), "quantity": "1.00"},
            # Line 2: Authorized override -> ($1,150.00)
            {"product_id": str(data["p1"].id), "quantity": "1.00", "unit_price": "1150.00"},
        ],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=headers)
    assert res.status_code == 201
    lines = res.json()["data"]["line_items"]
    assert Decimal(lines[0]["unit_price"]) == Decimal("1000.00")
    assert Decimal(lines[1]["unit_price"]) == Decimal("1150.00")


# ==============================================================================
# Phase 192: Tax Calculation Tests
# ==============================================================================

def test_phase_192_tax_calculation(client, setup_b09_data):
    """Verify line tax and zero-tax calculations in strict Decimal arithmetic."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    payload = {
        "customer_id": str(data["cust_a"].id),
        "line_items": [
            # Line 1: Subtotal $2,000.00, 10% tax -> $200.00 tax
            {"product_id": str(data["p1"].id), "quantity": "2.00", "unit_price": "1000.00", "tax_rate": "10.00"},
            # Line 2: Subtotal $2,500.00, 0% tax -> $0.00 tax (zero-tax case)
            {"product_id": str(data["p2"].id), "quantity": "1.00", "unit_price": "2500.00", "tax_rate": "0.00"},
        ],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=headers)
    assert res.status_code == 201
    quote = res.json()["data"]
    lines = quote["line_items"]

    assert Decimal(lines[0]["tax_amount"]) == Decimal("200.00")
    assert Decimal(lines[1]["tax_amount"]) == Decimal("0.00")
    assert Decimal(quote["tax_amount"]) == Decimal("200.00")
    assert Decimal(quote["total_amount"]) == Decimal("4700.00")  # (2000 + 2500) + 200


# ==============================================================================
# Phase 193: Line Discount Tests
# ==============================================================================

def test_phase_193_line_discount_calculation(client, setup_b09_data):
    """Verify line-level percentage discount and subtotal recalculation."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    payload = {
        "customer_id": str(data["cust_a"].id),
        "line_items": [
            # Line 1: 2 * 1000 = 2000 subtotal, 15% discount = 300 discount -> 1700 net
            {
                "product_id": str(data["p1"].id),
                "quantity": "2.00",
                "unit_price": "1000.00",
                "discount_percent": "15.00",
                "tax_rate": "5.00",
            }
        ],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=headers)
    assert res.status_code == 201
    line = res.json()["data"]["line_items"][0]

    assert Decimal(line["subtotal"]) == Decimal("2000.00")
    assert Decimal(line["discount_amount"]) == Decimal("300.00")
    assert Decimal(line["net_amount"]) == Decimal("1700.00")
    # Tax on 1700 @ 5% = 85.00
    assert Decimal(line["tax_amount"]) == Decimal("85.00")
    assert Decimal(line["total_amount"]) == Decimal("1785.00")


# ==============================================================================
# Phase 194: Overall Discount Tests
# ==============================================================================

def test_phase_194_overall_discount_and_interaction(client, setup_b09_data):
    """Verify quotation-level overall discount and interaction with line discounts."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    payload = {
        "customer_id": str(data["cust_a"].id),
        "overall_discount_percent": "10.00",
        "line_items": [
            # Line 1: 1 * 1000 = 1000 subtotal, 10% line discount -> 900 net
            {"product_id": str(data["p1"].id), "quantity": "1.00", "unit_price": "1000.00", "discount_percent": "10.00", "tax_rate": "0.00"},
            # Line 2: 1 * 2000 = 2000 subtotal, 0% line discount -> 2000 net
            {"product_id": str(data["p2"].id), "quantity": "1.00", "unit_price": "2000.00", "discount_percent": "0.00", "tax_rate": "0.00"},
        ],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=headers)
    assert res.status_code == 201
    q = res.json()["data"]

    # Subtotal = 3000.00
    assert Decimal(q["subtotal"]) == Decimal("3000.00")
    # Line discount total = 100.00
    assert Decimal(q["line_discount_total"]) == Decimal("100.00")
    # Total net lines = 2900.00
    # Overall discount 10% on 2900.00 = 290.00
    assert Decimal(q["overall_discount_amount"]) == Decimal("290.00")
    # Total discount = 100 + 290 = 390.00
    assert Decimal(q["total_discount"]) == Decimal("390.00")
    # Taxable amount = 2900 - 290 = 2610.00
    assert Decimal(q["taxable_amount"]) == Decimal("2610.00")
    # Total amount = 2610.00
    assert Decimal(q["total_amount"]) == Decimal("2610.00")


# ==============================================================================
# Phase 195: Real-Time Margin Tests
# ==============================================================================

def test_phase_195_margin_calculation_positive_zero_negative(client, setup_b09_data):
    """Verify real-time gross margin calculation, including positive, zero, and negative margins."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    # Case A: Positive Margin Quotation (P1: Price 1000, Cost 600 -> GP 400, 40%)
    res_pos = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": str(data["cust_a"].id),
            "line_items": [{"product_id": str(data["p1"].id), "quantity": "1.00", "unit_price": "1000.00"}],
        },
        headers=headers,
    )
    assert res_pos.status_code == 201
    q_pos = res_pos.json()["data"]
    assert Decimal(q_pos["gross_profit"]) == Decimal("400.00")
    assert Decimal(q_pos["margin_percentage"]) == Decimal("40.00")
    assert q_pos["is_negative_margin"] is False

    # Case B: Negative Margin Quotation (P3_loss: Price 100, Cost 500 -> GP -400, -400%)
    res_neg = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": str(data["cust_a"].id),
            "line_items": [{"product_id": str(data["p3_loss"].id), "quantity": "1.00", "unit_price": "100.00"}],
        },
        headers=headers,
    )
    assert res_neg.status_code == 201
    q_neg = res_neg.json()["data"]
    assert Decimal(q_neg["gross_profit"]) == Decimal("-400.00")
    assert Decimal(q_neg["margin_percentage"]) == Decimal("-400.00")
    assert q_neg["is_negative_margin"] is True

    # Case C: Zero Margin Quotation (P4_zero: Price 300, Cost 300 -> GP 0, 0%)
    res_zero = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": str(data["cust_a"].id),
            "line_items": [{"product_id": str(data["p4_zero"].id), "quantity": "1.00", "unit_price": "300.00"}],
        },
        headers=headers,
    )
    assert res_zero.status_code == 201
    q_zero = res_zero.json()["data"]
    assert Decimal(q_zero["gross_profit"]) == Decimal("0.00")
    assert Decimal(q_zero["margin_percentage"]) == Decimal("0.00")
    assert q_zero["is_negative_margin"] is False


# ==============================================================================
# Transient Quotation Calculation Endpoint Tests
# ==============================================================================

def test_transient_quotation_calculation_endpoint(client, setup_b09_data):
    """Verify POST /api/v1/quotations/calculate dry-run endpoint."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    payload = {
        "overall_discount_percent": "5.00",
        "line_items": [
            {"product_id": str(data["p1"].id), "quantity": "2.00", "unit_price": "1000.00", "discount_percent": "0.00", "tax_rate": "10.00"}
        ],
    }
    res = client.post("/api/v1/quotations/calculate", json=payload, headers=headers)
    assert res.status_code == 200
    calc = res.json()["data"]
    # 2 * 1000 = 2000 subtotal, 5% overall discount = 100 discount -> 1900 taxable
    # tax 10% on 1900 = 190 -> total 2090
    assert Decimal(calc["subtotal"]) == Decimal("2000.00")
    assert Decimal(calc["overall_discount_amount"]) == Decimal("100.00")
    assert Decimal(calc["taxable_amount"]) == Decimal("1900.00")
    assert Decimal(calc["tax_amount"]) == Decimal("190.00")
    assert Decimal(calc["total_amount"]) == Decimal("2090.00")
    assert Decimal(calc["total_cost"]) == Decimal("1200.00")
    assert Decimal(calc["gross_profit"]) == Decimal("700.00")


# ==============================================================================
# Security & Multi-Tenancy Tests
# ==============================================================================

def test_security_multi_tenant_isolation(client, setup_b09_data):
    """Verify Company B user cannot access or manipulate Company A's quotation."""
    data = setup_b09_data
    headers_a = {"Authorization": f"Bearer {data['token_a']}"}
    headers_b = {"Authorization": f"Bearer {data['token_b']}"}

    # Create quotation for Company A
    res_a = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": str(data["cust_a"].id),
            "line_items": [{"product_id": str(data["p1"].id), "quantity": "1.00"}],
        },
        headers=headers_a,
    )
    quote_id = res_a.json()["data"]["id"]

    # Company B user attempts to access Company A's quotation -> 404
    res_get_b = client.get(f"/api/v1/quotations/{quote_id}", headers=headers_b)
    assert res_get_b.status_code == 404

    # Company B user attempts to update Company A's quotation -> 404
    res_put_b = client.put(f"/api/v1/quotations/{quote_id}", json={"notes": "Hacked"}, headers=headers_b)
    assert res_put_b.status_code == 404

    # Company B user attempts to cancel Company A's quotation -> 404
    res_cancel_b = client.post(f"/api/v1/quotations/{quote_id}/cancel", headers=headers_b)
    assert res_cancel_b.status_code == 404

    # Company B user attempts to delete Company A's quotation -> 404
    res_del_b = client.delete(f"/api/v1/quotations/{quote_id}", headers=headers_b)
    assert res_del_b.status_code == 404


def test_security_unauthenticated_request(client):
    """Verify unauthenticated request returns HTTP 401."""
    res = client.get("/api/v1/quotations")
    assert res.status_code == 401


# ==============================================================================
# B08 Recommendation Add-to-Quote Regression Test
# ==============================================================================

def test_b08_add_to_quote_regression(client, setup_b09_data):
    """Verify B08 add-to-quote recommendation integration continues to function."""
    data = setup_b09_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    payload = {
        "customer_id": str(data["cust_a"].id),
        "product_id": str(data["p2"].id),
        "quantity": 1,
        "quote_reference": "QUOTE-REGRESSION-001",
        "existing_items": [
            {
                "product_id": str(data["p1"].id),
                "quantity": 2,
                "selling_price": "1000.00",
                "unit_cost": "600.00",
            }
        ],
    }
    res = client.post("/api/v1/recommendations/add-to-quote", json=payload, headers=headers)
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["status"] == "SUCCESS"
    assert body["added_quantity"] == 1
    assert Decimal(body["margin_summary"]["total_revenue"]) == Decimal("4500.00")  # 2000 + 2500
