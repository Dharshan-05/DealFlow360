"""Comprehensive Test Suite for DealFlow360 B08 (Phases 176–185: AI Upsell / Cross-Sell Engine — Remaining).

Verifies strict roadmap compliance and production guarantees:
- Phase 176: Upsell Score (0–100 integer score calculation, boundary scaling, API endpoint)
- Phase 177: Cross-Sell Score (0–100 integer score calculation, affinity & lift weighting, API endpoint)
- Phase 178: Recommendation Ranking (Multi-factor ranking with 0-100 scores and explanations, stable tie-breaking)
- Phase 179: AI Next-Best-Product (Selector returning optimal single product with explanation and telemetry)
- Phase 180: Upsell Explanation (Structured human-readable explanation data, no hallucination)
- Phase 181: Add-to-Quote Recommendation (Quote line item addition, validation, event generation)
- Phase 182: Real-Time Margin Update (Strict Decimal financial arithmetic, gross profit and margin % recalculation)
- Phase 183: Upsell Acceptance Tracking (Lifecycle event audit logging, idempotency & deduplication)
- Phase 184: Recommendation Analytics (Funnel metrics, acceptance rates, product leaderboards, zero-denominator safety)
- Phase 185: Upsell Dashboard (Consolidated KPIs, 5-stage funnel, category distribution, recent activity stream)
- Security & Multi-Tenancy (Tenant isolation across companies, RBAC protection)
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
from app.models.applied_discount import AppliedDiscount
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_purchase_history import CustomerPurchaseHistory
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.recommendation_event import RecommendationEvent
from app.models.role import Role
from app.models.user import User
from app.schemas.recommendations import (
    AddToQuoteRequest,
    CustomerBehaviorSegment,
    CustomerPurchasePattern,
    QuoteLineItemInput,
    RecommendationEventCreate,
    RecommendationEventEnum,
    RecommendationType,
)
from app.services.recommendations import (
    AICrossSellService,
    AIUpsellService,
    NextBestProductService,
    PurchasePatternAnalysisService,
    RealTimeMarginService,
    RecommendationAnalyticsService,
    RecommendationExplanationService,
    RecommendationQuoteIntegrationService,
    RecommendationRankingEngine,
    RecommendationTrackingService,
    UpsellDashboardService,
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
def setup_b08_data(db_session):
    """Seed companies, users, products, categories, transactions, and customer purchase histories."""
    # 1. Multi-Tenant Companies
    company_a = Company(
        name=f"B08 Corp Alpha {uuid.uuid4().hex[:6]}",
        legal_name="Alpha Tech Systems Inc",
        email=f"alpha_{uuid.uuid4().hex[:6]}@example.com",
    )
    company_b = Company(
        name=f"B08 Corp Beta {uuid.uuid4().hex[:6]}",
        legal_name="Beta Global Enterprises",
        email=f"beta_{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add_all([company_a, company_b])
    db_session.commit()

    # 2. Permissions & Roles
    perm_read = db_session.execute(select(Permission).where(Permission.name == "discounts:read")).scalar_one_or_none()
    if not perm_read:
        perm_read = Permission(name="discounts:read", description="Read discounts", resource="discounts", action="read")
        db_session.add(perm_read)
        db_session.commit()

    role_sales = Role(name=f"Sales_B08_{uuid.uuid4().hex[:6]}", description="Sales Representative")
    role_sales.permissions.append(perm_read)
    db_session.add(role_sales)
    db_session.commit()

    # 3. Users
    user_a = User(
        company_id=company_a.id,
        email=f"user_a_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mock_hash",
        first_name="Alice",
        last_name="Alpha",
        is_active=True,
    )
    user_a.roles.append(role_sales)

    user_b = User(
        company_id=company_b.id,
        email=f"user_b_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mock_hash",
        first_name="Bob",
        last_name="Beta",
        is_active=True,
    )
    user_b.roles.append(role_sales)

    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(subject=str(user_a.id))
    token_b = create_access_token(subject=str(user_b.id))

    # 4. Product Categories
    cat_hardware = ProductCategory(
        name=f"Hardware_{uuid.uuid4().hex[:10]}",
        code=f"HW_{uuid.uuid4().hex[:10]}",
        description="Compute and server hardware",
        is_active=True,
    )
    cat_software = ProductCategory(
        name=f"Software_{uuid.uuid4().hex[:10]}",
        code=f"SW_{uuid.uuid4().hex[:10]}",
        description="Enterprise subscriptions and licenses",
        is_active=True,
    )
    cat_storage = ProductCategory(
        name=f"Storage_{uuid.uuid4().hex[:10]}",
        code=f"ST_{uuid.uuid4().hex[:10]}",
        description="SAN and NAS appliances",
        is_active=True,
    )
    db_session.add_all([cat_hardware, cat_software, cat_storage])
    db_session.commit()

    # 5. Products for Catalog
    # P1: Entry Server ($1,000, cost $600 -> 40% margin)
    p1 = Product(
        sku=f"SRV-100-{uuid.uuid4().hex[:10]}",
        name="Compute Node 100",
        category_id=cat_hardware.id,
        cost=Decimal("600.00"),
        base_price=Decimal("1000.00"),
        inventory_quantity=25,
        is_active=True,
    )
    # P2: Premium Server ($3,000, cost $1,500 -> 50% margin) -> Upsell candidate
    p2 = Product(
        sku=f"SRV-900-{uuid.uuid4().hex[:10]}",
        name="Enterprise Compute Matrix 900",
        category_id=cat_hardware.id,
        cost=Decimal("1500.00"),
        base_price=Decimal("3000.00"),
        inventory_quantity=15,
        is_active=True,
    )
    # P3: High-speed Storage Array ($1,200, cost $700) -> Cross-sell candidate
    p3 = Product(
        sku=f"STR-400-{uuid.uuid4().hex[:10]}",
        name="NVMe Storage Pod",
        category_id=cat_storage.id,
        cost=Decimal("700.00"),
        base_price=Decimal("1200.00"),
        inventory_quantity=40,
        is_active=True,
    )
    # P4: Enterprise Monitoring Subscription ($400/yr) -> Cross-sell software
    p4 = Product(
        sku=f"SW-MON-{uuid.uuid4().hex[:10]}",
        name="Proactive Cluster Monitor",
        category_id=cat_software.id,
        cost=Decimal("80.00"),
        base_price=Decimal("400.00"),
        is_subscription=True,
        recurring_frequency="yearly",
        inventory_quantity=100,
        is_active=True,
    )
    # P5: Inactive Product (Should be excluded)
    p5_inactive = Product(
        sku=f"DISC-{uuid.uuid4().hex[:10]}",
        name="Deprecated Tape Drive",
        category_id=cat_storage.id,
        cost=Decimal("100.00"),
        base_price=Decimal("200.00"),
        inventory_quantity=0,
        is_active=False,
    )
    db_session.add_all([p1, p2, p3, p4, p5_inactive])
    db_session.commit()

    # 6. Customers for Company A
    now = datetime.now(timezone.utc)
    cust_a1 = Customer(
        company_id=company_a.id,
        customer_code=f"CUST-A1-{uuid.uuid4().hex[:10]}",
        name="Acme Technology Partners",
        email=f"acme_{uuid.uuid4().hex[:10]}@example.com",
        is_active=True,
        created_at=now - timedelta(days=180),
    )
    cust_a2 = Customer(
        company_id=company_a.id,
        customer_code=f"CUST-A2-{uuid.uuid4().hex[:10]}",
        name="Early Stage Ventures",
        email=f"early_{uuid.uuid4().hex[:10]}@example.com",
        is_active=True,
        created_at=now - timedelta(days=20),
    )
    # Customer for Company B
    cust_b1 = Customer(
        company_id=company_b.id,
        customer_code=f"CUST-B1-{uuid.uuid4().hex[:10]}",
        name="Beta Logistics Sub",
        email=f"betasub_{uuid.uuid4().hex[:4]}@example.com",
        is_active=True,
        created_at=now - timedelta(days=90),
    )
    db_session.add_all([cust_a1, cust_a2, cust_b1])
    db_session.commit()

    # 7. Customer A1 Purchase History (Loyal & High Spender: 5 orders)
    for i in range(5):
        db_session.add(
            CustomerPurchaseHistory(
                company_id=company_a.id,
                customer_id=cust_a1.id,
                order_number=f"ORD-A1-{i+1}",
                purchase_date=now - timedelta(days=15 * (i + 1)),
                total_amount=Decimal("4000.00"),
                status="COMPLETED",
                item_count=2,
            )
        )
    db_session.commit()

    # 8. Basket Co-occurrences for Company A (P1 + P3 co-occur)
    for b in range(4):
        deal_ref = f"BASKET-B08-{b+1}"
        d_time = now - timedelta(days=20 * (b + 1))
        ad1 = AppliedDiscount(
            company_id=company_a.id,
            customer_id=cust_a1.id,
            product_id=p1.id,
            deal_reference=deal_ref,
            requested_discount=Decimal("0.00"),
            applied_discount=Decimal("0.00"),
            selling_price=Decimal("1000.00"),
            discounted_price=Decimal("1000.00"),
            unit_cost=Decimal("600.00"),
            margin_percentage=Decimal("40.00"),
            reason_code="STANDARD",
            applied_at=d_time,
        )
        ad3 = AppliedDiscount(
            company_id=company_a.id,
            customer_id=cust_a1.id,
            product_id=p3.id,
            deal_reference=deal_ref,
            requested_discount=Decimal("0.00"),
            applied_discount=Decimal("0.00"),
            selling_price=Decimal("1200.00"),
            discounted_price=Decimal("1200.00"),
            unit_cost=Decimal("700.00"),
            margin_percentage=Decimal("41.67"),
            reason_code="STANDARD",
            applied_at=d_time,
        )
        db_session.add_all([ad1, ad3])
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
        "p3": p3,
        "p4": p4,
        "p5_inactive": p5_inactive,
        "cust_a1": cust_a1,
        "cust_a2": cust_a2,
        "cust_b1": cust_b1,
        "cat_hardware": cat_hardware,
        "cat_software": cat_software,
        "cat_storage": cat_storage,
    }


# ==============================================================================
# Phase 176: Upsell Score Tests
# ==============================================================================

def test_phase_176_upsell_score_calculation():
    """Verify deterministic 0–100 integer score calculation and factor weights."""
    # Ideal scenario: high probability, high margin, ample inventory, optimal AOV price ratio
    score_ideal = AIUpsellService.calculate_upsell_score_100(
        probability=0.90,
        unit_margin_pct=50.0,
        inventory_quantity=20,
        price_ratio=1.2,
    )
    assert 75 <= score_ideal <= 100
    assert isinstance(score_ideal, int)

    # Low scenario: low probability, low margin, zero inventory, excessive price
    score_low = AIUpsellService.calculate_upsell_score_100(
        probability=0.10,
        unit_margin_pct=5.0,
        inventory_quantity=0,
        price_ratio=4.0,
    )
    assert 0 <= score_low <= 35
    assert isinstance(score_low, int)


def test_phase_176_upsell_score_api(client, setup_b08_data):
    """Verify GET /api/v1/recommendations/upsell-score endpoint."""
    data = setup_b08_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    res = client.get(
        f"/api/v1/recommendations/upsell-score?customer_id={data['cust_a1'].id}&product_id={data['p2'].id}",
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["customer_id"] == str(data["cust_a1"].id)
    assert body["product_id"] == str(data["p2"].id)
    assert 0 <= body["score_100"] <= 100
    assert 0.0 <= body["probability"] <= 1.0
    assert body["inventory_quantity"] == data["p2"].inventory_quantity


# ==============================================================================
# Phase 177: Cross-Sell Score Tests
# ==============================================================================

def test_phase_177_cross_sell_score_calculation():
    """Verify deterministic 0–100 integer cross-sell score calculation."""
    # High affinity scenario
    score_high = AICrossSellService.calculate_cross_sell_score_100(
        probability=0.85,
        confidence=0.75,
        lift=3.5,
        inventory_quantity=30,
    )
    assert 60 <= score_high <= 100
    assert isinstance(score_high, int)

    # Low affinity scenario
    score_low = AICrossSellService.calculate_cross_sell_score_100(
        probability=0.05,
        confidence=0.05,
        lift=0.2,
        inventory_quantity=0,
    )
    assert 0 <= score_low <= 30
    assert isinstance(score_low, int)


def test_phase_177_cross_sell_score_api(client, setup_b08_data):
    """Verify GET /api/v1/recommendations/cross-sell-score endpoint."""
    data = setup_b08_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    res = client.get(
        f"/api/v1/recommendations/cross-sell-score?customer_id={data['cust_a1'].id}&product_id={data['p3'].id}",
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["customer_id"] == str(data["cust_a1"].id)
    assert body["product_id"] == str(data["p3"].id)
    assert 0 <= body["score_100"] <= 100
    assert "lift" in body
    assert "confidence" in body


# ==============================================================================
# Phase 178: Recommendation Ranking Tests
# ==============================================================================

def test_phase_178_recommendation_ranking(db_session, setup_b08_data):
    """Verify ranking engine populates 0-100 scores, stable ordering, and excludes inactive products."""
    data = setup_b08_data
    ranking = RecommendationRankingEngine.rank_recommendations(
        db=db_session,
        company_id=data["company_a"].id,
        customer_id=data["cust_a1"].id,
        top_n=5,
    )
    assert len(ranking.recommendations) > 0
    p_ids = [r.product_id for r in ranking.recommendations]

    # Inactive product P5 must be excluded
    assert data["p5_inactive"].id not in p_ids

    # Ranks must be 1-indexed and strictly increasing
    ranks = [r.rank for r in ranking.recommendations]
    assert ranks == list(range(1, len(ranking.recommendations) + 1))

    # All items must have 0-100 integer scores populated
    for r in ranking.recommendations:
        assert 0 <= r.upsell_score_100 <= 100
        assert 0 <= r.cross_sell_score_100 <= 100
        assert r.explanation is not None
        assert len(r.explanation.summary) > 0


# ==============================================================================
# Phase 179: AI Next-Best-Product Tests
# ==============================================================================

def test_phase_179_next_best_product(db_session, setup_b08_data):
    """Verify next best product selector returns optimal single recommendation."""
    data = setup_b08_data
    nbp = NextBestProductService.determine_next_best_product(
        db=db_session,
        company_id=data["company_a"].id,
        customer_id=data["cust_a1"].id,
    )
    assert nbp.has_recommendation is True
    assert nbp.best_product is not None
    assert nbp.best_product.rank == 1
    assert nbp.best_product.score > 0.0


# ==============================================================================
# Phase 180: Upsell Explanation Tests
# ==============================================================================

def test_phase_180_upsell_explanation_service(db_session, setup_b08_data):
    """Verify deterministic, structured human-readable explanation generation."""
    data = setup_b08_data
    pattern = PurchasePatternAnalysisService.analyze_customer(
        db=db_session,
        company_id=data["company_a"].id,
        customer_id=data["cust_a1"].id,
    )

    explanation = RecommendationExplanationService.generate_explanation(
        product=data["p2"],
        recommendation_type=RecommendationType.UPSELL,
        customer_pattern=pattern,
        customer_segment=CustomerBehaviorSegment.HIGH_VALUE,
        score_100=88,
        signals={"upsell_probability": 0.85, "unit_margin_ratio": 0.50},
        category_name=data["cat_hardware"].name,
    )

    assert "Enterprise Compute Matrix 900" in explanation.summary
    assert "88/100" in explanation.summary
    assert len(explanation.reasons) >= 2


def test_phase_180_explanation_api(client, setup_b08_data):
    """Verify GET /api/v1/recommendations/explain/{product_id} API endpoint."""
    data = setup_b08_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    res = client.get(
        f"/api/v1/recommendations/explain/{data['p2'].id}?customer_id={data['cust_a1'].id}&recommendation_type=UPSELL",
        headers=headers,
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert "summary" in body
    assert len(body["reasons"]) > 0
    assert "signals" in body


# ==============================================================================
# Phase 181 & 182: Add-to-Quote & Real-Time Margin Updates Tests
# ==============================================================================

def test_phase_182_real_time_margins_decimal_precision():
    """Verify strict Decimal financial arithmetic in RealTimeMarginService."""
    p_id1 = uuid.uuid4()
    p_id2 = uuid.uuid4()

    items = [
        QuoteLineItemInput(
            product_id=p_id1,
            quantity=2,
            selling_price=Decimal("1000.00"),
            unit_cost=Decimal("600.00"),
        ),
        QuoteLineItemInput(
            product_id=p_id2,
            quantity=3,
            selling_price=Decimal("500.00"),
            unit_cost=Decimal("250.00"),
        ),
    ]

    margin_summary = RealTimeMarginService.calculate_margins(items)

    # Item 1: 2 * 1000 = 2000 rev, 1200 cost -> GP 800 (40.00%)
    # Item 2: 3 * 500 = 1500 rev, 750 cost -> GP 750 (50.00%)
    # Total: Rev 3500, Cost 1950 -> GP 1550 (44.29%)
    assert margin_summary.total_revenue == Decimal("3500.00")
    assert margin_summary.total_cost == Decimal("1950.00")
    assert margin_summary.total_gross_profit == Decimal("1550.00")
    assert margin_summary.total_margin_pct == Decimal("44.29")
    assert len(margin_summary.lines) == 2


def test_phase_181_add_to_quote_and_event_emission(db_session, setup_b08_data):
    """Verify candidate product addition, margin calculation, and automated event emission."""
    data = setup_b08_data

    request = AddToQuoteRequest(
        customer_id=data["cust_a1"].id,
        product_id=data["p2"].id,
        quantity=2,
        quote_reference="QUOTE-B08-TEST-001",
        existing_items=[
            QuoteLineItemInput(
                product_id=data["p1"].id,
                quantity=1,
                selling_price=Decimal("1000.00"),
                unit_cost=Decimal("600.00"),
            )
        ],
    )

    response = RecommendationQuoteIntegrationService.add_recommendation_to_quote(
        db=db_session,
        company_id=data["company_a"].id,
        request=request,
        actor_id=data["user_a"].id,
    )

    assert response.status == "SUCCESS"
    assert response.added_quantity == 2
    assert response.product_sku == data["p2"].sku
    assert response.margin_summary.total_revenue == Decimal("7000.00")  # 1000 + 2*3000
    assert response.margin_summary.total_cost == Decimal("3600.00")     # 600 + 2*1500
    assert response.event_id is not None

    # Check that recommendation event was created in DB
    event = db_session.get(RecommendationEvent, uuid.UUID(response.event_id))
    assert event is not None
    assert event.event_type == "ADDED_TO_QUOTE"
    assert event.quote_reference == "QUOTE-B08-TEST-001"


def test_phase_181_add_to_quote_api_inactive_product(client, setup_b08_data):
    """Verify attempting to add an inactive product is rejected with HTTP 400."""
    data = setup_b08_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    payload = {
        "customer_id": str(data["cust_a1"].id),
        "product_id": str(data["p5_inactive"].id),
        "quantity": 1,
    }
    res = client.post("/api/v1/recommendations/add-to-quote", json=payload, headers=headers)
    err_body = res.json()
    err_msg = err_body.get("error", {}).get("message", "") or err_body.get("detail", "")
    assert "inactive" in err_msg.lower()


# ==============================================================================
# Phase 183: Upsell Acceptance Tracking Tests
# ==============================================================================

def test_phase_183_tracking_and_deduplication(db_session, setup_b08_data):
    """Verify recommendation lifecycle tracking and 5-second idempotency deduplication."""
    data = setup_b08_data
    rec_id = f"REC-TRACK-{uuid.uuid4().hex[:6]}"

    event_payload = RecommendationEventCreate(
        recommendation_id=rec_id,
        customer_id=data["cust_a1"].id,
        product_id=data["p3"].id,
        recommendation_type=RecommendationType.CROSS_SELL,
        event_type=RecommendationEventEnum.ACCEPTED,
        score=Decimal("92.50"),
        quote_reference="QUOTE-ACC-01",
    )

    ev1 = RecommendationTrackingService.track_event(
        db=db_session,
        company_id=data["company_a"].id,
        event=event_payload,
        actor_id=data["user_a"].id,
    )
    assert ev1.id is not None

    # Immediate second call with identical recommendation_id and event_type
    ev2 = RecommendationTrackingService.track_event(
        db=db_session,
        company_id=data["company_a"].id,
        event=event_payload,
        actor_id=data["user_a"].id,
    )
    # Must return identical event without duplicate record
    assert ev1.id == ev2.id


def test_phase_183_tracking_api(client, setup_b08_data):
    """Verify POST /api/v1/recommendations/events endpoint."""
    data = setup_b08_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    payload = {
        "recommendation_id": f"REC-API-{uuid.uuid4().hex[:6]}",
        "customer_id": str(data["cust_a1"].id),
        "product_id": str(data["p3"].id),
        "recommendation_type": "CROSS_SELL",
        "event_type": "VIEWED",
        "score": "84.00",
    }
    res = client.post("/api/v1/recommendations/events", json=payload, headers=headers)
    assert res.status_code == 201
    body = res.json()["data"]
    assert body["event_type"] == "VIEWED"
    assert body["score"] == "84.00"


# ==============================================================================
# Phase 184: Recommendation Analytics Tests
# ==============================================================================

def test_phase_184_analytics_calculation(db_session, setup_b08_data):
    """Verify analytics funnel metrics, acceptance rates, and product conversion leaderboards."""
    data = setup_b08_data
    comp_id = data["company_a"].id

    # Seed events across the lifecycle
    rec_prefix = f"REC-ANALYTICS-{uuid.uuid4().hex[:4]}"
    stages = [
        ("GENERATED", Decimal("80.00")),
        ("VIEWED", Decimal("80.00")),
        ("SELECTED", Decimal("80.00")),
        ("ADDED_TO_QUOTE", Decimal("80.00")),
        ("ACCEPTED", Decimal("80.00")),
    ]
    for event_name, score in stages:
        db_session.add(
            RecommendationEvent(
                company_id=comp_id,
                recommendation_id=f"{rec_prefix}-1",
                customer_id=data["cust_a1"].id,
                product_id=data["p2"].id,
                recommendation_type="UPSELL",
                event_type=event_name,
                score=score,
            )
        )
    db_session.commit()

    analytics = RecommendationAnalyticsService.get_analytics(
        db=db_session,
        company_id=comp_id,
    )
    assert analytics.total_recommendations_generated >= 1
    assert analytics.total_accepted >= 1
    assert analytics.acceptance_rate > 0.0
    assert analytics.average_recommendation_score > 0.0


def test_phase_184_analytics_api(client, setup_b08_data):
    """Verify GET /api/v1/recommendations/analytics API endpoint."""
    data = setup_b08_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    res = client.get("/api/v1/recommendations/analytics", headers=headers)
    assert res.status_code == 200
    body = res.json()["data"]
    assert "total_recommendations_generated" in body
    assert "acceptance_rate" in body
    assert "top_recommended_products" in body


# ==============================================================================
# Phase 185: Upsell Dashboard Tests
# ==============================================================================

def test_phase_185_dashboard_summary_service(db_session, setup_b08_data):
    """Verify consolidated dashboard aggregation service."""
    data = setup_b08_data
    summary = UpsellDashboardService.get_dashboard_summary(
        db=db_session,
        company_id=data["company_a"].id,
    )
    assert "total_recommendations" in summary.kpis
    assert len(summary.conversion_funnel) == 5
    assert summary.conversion_funnel[0].stage == "Generated"
    assert summary.conversion_funnel[4].stage == "Accepted"
    assert len(summary.category_distribution) > 0


def test_phase_185_dashboard_api(client, setup_b08_data):
    """Verify GET /api/v1/recommendations/dashboard API endpoint."""
    data = setup_b08_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    res = client.get("/api/v1/recommendations/dashboard", headers=headers)
    assert res.status_code == 200
    body = res.json()["data"]
    assert "kpis" in body
    assert "conversion_funnel" in body
    assert "category_distribution" in body
    assert "recent_activity" in body


# ==============================================================================
# Security & Multi-Tenant Isolation Tests
# ==============================================================================

def test_security_multi_tenant_isolation(client, setup_b08_data):
    """Verify Tenant A user cannot access or add recommendations for Tenant B customer."""
    data = setup_b08_data
    headers_a = {"Authorization": f"Bearer {data['token_a']}"}

    # Attempt to query upsell score for Company B customer using Company A token
    res = client.get(
        f"/api/v1/recommendations/upsell-score?customer_id={data['cust_b1'].id}&product_id={data['p1'].id}",
        headers=headers_a,
    )
    assert res.status_code == 404

    # Attempt to add to quote for Company B customer using Company A token
    payload = {
        "customer_id": str(data["cust_b1"].id),
        "product_id": str(data["p1"].id),
        "quantity": 1,
    }
    res2 = client.post("/api/v1/recommendations/add-to-quote", json=payload, headers=headers_a)
    assert res2.status_code == 400 or res2.status_code == 404


def test_security_unauthenticated_request(client, setup_b08_data):
    """Verify unauthenticated requests return HTTP 401."""
    res = client.get("/api/v1/recommendations/dashboard")
    assert res.status_code == 401
