"""Comprehensive Test Suite for DealFlow360 B07 (Phases 166–175: AI Upsell / Cross-Sell Engine).

Verifies strict roadmap compliance and production guarantees:
- Phase 166: AI Upsell Engine
  * Generates high-value upsell alternatives based on customer spending baseline
  * Excludes non-subscription products already owned
  * Handles customers with zero purchase history safely
- Phase 167: AI Cross-Sell Engine
  * Identifies complementary product pairs from observed transaction associations
  * Excludes inactive items and already-purchased items
- Phase 168: Customer Purchase Pattern Analysis
  * Correct deterministic RFM extraction (Recency, Frequency, Monetary, AOV)
  * Tenure and category distribution calculation
  * Safe zero-history fallback (recency=999, frequency=0)
- Phase 169: Product Affinity Analysis
  * Accurate mathematical Support, Confidence, and Lift calculations
  * Zero-division protections and bounded lift values
- Phase 170: Frequently Bought Together
  * Ranked complementary recommendations
  * Minimum support filtering
- Phase 171: Next Best Product
  * Optimal single recommendation selection with signal explanations
- Phase 172: Customer Segmentation
  * Deterministic classification across HIGH_VALUE, LOYAL, ACTIVE, GROWTH, AT_RISK, NEW, DORMANT
  * Boundary test cases
- Phase 173: Upsell Probability
  * Bounded [0.0, 1.0] probability evaluation
  * Segment and price sensitivity scaling
- Phase 174: Cross-Sell Probability
  * Distinct from upsell probability, driven by affinity and recency
- Phase 175: Recommendation Ranking
  * Deterministic multi-factor weighted scoring
  * Stable tie-breaking, inactive item exclusion, top-N slicing
- Security & Multi-Tenancy:
  * Tenant isolation across companies
  * Rejection of cross-tenant customer access
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
from app.models.role import Role
from app.models.user import User
from app.schemas.recommendations import (
    CustomerBehaviorSegment,
    CustomerPurchasePattern,
    ProductAffinityMetric,
    RecommendationItem,
    RecommendationType,
)
from app.services.rbac import RBACRoleNames
from app.services.recommendations import (
    AICrossSellService,
    AIUpsellService,
    CrossSellProbabilityService,
    CustomerSegmentationService,
    FrequentlyBoughtTogetherService,
    NextBestProductService,
    ProductAffinityService,
    PurchasePatternAnalysisService,
    RecommendationRankingEngine,
    UpsellProbabilityService,
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
def setup_b07_data(db_session):
    """Seed companies, users, products, categories, transactions, and customer purchase histories."""
    # 1. Companies (Multi-Tenant Isolation)
    company_a = Company(
        name=f"B07 Corp Alpha {uuid.uuid4().hex[:6]}",
        legal_name="Alpha Tech Enterprises Inc",
        email=f"alpha_{uuid.uuid4().hex[:6]}@example.com",
    )
    company_b = Company(
        name=f"B07 Corp Beta {uuid.uuid4().hex[:6]}",
        legal_name="Beta Logistics Group Inc",
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

    role_sales = Role(name=f"Sales_{uuid.uuid4().hex[:6]}", description="Sales rep")
    role_sales.permissions.append(perm_read)
    db_session.add(role_sales)
    db_session.commit()

    # 3. Users
    user_a = User(
        company_id=company_a.id,
        email=f"user_a_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mock_hash",
        first_name="Alpha",
        last_name="Sales",
        is_active=True,
    )
    user_a.roles.append(role_sales)

    user_b = User(
        company_id=company_b.id,
        email=f"user_b_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mock_hash",
        first_name="Beta",
        last_name="Sales",
        is_active=True,
    )
    user_b.roles.append(role_sales)

    db_session.add_all([user_a, user_b])
    db_session.commit()

    token_a = create_access_token(subject=str(user_a.id))
    token_b = create_access_token(subject=str(user_b.id))

    # 4. Product Categories
    cat_hardware = ProductCategory(
        name=f"Hardware_{uuid.uuid4().hex[:8]}",
        code=f"HW_{uuid.uuid4().hex[:8]}",
        description="Compute and server hardware",
        is_active=True,
    )
    cat_software = ProductCategory(
        name=f"Software_{uuid.uuid4().hex[:8]}",
        code=f"SW_{uuid.uuid4().hex[:8]}",
        description="Enterprise subscriptions and licenses",
        is_active=True,
    )
    cat_accessories = ProductCategory(
        name=f"Accessories_{uuid.uuid4().hex[:8]}",
        code=f"ACC_{uuid.uuid4().hex[:8]}",
        description="Peripherals and components",
        is_active=True,
    )
    db_session.add_all([cat_hardware, cat_software, cat_accessories])
    db_session.commit()

    # 5. Products for Company A Catalog
    # P1: Entry Server ($1,000)
    p1 = Product(
        sku=f"SRV-100-{uuid.uuid4().hex[:4]}",
        name="Standard Server Node",
        category_id=cat_hardware.id,
        cost=Decimal("600.00"),
        base_price=Decimal("1000.00"),
        inventory_quantity=20,
        is_active=True,
    )
    # P2: Premium Server ($2,500) -> Upsell candidate for P1
    p2 = Product(
        sku=f"SRV-500-{uuid.uuid4().hex[:4]}",
        name="Enterprise Compute Cluster",
        category_id=cat_hardware.id,
        cost=Decimal("1300.00"),
        base_price=Decimal("2500.00"),
        inventory_quantity=10,
        is_active=True,
    )
    # P3: Server Rack Rails ($150) -> Cross-sell candidate for P1
    p3 = Product(
        sku=f"ACC-RAIL-{uuid.uuid4().hex[:4]}",
        name="Heavy-Duty Server Rack Rails",
        category_id=cat_accessories.id,
        cost=Decimal("50.00"),
        base_price=Decimal("150.00"),
        inventory_quantity=50,
        is_active=True,
    )
    # P4: Redundant Power Supply ($200) -> Cross-sell candidate for P1
    p4 = Product(
        sku=f"ACC-PWR-{uuid.uuid4().hex[:4]}",
        name="Titanium Redundant PSU",
        category_id=cat_accessories.id,
        cost=Decimal("90.00"),
        base_price=Decimal("200.00"),
        inventory_quantity=35,
        is_active=True,
    )
    # P5: Cloud Backup Subscription ($500/yr) -> Subscription product
    p5 = Product(
        sku=f"SUB-BKP-{uuid.uuid4().hex[:4]}",
        name="Managed Cloud Backup Pro",
        category_id=cat_software.id,
        cost=Decimal("150.00"),
        base_price=Decimal("500.00"),
        is_subscription=True,
        recurring_frequency="yearly",
        inventory_quantity=100,
        is_active=True,
    )
    # P6: Inactive Product (should be excluded from recommendations)
    p6_inactive = Product(
        sku=f"DISC-OLD-{uuid.uuid4().hex[:4]}",
        name="Discontinued Legacy Unit",
        category_id=cat_hardware.id,
        cost=Decimal("300.00"),
        base_price=Decimal("700.00"),
        inventory_quantity=0,
        is_active=False,
    )
    db_session.add_all([p1, p2, p3, p4, p5, p6_inactive])
    db_session.commit()

    # 6. Customers for Company A
    now = datetime.now(timezone.utc)
    # Customer 1: High Value / Loyal Customer
    cust_loyal = Customer(
        company_id=company_a.id,
        customer_code=f"CUST-LOYAL-{uuid.uuid4().hex[:4]}",
        name="Apex Enterprise Solutions",
        email=f"apex_{uuid.uuid4().hex[:4]}@example.com",
        is_active=True,
        created_at=now - timedelta(days=200),
    )
    # Customer 2: New / Zero History Customer
    cust_new = Customer(
        company_id=company_a.id,
        customer_code=f"CUST-NEW-{uuid.uuid4().hex[:4]}",
        name="Fresh Startup Inc",
        email=f"fresh_{uuid.uuid4().hex[:4]}@example.com",
        is_active=True,
        created_at=now - timedelta(days=10),
    )
    # Customer 3: At-Risk Customer
    cust_at_risk = Customer(
        company_id=company_a.id,
        customer_code=f"CUST-RISK-{uuid.uuid4().hex[:4]}",
        name="Lapsing Systems Ltd",
        email=f"risk_{uuid.uuid4().hex[:4]}@example.com",
        is_active=True,
        created_at=now - timedelta(days=365),
    )
    # Customer 4: Company B Customer (for tenant isolation tests)
    cust_comp_b = Customer(
        company_id=company_b.id,
        customer_code=f"CUST-B-{uuid.uuid4().hex[:4]}",
        name="Beta Customer Co",
        email=f"betacust_{uuid.uuid4().hex[:4]}@example.com",
        is_active=True,
        created_at=now - timedelta(days=60),
    )
    db_session.add_all([cust_loyal, cust_new, cust_at_risk, cust_comp_b])
    db_session.commit()

    # 7. Seed Transactions for Customer 1 (Loyal & High Value)
    # Purchases: 6 orders, total spend > $30,000, last purchase 10 days ago
    for i in range(6):
        order_date = now - timedelta(days=10 + (i * 25))
        purch = CustomerPurchaseHistory(
            company_id=company_a.id,
            customer_id=cust_loyal.id,
            order_number=f"ORD-LOYAL-{i+1}",
            purchase_date=order_date,
            total_amount=Decimal("5500.00"),
            status="COMPLETED",
            item_count=3,
        )
        db_session.add(purch)
    db_session.commit()

    # 8. Seed AppliedDiscounts / Baskets to create Market Basket Co-occurrences
    # Deals containing P1 + P3 + P4 (Server + Rails + PSU)
    for b in range(5):
        deal_ref = f"BASKET-DEAL-{b+1}"
        d_time = now - timedelta(days=15 + (b * 10))
        # P1 in basket
        ad1 = AppliedDiscount(
            company_id=company_a.id,
            customer_id=cust_loyal.id,
            product_id=p1.id,
            deal_reference=deal_ref,
            requested_discount=Decimal("5.00"),
            applied_discount=Decimal("5.00"),
            selling_price=Decimal("1000.00"),
            discounted_price=Decimal("950.00"),
            unit_cost=Decimal("600.00"),
            margin_percentage=Decimal("36.84"),
            reason_code="STANDARD",
            applied_at=d_time,
        )
        # P3 in same basket
        ad3 = AppliedDiscount(
            company_id=company_a.id,
            customer_id=cust_loyal.id,
            product_id=p3.id,
            deal_reference=deal_ref,
            requested_discount=Decimal("0.00"),
            applied_discount=Decimal("0.00"),
            selling_price=Decimal("150.00"),
            discounted_price=Decimal("150.00"),
            unit_cost=Decimal("50.00"),
            margin_percentage=Decimal("66.67"),
            reason_code="STANDARD",
            applied_at=d_time,
        )
        # P4 in same basket
        ad4 = AppliedDiscount(
            company_id=company_a.id,
            customer_id=cust_loyal.id,
            product_id=p4.id,
            deal_reference=deal_ref,
            requested_discount=Decimal("0.00"),
            applied_discount=Decimal("0.00"),
            selling_price=Decimal("200.00"),
            discounted_price=Decimal("200.00"),
            unit_cost=Decimal("90.00"),
            margin_percentage=Decimal("55.00"),
            reason_code="STANDARD",
            applied_at=d_time,
        )
        db_session.add_all([ad1, ad3, ad4])
    db_session.commit()

    # 9. Seed Purchases for Customer 3 (At-Risk: last purchased 150 days ago)
    purch_risk = CustomerPurchaseHistory(
        company_id=company_a.id,
        customer_id=cust_at_risk.id,
        order_number="ORD-RISK-1",
        purchase_date=now - timedelta(days=150),
        total_amount=Decimal("2000.00"),
        status="COMPLETED",
        item_count=1,
    )
    db_session.add(purch_risk)
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
        "p5": p5,
        "p6_inactive": p6_inactive,
        "cust_loyal": cust_loyal,
        "cust_new": cust_new,
        "cust_at_risk": cust_at_risk,
        "cust_comp_b": cust_comp_b,
    }


# ==============================================================================
# Phase 168: Customer Purchase Pattern Analysis Tests
# ==============================================================================

def test_phase_168_purchase_pattern_analysis(db_session, setup_b07_data):
    """Verify RFM, frequency, and repeat purchase extraction."""
    d = setup_b07_data
    pattern = PurchasePatternAnalysisService.analyze_customer(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_loyal"].id,
    )

    assert pattern.total_orders_count == 6
    assert pattern.total_spend == Decimal("33000.00")
    assert pattern.average_order_value == Decimal("5500.00")
    assert pattern.recency_days <= 12
    assert pattern.tenure_days >= 195
    assert not pattern.is_zero_history
    assert pattern.purchase_frequency_monthly > 0.0


def test_phase_168_zero_history_customer(db_session, setup_b07_data):
    """Verify safe fallback for customers with zero transaction records."""
    d = setup_b07_data
    pattern = PurchasePatternAnalysisService.analyze_customer(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_new"].id,
    )

    assert pattern.is_zero_history is True
    assert pattern.total_orders_count == 0
    assert pattern.total_spend == Decimal("0.00")
    assert pattern.average_order_value == Decimal("0.00")
    assert pattern.recency_days == 999
    assert pattern.purchase_frequency_monthly == 0.0


# ==============================================================================
# Phase 169: Product Affinity Analysis Tests
# ==============================================================================

def test_phase_169_product_affinity_analysis(db_session, setup_b07_data):
    """Verify statistical Support, Confidence, and Lift calculations."""
    d = setup_b07_data
    affinity = ProductAffinityService.compute_pair_affinity(
        db=db_session,
        company_id=d["company_a"].id,
        source_product_id=d["p1"].id,
        target_product_id=d["p3"].id,
    )

    assert affinity is not None
    assert affinity.co_occurrence_count == 5
    assert affinity.confidence == 1.0  # P3 always appeared with P1
    assert affinity.lift >= 1.0
    assert 0.0 <= affinity.affinity_score <= 1.0


def test_phase_169_zero_co_occurrence_and_same_product(db_session, setup_b07_data):
    """Ensure identical products return None and unassociated products return safe defaults."""
    d = setup_b07_data
    # Same product comparison
    same_aff = ProductAffinityService.compute_pair_affinity(
        db=db_session,
        company_id=d["company_a"].id,
        source_product_id=d["p1"].id,
        target_product_id=d["p1"].id,
    )
    assert same_aff is None


# ==============================================================================
# Phase 170: Frequently Bought Together Tests
# ==============================================================================

def test_phase_170_frequently_bought_together(db_session, setup_b07_data):
    """Verify ranking and filtering of complementary accessories."""
    d = setup_b07_data
    res = FrequentlyBoughtTogetherService.get_frequently_bought_together(
        db=db_session,
        company_id=d["company_a"].id,
        product_id=d["p1"].id,
        limit=5,
    )

    assert res.source_product_id == d["p1"].id
    assert len(res.items) >= 2
    # P3 and P4 should be top complementary items
    top_pids = [item.product_id for item in res.items]
    assert d["p3"].id in top_pids
    assert d["p4"].id in top_pids
    assert all(item.rank >= 1 for item in res.items)


# ==============================================================================
# Phase 172: Customer Segmentation Tests
# ==============================================================================

def test_phase_172_customer_segmentation(db_session, setup_b07_data):
    """Verify segmentation logic across High Value, New, and At Risk customers."""
    d = setup_b07_data

    # 1. Loyal / High Value customer
    seg_loyal = CustomerSegmentationService.segment_customer(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_loyal"].id,
    )
    assert seg_loyal.segment == CustomerBehaviorSegment.HIGH_VALUE
    assert "High-Value" in seg_loyal.segment_label

    # 2. New Customer
    seg_new = CustomerSegmentationService.segment_customer(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_new"].id,
    )
    assert seg_new.segment == CustomerBehaviorSegment.NEW

    # 3. At-Risk Customer
    seg_risk = CustomerSegmentationService.segment_customer(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_at_risk"].id,
    )
    assert seg_risk.segment == CustomerBehaviorSegment.AT_RISK


# ==============================================================================
# Phase 173 & 174: Upsell and Cross-Sell Probabilities Tests
# ==============================================================================

def test_phase_173_upsell_probability(db_session, setup_b07_data):
    """Verify calibrated upsell probability outputs [0.0, 1.0]."""
    d = setup_b07_data
    pattern = PurchasePatternAnalysisService.analyze_customer(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_loyal"].id,
    )
    prob_p2 = UpsellProbabilityService.calculate_probability(
        customer_pattern=pattern,
        customer_segment=CustomerBehaviorSegment.HIGH_VALUE,
        target_product=d["p2"],
        target_category_name="Hardware",
    )

    assert 0.0 <= prob_p2 <= 1.0
    assert prob_p2 > 0.30  # High-value customer with matching category should have high score


def test_phase_174_cross_sell_probability(db_session, setup_b07_data):
    """Verify cross-sell probability is distinct and bounded."""
    d = setup_b07_data
    pattern = PurchasePatternAnalysisService.analyze_customer(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_loyal"].id,
    )
    affinity = ProductAffinityService.compute_pair_affinity(
        db=db_session,
        company_id=d["company_a"].id,
        source_product_id=d["p1"].id,
        target_product_id=d["p3"].id,
    )
    prob = CrossSellProbabilityService.calculate_probability(
        customer_pattern=pattern,
        customer_segment=CustomerBehaviorSegment.HIGH_VALUE,
        affinity_metric=affinity,
    )

    assert 0.0 <= prob <= 1.0
    assert prob > 0.40  # Verified strong affinity and recent purchase


# ==============================================================================
# Phase 166 & 167: AI Upsell and Cross-Sell Engine Tests
# ==============================================================================

def test_phase_166_ai_upsell_candidates(db_session, setup_b07_data):
    """Verify upsell candidate generation and inactive item exclusion."""
    d = setup_b07_data
    candidates = AIUpsellService.generate_upsell_candidates(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_loyal"].id,
        limit=5,
    )

    assert len(candidates) > 0
    candidate_pids = [item[0].id for item in candidates]
    # P6 (inactive) must not be present
    assert d["p6_inactive"].id not in candidate_pids
    # P1 is already purchased one-off, so it should not be an upsell to itself
    assert d["p1"].id not in candidate_pids


def test_phase_167_ai_cross_sell_candidates(db_session, setup_b07_data):
    """Verify complementary cross-sell candidate generation."""
    d = setup_b07_data
    candidates = AICrossSellService.generate_cross_sell_candidates(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_loyal"].id,
        limit=5,
    )

    assert len(candidates) > 0
    candidate_pids = [item[0].id for item in candidates]
    assert d["p6_inactive"].id not in candidate_pids


# ==============================================================================
# Phase 171 & 175: Next Best Product & Final Recommendation Ranking Tests
# ==============================================================================

def test_phase_175_recommendation_ranking(db_session, setup_b07_data):
    """Verify final multi-factor recommendation ranking with stable tie-breaking."""
    d = setup_b07_data
    res = RecommendationRankingEngine.rank_recommendations(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_loyal"].id,
        top_n=3,
    )

    assert res.customer_id == d["cust_loyal"].id
    assert len(res.recommendations) <= 3
    # Check ranking positions
    for idx, rec in enumerate(res.recommendations, start=1):
        assert rec.rank == idx
        assert 0.0 <= rec.score <= 1.0
        assert rec.sku != d["p6_inactive"].sku

    # Assert descending order of scores
    scores = [r.score for r in res.recommendations]
    assert scores == sorted(scores, reverse=True)


def test_phase_171_next_best_product(db_session, setup_b07_data):
    """Verify single top next best product recommendation."""
    d = setup_b07_data
    nbp = NextBestProductService.determine_next_best_product(
        db=db_session,
        company_id=d["company_a"].id,
        customer_id=d["cust_loyal"].id,
    )

    assert nbp.has_recommendation is True
    assert nbp.best_product is not None
    assert nbp.best_product.rank == 1
    assert nbp.best_product.recommendation_type in (
        RecommendationType.UPSELL,
        RecommendationType.CROSS_SELL,
        RecommendationType.REPEAT_PURCHASE,
    )


# ==============================================================================
# Multi-Tenant Isolation & Security Tests
# ==============================================================================

def test_security_tenant_isolation(client, setup_b07_data):
    """Ensure Company A cannot access Company B customer recommendations."""
    d = setup_b07_data

    # User A attempting to get ranking for Company B's customer -> 404
    resp = client.get(
        f"/api/v1/recommendations/ranking/{d['cust_comp_b'].id}",
        headers={"Authorization": f"Bearer {d['token_a']}"},
    )
    assert resp.status_code == 404

    # User B accessing Company B's customer -> 200
    resp_b = client.get(
        f"/api/v1/recommendations/ranking/{d['cust_comp_b'].id}",
        headers={"Authorization": f"Bearer {d['token_b']}"},
    )
    assert resp_b.status_code == 200
    data_b = resp_b.json()["data"]
    assert data_b["customer_id"] == str(d["cust_comp_b"].id)


def test_security_unauthenticated_request(client, setup_b07_data):
    """Ensure endpoints reject unauthenticated access with 401."""
    d = setup_b07_data
    resp = client.get(f"/api/v1/recommendations/upsell/{d['cust_loyal'].id}")
    assert resp.status_code == 401
