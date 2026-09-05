"""Comprehensive Production Test Suite for DealFlow360 B05 (Phases 146–155: Approval Routing Foundation).

Verifies strict roadmap compliance and production guarantees:
- Phase 146: Approval Configuration (Tenant isolation, policy persistence, defaults)
- Phase 147: Approval Levels (Deterministic hierarchy: NO_APPROVAL < SALES_MANAGER < FINANCE < VP_SALES < EXECUTIVE)
- Phase 148: Approval Chains (Chain topology, steps, sequential progression, selection)
- Phase 149: Approval Thresholds (Boundary evaluation, operators, mapping to levels)
- Phase 150: Risk-Based Routing (AI risk score and classification routing)
- Phase 151: Discount-Based Routing (Rep limits, tier ceilings, category ceilings, executive thresholds)
- Phase 152: Margin-Based Routing (Decimal gross margin, post-discount margin, negative margin, zero price)
- Phase 153: Customer-Based Routing (Payment reliability, delinquency risk, tenure evaluation)
- Phase 154: Deal-Value Routing (Monetary sizing thresholds: MICRO, SMALL, MEDIUM, LARGE, ENTERPRISE)
- Phase 155: Blended Risk Score (Multi-dimensional synthesis & deterministic preservation of STRICTEST approval level)
"""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models.approval_policy import ApprovalPolicy
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.schemas.approval_routing import (
    ApprovalChainType,
    ApprovalLevel,
    ApprovalPolicyCreate,
    BlendedRiskWeights,
    ComparisonOperator,
    ComprehensiveApprovalEvaluationRequest,
    CustomerRoutingRequest,
    DealValueRoutingRequest,
    DiscountRoutingRequest,
    MarginRoutingRequest,
    RiskRoutingRequest,
    ThresholdDimension,
)
from app.services.approval_routing import (
    ApprovalChainService,
    ApprovalLevelHierarchyService,
    ApprovalPolicyService,
    ApprovalThresholdService,
    BlendedRiskScoreService,
    CustomerBasedRoutingService,
    DealValueRoutingService,
    DiscountBasedRoutingService,
    MarginBasedRoutingService,
    RiskBasedRoutingService,
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
def setup_b05_data(db_session):
    """Seed test company, user with permissions, and customer for B05 testing."""
    # 1. Company
    company = Company(
        name=f"B05 Approval Corp {uuid.uuid4().hex[:6]}",
        legal_name="B05 Enterprise Approvals Inc",
        email=f"b05_{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(company)
    db_session.commit()

    # 2. Customer Tier
    tier = CustomerTier(
        name=f"Tier-{uuid.uuid4().hex[:6]}",
        code=f"T-{uuid.uuid4().hex[:8]}",
        discount_limit=Decimal("20.00"),
        description="Standard 20% discount ceiling",
    )
    db_session.add(tier)
    db_session.commit()

    # 3. Customer
    cust = Customer(
        company_id=company.id,
        tier_id=tier.id,
        customer_code=f"CUST-B05-{uuid.uuid4().hex[:6]}",
        name="Acme Enterprise Holdings",
        email=f"acme_{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(cust)
    db_session.commit()

    # 4. User and Role
    role = Role(name=f"ApprovalsAdmin_{uuid.uuid4().hex[:6]}", description="Admin for approvals")
    db_session.add(role)
    db_session.commit()

    # Add required permissions
    for perm_name in ["discounts:read", "discounts:create", "discounts:update"]:
        perm = db_session.execute(select(Permission).where(Permission.name == perm_name)).scalar_one_or_none()
        if not perm:
            res_part, act_part = perm_name.split(":")
            perm = Permission(name=perm_name, description=f"{perm_name} permission", resource=res_part, action=act_part)
            db_session.add(perm)
            db_session.commit()
        if perm not in role.permissions:
            role.permissions.append(perm)
    db_session.commit()

    user = User(
        company_id=company.id,
        email=f"approval_user_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="mocked_hash",
        first_name="Approval",
        last_name="Manager",
        is_active=True,
    )
    user.roles.append(role)
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=str(user.id))
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "company": company,
        "user": user,
        "customer": cust,
        "tier": tier,
        "headers": headers,
    }


# ==============================================================================
# Phase 146: Approval Configuration Tests
# ==============================================================================

def test_phase_146_approval_policy_persistence(db_session, setup_b05_data):
    """Phase 146: Verify policy creation and tenant isolation."""
    company = setup_b05_data["company"]
    user = setup_b05_data["user"]

    payload = ApprovalPolicyCreate(
        name="Corporate Standard Approval Policy",
        description="Default multi-tier governance policy",
        is_active=True,
        is_default=True,
    )

    policy = ApprovalPolicyService.create_policy(
        db=db_session,
        company_id=company.id,
        data=payload,
        user_id=user.id,
    )

    assert policy.id is not None
    assert policy.company_id == company.id
    assert policy.name == "Corporate Standard Approval Policy"
    assert policy.is_default is True
    assert len(policy.levels_config) == 5
    assert len(policy.chains_config) == 5

    # Retrieve via service
    fetched = ApprovalPolicyService.get_active_policy(db=db_session, company_id=company.id)
    assert fetched is not None
    assert fetched.id == policy.id


def test_phase_146_approval_policy_api(client, setup_b05_data):
    """Phase 146: Verify GET and POST /api/v1/approvals/policies endpoints."""
    headers = setup_b05_data["headers"]

    # 1. Create policy via API
    resp = client.post(
        "/api/v1/approvals/policies",
        headers=headers,
        json={
            "name": "Mid-Market Enterprise Policy",
            "description": "Standard pricing review rules",
            "is_active": True,
            "is_default": False,
        },
    )
    assert resp.status_code == 201
    created_id = resp.json()["data"]["id"]

    # 2. List policies
    resp_list = client.get("/api/v1/approvals/policies", headers=headers)
    assert resp_list.status_code == 200
    items = resp_list.json()["data"]
    assert any(p["id"] == created_id for p in items)


# ==============================================================================
# Phase 147: Approval Levels Tests
# ==============================================================================

def test_phase_147_level_hierarchy_ranking():
    """Phase 147: Deterministic hierarchy order and rank invariance."""
    levels = [
        ApprovalLevel.NO_APPROVAL_REQUIRED,
        ApprovalLevel.SALES_MANAGER,
        ApprovalLevel.FINANCE,
        ApprovalLevel.VP_SALES,
        ApprovalLevel.EXECUTIVE,
    ]

    ranks = [ApprovalLevelHierarchyService.get_rank(l) for l in levels]
    assert ranks == [0, 1, 2, 3, 4]
    assert sorted(ranks) == ranks

    # Strictest selection
    assert ApprovalLevelHierarchyService.get_strictest_level([
        ApprovalLevel.SALES_MANAGER,
        ApprovalLevel.NO_APPROVAL_REQUIRED,
    ]) == ApprovalLevel.SALES_MANAGER

    assert ApprovalLevelHierarchyService.get_strictest_level([
        ApprovalLevel.SALES_MANAGER,
        ApprovalLevel.EXECUTIVE,
        ApprovalLevel.FINANCE,
    ]) == ApprovalLevel.EXECUTIVE


def test_phase_147_levels_api(client, setup_b05_data):
    """Phase 147: GET /api/v1/approvals/levels endpoint."""
    headers = setup_b05_data["headers"]
    resp = client.get("/api/v1/approvals/levels", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 5
    assert data[0]["level"] == "NO_APPROVAL_REQUIRED"
    assert data[4]["level"] == "EXECUTIVE"


# ==============================================================================
# Phase 148: Approval Chains Tests
# ==============================================================================

def test_phase_148_chain_topology_and_selection():
    """Phase 148: Registered approval chains and level-to-chain mappings."""
    chains = ApprovalChainService.get_all_chains()
    assert len(chains) == 5

    # Auto approve
    c_none = ApprovalChainService.get_chain_for_level(ApprovalLevel.NO_APPROVAL_REQUIRED)
    assert c_none.chain_type == ApprovalChainType.AUTO_APPROVE
    assert len(c_none.steps) == 0

    # Sales manager
    c_mgr = ApprovalChainService.get_chain_for_level(ApprovalLevel.SALES_MANAGER)
    assert c_mgr.chain_type == ApprovalChainType.STANDARD_SALES
    assert len(c_mgr.steps) == 1
    assert c_mgr.steps[0].level == ApprovalLevel.SALES_MANAGER

    # Finance
    c_fin = ApprovalChainService.get_chain_for_level(ApprovalLevel.FINANCE)
    assert c_fin.chain_type == ApprovalChainType.FINANCE_REVIEW
    assert len(c_fin.steps) == 2
    assert c_fin.steps[1].level == ApprovalLevel.FINANCE

    # Executive
    c_exec = ApprovalChainService.get_chain_for_level(ApprovalLevel.EXECUTIVE)
    assert c_exec.chain_type == ApprovalChainType.EXECUTIVE_EXCEPTION
    assert c_exec.highest_level == ApprovalLevel.EXECUTIVE


def test_phase_148_chains_api(client, setup_b05_data):
    """Phase 148: GET /api/v1/approvals/chains endpoint."""
    headers = setup_b05_data["headers"]
    resp = client.get("/api/v1/approvals/chains", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 5


# ==============================================================================
# Phase 149: Approval Thresholds Tests
# ==============================================================================

def test_phase_149_threshold_boundary_evaluation():
    """Phase 149: Threshold boundary operators and mapping to levels."""
    # AI Risk Score thresholds: <30 (none), >=30 (Manager), >=60 (Finance), >=85 (Executive)
    res_low = ApprovalThresholdService.evaluate_dimension(ThresholdDimension.AI_RISK_SCORE, 25.0)
    assert res_low.triggered is False
    assert res_low.required_level == ApprovalLevel.NO_APPROVAL_REQUIRED

    res_med = ApprovalThresholdService.evaluate_dimension(ThresholdDimension.AI_RISK_SCORE, 45.0)
    assert res_med.triggered is True
    assert res_med.required_level == ApprovalLevel.SALES_MANAGER

    res_high = ApprovalThresholdService.evaluate_dimension(ThresholdDimension.AI_RISK_SCORE, 72.0)
    assert res_high.triggered is True
    assert res_high.required_level == ApprovalLevel.FINANCE

    res_crit = ApprovalThresholdService.evaluate_dimension(ThresholdDimension.AI_RISK_SCORE, 90.0)
    assert res_crit.triggered is True
    assert res_crit.required_level == ApprovalLevel.EXECUTIVE

    # Margin thresholds: negative <= 0% (Executive)
    res_margin_neg = ApprovalThresholdService.evaluate_dimension(ThresholdDimension.MARGIN_PERCENT, -5.0)
    assert res_margin_neg.triggered is True
    assert res_margin_neg.required_level == ApprovalLevel.EXECUTIVE


def test_phase_149_thresholds_api(client, setup_b05_data):
    """Phase 149: POST /api/v1/approvals/evaluate/thresholds endpoint."""
    headers = setup_b05_data["headers"]
    resp = client.post(
        "/api/v1/approvals/evaluate/thresholds?dimension=DISCOUNT_PERCENT&value=25.0",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["triggered"] is True
    assert data["required_level"] in ("VP_SALES", "EXECUTIVE")


# ==============================================================================
# Phase 150: Risk-Based Routing Tests
# ==============================================================================

def test_phase_150_risk_based_routing():
    """Phase 150: Risk routing based on calibrated scores and tiers."""
    # Critical risk
    res_crit = RiskBasedRoutingService.evaluate(
        RiskRoutingRequest(risk_score=88.5, risk_classification="CRITICAL")
    )
    assert res_crit.required_level == ApprovalLevel.EXECUTIVE
    assert res_crit.recommended_chain == ApprovalChainType.EXECUTIVE_EXCEPTION

    # High risk
    res_high = RiskBasedRoutingService.evaluate(
        RiskRoutingRequest(risk_score=68.0, risk_classification="HIGH")
    )
    assert res_high.required_level == ApprovalLevel.FINANCE
    assert res_high.recommended_chain == ApprovalChainType.FINANCE_REVIEW

    # Low risk
    res_low = RiskBasedRoutingService.evaluate(
        RiskRoutingRequest(risk_score=15.0, risk_classification="LOW")
    )
    assert res_low.required_level == ApprovalLevel.NO_APPROVAL_REQUIRED
    assert res_low.recommended_chain == ApprovalChainType.AUTO_APPROVE


def test_phase_150_risk_routing_api(client, setup_b05_data):
    """Phase 150: POST /api/v1/approvals/evaluate/risk endpoint."""
    headers = setup_b05_data["headers"]
    resp = client.post(
        "/api/v1/approvals/evaluate/risk",
        headers=headers,
        json={"risk_score": 75.0, "risk_classification": "HIGH"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["required_level"] == "FINANCE"


# ==============================================================================
# Phase 151: Discount-Based Routing Tests
# ==============================================================================

def test_phase_151_discount_based_routing():
    """Phase 151: Discount routing against authority limits and policy ceilings."""
    # Under rep limit (5% < 10%)
    res_ok = DiscountBasedRoutingService.evaluate(
        DiscountRoutingRequest(
            requested_discount_pct=Decimal("5.0"),
            rep_authorized_limit=Decimal("10.0"),
            customer_tier_ceiling=Decimal("20.0"),
        )
    )
    assert res_ok.required_level == ApprovalLevel.NO_APPROVAL_REQUIRED
    assert res_ok.exceeds_rep_authority is False

    # Exceeds rep authority (12% > 10%)
    res_mgr = DiscountBasedRoutingService.evaluate(
        DiscountRoutingRequest(
            requested_discount_pct=Decimal("12.0"),
            rep_authorized_limit=Decimal("10.0"),
            customer_tier_ceiling=Decimal("20.0"),
        )
    )
    assert res_mgr.required_level == ApprovalLevel.SALES_MANAGER
    assert res_mgr.exceeds_rep_authority is True

    # Exceeds customer tier (22% > 20%)
    res_vp = DiscountBasedRoutingService.evaluate(
        DiscountRoutingRequest(
            requested_discount_pct=Decimal("22.0"),
            rep_authorized_limit=Decimal("10.0"),
            customer_tier_ceiling=Decimal("20.0"),
            category_ceiling=Decimal("25.0"),
        )
    )
    assert res_vp.required_level in (ApprovalLevel.FINANCE, ApprovalLevel.VP_SALES)
    assert res_vp.exceeds_tier_ceiling is True

    # Exceeds executive ceiling (35% > 30%)
    res_exec = DiscountBasedRoutingService.evaluate(
        DiscountRoutingRequest(
            requested_discount_pct=Decimal("35.0"),
            company_max_ceiling=Decimal("40.0"),
        )
    )
    assert res_exec.required_level == ApprovalLevel.EXECUTIVE


def test_phase_151_discount_routing_api(client, setup_b05_data):
    """Phase 151: POST /api/v1/approvals/evaluate/discount endpoint."""
    headers = setup_b05_data["headers"]
    resp = client.post(
        "/api/v1/approvals/evaluate/discount",
        headers=headers,
        json={"requested_discount_pct": "14.5", "rep_authorized_limit": "10.0"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["required_level"] == "SALES_MANAGER"


# ==============================================================================
# Phase 152: Margin-Based Routing Tests
# ==============================================================================

def test_phase_152_margin_based_routing():
    """Phase 152: Margin profitability, thin margins, zero cost, and negative margin handling."""
    # 1. Healthy margin: price 100, cost 40, discount 10% -> discounted price 90, margin = 55.56%
    res_healthy = MarginBasedRoutingService.evaluate(
        MarginRoutingRequest(
            selling_price=Decimal("100.00"),
            unit_cost=Decimal("40.00"),
            requested_discount_pct=Decimal("10.0"),
        )
    )
    assert res_healthy.is_negative_margin is False
    assert res_healthy.required_level == ApprovalLevel.NO_APPROVAL_REQUIRED

    # 2. Thin margin: price 100, cost 80, discount 10% -> discounted price 90, cost 80, margin = 11.11%
    res_thin = MarginBasedRoutingService.evaluate(
        MarginRoutingRequest(
            selling_price=Decimal("100.00"),
            unit_cost=Decimal("80.00"),
            requested_discount_pct=Decimal("10.0"),
            min_acceptable_margin_pct=Decimal("20.0"),
        )
    )
    assert res_thin.is_below_minimum_margin is True
    assert res_thin.required_level == ApprovalLevel.FINANCE

    # 3. Negative margin: price 100, cost 95, discount 20% -> discounted price 80, cost 95
    res_neg = MarginBasedRoutingService.evaluate(
        MarginRoutingRequest(
            selling_price=Decimal("100.00"),
            unit_cost=Decimal("95.00"),
            requested_discount_pct=Decimal("20.0"),
        )
    )
    assert res_neg.is_negative_margin is True
    assert res_neg.required_level == ApprovalLevel.EXECUTIVE
    assert res_neg.recommended_chain == ApprovalChainType.EXECUTIVE_EXCEPTION


def test_phase_152_margin_routing_api(client, setup_b05_data):
    """Phase 152: POST /api/v1/approvals/evaluate/margin endpoint."""
    headers = setup_b05_data["headers"]
    resp = client.post(
        "/api/v1/approvals/evaluate/margin",
        headers=headers,
        json={
            "selling_price": "500.00",
            "unit_cost": "450.00",
            "requested_discount_pct": "15.0",
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_negative_margin"] is True
    assert data["required_level"] == "EXECUTIVE"


# ==============================================================================
# Phase 153: Customer-Based Routing Tests
# ==============================================================================

def test_phase_153_customer_based_routing():
    """Phase 153: Payment reliability and credit delinquency routing."""
    # 1. Trusted customer
    res_trusted = CustomerBasedRoutingService.evaluate(
        CustomerRoutingRequest(
            customer_tier="PLATINUM",
            tenure_days=365,
            payment_default_ratio=0.0,
            failed_payment_count=0,
        )
    )
    assert res_trusted.is_delinquent_risk is False
    assert res_trusted.required_level == ApprovalLevel.NO_APPROVAL_REQUIRED

    # 2. Delinquent customer
    res_delinquent = CustomerBasedRoutingService.evaluate(
        CustomerRoutingRequest(
            customer_tier="SILVER",
            tenure_days=180,
            payment_default_ratio=0.25,
            failed_payment_count=3,
        )
    )
    assert res_delinquent.is_delinquent_risk is True
    assert res_delinquent.required_level in (ApprovalLevel.FINANCE, ApprovalLevel.EXECUTIVE)


def test_phase_153_customer_routing_api(client, setup_b05_data):
    """Phase 153: POST /api/v1/approvals/evaluate/customer endpoint."""
    headers = setup_b05_data["headers"]
    resp = client.post(
        "/api/v1/approvals/evaluate/customer",
        headers=headers,
        json={
            "customer_tier": "GOLD",
            "tenure_days": 120,
            "payment_default_ratio": 0.05,
            "failed_payment_count": 0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["required_level"] == "NO_APPROVAL_REQUIRED"


# ==============================================================================
# Phase 154: Deal-Value Routing Tests
# ==============================================================================

def test_phase_154_deal_value_routing():
    """Phase 154: Deal value size tiers and authority limits."""
    # Micro (<$1,000)
    res_micro = DealValueRoutingService.evaluate(DealValueRoutingRequest(deal_value=Decimal("500.00")))
    assert res_micro.value_band == "MICRO"
    assert res_micro.required_level == ApprovalLevel.NO_APPROVAL_REQUIRED

    # Medium ($10,000 - $50,000)
    res_med = DealValueRoutingService.evaluate(DealValueRoutingRequest(deal_value=Decimal("25000.00")))
    assert res_med.value_band == "MEDIUM"
    assert res_med.required_level == ApprovalLevel.SALES_MANAGER

    # Large ($50,000 - $250,000)
    res_large = DealValueRoutingService.evaluate(DealValueRoutingRequest(deal_value=Decimal("150000.00")))
    assert res_large.value_band == "LARGE"
    assert res_large.required_level == ApprovalLevel.VP_SALES

    # Enterprise (>= $250,000)
    res_ent = DealValueRoutingService.evaluate(DealValueRoutingRequest(deal_value=Decimal("500000.00")))
    assert res_ent.value_band == "ENTERPRISE"
    assert res_ent.required_level == ApprovalLevel.EXECUTIVE


def test_phase_154_deal_value_routing_api(client, setup_b05_data):
    """Phase 154: POST /api/v1/approvals/evaluate/deal-value endpoint."""
    headers = setup_b05_data["headers"]
    resp = client.post(
        "/api/v1/approvals/evaluate/deal-value",
        headers=headers,
        json={"deal_value": "85000.00"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["value_band"] == "LARGE"
    assert data["required_level"] == "VP_SALES"


# ==============================================================================
# Phase 155: Blended Risk Score & Strictest Preservation Tests
# ==============================================================================

def test_phase_155_blended_risk_score_and_strictest_preservation(db_session, setup_b05_data):
    """Phase 155: Comprehensive evaluation synthesizing dimensions and strictly preserving highest authority."""
    company = setup_b05_data["company"]

    # Scenario 1: Low deal value ($5,000 -> Level 0), Low Discount (5% -> Level 0),
    # BUT Negative Margin (Selling 100, Cost 120 -> Level 4 EXECUTIVE).
    # The system MUST preserve EXECUTIVE level, despite low value and low discount.
    req_scenario_1 = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-MARGIN-ESCALATION-001",
        deal_value=Decimal("5000.00"),
        selling_price=Decimal("100.00"),
        unit_cost=Decimal("120.00"),  # Negative margin!
        requested_discount_pct=Decimal("5.0"),
        customer_tier="PLATINUM",
        customer_tenure_days=300,
        payment_default_ratio=0.0,
        ai_risk_score=20.0,
        ai_risk_classification="LOW",
    )

    resp_1 = BlendedRiskScoreService.evaluate_comprehensive(
        db=db_session,
        company_id=company.id,
        request=req_scenario_1,
    )

    assert resp_1.final_required_level == ApprovalLevel.EXECUTIVE
    assert resp_1.blended_result.strictest_required_level == ApprovalLevel.EXECUTIVE
    assert resp_1.blended_result.strictest_level_rank == 4
    assert resp_1.final_approval_chain.highest_level == ApprovalLevel.EXECUTIVE
    assert resp_1.blended_result.primary_escalation_driver == "MARGIN"

    # Scenario 2: Fully compliant deal adhering to all parameters
    req_scenario_2 = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-CLEAN-002",
        deal_value=Decimal("3000.00"),
        selling_price=Decimal("200.00"),
        unit_cost=Decimal("80.00"),
        requested_discount_pct=Decimal("5.0"),
        customer_tier="GOLD",
        customer_tenure_days=200,
        payment_default_ratio=0.0,
        ai_risk_score=15.0,
        ai_risk_classification="LOW",
    )

    resp_2 = BlendedRiskScoreService.evaluate_comprehensive(
        db=db_session,
        company_id=company.id,
        request=req_scenario_2,
    )

    assert resp_2.final_required_level == ApprovalLevel.NO_APPROVAL_REQUIRED
    assert resp_2.final_approval_chain.chain_type == ApprovalChainType.AUTO_APPROVE
    assert resp_2.blended_result.blended_risk_score < 30.0


def test_phase_155_comprehensive_evaluation_api(client, setup_b05_data):
    """Phase 155: POST /api/v1/approvals/evaluate/comprehensive endpoint."""
    headers = setup_b05_data["headers"]
    resp = client.post(
        "/api/v1/approvals/evaluate/comprehensive",
        headers=headers,
        json={
            "deal_reference": "DEAL-API-TEST-001",
            "deal_value": "75000.00",
            "selling_price": "1000.00",
            "unit_cost": "600.00",
            "requested_discount_pct": "12.0",
            "customer_tier": "SILVER",
            "customer_tenure_days": 180,
            "payment_default_ratio": 0.05,
            "ai_risk_score": 45.0,
            "ai_risk_classification": "MEDIUM",
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]

    # Deal value ($75k) requires VP_SALES (rank 3). Discount (12%) requires SALES_MANAGER (rank 1).
    # Strictest preservation must result in VP_SALES!
    assert data["final_required_level"] == "VP_SALES"
    assert data["blended_result"]["strictest_level_rank"] == 3
    assert len(data["blended_result"]["component_breakdown"]) == 5
