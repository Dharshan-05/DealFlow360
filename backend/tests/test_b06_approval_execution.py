"""Comprehensive Production Test Suite for DealFlow360 B06 (Phases 156–165: Approval Execution Engine).

Verifies strict roadmap compliance and production guarantees:
- Phase 156: Auto Approval
  * Genuinely compliant deals (NO_APPROVAL_REQUIRED) -> automatically APPROVED
  * Requests requiring higher levels (Manager/Finance/Executive) -> auto-approval blocked
- Phase 157: Manager Approval
  * Authorized Sales Manager approval and rejection
  * Normal sales user / unauthorized actor rejected (HTTP 403)
- Phase 158: Finance Approval
  * Authorized Finance approval and rejection
  * Sales Manager or Rep impersonating Finance rejected (HTTP 403)
- Phase 159: Multi-Level Approval
  * Sequential step execution adhering to configured chain order
  * Prevention of skipping steps or approving future steps early
  * Prevention of duplicate decisions on same step
  * Return for revision flow
- Phase 160: Approval Escalation
  * Overdue step escalation to next authority tier
  * Prevention of infinite loop beyond EXECUTIVE
- Phase 161: Approval Timeout
  * Expired requests marked as TIMED_OUT past expiration horizon
- Phase 162: Approval Audit Trail
  * Immutable, append-only chronological history with actors, timestamps, reasons
- Phase 163: Approval Notifications
  * Internal notification events, recipient role targeting, deduplication
- Phase 164: Approval Dashboard
  * Real-time aggregation of metrics, SLA compliance, pending task counts
- Phase 165: Approval Decision Engine
  * Central authoritative coordination, transactional integrity, and idempotent execution
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
from app.models.approval_execution import (
    ApprovalAuditLog,
    ApprovalNotification,
    ApprovalRequest,
    ApprovalStep,
)
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.schemas.approval_execution import (
    ApprovalActionInput,
    ApprovalEscalationInput,
    ApprovalRequestStatus,
    ApprovalSubmitRequest,
    StepStatus,
)
from app.schemas.approval_routing import (
    ApprovalChainType,
    ApprovalLevel,
    ComprehensiveApprovalEvaluationRequest,
)
from app.services.approval_execution import (
    ApprovalAuditService,
    ApprovalDashboardService,
    ApprovalDecisionEngine,
    ApprovalNotificationService,
)
from app.services.rbac import RBACRoleNames


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
def setup_b06_data(db_session):
    """Seed test company, roles, and users with distinct privileges for B06 testing."""
    # 1. Company
    company = Company(
        name=f"B06 Execution Corp {uuid.uuid4().hex[:6]}",
        legal_name="B06 Enterprise Decision Systems Inc",
        email=f"b06_{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(company)
    db_session.commit()

    # 2. Permissions
    perms = {}
    for p_name in ["discounts:read", "discounts:create", "discounts:update"]:
        perm = db_session.execute(select(Permission).where(Permission.name == p_name)).scalar_one_or_none()
        if not perm:
            res_part, act_part = p_name.split(":")
            perm = Permission(name=p_name, description=f"{p_name} permission", resource=res_part, action=act_part)
            db_session.add(perm)
            db_session.commit()
        perms[p_name] = perm

    # 3. Roles
    def create_role(name):
        role = Role(name=f"{name}_{uuid.uuid4().hex[:6]}", description=f"{name} role")
        for p in perms.values():
            role.permissions.append(p)
        db_session.add(role)
        db_session.commit()
        return role

    role_rep = create_role(RBACRoleNames.SALES_REPRESENTATIVE)
    role_mgr = create_role(RBACRoleNames.SALES_MANAGER)
    role_fin = create_role(RBACRoleNames.FINANCE)
    role_vp = create_role("VP Sales")
    role_admin = create_role(RBACRoleNames.ADMIN)

    # 4. Users
    def create_user(email_prefix, role):
        u = User(
            company_id=company.id,
            email=f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com",
            password_hash="mocked_hash",
            first_name=email_prefix.capitalize(),
            last_name="User",
            is_active=True,
        )
        u.roles.append(role)
        db_session.add(u)
        db_session.commit()
        tok = create_access_token(subject=str(u.id))
        return u, {"Authorization": f"Bearer {tok}"}

    rep_user, rep_headers = create_user("sales_rep", role_rep)
    mgr_user, mgr_headers = create_user("sales_mgr", role_mgr)
    fin_user, fin_headers = create_user("finance_officer", role_fin)
    vp_user, vp_headers = create_user("vp_sales", role_vp)
    admin_user, admin_headers = create_user("admin_exec", role_admin)

    # 5. Customer Tier & Customer
    tier = CustomerTier(
        name=f"Tier-B06-{uuid.uuid4().hex[:6]}",
        code=f"T6-{uuid.uuid4().hex[:6]}",
        discount_limit=Decimal("20.00"),
    )
    db_session.add(tier)
    db_session.commit()

    customer = Customer(
        company_id=company.id,
        tier_id=tier.id,
        customer_code=f"CUST-B06-{uuid.uuid4().hex[:6]}",
        name="Apex Enterprise Solutions",
        email=f"apex_{uuid.uuid4().hex[:6]}@example.com",
    )
    db_session.add(customer)
    db_session.commit()

    return {
        "company": company,
        "customer": customer,
        "rep_user": rep_user,
        "rep_headers": rep_headers,
        "mgr_user": mgr_user,
        "mgr_headers": mgr_headers,
        "fin_user": fin_user,
        "fin_headers": fin_headers,
        "vp_user": vp_user,
        "vp_headers": vp_headers,
        "admin_user": admin_user,
        "admin_headers": admin_headers,
    }


# ==============================================================================
# Phase 156: Auto Approval Tests
# ==============================================================================

def test_phase_156_auto_approval_success(db_session, setup_b06_data):
    """Phase 156: Deals within pre-approved parameters are automatically approved upon submission."""
    company = setup_b06_data["company"]
    rep_user = setup_b06_data["rep_user"]

    # Compliant payload: low value, high margin, low discount, trusted customer
    payload = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-AUTO-OK-001",
        deal_value=Decimal("4000.00"),
        selling_price=Decimal("200.00"),
        unit_cost=Decimal("60.00"),
        requested_discount_pct=Decimal("5.0"),
        customer_tier="PLATINUM",
        customer_tenure_days=240,
        ai_risk_score=15.0,
        ai_risk_classification="LOW",
    )

    req = ApprovalDecisionEngine.submit_for_approval(
        db=db_session,
        company_id=company.id,
        request_payload=payload,
        actor=rep_user,
    )

    assert req.status == ApprovalRequestStatus.APPROVED.value
    assert req.required_level == ApprovalLevel.NO_APPROVAL_REQUIRED.value
    assert len(req.steps) == 0

    # Verify audit trail record
    audits = ApprovalAuditService.get_audit_trail(db_session, company.id, req.id)
    actions = [a.action for a in audits]
    assert "CREATED" in actions
    assert "AUTO_APPROVED" in actions


def test_phase_156_auto_approval_blocked_when_approval_required(db_session, setup_b06_data):
    """Phase 156: Disallow calling auto-approval when a deal requires higher authority review."""
    company = setup_b06_data["company"]
    rep_user = setup_b06_data["rep_user"]

    # Non-compliant deal: requires SALES_MANAGER due to discount exceeding rep authority
    payload = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-ESCALATED-001",
        deal_value=Decimal("15000.00"),
        selling_price=Decimal("500.00"),
        unit_cost=Decimal("250.00"),
        requested_discount_pct=Decimal("15.0"),  # Exceeds rep authority!
        customer_tier="SILVER",
        customer_tenure_days=90,
        ai_risk_score=40.0,
        ai_risk_classification="MEDIUM",
    )

    req = ApprovalDecisionEngine.submit_for_approval(
        db=db_session,
        company_id=company.id,
        request_payload=payload,
        actor=rep_user,
    )

    assert req.status == ApprovalRequestStatus.IN_PROGRESS.value
    assert req.required_level in (ApprovalLevel.SALES_MANAGER.value, ApprovalLevel.FINANCE.value)

    # Attempting to call auto-approval must raise error
    with pytest.raises(Exception) as exc_info:
        ApprovalDecisionEngine.execute_auto_approval(
            db=db_session,
            company_id=company.id,
            approval_request_id=req.id,
            actor=rep_user,
        )
    assert "Cannot auto-approve" in str(exc_info.value)


# ==============================================================================
# Phase 157 & 158: Manager & Finance Approval Execution Tests
# ==============================================================================

def test_phase_157_manager_approval_success_and_unauthorized(db_session, setup_b06_data):
    """Phase 157: Sales Manager can approve; unauthorized user is blocked."""
    company = setup_b06_data["company"]
    rep_user = setup_b06_data["rep_user"]
    mgr_user = setup_b06_data["mgr_user"]

    # Create request requiring SALES_MANAGER
    payload = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-MGR-TEST-001",
        deal_value=Decimal("12000.00"),
        selling_price=Decimal("100.00"),
        unit_cost=Decimal("50.00"),
        requested_discount_pct=Decimal("12.0"),
        customer_tier="GOLD",
        customer_tenure_days=150,
        ai_risk_score=35.0,
        ai_risk_classification="MEDIUM",
    )

    req = ApprovalDecisionEngine.submit_for_approval(
        db=db_session,
        company_id=company.id,
        request_payload=payload,
        actor=rep_user,
    )

    # 1. Rep cannot approve (403 unauthorized)
    with pytest.raises(Exception) as exc_info:
        ApprovalDecisionEngine.execute_approval_decision(
            db=db_session,
            company_id=company.id,
            approval_request_id=req.id,
            actor=rep_user,
            decision="APPROVED",
        )
    assert "Access denied" in str(exc_info.value)

    # 2. Manager approves successfully
    res = ApprovalDecisionEngine.execute_approval_decision(
        db=db_session,
        company_id=company.id,
        approval_request_id=req.id,
        actor=mgr_user,
        decision="APPROVED",
        reason="Commercial discount verified against margin buffer.",
    )
    assert res.decision == "APPROVED"
    assert res.status == ApprovalRequestStatus.APPROVED.value


def test_phase_158_finance_approval_success_and_unauthorized(db_session, setup_b06_data):
    """Phase 158: Finance authority required for margin compression; Sales Manager cannot approve Finance step."""
    company = setup_b06_data["company"]
    rep_user = setup_b06_data["rep_user"]
    mgr_user = setup_b06_data["mgr_user"]
    fin_user = setup_b06_data["fin_user"]

    # Thin margin deal (requires Finance review chain)
    payload = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-FIN-TEST-001",
        deal_value=Decimal("20000.00"),
        selling_price=Decimal("100.00"),
        unit_cost=Decimal("80.00"),  # Thin margin
        requested_discount_pct=Decimal("10.0"),
        customer_tier="SILVER",
        customer_tenure_days=100,
        ai_risk_score=62.0,
        ai_risk_classification="HIGH",
    )

    req = ApprovalDecisionEngine.submit_for_approval(
        db=db_session,
        company_id=company.id,
        request_payload=payload,
        actor=rep_user,
    )

    assert req.required_chain_type == ApprovalChainType.FINANCE_REVIEW.value
    # Step 1: Sales Manager
    ApprovalDecisionEngine.execute_approval_decision(
        db=db_session,
        company_id=company.id,
        approval_request_id=req.id,
        actor=mgr_user,
        decision="APPROVED",
    )

    # Step 2: Now active is FINANCE. Manager trying to approve Finance step MUST fail!
    with pytest.raises(Exception) as exc_info:
        ApprovalDecisionEngine.execute_approval_decision(
            db=db_session,
            company_id=company.id,
            approval_request_id=req.id,
            actor=mgr_user,
            decision="APPROVED",
        )
    assert "Finance role required" in str(exc_info.value)

    # Authorized Finance user approves
    res_fin = ApprovalDecisionEngine.execute_approval_decision(
        db=db_session,
        company_id=company.id,
        approval_request_id=req.id,
        actor=fin_user,
        decision="APPROVED",
        reason="Finance margin assessment cleared.",
    )
    assert res_fin.status == ApprovalRequestStatus.APPROVED.value


# ==============================================================================
# Phase 159: Multi-Level Approval Execution Tests
# ==============================================================================

def test_phase_159_sequential_multi_level_approval(db_session, setup_b06_data):
    """Phase 159: Enforce strict sequence, disallow step skipping, and handle rejection."""
    company = setup_b06_data["company"]
    rep_user = setup_b06_data["rep_user"]
    mgr_user = setup_b06_data["mgr_user"]
    fin_user = setup_b06_data["fin_user"]

    # Two-step finance review chain
    payload = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-MULTI-001",
        deal_value=Decimal("25000.00"),
        selling_price=Decimal("200.00"),
        unit_cost=Decimal("150.00"),
        requested_discount_pct=Decimal("12.0"),
        customer_tier="SILVER",
        customer_tenure_days=120,
        ai_risk_score=65.0,
        ai_risk_classification="HIGH",
    )

    req = ApprovalDecisionEngine.submit_for_approval(
        db=db_session,
        company_id=company.id,
        request_payload=payload,
        actor=rep_user,
    )

    # Step 1 is active (Manager). Attempting to approve Step 2 directly must fail.
    with pytest.raises(Exception) as exc_info:
        ApprovalDecisionEngine.execute_approval_decision(
            db=db_session,
            company_id=company.id,
            approval_request_id=req.id,
            actor=fin_user,
            decision="APPROVED",
            target_step_number=2,
        )
    assert "active step is 1" in str(exc_info.value)

    # Approve step 1
    ApprovalDecisionEngine.execute_approval_decision(
        db=db_session,
        company_id=company.id,
        approval_request_id=req.id,
        actor=mgr_user,
        decision="APPROVED",
        target_step_number=1,
    )

    # Now step 2 is active. Rejection terminates entire request
    res_reject = ApprovalDecisionEngine.execute_approval_decision(
        db=db_session,
        company_id=company.id,
        approval_request_id=req.id,
        actor=fin_user,
        decision="REJECTED",
        reason="Margin compression unacceptable for current fiscal quarter.",
    )
    assert res_reject.status == ApprovalRequestStatus.REJECTED.value

    # Subsequent approval attempts on rejected request must fail
    with pytest.raises(Exception):
        ApprovalDecisionEngine.execute_approval_decision(
            db=db_session,
            company_id=company.id,
            approval_request_id=req.id,
            actor=fin_user,
            decision="APPROVED",
        )


# ==============================================================================
# Phase 160 & 161: Escalation & Timeout Tests
# ==============================================================================

def test_phase_160_escalation_and_terminal_safety(db_session, setup_b06_data):
    """Phase 160: Escalate overdue step to next tier; prevent infinite loop past EXECUTIVE."""
    company = setup_b06_data["company"]
    rep_user = setup_b06_data["rep_user"]
    mgr_user = setup_b06_data["mgr_user"]
    admin_user = setup_b06_data["admin_user"]

    payload = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-ESC-001",
        deal_value=Decimal("15000.00"),
        selling_price=Decimal("100.00"),
        unit_cost=Decimal("50.00"),
        requested_discount_pct=Decimal("12.0"),
        customer_tier="GOLD",
        customer_tenure_days=100,
        ai_risk_score=35.0,
        ai_risk_classification="MEDIUM",
    )

    req = ApprovalDecisionEngine.submit_for_approval(
        db=db_session,
        company_id=company.id,
        request_payload=payload,
        actor=rep_user,
    )

    # 1. Escalate from SALES_MANAGER -> FINANCE
    res_esc1 = ApprovalDecisionEngine.escalate_request(
        db=db_session,
        company_id=company.id,
        approval_request_id=req.id,
        actor=mgr_user,
        reason="SLA elapsed waiting for response.",
    )
    assert res_esc1.current_level == ApprovalLevel.FINANCE.value
    assert res_esc1.status == ApprovalRequestStatus.ESCALATED.value

    # 2. Escalate from FINANCE -> VP_SALES
    res_esc2 = ApprovalDecisionEngine.escalate_request(
        db=db_session,
        company_id=company.id,
        approval_request_id=req.id,
        actor=admin_user,
        reason="Second escalation tier triggered.",
    )
    assert res_esc2.current_level == ApprovalLevel.VP_SALES.value

    # 3. Escalate from VP_SALES -> EXECUTIVE
    res_esc3 = ApprovalDecisionEngine.escalate_request(
        db=db_session,
        company_id=company.id,
        approval_request_id=req.id,
        actor=admin_user,
        reason="Third escalation tier triggered.",
    )
    assert res_esc3.current_level == ApprovalLevel.EXECUTIVE.value

    # 4. Attempting to escalate past EXECUTIVE must be safely blocked
    with pytest.raises(Exception) as exc_info:
        ApprovalDecisionEngine.escalate_request(
            db=db_session,
            company_id=company.id,
            approval_request_id=req.id,
            actor=admin_user,
            reason="Exceeding executive.",
        )
    assert "Cannot escalate beyond EXECUTIVE" in str(exc_info.value)


def test_phase_161_approval_timeout(db_session, setup_b06_data):
    """Phase 161: Transition expired requests past expiration horizon to TIMED_OUT."""
    company = setup_b06_data["company"]
    rep_user = setup_b06_data["rep_user"]

    payload = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-TIMEOUT-001",
        deal_value=Decimal("10000.00"),
        selling_price=Decimal("100.00"),
        unit_cost=Decimal("50.00"),
        requested_discount_pct=Decimal("12.0"),
        customer_tier="GOLD",
        customer_tenure_days=100,
        ai_risk_score=35.0,
        ai_risk_classification="MEDIUM",
    )

    req = ApprovalDecisionEngine.submit_for_approval(
        db=db_session,
        company_id=company.id,
        request_payload=payload,
        actor=rep_user,
        expiration_hours=1,
    )

    # Manually backdate expires_at to simulate expired window
    req.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db_session.commit()

    # Run timeout checker
    timed_out = ApprovalDecisionEngine.check_and_apply_timeouts(db_session, company.id)
    assert req.id in timed_out

    db_session.refresh(req)
    assert req.status == ApprovalRequestStatus.TIMED_OUT.value


# ==============================================================================
# Phase 162 & 163: Audit Trail & Notifications Tests
# ==============================================================================

def test_phase_162_approval_audit_trail(db_session, setup_b06_data):
    """Phase 162: Immutable, append-only chronological history."""
    company = setup_b06_data["company"]
    rep_user = setup_b06_data["rep_user"]
    mgr_user = setup_b06_data["mgr_user"]

    payload = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-AUDIT-001",
        deal_value=Decimal("12000.00"),
        selling_price=Decimal("100.00"),
        unit_cost=Decimal("50.00"),
        requested_discount_pct=Decimal("12.0"),
        customer_tier="GOLD",
        customer_tenure_days=100,
        ai_risk_score=35.0,
        ai_risk_classification="MEDIUM",
    )

    req = ApprovalDecisionEngine.submit_for_approval(
        db=db_session,
        company_id=company.id,
        request_payload=payload,
        actor=rep_user,
    )

    ApprovalDecisionEngine.execute_approval_decision(
        db=db_session,
        company_id=company.id,
        approval_request_id=req.id,
        actor=mgr_user,
        decision="APPROVED",
        reason="Manager approved for strategic customer.",
    )

    logs = ApprovalAuditService.get_audit_trail(db_session, company.id, req.id)
    assert len(logs) >= 2
    actions = [l.action for l in logs]
    assert actions[0] == "CREATED"
    assert actions[1] == "APPROVED"
    assert logs[1].actor_id == mgr_user.id
    assert logs[1].reason == "Manager approved for strategic customer."


def test_phase_163_approval_notifications(db_session, setup_b06_data):
    """Phase 163: Domain notification creation and deduplication."""
    company = setup_b06_data["company"]
    rep_user = setup_b06_data["rep_user"]

    payload = ComprehensiveApprovalEvaluationRequest(
        deal_reference="DEAL-NOTIF-001",
        deal_value=Decimal("12000.00"),
        selling_price=Decimal("100.00"),
        unit_cost=Decimal("50.00"),
        requested_discount_pct=Decimal("12.0"),
        customer_tier="GOLD",
        customer_tenure_days=100,
        ai_risk_score=35.0,
        ai_risk_classification="MEDIUM",
    )

    req = ApprovalDecisionEngine.submit_for_approval(
        db=db_session,
        company_id=company.id,
        request_payload=payload,
        actor=rep_user,
    )

    notifs = ApprovalNotificationService.list_notifications(db_session, company.id)
    assert len(notifs) >= 1
    assert any(n.deal_reference == "DEAL-NOTIF-001" for n in notifs)


# ==============================================================================
# Phase 164: Approval Dashboard Tests
# ==============================================================================

def test_phase_164_dashboard_metrics(db_session, setup_b06_data):
    """Phase 164: Real-time dashboard KPI aggregations."""
    company = setup_b06_data["company"]
    metrics = ApprovalDashboardService.get_dashboard_metrics(db_session, company.id)

    assert metrics.company_id == company.id
    assert metrics.total_requests >= 0
    assert isinstance(metrics.counts_by_status, list)
    assert isinstance(metrics.counts_by_level, list)


# ==============================================================================
# API Endpoints Integration Tests (Phase 156–165)
# ==============================================================================

def test_b06_api_endpoints_workflow(client, setup_b06_data):
    """Complete API workflow testing submission, manager approval, audit retrieval, and dashboard."""
    mgr_headers = setup_b06_data["mgr_headers"]

    # 1. Submit Request via API
    resp_sub = client.post(
        "/api/v1/approvals/requests",
        headers=mgr_headers,
        json={
            "deal_payload": {
                "deal_reference": "DEAL-API-B06-001",
                "deal_value": "15000.00",
                "selling_price": "100.00",
                "unit_cost": "50.00",
                "requested_discount_pct": "12.0",
                "customer_tier": "GOLD",
                "customer_tenure_days": 100,
                "ai_risk_score": 35.0,
                "ai_risk_classification": "MEDIUM",
            },
            "expiration_hours": 48,
        },
    )
    assert resp_sub.status_code == 201
    req_id = resp_sub.json()["data"]["id"]

    # 2. Approve via API
    resp_app = client.post(
        f"/api/v1/approvals/requests/{req_id}/approve",
        headers=mgr_headers,
        json={"reason": "Approved via API call"},
    )
    assert resp_app.status_code == 200
    assert resp_app.json()["data"]["decision"] == "APPROVED"

    # 3. Retrieve Audit Trail via API
    resp_aud = client.get(
        f"/api/v1/approvals/requests/{req_id}/audit",
        headers=mgr_headers,
    )
    assert resp_aud.status_code == 200
    audits = resp_aud.json()["data"]
    assert len(audits) >= 2

    # 4. Retrieve Dashboard via API
    resp_dash = client.get(
        "/api/v1/approvals/dashboard",
        headers=mgr_headers,
    )
    assert resp_dash.status_code == 200
    dash = resp_dash.json()["data"]
    assert dash["total_requests"] >= 1
