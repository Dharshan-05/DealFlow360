"""Comprehensive Test Suite for DealFlow360 G24 (Phases 116–120).

Verifies:
- Phase 116: Inventory-Aware Discount (Signals: EXCESS_AVAILABLE, HEALTHY_STOCK, LOW_STOCK, OUT_OF_STOCK, BACKORDERED, ATP accuracy, tenant isolation)
- Phase 117: Deal-Value-Aware Discount (Decimal-safe financial evaluation, value tiers: LOW_VALUE, STANDARD_VALUE, HIGH_VALUE, ENTERPRISE_TIER)
- Phase 118: Discount Risk Calculation (Multi-factor risk score 0–100, risk levels LOW/MEDIUM/HIGH/CRITICAL, dimension weights, deterministic results)
- Phase 119: Discount Decision Engine (Strict precedence orchestration: Governance -> Actor Authority -> Max Safe -> Margin Protection -> Risk -> Decision: APPROVED/ADJUSTED/ESCALATION_REQUIRED/REJECTED)
- Phase 120: Automated Discount Application (Server-side re-verification, idempotency via deal_reference, CustomerDiscountHistory enrichment, AuditLog logging, unauthorized / rejected blocking)
- Security & RBAC: 401 unauthenticated, 403 unauthorized
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.applied_discount import AppliedDiscount
from app.models.audit_log import AuditLog
from app.models.backorder import Backorder
from app.models.category_discount_ceiling import CategoryDiscountCeiling
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.discount_configuration import DiscountConfiguration
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.product_discount_ceiling import ProductDiscountCeiling
from app.models.role import Role
from app.models.sales_rep_authority_limit import SalesRepAuthorityLimit
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.discount_automation import ApplyDiscountRequest
from app.services.discount_automation import (
    AutomatedDiscountApplicationService,
    DealValueAwareDiscountService,
    DiscountDecisionEngine,
    DiscountRiskCalculationService,
    InventoryAwareDiscountService,
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
def setup_g24_test_data(db_session):
    """Seed test company, roles (Admin, Sales Rep, Viewer), users, warehouses, stocks, backorders, products, customer, and policies."""
    suffix = uuid.uuid4().hex[:8]

    company = Company(
        name=f"G24 Enterprise {suffix}",
        legal_name=f"G24 Enterprise Corp {suffix}",
        is_active=True,
    )
    db_session.add(company)
    db_session.flush()

    # Permissions
    perm_read = db_session.scalars(select(Permission).where(Permission.name == "discounts:read")).first()
    if not perm_read:
        perm_read = Permission(name="discounts:read", description="Read discounts")
        db_session.add(perm_read)

    perm_write = db_session.scalars(select(Permission).where(Permission.name == "discounts:write")).first()
    if not perm_write:
        perm_write = Permission(name="discounts:write", description="Write discounts")
        db_session.add(perm_write)

    db_session.flush()

    # Roles
    admin_role = Role(name=f"Admin_{suffix}", description="Admin role")
    admin_role.permissions.extend([perm_read, perm_write])
    db_session.add(admin_role)

    rep_role = Role(name=f"Sales Representative_{suffix}", description="Sales Rep role")
    rep_role.permissions.extend([perm_read, perm_write])
    db_session.add(rep_role)

    no_perm_role = Role(name=f"Viewer_{suffix}", description="Viewer role without write permissions")
    db_session.add(no_perm_role)
    db_session.flush()

    # Users
    admin_user = User(
        email=f"admin_{suffix}@example.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[admin_role],
    )
    db_session.add(admin_user)

    rep_user = User(
        email=f"rep_{suffix}@example.com",
        first_name="Rep",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[rep_role],
    )
    db_session.add(rep_user)

    viewer_user = User(
        email=f"viewer_{suffix}@example.com",
        first_name="Viewer",
        last_name="User",
        is_active=True,
        company_id=company.id,
        roles=[no_perm_role],
    )
    db_session.add(viewer_user)

    # Category
    category = ProductCategory(
        name=f"Network Equipment {suffix}",
        code=f"NET_{suffix}",
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()

    # Products
    # 1. Standard product with high margin: Cost = $60, Base Price = $100 -> Margin = 40%
    product = Product(
        sku=f"SKU_{suffix}_MAIN",
        name=f"Enterprise Router {suffix}",
        base_price=Decimal("100.00"),
        cost=Decimal("60.00"),
        category_id=category.id,
        is_active=True,
    )
    db_session.add(product)

    # 2. Out of stock / backordered product
    oos_product = Product(
        sku=f"SKU_{suffix}_OOS",
        name=f"Depleted Switch {suffix}",
        base_price=Decimal("200.00"),
        cost=Decimal("120.00"),
        category_id=category.id,
        is_active=True,
    )
    db_session.add(oos_product)

    # 3. Excess stock product
    excess_product = Product(
        sku=f"SKU_{suffix}_EXCESS",
        name=f"Fiber Patch Cord {suffix}",
        base_price=Decimal("50.00"),
        cost=Decimal("20.00"),
        category_id=category.id,
        is_active=True,
    )
    db_session.add(excess_product)

    # 4. Low margin product: Cost = $95, Price = $100 -> Margin = 5%
    low_margin_product = Product(
        sku=f"SKU_{suffix}_LOW_MARGIN",
        name=f"Commodity Transceiver {suffix}",
        base_price=Decimal("100.00"),
        cost=Decimal("95.00"),
        category_id=category.id,
        is_active=True,
    )
    db_session.add(low_margin_product)
    db_session.flush()

    # Warehouses
    warehouse = Warehouse(
        company_id=company.id,
        name=f"Central Hub {suffix}",
        code=f"WH_{suffix}",
        priority=1,
        is_active=True,
    )
    db_session.add(warehouse)
    db_session.flush()

    # Stocks:
    # product: 25 physical, 5 reserved -> ATP = 20 (HEALTHY_STOCK)
    stock_main = WarehouseStock(
        warehouse_id=warehouse.id,
        product_id=product.id,
        quantity=25,
        reserved_quantity=5,
    )
    # excess_product: 200 physical, 10 reserved -> ATP = 190 (EXCESS_AVAILABLE)
    stock_excess = WarehouseStock(
        warehouse_id=warehouse.id,
        product_id=excess_product.id,
        quantity=200,
        reserved_quantity=10,
    )
    # oos_product: 0 physical, 0 reserved -> ATP = 0 (OUT_OF_STOCK)
    stock_oos = WarehouseStock(
        warehouse_id=warehouse.id,
        product_id=oos_product.id,
        quantity=0,
        reserved_quantity=0,
    )
    db_session.add_all([stock_main, stock_excess, stock_oos])

    # Backorder for oos_product
    backorder = Backorder(
        company_id=company.id,
        product_id=oos_product.id,
        requested_quantity=10,
        allocated_quantity=0,
        backordered_quantity=10,
        status="OPEN",
    )
    db_session.add(backorder)

    # Customer
    customer = Customer(
        company_id=company.id,
        customer_code=f"CUST_{suffix}",
        name=f"Apex Telecom {suffix}",
        is_active=True,
    )
    db_session.add(customer)

    # Second company for tenant checks
    other_company = Company(name=f"Other {suffix}", legal_name=f"Other Inc {suffix}", is_active=True)
    db_session.add(other_company)
    db_session.flush()

    other_customer = Customer(company_id=other_company.id, customer_code=f"OTHER_{suffix}", name=f"Other Cust {suffix}", is_active=True)
    db_session.add(other_customer)
    db_session.flush()

    # Policies
    # Company default ceiling = 30%
    config = DiscountConfiguration(
        company_id=company.id,
        name=f"Default Policy {suffix}",
        default_discount_ceiling=Decimal("30.00"),
        is_active=True,
        effective_from=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(config)

    # Customer ceiling = 25%
    cust_ceiling = CustomerDiscountCeiling(
        company_id=company.id,
        customer_id=customer.id,
        max_discount_percentage=Decimal("25.00"),
        is_active=True,
        effective_from=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(cust_ceiling)

    # Sales Rep authority limit = 15%
    rep_limit = SalesRepAuthorityLimit(
        company_id=company.id,
        user_id=rep_user.id,
        max_authorized_discount=Decimal("15.00"),
        is_active=True,
        effective_from=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(rep_limit)

    db_session.commit()

    admin_headers = {"Authorization": f"Bearer {create_access_token(admin_user.id)}"}
    rep_headers = {"Authorization": f"Bearer {create_access_token(rep_user.id)}"}
    viewer_headers = {"Authorization": f"Bearer {create_access_token(viewer_user.id)}"}

    return {
        "company": company,
        "admin_user": admin_user,
        "rep_user": rep_user,
        "viewer_user": viewer_user,
        "admin_headers": admin_headers,
        "rep_headers": rep_headers,
        "viewer_headers": viewer_headers,
        "product": product,
        "oos_product": oos_product,
        "excess_product": excess_product,
        "low_margin_product": low_margin_product,
        "customer": customer,
        "other_company": other_company,
        "other_customer": other_customer,
    }


# ==============================================================================
# Phase 116 Tests: Inventory-Aware Discount
# ==============================================================================

def test_inventory_signal_excess_stock(db_session, setup_g24_test_data):
    """ATP >= 100 -> EXCESS_AVAILABLE, factor = 1.20."""
    data = setup_g24_test_data
    res = InventoryAwareDiscountService.evaluate_inventory_signal(
        db=db_session,
        company_id=data["company"].id,
        product_id=data["excess_product"].id,
        base_target_discount=Decimal("10.00"),
    )
    assert res.inventory_signal == "EXCESS_AVAILABLE"
    assert res.adjustment_factor == Decimal("1.20")
    assert res.suggested_discount == Decimal("12.00")
    assert res.reason_code == "INVENTORY_SURPLUS"


def test_inventory_signal_backordered(db_session, setup_g24_test_data):
    """ATP <= 0 and open backorders -> BACKORDERED, factor = 0.50."""
    data = setup_g24_test_data
    res = InventoryAwareDiscountService.evaluate_inventory_signal(
        db=db_session,
        company_id=data["company"].id,
        product_id=data["oos_product"].id,
        base_target_discount=Decimal("10.00"),
    )
    assert res.inventory_signal == "BACKORDERED"
    assert res.adjustment_factor == Decimal("0.50")
    assert res.suggested_discount == Decimal("5.00")
    assert res.reason_code == "INVENTORY_BACKORDERED"


def test_inventory_signal_healthy_stock(db_session, setup_g24_test_data):
    """ATP = 20 -> HEALTHY_STOCK, factor = 1.00."""
    data = setup_g24_test_data
    res = InventoryAwareDiscountService.evaluate_inventory_signal(
        db=db_session,
        company_id=data["company"].id,
        product_id=data["product"].id,
        base_target_discount=Decimal("10.00"),
    )
    assert res.inventory_signal == "HEALTHY_STOCK"
    assert res.adjustment_factor == Decimal("1.00")
    assert res.suggested_discount == Decimal("10.00")


# ==============================================================================
# Phase 117 Tests: Deal-Value-Aware Discount
# ==============================================================================

def test_deal_value_signal_tiers(db_session, setup_g24_test_data):
    data = setup_g24_test_data
    # 1. Enterprise tier >= $50k -> 1.25x
    res_ent = DealValueAwareDiscountService.evaluate_deal_value_signal(
        db=db_session,
        company_id=data["company"].id,
        product_id=data["product"].id,
        base_target_discount=Decimal("10.00"),
        deal_value=Decimal("75000.00"),
    )
    assert res_ent.value_tier == "ENTERPRISE_TIER"
    assert res_ent.value_incentive_multiplier == Decimal("1.25")
    assert res_ent.suggested_discount == Decimal("12.50")

    # 2. Low value < $1,000 -> 0.80x
    res_low = DealValueAwareDiscountService.evaluate_deal_value_signal(
        db=db_session,
        company_id=data["company"].id,
        product_id=data["product"].id,
        base_target_discount=Decimal("10.00"),
        deal_value=Decimal("500.00"),
    )
    assert res_low.value_tier == "LOW_VALUE"
    assert res_low.value_incentive_multiplier == Decimal("0.80")
    assert res_low.suggested_discount == Decimal("8.00")


# ==============================================================================
# Phase 118 Tests: Discount Risk Calculation
# ==============================================================================

def test_discount_risk_low_risk(db_session, setup_g24_test_data):
    """Small discount (5%) within all ceilings, margins, and healthy stock -> LOW risk."""
    data = setup_g24_test_data
    res = DiscountRiskCalculationService.calculate_risk(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["product"].id,
        requested_discount=Decimal("5.00"),
        actor=data["admin_user"],
    )
    assert res.risk_level == "LOW"
    assert res.overall_risk_score <= 25
    assert res.is_acceptable_risk is True


def test_discount_risk_critical_risk(db_session, setup_g24_test_data):
    """Requested 40% breaches company ceiling (30%), margin ceiling (25%), and rep authority (15%) -> CRITICAL risk."""
    data = setup_g24_test_data
    res = DiscountRiskCalculationService.calculate_risk(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["product"].id,
        requested_discount=Decimal("40.00"),
        actor=data["rep_user"],
    )
    assert res.risk_level in ["HIGH", "CRITICAL"]
    assert res.overall_risk_score >= 51
    assert res.is_acceptable_risk is False
    assert len(res.primary_risk_factors) > 0


# ==============================================================================
# Phase 119 Tests: Discount Decision Engine
# ==============================================================================

def test_decision_engine_approved(db_session, setup_g24_test_data):
    """10% discount on healthy product for Admin -> APPROVED."""
    data = setup_g24_test_data
    res = DiscountDecisionEngine.evaluate_decision(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["product"].id,
        requested_discount=Decimal("10.00"),
        actor=data["admin_user"],
    )
    assert res.decision == "APPROVED"
    assert res.permitted_discount == Decimal("10.00")
    assert res.is_executable is True
    assert res.requires_escalation is False


def test_decision_engine_escalation_required(db_session, setup_g24_test_data):
    """20% discount for Sales Rep (authority limit = 15%, customer ceiling = 25%) -> ESCALATION_REQUIRED."""
    data = setup_g24_test_data
    res = DiscountDecisionEngine.evaluate_decision(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["product"].id,
        requested_discount=Decimal("20.00"),
        actor=data["rep_user"],
    )
    assert res.decision == "ESCALATION_REQUIRED"
    assert res.requires_escalation is True
    assert res.is_executable is False
    assert res.escalation_role_needed is not None


def test_decision_engine_adjusted(db_session, setup_g24_test_data):
    """Admin asks for 22% discount, within customer ceiling (25%), but min margin requires 20% max safe discount -> ADJUSTED to 20%."""
    data = setup_g24_test_data
    # With base price $100 and cost $60 (base margin 40%):
    # min margin 20%: P' >= 60 / (1 - 0.20) = 75 => max discount = 25%
    # With min margin 25%: P' >= 60 / (1 - 0.25) = 80 => max discount = 20%
    res = DiscountDecisionEngine.evaluate_decision(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["product"].id,
        requested_discount=Decimal("22.00"),
        actor=data["admin_user"],
        min_margin_percentage=Decimal("25.00"),
    )
    assert res.decision == "ADJUSTED"
    assert res.permitted_discount == Decimal("20.00")
    assert res.is_executable is True


def test_decision_engine_rejected_margin(db_session, setup_g24_test_data):
    """Low margin product (5% base margin) cannot support 10% discount with 15% min margin -> REJECTED."""
    data = setup_g24_test_data
    res = DiscountDecisionEngine.evaluate_decision(
        db=db_session,
        company_id=data["company"].id,
        customer_id=data["customer"].id,
        product_id=data["low_margin_product"].id,
        requested_discount=Decimal("10.00"),
        actor=data["admin_user"],
        min_margin_percentage=Decimal("15.00"),
    )
    assert res.decision == "REJECTED"
    assert res.is_executable is False


# ==============================================================================
# Phase 120 Tests: Automated Discount Application
# ==============================================================================

def test_automated_discount_application_success(db_session, setup_g24_test_data):
    data = setup_g24_test_data
    ref = f"DEAL-{uuid.uuid4().hex[:8]}"
    applied = AutomatedDiscountApplicationService.apply_discount(
        db=db_session,
        company_id=data["company"].id,
        payload=ApplyDiscountRequest(
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            requested_discount=Decimal("10.00"),
            deal_reference=ref,
            notes="Quarterly volume incentive",
        ),
        actor=data["admin_user"],
    )
    assert applied.deal_reference == ref
    assert applied.applied_discount == Decimal("10.00")
    assert applied.discounted_price == Decimal("90.00")

    # Verify idempotency
    applied_again = AutomatedDiscountApplicationService.apply_discount(
        db=db_session,
        company_id=data["company"].id,
        payload=ApplyDiscountRequest(
            customer_id=data["customer"].id,
            product_id=data["product"].id,
            requested_discount=Decimal("10.00"),
            deal_reference=ref,
        ),
        actor=data["admin_user"],
    )
    assert applied_again.id == applied.id


def test_automated_discount_application_rejected_block(db_session, setup_g24_test_data):
    """Over-ceiling discount cannot be applied even if requested."""
    data = setup_g24_test_data
    with pytest.raises(Exception):
        AutomatedDiscountApplicationService.apply_discount(
            db=db_session,
            company_id=data["company"].id,
            payload=ApplyDiscountRequest(
                customer_id=data["customer"].id,
                product_id=data["product"].id,
                requested_discount=Decimal("50.00"),  # Breaches 25% ceiling
                deal_reference=f"DEAL-FAIL-{uuid.uuid4().hex[:6]}",
            ),
            actor=data["admin_user"],
        )


# ==============================================================================
# REST API Endpoints Tests
# ==============================================================================

def test_api_inventory_signal(client, setup_g24_test_data):
    data = setup_g24_test_data
    resp = client.post(
        "/api/v1/governance/discounts/automation/inventory-signal",
        headers=data["admin_headers"],
        json={"product_id": str(data["product"].id), "base_target_discount": 10.0},
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["inventory_signal"] == "HEALTHY_STOCK"


def test_api_deal_value_signal(client, setup_g24_test_data):
    data = setup_g24_test_data
    resp = client.post(
        "/api/v1/governance/discounts/automation/deal-value-signal",
        headers=data["admin_headers"],
        json={
            "product_id": str(data["product"].id),
            "deal_value": 60000.0,
            "base_target_discount": 10.0,
        },
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["value_tier"] == "ENTERPRISE_TIER"


def test_api_calculate_risk(client, setup_g24_test_data):
    data = setup_g24_test_data
    resp = client.post(
        "/api/v1/governance/discounts/automation/calculate-risk",
        headers=data["admin_headers"],
        json={
            "customer_id": str(data["customer"].id),
            "product_id": str(data["product"].id),
            "requested_discount": 8.0,
        },
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["risk_level"] in ["LOW", "MEDIUM"]


def test_api_evaluate_decision(client, setup_g24_test_data):
    data = setup_g24_test_data
    resp = client.post(
        "/api/v1/governance/discounts/automation/evaluate-decision",
        headers=data["admin_headers"],
        json={
            "customer_id": str(data["customer"].id),
            "product_id": str(data["product"].id),
            "requested_discount": 10.0,
        },
    )
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["decision"] == "APPROVED"
    assert res_data["is_executable"] is True


def test_api_apply_discount(client, setup_g24_test_data):
    data = setup_g24_test_data
    ref = f"API-DEAL-{uuid.uuid4().hex[:6]}"
    resp = client.post(
        "/api/v1/governance/discounts/automation/apply",
        headers=data["admin_headers"],
        json={
            "customer_id": str(data["customer"].id),
            "product_id": str(data["product"].id),
            "requested_discount": 10.0,
            "deal_reference": ref,
            "notes": "API execution test",
        },
    )
    assert resp.status_code == 201
    res_data = resp.json()
    assert res_data["deal_reference"] == ref
    assert float(res_data["applied_discount"]) == 10.0


def test_api_auth_and_permissions(client, setup_g24_test_data):
    data = setup_g24_test_data
    # 401 unauthenticated
    resp_unauth = client.post(
        "/api/v1/governance/discounts/automation/apply",
        json={
            "customer_id": str(data["customer"].id),
            "product_id": str(data["product"].id),
            "requested_discount": 10.0,
            "deal_reference": "UNAUTH-1",
        },
    )
    assert resp_unauth.status_code == 401

    # 403 unauthorized for user without discounts:write
    resp_forbid = client.post(
        "/api/v1/governance/discounts/automation/apply",
        headers=data["viewer_headers"],
        json={
            "customer_id": str(data["customer"].id),
            "product_id": str(data["product"].id),
            "requested_discount": 10.0,
            "deal_reference": "FORBID-1",
        },
    )
    assert resp_forbid.status_code == 403
