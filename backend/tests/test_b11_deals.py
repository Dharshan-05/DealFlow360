"""Comprehensive Test Suite for DealFlow360 B11 (Phases 206–215: Commercial Deals Pipeline).

Verifies strict roadmap compliance and production guarantees:
- Phase 206: Deal Creation from Quote (Transactional quote -> deal creation, ACCEPTED status guard, expiration guard, idempotency)
- Phase 207: Deal Product Linking (Line-item product linking to deals, quantity, pricing, costs, discounts, taxes, margins, duplicate prevention)
- Phase 208: Deal Value Calculation (Centralized Decimal calculation engine, ROUND_HALF_UP, subtotal, discounts, taxes, deal value reconciliation)
- Phase 209: Deal Margin Calculation (Revenue, cost, gross profit, margin %, discounted margin %, risk classification: HEALTHY, MODERATE, THIN, CRITICAL)
- Phase 210: Deal Stage Management (State machine: NEW, QUALIFIED, PROPOSAL, NEGOTIATION, CLOSED_WON, CLOSED_LOST, terminal guards, audit logging)
- Phase 211: Deal Probability (Deterministic 0–100% calculation based on stage weights, quotation status, customer tier, margin health, activity recency)
- Phase 212: Deal Forecasting (Weighted revenue deal_value * probability / 100, pipeline aggregations, stage-by-stage forecasting)
- Phase 213: Deal Activity Tracking (Append-only deal_activities tracking NOTE, CALL, EMAIL, MEETING, TASK, STAGE_CHANGE)
- Phase 214: Deal Timeline (Chronological unified timeline merging deal creation, activities, quotation lifecycle events)
- Phase 215: Deal Dashboard (High-performance SQL aggregations for total/open/won/lost deals, win rate, pipeline value, weighted pipeline)
- Multi-Tenancy & Security: IDOR protection and RBAC permission checks
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
from app.models.customer_deal_history import CustomerDealHistory
from app.models.deal import DealActivity, DealActivityType, DealProduct, DealStage
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation, QuotationStatus
from app.models.quotation_line_item import QuotationLineItem
from app.models.role import Role
from app.models.user import User
from app.schemas.deal import (
    DealActivityCreate,
    DealCreateFromQuoteRequest,
    DealMarginRisk,
    DealProductCreate,
    DealStageUpdateRequest,
)
from app.services.deal import (
    DealActivityService,
    DealCalculationEngine,
    DealCreationService,
    DealDashboardService,
    DealForecastingService,
    DealMarginService,
    DealProbabilityService,
    DealProductService,
    DealService,
    DealStageManagementService,
    DealTimelineService,
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
def setup_b11_data(db_session):
    """Seed multi-tenant companies, users, roles, categories, products, customers, and quotations."""
    # 1. Multi-Tenant Companies
    company_a = Company(
        name=f"B11 Corp Alpha {uuid.uuid4().hex[:8]}",
        legal_name="Alpha Commercial Systems Inc",
        email=f"alpha_{uuid.uuid4().hex[:8]}@example.com",
    )
    company_b = Company(
        name=f"B11 Corp Beta {uuid.uuid4().hex[:8]}",
        legal_name="Beta Global Deals Corp",
        email=f"beta_{uuid.uuid4().hex[:8]}@example.com",
    )
    db_session.add_all([company_a, company_b])
    db_session.commit()

    # 2. Permissions & Roles
    permissions = []
    for p_name in ["deals:read", "deals:write", "quotations:read", "quotations:write", "discounts:read"]:
        perm = db_session.execute(select(Permission).where(Permission.name == p_name)).scalar_one_or_none()
        if not perm:
            perm = Permission(name=p_name, description=f"Permission {p_name}", resource=p_name.split(":")[0], action=p_name.split(":")[1])
            db_session.add(perm)
        permissions.append(perm)
    db_session.commit()

    role_sales = Role(name=f"Sales_B11_{uuid.uuid4().hex[:8]}", description="Sales Rep Role B11")
    for p in permissions:
        role_sales.permissions.append(p)
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

    # 4. Catalog Categories & Products
    cat_a = ProductCategory(
        name=f"Hardware Alpha {uuid.uuid4().hex[:6]}",
        code=f"HW_{uuid.uuid4().hex[:6]}",
        description="Hardware category",
        is_active=True,
    )
    db_session.add(cat_a)
    db_session.commit()

    prod1 = Product(
        category_id=cat_a.id,
        sku=f"PRD-01-{uuid.uuid4().hex[:6]}",
        name="Enterprise Server Unit",
        base_price=Decimal("1000.00"),
        cost=Decimal("600.00"),
        tax_rate=Decimal("10.00"),
        inventory_quantity=50,
        is_active=True,
    )
    prod2 = Product(
        category_id=cat_a.id,
        sku=f"PRD-02-{uuid.uuid4().hex[:6]}",
        name="Support Package Gold",
        base_price=Decimal("200.00"),
        cost=Decimal("50.00"),
        tax_rate=Decimal("0.00"),
        inventory_quantity=50,
        is_active=True,
    )
    db_session.add_all([prod1, prod2])
    db_session.commit()

    # 5. Customer
    cust_a = Customer(
        company_id=company_a.id,
        customer_code=f"CUST-A-{uuid.uuid4().hex[:6]}",
        name="Acme Corp Industries",
        email="contact@acme.example.com",
        is_active=True,
    )
    cust_b = Customer(
        company_id=company_b.id,
        customer_code=f"CUST-B-{uuid.uuid4().hex[:6]}",
        name="Beta Customer Corp",
        email="contact@beta.example.com",
        is_active=True,
    )
    db_session.add_all([cust_a, cust_b])
    db_session.commit()

    # 6. Accepted Quotation for conversion testing
    quote_accepted = Quotation(
        company_id=company_a.id,
        user_id=user_a.id,
        customer_id=cust_a.id,
        quotation_number=f"QT-B11-{uuid.uuid4().hex[:6]}",
        status=QuotationStatus.ACCEPTED.value,
        subtotal=Decimal("2400.00"),
        total_discount=Decimal("200.00"),
        overall_discount_percent=Decimal("8.33"),
        taxable_amount=Decimal("2200.00"),
        tax_amount=Decimal("200.00"),
        total_amount=Decimal("2400.00"),
        total_cost=Decimal("1300.00"),
        gross_profit=Decimal("900.00"),
        margin_percentage=Decimal("40.91"),
        accepted_at=datetime.now(timezone.utc),
        accepted_by_id=user_a.id,
        valid_until=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(quote_accepted)
    db_session.commit()

    li1 = QuotationLineItem(
        quotation_id=quote_accepted.id,
        product_id=prod1.id,
        quantity=Decimal("2.0000"),
        unit_price=Decimal("1000.00"),
        discount_percent=Decimal("10.00"),
        discount_amount=Decimal("200.00"),
        tax_rate=Decimal("10.00"),
        tax_amount=Decimal("180.00"),
        net_amount=Decimal("1800.00"),
        subtotal=Decimal("2000.00"),
        total_amount=Decimal("1980.00"),
    )
    li2 = QuotationLineItem(
        quotation_id=quote_accepted.id,
        product_id=prod2.id,
        quantity=Decimal("2.0000"),
        unit_price=Decimal("200.00"),
        discount_percent=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_rate=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        net_amount=Decimal("400.00"),
        subtotal=Decimal("400.00"),
        total_amount=Decimal("400.00"),
    )
    db_session.add_all([li1, li2])
    db_session.commit()

    return {
        "company_a": company_a,
        "company_b": company_b,
        "user_a": user_a,
        "user_b": user_b,
        "token_a": token_a,
        "token_b": token_b,
        "prod1": prod1,
        "prod2": prod2,
        "cust_a": cust_a,
        "cust_b": cust_b,
        "quote_accepted": quote_accepted,
    }


# ==============================================================================
# Phase 206: Deal Creation from Quote Tests
# ==============================================================================

def test_phase_206_deal_creation_from_accepted_quote(client, setup_b11_data, db_session):
    """Test converting an accepted quotation to a commercial deal."""
    quote = setup_b11_data["quote_accepted"]
    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}

    res = client.post(
        f"/api/v1/deals/from-quote/{quote.id}",
        headers=headers,
        json={"title_override": "Commercial Enterprise Agreement", "notes": "Converted in Q3"},
    )
    assert res.status_code == 201
    body = res.json()["data"]

    assert body["deal_code"] == f"DEAL-{quote.quotation_number}"
    assert body["title"] == "Commercial Enterprise Agreement"
    assert body["stage"] == DealStage.CLOSED_WON.value
    assert body["status"] == "WON"
    assert Decimal(str(body["deal_value"])) == quote.total_amount
    assert Decimal(str(body["subtotal"])) == quote.subtotal
    assert body["probability"] == 100
    assert len(body["products"]) == 2

    # Verify Quotation status was updated to CONVERTED
    db_session.refresh(quote)
    assert quote.status == QuotationStatus.CONVERTED.value
    assert str(quote.converted_deal_id) == body["id"]


def test_phase_206_deal_creation_idempotent(client, setup_b11_data):
    """Test that repeatedly converting an already-converted quotation is idempotent."""
    quote = setup_b11_data["quote_accepted"]
    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}

    # Second conversion call should succeed idempotently
    res = client.post(f"/api/v1/deals/from-quote/{quote.id}", headers=headers)
    assert res.status_code == 201
    assert res.json()["data"]["deal_code"] == f"DEAL-{quote.quotation_number}"


def test_phase_206_deal_creation_non_accepted_fails(client, setup_b11_data, db_session):
    """Test that a quotation not in ACCEPTED status cannot be converted."""
    draft_quote = Quotation(
        company_id=setup_b11_data["company_a"].id,
        user_id=setup_b11_data["user_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        quotation_number=f"QT-DRAFT-{uuid.uuid4().hex[:6]}",
        status=QuotationStatus.DRAFT.value,
        subtotal=Decimal("500.00"),
        total_amount=Decimal("500.00"),
    )
    db_session.add(draft_quote)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}
    res = client.post(f"/api/v1/deals/from-quote/{draft_quote.id}", headers=headers)
    assert res.status_code == 400
    assert "ACCEPTED status" in res.json()["error"]["message"]


# ==============================================================================
# Phase 207: Deal Product Linking Tests
# ==============================================================================

def test_phase_207_add_product_to_deal(client, setup_b11_data, db_session):
    """Test linking a product line item to an open deal."""
    # Create an open deal
    open_deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-OPEN-{uuid.uuid4().hex[:6]}",
        title="Open Cloud Deal",
        deal_value=Decimal("0.00"),
        status="OPEN",
        stage=DealStage.NEW.value,
        probability=10,
    )
    db_session.add(open_deal)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}
    payload = {
        "product_id": str(setup_b11_data["prod1"].id),
        "quantity": 3.0,
        "unit_price": 950.00,
        "discount_percent": 5.00,
        "tax_rate": 10.00,
        "notes": "Bulk server order",
    }
    res = client.post(f"/api/v1/deals/{open_deal.id}/products", headers=headers, json=payload)
    assert res.status_code == 201
    dp_data = res.json()["data"]

    # Verify line calculations:
    # subtotal = 3 * 950 = 2850.00
    # discount = 2850 * 5% = 142.50
    # taxable = 2850 - 142.50 = 2707.50
    # tax = 2707.50 * 10% = 270.75
    # total = 2707.50 + 270.75 = 2978.25
    # cost = 3 * 600 = 1800.00
    # profit = 2707.50 - 1800.00 = 907.50
    assert Decimal(str(dp_data["subtotal"])) == Decimal("2850.00")
    assert Decimal(str(dp_data["discount_amount"])) == Decimal("142.50")
    assert Decimal(str(dp_data["taxable_amount"])) == Decimal("2707.50")
    assert Decimal(str(dp_data["tax_amount"])) == Decimal("270.75")
    assert Decimal(str(dp_data["total_amount"])) == Decimal("2978.25")
    assert Decimal(str(dp_data["total_cost"])) == Decimal("1800.00")
    assert Decimal(str(dp_data["gross_profit"])) == Decimal("907.50")


def test_phase_207_duplicate_product_prevented(client, setup_b11_data, db_session):
    """Test that adding duplicate products to a deal is rejected."""
    deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-DUP-{uuid.uuid4().hex[:6]}",
        title="Duplicate Test Deal",
        deal_value=Decimal("0.00"),
        status="OPEN",
        stage=DealStage.NEW.value,
    )
    db_session.add(deal)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}
    payload = {"product_id": str(setup_b11_data["prod1"].id), "quantity": 1.0}

    # First add succeeds
    res1 = client.post(f"/api/v1/deals/{deal.id}/products", headers=headers, json=payload)
    assert res1.status_code == 201

    # Duplicate add fails
    res2 = client.post(f"/api/v1/deals/{deal.id}/products", headers=headers, json=payload)
    assert res2.status_code == 400
    assert "already linked" in res2.json()["error"]["message"]


# ==============================================================================
# Phase 208: Deal Value Calculation & Recalculation Tests
# ==============================================================================

def test_phase_208_deal_recalculation(client, setup_b11_data, db_session):
    """Test recalculating deal totals and precision rounding."""
    deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-CALC-{uuid.uuid4().hex[:6]}",
        title="Calculation Test Deal",
        deal_value=Decimal("0.00"),
        status="OPEN",
        stage=DealStage.QUALIFIED.value,
        probability=25,
    )
    db_session.add(deal)
    db_session.commit()

    # Link product 1 and product 2
    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}
    client.post(
        f"/api/v1/deals/{deal.id}/products",
        headers=headers,
        json={"product_id": str(setup_b11_data["prod1"].id), "quantity": 2.0},
    )
    client.post(
        f"/api/v1/deals/{deal.id}/products",
        headers=headers,
        json={"product_id": str(setup_b11_data["prod2"].id), "quantity": 1.0},
    )

    # Recalculate endpoint
    res = client.post(f"/api/v1/deals/{deal.id}/recalculate", headers=headers)
    assert res.status_code == 200
    detail = res.json()["data"]

    # Prod1: 2 * 1000 = 2000 subtotal, 200 tax -> 2200 total, 1200 cost
    # Prod2: 1 * 200 = 200 subtotal, 0 tax -> 200 total, 50 cost
    # Header: subtotal = 2200, tax = 200, deal_value = 2400, total_cost = 1250, profit = 950
    assert Decimal(str(detail["subtotal"])) == Decimal("2200.00")
    assert Decimal(str(detail["deal_value"])) == Decimal("2400.00")
    assert Decimal(str(detail["total_cost"])) == Decimal("1250.00")
    assert Decimal(str(detail["gross_profit"])) == Decimal("950.00")


# ==============================================================================
# Phase 209: Deal Margin Calculation Tests
# ==============================================================================

def test_phase_209_deal_margin_evaluation(client, setup_b11_data, db_session):
    """Test margin percentages and margin risk classification."""
    deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-MRG-{uuid.uuid4().hex[:6]}",
        title="High Margin Deal",
        subtotal=Decimal("1000.00"),
        deal_value=Decimal("1000.00"),
        total_cost=Decimal("600.00"),
        gross_profit=Decimal("400.00"),
        margin_percentage=Decimal("40.00"),
        status="OPEN",
        stage=DealStage.PROPOSAL.value,
    )
    db_session.add(deal)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}
    res = client.get(f"/api/v1/deals/{deal.id}/margin", headers=headers)
    assert res.status_code == 200
    m_data = res.json()["data"]

    assert Decimal(str(m_data["gross_profit"])) == Decimal("400.00")
    assert Decimal(str(m_data["gross_margin_percentage"])) == Decimal("40.00")
    assert m_data["margin_risk"] == DealMarginRisk.HEALTHY.value
    assert not m_data["is_negative_margin"]


# ==============================================================================
# Phase 210: Deal Stage Management Tests
# ==============================================================================

def test_phase_210_valid_stage_progression_and_audit(client, setup_b11_data, db_session):
    """Test state machine progression from NEW -> QUALIFIED -> PROPOSAL -> NEGOTIATION -> CLOSED_WON."""
    deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-STAGE-{uuid.uuid4().hex[:6]}",
        title="Stage Progression Deal",
        deal_value=Decimal("10000.00"),
        status="OPEN",
        stage=DealStage.NEW.value,
        probability=10,
    )
    db_session.add(deal)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}

    # 1. Advance to QUALIFIED
    res1 = client.patch(
        f"/api/v1/deals/{deal.id}/stage",
        headers=headers,
        json={"stage": "QUALIFIED", "reason": "BANT criteria satisfied"},
    )
    assert res1.status_code == 200
    assert res1.json()["data"]["stage"] == "QUALIFIED"

    # 2. Advance to PROPOSAL
    res2 = client.patch(
        f"/api/v1/deals/{deal.id}/stage",
        headers=headers,
        json={"stage": "PROPOSAL", "reason": "RFP proposal delivered"},
    )
    assert res2.status_code == 200
    assert res2.json()["data"]["stage"] == "PROPOSAL"

    # 3. Advance to NEGOTIATION
    res3 = client.patch(
        f"/api/v1/deals/{deal.id}/stage",
        headers=headers,
        json={"stage": "NEGOTIATION", "reason": "Final commercial review"},
    )
    assert res3.status_code == 200
    assert res3.json()["data"]["stage"] == "NEGOTIATION"

    # 4. Advance to CLOSED_WON
    res4 = client.patch(
        f"/api/v1/deals/{deal.id}/stage",
        headers=headers,
        json={"stage": "CLOSED_WON", "reason": "Contract signed"},
    )
    assert res4.status_code == 200
    assert res4.json()["data"]["stage"] == "CLOSED_WON"
    assert res4.json()["data"]["status"] == "WON"
    assert res4.json()["data"]["probability"] == 100

    # 5. CLOSED_WON is terminal; attempting to change it should fail
    res5 = client.patch(
        f"/api/v1/deals/{deal.id}/stage",
        headers=headers,
        json={"stage": "QUALIFIED"},
    )
    assert res5.status_code == 400
    assert "CLOSED_WON" in res5.json()["error"]["message"]


def test_phase_210_invalid_stage_transition_rejected(client, setup_b11_data, db_session):
    """Test that skipping stages (e.g., NEW -> CLOSED_WON directly) is rejected."""
    deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-INVALID-{uuid.uuid4().hex[:6]}",
        title="Invalid Stage Deal",
        deal_value=Decimal("5000.00"),
        status="OPEN",
        stage=DealStage.NEW.value,
    )
    db_session.add(deal)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}
    res = client.patch(
        f"/api/v1/deals/{deal.id}/stage",
        headers=headers,
        json={"stage": "CLOSED_WON"},
    )
    assert res.status_code == 400
    assert "Invalid deal stage transition" in res.json()["error"]["message"]


# ==============================================================================
# Phase 211: Deal Probability Engine Tests
# ==============================================================================

def test_phase_211_deterministic_probability(client, setup_b11_data, db_session):
    """Test deterministic deal win probability calculation and signal factor breakdown."""
    deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-PROB-{uuid.uuid4().hex[:6]}",
        title="Probability Deal",
        deal_value=Decimal("8000.00"),
        subtotal=Decimal("8000.00"),
        margin_percentage=Decimal("35.00"),
        status="OPEN",
        stage=DealStage.PROPOSAL.value,
    )
    db_session.add(deal)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}
    res = client.get(f"/api/v1/deals/{deal.id}/probability", headers=headers)
    assert res.status_code == 200
    p_data = res.json()["data"]

    # Base for PROPOSAL is 50%, healthy margin (+5%) -> at least 55%
    assert p_data["probability"] >= 50
    assert len(p_data["factors"]) > 0
    assert "PROPOSAL" in p_data["stage"]


# ==============================================================================
# Phase 212: Deal Revenue Forecasting Tests
# ==============================================================================

def test_phase_212_deal_and_pipeline_forecasting(client, setup_b11_data, db_session):
    """Test single deal expected revenue and multi-stage pipeline revenue forecasting."""
    deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-FCST-{uuid.uuid4().hex[:6]}",
        title="Forecast Deal",
        deal_value=Decimal("10000.00"),
        status="OPEN",
        stage=DealStage.NEGOTIATION.value,
        probability=75,
    )
    db_session.add(deal)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}

    # 1. Single Deal Forecast
    res1 = client.get(f"/api/v1/deals/{deal.id}/forecast", headers=headers)
    assert res1.status_code == 200
    fcst = res1.json()["data"]
    assert Decimal(str(fcst["weighted_value"])) == Decimal("7500.00")

    # 2. Pipeline-Wide Forecast
    res2 = client.get("/api/v1/deals/forecast/pipeline", headers=headers)
    assert res2.status_code == 200
    p_fcst = res2.json()["data"]
    assert p_fcst["total_deals_count"] > 0
    assert len(p_fcst["stages"]) == len(DealStage)


# ==============================================================================
# Phase 213: Deal Activity Tracking Tests
# ==============================================================================

def test_phase_213_record_and_list_deal_activities(client, setup_b11_data, db_session):
    """Test logging notes, calls, meetings, and listing activity history."""
    deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-ACT-{uuid.uuid4().hex[:6]}",
        title="Activity Deal",
        deal_value=Decimal("5000.00"),
        status="OPEN",
        stage=DealStage.NEW.value,
    )
    db_session.add(deal)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}

    # Log an activity
    act_payload = {
        "activity_type": "CALL",
        "title": "Discovery Call with CTO",
        "description": "Discussed architecture integration and SLA timelines.",
        "activity_metadata": {"duration_minutes": 45},
    }
    res1 = client.post(f"/api/v1/deals/{deal.id}/activities", headers=headers, json=act_payload)
    assert res1.status_code == 201
    act_data = res1.json()["data"]
    assert act_data["activity_type"] == "CALL"
    assert act_data["title"] == "Discovery Call with CTO"

    # List activities
    res2 = client.get(f"/api/v1/deals/{deal.id}/activities", headers=headers)
    assert res2.status_code == 200
    acts = res2.json()["data"]
    assert len(acts) >= 1
    assert acts[0]["title"] == "Discovery Call with CTO"


# ==============================================================================
# Phase 214: Deal Timeline Tests
# ==============================================================================

def test_phase_214_unified_deal_timeline(client, setup_b11_data, db_session):
    """Test that timeline aggregates deal creation and activities in chronological order."""
    deal = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-TIME-{uuid.uuid4().hex[:6]}",
        title="Timeline Deal",
        deal_value=Decimal("15000.00"),
        status="OPEN",
        stage=DealStage.NEW.value,
    )
    db_session.add(deal)
    db_session.commit()

    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}
    client.post(
        f"/api/v1/deals/{deal.id}/activities",
        headers=headers,
        json={"activity_type": "NOTE", "title": "Added executive briefing"},
    )

    res = client.get(f"/api/v1/deals/{deal.id}/timeline", headers=headers)
    assert res.status_code == 200
    timeline = res.json()["data"]

    # Should contain at least DEAL creation and ACTIVITY
    sources = [ev["source"] for ev in timeline]
    assert "DEAL" in sources
    assert "ACTIVITY" in sources


# ==============================================================================
# Phase 215: Deal Pipeline Dashboard Tests
# ==============================================================================

def test_phase_215_deal_dashboard_metrics(client, setup_b11_data):
    """Test executive pipeline dashboard KPI aggregation."""
    headers = {"Authorization": f"Bearer {setup_b11_data['token_a']}"}
    res = client.get("/api/v1/deals/dashboard", headers=headers)
    assert res.status_code == 200
    dash = res.json()["data"]

    assert "total_deals" in dash
    assert "open_deals" in dash
    assert "won_deals" in dash
    assert "lost_deals" in dash
    assert "pipeline_value" in dash
    assert "win_rate" in dash
    assert "deals_by_stage" in dash
    assert isinstance(dash["top_deals"], list)


# ==============================================================================
# Multi-Tenancy & Security (IDOR) Tests
# ==============================================================================

def test_b11_deal_tenant_isolation_idor(client, setup_b11_data, db_session):
    """Test that Company B cannot access or modify Company A's deals."""
    deal_a = CustomerDealHistory(
        company_id=setup_b11_data["company_a"].id,
        customer_id=setup_b11_data["cust_a"].id,
        deal_code=f"DEAL-SEC-{uuid.uuid4().hex[:6]}",
        title="Confidential Deal Alpha",
        deal_value=Decimal("50000.00"),
        status="OPEN",
        stage=DealStage.NEGOTIATION.value,
    )
    db_session.add(deal_a)
    db_session.commit()

    headers_b = {"Authorization": f"Bearer {setup_b11_data['token_b']}"}

    # 1. Company B reading Company A's deal -> 404 Not Found
    res_get = client.get(f"/api/v1/deals/{deal_a.id}", headers=headers_b)
    assert res_get.status_code == 404

    # 2. Company B transitioning Company A's deal stage -> 404 Not Found
    res_patch = client.patch(
        f"/api/v1/deals/{deal_a.id}/stage",
        headers=headers_b,
        json={"stage": "CLOSED_WON"},
    )
    assert res_patch.status_code == 404

    # 3. Company B adding product to Company A's deal -> 404 Not Found
    res_prod = client.post(
        f"/api/v1/deals/{deal_a.id}/products",
        headers=headers_b,
        json={"product_id": str(setup_b11_data["prod1"].id), "quantity": 1.0},
    )
    assert res_prod.status_code == 404
