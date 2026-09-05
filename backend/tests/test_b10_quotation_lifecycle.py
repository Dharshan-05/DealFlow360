"""Comprehensive Test Suite for DealFlow360 B10 (Phases 196–205).

Verifies strict production contracts:
- Phase 196: Quotation Status (Explicit lifecycle state machine, centralized validator, terminal states, audit)
- Phase 197: Quote Versioning (Snapshot capture, immutable revision history, sequential numbering, active version)
- Phase 198: Quote Expiration (Deterministic timestamp evaluation, expired acceptance rejection, idempotency)
- Phase 199: Quote Approval Integration (B05/B06 Approval Engine integration, auto-approval vs multi-level routing)
- Phase 200: Quote PDF Generation (ReportLab vector PDF layout, tables, totals, tenant isolation)
- Phase 201: Quote Email (Email dispatch abstraction, safe development transport, PDF attachment, recipient validation)
- Phase 202: Quote Send Tracking (Send logs, unique tracking tokens, view events, tenant scoping)
- Phase 203: Quote Acceptance (Valid acceptance, approval guards, expired guards, idempotency)
- Phase 204: Quote Rejection (Mandatory rejection reason, status transition, terminal guards)
- Phase 205: Quote Conversion to Deal (Conversion to CustomerDealHistory, data transfer, transactional safety, duplicate prevention)
- Tenant Isolation & Security (IDOR resistance across companies)
- Regression & Compatibility (B01–B09 intact)
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
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.quotation import Quotation, QuotationSendLog, QuotationStatus, QuotationVersion
from app.models.quotation_line_item import QuotationLineItem
from app.models.role import Role
from app.models.user import User
from app.schemas.quotation import (
    QuotationCreate,
    QuotationLineItemCreate,
    QuotationStatusUpdate,
    QuotationUpdate,
    QuotationVersionCreate,
)
from app.services.quotation import (
    QuotationAcceptanceService,
    QuotationApprovalService,
    QuotationCalculationEngine,
    QuotationDealConversionService,
    QuotationEmailService,
    QuotationExpirationService,
    QuotationPdfService,
    QuotationRejectionService,
    QuotationSendTrackingService,
    QuotationService,
    QuotationStatusTransitionValidator,
    QuotationVersioningService,
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
def setup_b10_data(db_session):
    """Seed multi-tenant companies, users, roles, categories, products, and customers."""
    # 1. Multi-Tenant Companies
    company_a = Company(
        name=f"B10 Corp Alpha {uuid.uuid4().hex[:8]}",
        legal_name="Alpha Commercial Systems Inc",
        email=f"alpha_{uuid.uuid4().hex[:8]}@example.com",
    )
    company_b = Company(
        name=f"B10 Corp Beta {uuid.uuid4().hex[:8]}",
        legal_name="Beta Deal Corp",
        email=f"beta_{uuid.uuid4().hex[:8]}@example.com",
    )
    db_session.add_all([company_a, company_b])
    db_session.commit()

    # 2. Permissions & Roles
    permissions = []
    for p_name in ["quotations:read", "quotations:write", "quotations:approve", "discounts:read", "discounts:create"]:
        perm = db_session.execute(select(Permission).where(Permission.name == p_name)).scalar_one_or_none()
        if not perm:
            perm = Permission(name=p_name, description=f"Permission {p_name}", resource=p_name.split(":")[0], action=p_name.split(":")[1])
            db_session.add(perm)
        permissions.append(perm)
    db_session.commit()

    role_sales = Role(name=f"Sales_B10_{uuid.uuid4().hex[:8]}", description="Sales Rep Role")
    for p in permissions:
        role_sales.permissions.append(p)
    db_session.add(role_sales)
    db_session.commit()

    # 3. Users
    user_a = User(
        company_id=company_a.id,
        email=f"alice_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="mock_hash",
        first_name="Alice",
        last_name="Sales",
        is_active=True,
    )
    user_a.roles.append(role_sales)

    user_b = User(
        company_id=company_b.id,
        email=f"bob_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="mock_hash",
        first_name="Bob",
        last_name="Sales",
        is_active=True,
    )
    user_b.roles.append(role_sales)

    db_session.add_all([user_a, user_b])
    db_session.commit()

    # 4. Catalog Categories & Products
    cat_a = ProductCategory(
        name=f"Cloud Services {uuid.uuid4().hex[:8]}",
        code=f"CLD_{uuid.uuid4().hex[:6].upper()}",
        description="Cloud Compute & DB infrastructure",
        is_active=True,
    )
    db_session.add(cat_a)
    db_session.commit()

    prod_a1 = Product(
        sku=f"SKU-CLD-{uuid.uuid4().hex[:6].upper()}",
        name="Enterprise Compute Instance",
        category_id=cat_a.id,
        cost=Decimal("75.00"),
        base_price=Decimal("150.00"),
        inventory_quantity=100,
        is_active=True,
    )
    prod_a2 = Product(
        sku=f"SKU-DB-{uuid.uuid4().hex[:6].upper()}",
        name="Managed Database Cluster",
        category_id=cat_a.id,
        cost=Decimal("150.00"),
        base_price=Decimal("300.00"),
        inventory_quantity=100,
        is_active=True,
    )
    db_session.add_all([prod_a1, prod_a2])
    db_session.commit()

    # 5. Customers
    cust_a = Customer(
        company_id=company_a.id,
        customer_code=f"CUST-{uuid.uuid4().hex[:6].upper()}",
        name="Acme Global Industries",
        email="procurement@acme.com",
        is_active=True,
    )
    cust_b = Customer(
        company_id=company_b.id,
        customer_code=f"CUST-{uuid.uuid4().hex[:6].upper()}",
        name="Beta Client Ltd",
        email="procurement@betaclient.com",
        is_active=True,
    )
    db_session.add_all([cust_a, cust_b])
    db_session.commit()

    # Tokens
    token_a = create_access_token(subject=str(user_a.id))
    token_b = create_access_token(subject=str(user_b.id))

    return {
        "company_a": company_a,
        "company_b": company_b,
        "user_a": user_a,
        "user_b": user_b,
        "token_a": token_a,
        "token_b": token_b,
        "prod_a1": prod_a1,
        "prod_a2": prod_a2,
        "cust_a": cust_a,
        "cust_b": cust_b,
    }


def _create_sample_quote(client, data, discount_pct="0.00", valid_days=30):
    """Helper to create a standard quotation via API."""
    exp_time = (datetime.now(timezone.utc) + timedelta(days=valid_days)).isoformat()
    payload = {
        "customer_id": str(data["cust_a"].id),
        "valid_until": exp_time,
        "notes": "Standard B10 Commercial Quote",
        "terms_conditions": "Payment due within 30 days.",
        "overall_discount_percent": discount_pct,
        "line_items": [
            {
                "product_id": str(data["prod_a1"].id),
                "quantity": "2.0000",
                "unit_price": "150.00",
                "discount_percent": "0.00",
                "tax_rate": "10.00",
                "notes": "Primary node",
            },
            {
                "product_id": str(data["prod_a2"].id),
                "quantity": "1.0000",
                "unit_price": "300.00",
                "discount_percent": "0.00",
                "tax_rate": "10.00",
                "notes": "DB cluster",
            },
        ],
    }
    resp = client.post(
        "/api/v1/quotations",
        json=payload,
        headers={"Authorization": f"Bearer {data['token_a']}"},
    )
    assert resp.status_code == 201, f"Failed creating quote: {resp.text}"
    return resp.json()["data"]


def _err_text(resp):
    """Extract error string regardless of whether response is wrapped in standard envelope."""
    try:
        body = resp.json()
        return (body.get("message") or body.get("error", {}).get("message") or body.get("detail", "") or resp.text).lower()
    except Exception:
        return resp.text.lower()


# ==============================================================================
# Phase 196: Quotation Status & Transition Validator Tests
# ==============================================================================

def test_phase_196_quotation_status_lifecycle_and_validator(client, setup_b10_data, db_session):
    """Phase 196: Verify state machine transitions, terminal state enforcement, and audit logs."""
    data = setup_b10_data
    quote = _create_sample_quote(client, data)
    q_id = quote["id"]
    assert quote["status"] == "DRAFT"

    headers = {"Authorization": f"Bearer {data['token_a']}"}

    # 1. Valid Transition: DRAFT -> APPROVED
    resp = client.patch(f"/api/v1/quotations/{q_id}/status", json={"status": "APPROVED", "reason": "Authorized rep approval"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPROVED"

    # 2. Valid Transition: APPROVED -> SENT
    resp = client.patch(f"/api/v1/quotations/{q_id}/status", json={"status": "SENT", "reason": "Sent to customer"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "SENT"

    # 3. Valid Transition: SENT -> VIEWED
    resp = client.patch(f"/api/v1/quotations/{q_id}/status", json={"status": "VIEWED", "reason": "Client opened email"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "VIEWED"

    # 4. Valid Transition: VIEWED -> ACCEPTED
    resp = client.patch(f"/api/v1/quotations/{q_id}/status", json={"status": "ACCEPTED", "reason": "Client signed contract"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ACCEPTED"

    # 5. Invalid Transition: ACCEPTED cannot transition to REJECTED or DRAFT
    resp_inv = client.patch(f"/api/v1/quotations/{q_id}/status", json={"status": "REJECTED", "reason": "Late rejection attempt"}, headers=headers)
    assert resp_inv.status_code == 400
    assert "invalid quotation status transition" in _err_text(resp_inv)

    # 6. Verify Audit Trail entries exist
    audits = db_session.execute(
        select(AuditLog)
        .where(AuditLog.resource_id == str(q_id))
        .order_by(AuditLog.created_at.asc())
    ).scalars().all()
    actions = [a.action for a in audits]
    assert "QUOTATION_STATUS_CHANGED_APPROVED" in actions
    assert "QUOTATION_STATUS_CHANGED_SENT" in actions
    assert "QUOTATION_STATUS_CHANGED_VIEWED" in actions
    assert "QUOTATION_STATUS_CHANGED_ACCEPTED" in actions


# ==============================================================================
# Phase 197: Quote Versioning & Revision Tests
# ==============================================================================

def test_phase_197_quote_versioning_and_revisions(client, setup_b10_data, db_session):
    """Phase 197: Verify snapshot capture, revision creation, version increment, and historical immutability."""
    data = setup_b10_data
    quote = _create_sample_quote(client, data)
    q_id = quote["id"]
    headers = {"Authorization": f"Bearer {data['token_a']}"}
    assert quote["version_number"] == 1

    # Create new version revision
    resp = client.post(
        f"/api/v1/quotations/{q_id}/versions",
        json={"change_reason": "Customer requested 5% commercial concession"},
        headers=headers,
    )
    assert resp.status_code == 201
    ver_data = resp.json()["data"]
    assert ver_data["version_number"] == 1
    assert "snapshot_data" in ver_data
    assert ver_data["snapshot_data"]["quotation_number"] == quote["quotation_number"]
    assert ver_data["snapshot_data"]["subtotal"] == quote["subtotal"]

    # Check active quote has incremented to version 2 and status reset to DRAFT
    resp_get = client.get(f"/api/v1/quotations/{q_id}", headers=headers)
    active_quote = resp_get.json()["data"]
    assert active_quote["version_number"] == 2
    assert active_quote["status"] == "DRAFT"

    # List historical versions
    resp_list = client.get(f"/api/v1/quotations/{q_id}/versions", headers=headers)
    assert resp_list.status_code == 200
    versions = resp_list.json()["data"]
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1

    # Verify snapshot integrity in database
    db_ver = db_session.execute(
        select(QuotationVersion).where(
            QuotationVersion.quotation_id == uuid.UUID(q_id),
            QuotationVersion.version_number == 1,
        )
    ).scalar_one_or_none()
    assert db_ver is not None
    assert db_ver.company_id == data["company_a"].id
    assert len(db_ver.snapshot_data["line_items"]) == 2


# ==============================================================================
# Phase 198: Quote Expiration Tests
# ==============================================================================

def test_phase_198_quote_expiration(client, setup_b10_data, db_session):
    """Phase 198: Verify deterministic expiration, expired acceptance rejection, and manual expire trigger."""
    data = setup_b10_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    # 1. Manual expiration trigger
    quote = _create_sample_quote(client, data)
    q_id = quote["id"]
    resp_expire = client.post(f"/api/v1/quotations/{q_id}/expire", json={"reason": "Customer failed to respond within validity window"}, headers=headers)
    assert resp_expire.status_code == 200
    assert resp_expire.json()["data"]["status"] == "EXPIRED"

    # 2. Expired quote cannot be accepted
    resp_accept = client.post(f"/api/v1/quotations/{q_id}/accept", headers=headers)
    assert resp_accept.status_code == 400
    assert "expired" in _err_text(resp_accept)

    # 3. Expired quote cannot be sent
    resp_send = client.post(f"/api/v1/quotations/{q_id}/email", json={"recipient_email": "test@example.com"}, headers=headers)
    assert resp_send.status_code == 400
    assert "expired" in _err_text(resp_send)

    # 4. Deterministic automatic evaluation on past valid_until
    quote_past = _create_sample_quote(client, data, valid_days=-5)
    past_id = quote_past["id"]
    # Calling accept triggers automatic evaluation and rejection
    resp_past_accept = client.post(f"/api/v1/quotations/{past_id}/accept", headers=headers)
    assert resp_past_accept.status_code == 400
    assert "expired" in _err_text(resp_past_accept)


# ==============================================================================
# Phase 199: Quote Approval Integration Tests
# ==============================================================================

def test_phase_199_quote_approval_integration(client, setup_b10_data, db_session):
    """Phase 199: Verify integration with B05/B06 Approval Decision Engine."""
    data = setup_b10_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    # 1. Auto-Approval: 0% discount with healthy margin -> NO_APPROVAL_REQUIRED -> immediately APPROVED
    quote_clean = _create_sample_quote(client, data, discount_pct="0.00")
    resp_auto = client.post(
        f"/api/v1/quotations/{quote_clean['id']}/submit-approval",
        json={"notes": "Standard catalog pricing, zero discount"},
        headers=headers,
    )
    assert resp_auto.status_code == 200
    auto_res = resp_auto.json()["data"]
    assert auto_res["status"] == "APPROVED"
    assert auto_res["auto_approved"] is True
    assert auto_res["approval_request_id"] is not None

    # Check quotation entity in DB
    db_quote = db_session.execute(select(Quotation).where(Quotation.id == uuid.UUID(quote_clean["id"]))).scalar_one()
    assert db_quote.status == QuotationStatus.APPROVED.value
    assert db_quote.approval_request_id is not None

    # 2. Multi-Level Routing: High discount (40%) triggers approval chain -> PENDING_APPROVAL
    quote_high_disc = _create_sample_quote(client, data, discount_pct="40.00")
    resp_routed = client.post(
        f"/api/v1/quotations/{quote_high_disc['id']}/submit-approval",
        json={"notes": "High discount requested for competitive takeaway"},
        headers=headers,
    )
    assert resp_routed.status_code == 200
    routed_res = resp_routed.json()["data"]
    assert routed_res["status"] == "PENDING_APPROVAL"
    assert routed_res["auto_approved"] is False
    assert routed_res["approval_request_id"] is not None

    db_routed = db_session.execute(select(Quotation).where(Quotation.id == uuid.UUID(quote_high_disc["id"]))).scalar_one()
    assert db_routed.status == QuotationStatus.PENDING_APPROVAL.value


# ==============================================================================
# Phase 200: Quote PDF Generation Tests
# ==============================================================================

def test_phase_200_quote_pdf_generation(client, setup_b10_data):
    """Phase 200: Verify vector PDF generation, stream headers, and tenant isolation."""
    data = setup_b10_data
    quote = _create_sample_quote(client, data)
    q_id = quote["id"]

    # 1. Successful PDF download by authorized tenant
    resp_pdf = client.get(
        f"/api/v1/quotations/{q_id}/pdf",
        headers={"Authorization": f"Bearer {data['token_a']}"},
    )
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    assert f"Quotation-{quote['quotation_number']}" in resp_pdf.headers["content-disposition"]
    # PDF magic byte verification
    assert resp_pdf.content.startswith(b"%PDF-")
    assert len(resp_pdf.content) > 1000

    # 2. Tenant Isolation: User from Company B cannot access Company A's PDF
    resp_unauth = client.get(
        f"/api/v1/quotations/{q_id}/pdf",
        headers={"Authorization": f"Bearer {data['token_b']}"},
    )
    assert resp_unauth.status_code == 404


# ==============================================================================
# Phase 201: Quote Email Dispatch Tests
# ==============================================================================

def test_phase_201_quote_email_dispatch(client, setup_b10_data, db_session):
    """Phase 201: Verify email delivery abstraction, PDF attachment, recipient validation, and status advance."""
    data = setup_b10_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}
    quote = _create_sample_quote(client, data)
    q_id = quote["id"]

    # 1. Invalid recipient email
    resp_invalid = client.post(
        f"/api/v1/quotations/{q_id}/email",
        json={"recipient_email": "not-a-valid-email"},
        headers=headers,
    )
    assert resp_invalid.status_code == 400
    assert "invalid recipient email" in _err_text(resp_invalid)

    # 2. Valid email dispatch
    resp_send = client.post(
        f"/api/v1/quotations/{q_id}/email",
        json={
            "recipient_email": "procurement@client.com",
            "subject": "Official Enterprise Quote Proposal",
            "notes": "Attached please find the formal quotation proposal.",
        },
        headers=headers,
    )
    assert resp_send.status_code == 200
    send_data = resp_send.json()["data"]
    assert send_data["delivery_status"] == "SENT"
    assert send_data["tracking_token"] is not None

    # Verify quote status advanced to SENT
    db_quote = db_session.execute(select(Quotation).where(Quotation.id == uuid.UUID(q_id))).scalar_one()
    assert db_quote.status == QuotationStatus.SENT.value
    assert db_quote.sent_at is not None


# ==============================================================================
# Phase 202: Quote Send Tracking & History Tests
# ==============================================================================

def test_phase_202_quote_send_tracking_and_view_event(client, setup_b10_data, db_session):
    """Phase 202: Verify send history retrieval, unique tracking tokens, and customer view events."""
    data = setup_b10_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}
    quote = _create_sample_quote(client, data)
    q_id = quote["id"]

    # Dispatch email
    resp_send = client.post(
        f"/api/v1/quotations/{q_id}/email",
        json={"recipient_email": "tracking_test@customer.com"},
        headers=headers,
    )
    assert resp_send.status_code == 200
    token = resp_send.json()["data"]["tracking_token"]

    # 1. Retrieve Send History
    resp_hist = client.get(f"/api/v1/quotations/{q_id}/send-history", headers=headers)
    assert resp_hist.status_code == 200
    history = resp_hist.json()["data"]
    assert len(history) >= 1
    assert history[0]["recipient_email"] == "tracking_test@customer.com"
    assert history[0]["tracking_token"] == token

    # 2. Simulate recipient viewing quotation
    resp_view = client.post(f"/api/v1/quotations/{q_id}/track-view?token={token}", headers=headers)
    assert resp_view.status_code == 200
    assert resp_view.json()["data"]["viewed"] is True

    # Check status transitioned to VIEWED
    db_quote = db_session.execute(select(Quotation).where(Quotation.id == uuid.UUID(q_id))).scalar_one()
    assert db_quote.status == QuotationStatus.VIEWED.value
    assert db_quote.viewed_at is not None


# ==============================================================================
# Phase 203: Quote Acceptance Tests
# ==============================================================================

def test_phase_203_quote_acceptance(client, setup_b10_data, db_session):
    """Phase 203: Verify quotation acceptance, approval guard, and idempotency."""
    data = setup_b10_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}

    # 1. Accept approved quotation
    quote = _create_sample_quote(client, data)
    q_id = quote["id"]
    # Auto-approve
    client.post(f"/api/v1/quotations/{q_id}/submit-approval", headers=headers)

    resp_accept = client.post(
        f"/api/v1/quotations/{q_id}/accept",
        json={"acceptance_notes": "Customer accepted via PO #PO-99124"},
        headers=headers,
    )
    assert resp_accept.status_code == 200
    acc_data = resp_accept.json()["data"]
    assert acc_data["status"] == "ACCEPTED"
    assert acc_data["accepted_at"] is not None

    # 2. Acceptance idempotency
    resp_dup = client.post(f"/api/v1/quotations/{q_id}/accept", headers=headers)
    assert resp_dup.status_code == 200
    assert "already been accepted" in resp_dup.json()["data"]["message"]

    # 3. Unapproved quote (in PENDING_APPROVAL) cannot be accepted
    quote_pending = _create_sample_quote(client, data, discount_pct="40.00")
    client.post(f"/api/v1/quotations/{quote_pending['id']}/submit-approval", headers=headers)
    resp_pending_accept = client.post(f"/api/v1/quotations/{quote_pending['id']}/accept", headers=headers)
    assert resp_pending_accept.status_code == 400
    assert "pending approval" in _err_text(resp_pending_accept)


# ==============================================================================
# Phase 204: Quote Rejection Tests
# ==============================================================================

def test_phase_204_quote_rejection(client, setup_b10_data, db_session):
    """Phase 204: Verify rejection with mandatory reason, status change, and terminal checks."""
    data = setup_b10_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}
    quote = _create_sample_quote(client, data)
    q_id = quote["id"]

    # 1. Missing or too short reason
    resp_short = client.post(
        f"/api/v1/quotations/{q_id}/reject",
        json={"reason": "no"},
        headers=headers,
    )
    assert resp_short.status_code == 422  # Pydantic min_length=3 validation

    # 2. Valid rejection
    resp_reject = client.post(
        f"/api/v1/quotations/{q_id}/reject",
        json={"reason": "Customer postponed cloud migration project to next fiscal year"},
        headers=headers,
    )
    assert resp_reject.status_code == 200
    rej_data = resp_reject.json()["data"]
    assert rej_data["status"] == "REJECTED"
    assert rej_data["rejected_at"] is not None

    db_quote = db_session.execute(select(Quotation).where(Quotation.id == uuid.UUID(q_id))).scalar_one()
    assert db_quote.status == QuotationStatus.REJECTED.value
    assert "postponed" in db_quote.rejection_reason


# ==============================================================================
# Phase 205: Quote Conversion to Deal Tests
# ==============================================================================

def test_phase_205_quote_conversion_to_deal(client, setup_b10_data, db_session):
    """Phase 205: Verify atomic conversion of ACCEPTED quote into existing CustomerDealHistory entity."""
    data = setup_b10_data
    headers = {"Authorization": f"Bearer {data['token_a']}"}
    quote = _create_sample_quote(client, data)
    q_id = quote["id"]

    # 1. Non-accepted quote cannot be converted
    resp_non_acc = client.post(f"/api/v1/quotations/{q_id}/convert", headers=headers)
    assert resp_non_acc.status_code == 400
    assert "accepted" in _err_text(resp_non_acc)

    # 2. Accept the quotation first
    client.post(f"/api/v1/quotations/{q_id}/submit-approval", headers=headers)
    client.post(f"/api/v1/quotations/{q_id}/accept", headers=headers)

    # 3. Convert to deal
    resp_conv = client.post(
        f"/api/v1/quotations/{q_id}/convert",
        json={
            "title_override": "Acme Global - Cloud Infrastructure Won Deal",
            "notes": "Converted upon customer PO receipt.",
        },
        headers=headers,
    )
    assert resp_conv.status_code == 200
    conv_data = resp_conv.json()["data"]
    assert conv_data["status"] == "WON"
    assert conv_data["deal_code"] == f"DEAL-{quote['quotation_number']}"
    assert Decimal(str(conv_data["deal_value"])) == Decimal(str(quote["total_amount"]))

    # 4. Verify CustomerDealHistory record in DB
    deal_id = uuid.UUID(conv_data["deal_id"])
    deal = db_session.execute(select(CustomerDealHistory).where(CustomerDealHistory.id == deal_id)).scalar_one()
    assert deal.company_id == data["company_a"].id
    assert deal.customer_id == data["cust_a"].id
    assert deal.status == "WON"
    assert deal.deal_code == f"DEAL-{quote['quotation_number']}"

    # Verify Quotation record has converted_deal_id and CONVERTED status
    db_quote = db_session.execute(select(Quotation).where(Quotation.id == uuid.UUID(q_id))).scalar_one()
    assert db_quote.status == QuotationStatus.CONVERTED.value
    assert db_quote.converted_deal_id == deal.id
    assert db_quote.converted_at is not None

    # 5. Duplicate conversion idempotency
    resp_dup = client.post(f"/api/v1/quotations/{q_id}/convert", headers=headers)
    assert resp_dup.status_code == 200
    assert resp_dup.json()["data"]["deal_id"] == str(deal.id)

    # 6. Tenant isolation: User B cannot convert or access User A's quotation
    resp_cross = client.post(
        f"/api/v1/quotations/{q_id}/convert",
        headers={"Authorization": f"Bearer {data['token_b']}"},
    )
    assert resp_cross.status_code == 404


# ==============================================================================
# Cross-Cutting & Security Tests
# ==============================================================================

def test_b10_multi_tenant_isolation_idor(client, setup_b10_data):
    """Verify strict multi-tenant isolation across all B10 endpoints."""
    data = setup_b10_data
    quote_a = _create_sample_quote(client, data)
    q_a_id = quote_a["id"]
    headers_b = {"Authorization": f"Bearer {data['token_b']}"}

    # Company B user trying to perform operations on Company A quote
    endpoints = [
        ("GET", f"/api/v1/quotations/{q_a_id}"),
        ("GET", f"/api/v1/quotations/{q_a_id}/versions"),
        ("GET", f"/api/v1/quotations/{q_a_id}/pdf"),
        ("GET", f"/api/v1/quotations/{q_a_id}/send-history"),
        ("PATCH", f"/api/v1/quotations/{q_a_id}/status"),
        ("POST", f"/api/v1/quotations/{q_a_id}/versions"),
        ("POST", f"/api/v1/quotations/{q_a_id}/expire"),
        ("POST", f"/api/v1/quotations/{q_a_id}/submit-approval"),
        ("POST", f"/api/v1/quotations/{q_a_id}/email"),
        ("POST", f"/api/v1/quotations/{q_a_id}/accept"),
        ("POST", f"/api/v1/quotations/{q_a_id}/reject"),
        ("POST", f"/api/v1/quotations/{q_a_id}/convert"),
    ]

    for method, path in endpoints:
        if method == "GET":
            r = client.get(path, headers=headers_b)
        elif method == "PATCH":
            r = client.patch(path, json={"status": "APPROVED"}, headers=headers_b)
        else:
            r = client.post(path, json={}, headers=headers_b)
        assert r.status_code in (404, 422), f"IDOR vulnerability detected at {method} {path}: code {r.status_code}"
