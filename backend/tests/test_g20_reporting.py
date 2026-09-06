import pytest
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.core.jwt import create_access_token
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.models.role import Role
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.deal import DealStage
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.models.applied_discount import AppliedDiscount
from app.models.approval_execution import ApprovalRequest
from app.models.deal_health import DealHealthSnapshot, DealHealthClassification
from app.models.billing import Invoice, InvoiceStatus, PaymentStatus
from app.models.reporting import ScheduledReport, ReportExecution
from app.reporting.schemas import ReportFilterParams
from app.reporting.services import ReportingService
from app.reporting.exporters import ReportExporter
from app.reporting.scheduling import SchedulingService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def reporting_setup(db_session):
    # Company A (Primary)
    comp_a = Company(id=uuid.uuid4(), name=f"Rep Corp A {uuid.uuid4().hex[:6]}")
    comp_b = Company(id=uuid.uuid4(), name=f"Rep Corp B {uuid.uuid4().hex[:6]}")
    db_session.add_all([comp_a, comp_b])
    db_session.commit()

    role_admin = db_session.query(Role).filter_by(name="ADMIN").first()
    if not role_admin:
        role_admin = Role(id=uuid.uuid4(), name="ADMIN")
        db_session.add(role_admin)
        db_session.commit()

    user_a = User(
        id=uuid.uuid4(),
        company_id=comp_a.id,
        email=f"rep_a_{uuid.uuid4().hex[:6]}@example.com",
        first_name="Report",
        last_name="Admin",
        password_hash="fakehash",
        is_active=True,
    )
    user_a.roles.append(role_admin)

    user_b = User(
        id=uuid.uuid4(),
        company_id=comp_b.id,
        email=f"rep_b_{uuid.uuid4().hex[:6]}@example.com",
        first_name="Other",
        last_name="Admin",
        password_hash="fakehash",
        is_active=True,
    )
    user_b.roles.append(role_admin)
    db_session.add_all([user_a, user_b])
    db_session.commit()

    # Create test business data for Company A
    cust_a = Customer(
        id=uuid.uuid4(),
        company_id=comp_a.id,
        name="Acme Global",
        customer_code=f"ACM_{uuid.uuid4().hex[:4]}",
        is_active=True,
    )
    db_session.add(cust_a)
    db_session.commit()

    deal_1 = CustomerDealHistory(
        id=uuid.uuid4(),
        company_id=comp_a.id,
        customer_id=cust_a.id,
        deal_code=f"D-101-{uuid.uuid4().hex[:4]}",
        title="Enterprise Cloud License",
        deal_value=Decimal("50000.00"),
        gross_profit=Decimal("15000.00"),
        margin_percentage=Decimal("30.00"),
        stage=DealStage.CLOSED_WON.value,
        probability=100,
        expected_revenue=Decimal("50000.00"),
    )
    deal_2 = CustomerDealHistory(
        id=uuid.uuid4(),
        company_id=comp_a.id,
        customer_id=cust_a.id,
        deal_code=f"D-102-{uuid.uuid4().hex[:4]}",
        title="Standard Onboarding",
        deal_value=Decimal("10000.00"),
        gross_profit=Decimal("2000.00"),
        margin_percentage=Decimal("20.00"),
        stage=DealStage.NEW.value,
        probability=40,
        expected_revenue=Decimal("4000.00"),
    )
    db_session.add_all([deal_1, deal_2])

    prod_1 = Product(
        id=uuid.uuid4(),
        name="Industrial Sensor X",
        sku=f"SKU-{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db_session.add(prod_1)
    db_session.commit()

    wh_1 = Warehouse(
        id=uuid.uuid4(),
        company_id=comp_a.id,
        name="Main Hub",
        code=f"WH_{uuid.uuid4().hex[:4]}",
        is_active=True,
    )
    db_session.add(wh_1)
    db_session.commit()

    stock_1 = WarehouseStock(
        id=uuid.uuid4(),
        warehouse_id=wh_1.id,
        product_id=prod_1.id,
        quantity=100,
        reserved_quantity=20,
    )
    db_session.add(stock_1)

    app_req = ApprovalRequest(
        id=uuid.uuid4(),
        company_id=comp_a.id,
        deal_reference=deal_1.deal_code,
        deal_value=Decimal("50000.00"),
        selling_price=Decimal("50000.00"),
        unit_cost=Decimal("35000.00"),
        requested_discount_pct=Decimal("15.00"),
        status="APPROVED",
        required_level="L1",
        required_chain_type="STANDARD",
        current_step_number=1,
        total_steps=1,
        blended_risk_score=25.0,
        blended_risk_classification="LOW",
        routing_metadata={},
        submitted_by_id=user_a.id,
    )
    db_session.add(app_req)

    dh_snap = DealHealthSnapshot(
        id=uuid.uuid4(),
        company_id=comp_a.id,
        deal_id=deal_1.id,
        health_score=Decimal("85.00"),
        classification=DealHealthClassification.HEALTHY.value,
        conversion_probability=Decimal("0.8500"),
        stall_probability=Decimal("0.1000"),
        delay_probability=Decimal("0.0500"),
        anomaly_detected=False,
        anomaly_score=Decimal("10.00"),
    )
    db_session.add(dh_snap)

    inv_1 = Invoice(
        id=uuid.uuid4(),
        company_id=comp_a.id,
        customer_id=cust_a.id,
        invoice_number=f"INV-{uuid.uuid4().hex[:6]}",
        issue_date=datetime.now(timezone.utc).date(),
        due_date=datetime.now(timezone.utc).date(),
        total_amount=Decimal("50000.00"),
        amount_paid=Decimal("50000.00"),
        amount_due=Decimal("0.00"),
        status=InvoiceStatus.PAID.value,
        payment_status=PaymentStatus.PAID.value,
    )
    db_session.add(inv_1)
    db_session.commit()

    token_a = create_access_token(subject=str(user_a.id))
    token_b = create_access_token(subject=str(user_b.id))

    return {
        "comp_a": comp_a,
        "comp_b": comp_b,
        "user_a": user_a,
        "user_b": user_b,
        "token_a": token_a,
        "token_b": token_b,
    }


def test_phase_353_sales_report(reporting_setup, db_session):
    """Phase 353: Verify sales reporting aggregation and tenant isolation."""
    comp_a = reporting_setup["comp_a"]
    filters = ReportFilterParams()
    res = ReportingService.get_sales_report(db_session, comp_a.id, filters)
    assert res.summary.total_deals == 2
    assert res.summary.won_deals == 1
    assert res.summary.win_rate == 50.0
    assert res.summary.total_pipeline_value == Decimal("60000.00")
    assert res.summary.total_won_revenue == Decimal("50000.00")
    assert len(res.items) == 2


def test_phase_354_customer_report(reporting_setup, db_session):
    """Phase 354: Verify customer reporting aggregation."""
    comp_a = reporting_setup["comp_a"]
    filters = ReportFilterParams()
    res = ReportingService.get_customer_report(db_session, comp_a.id, filters)
    assert res.summary.total_customers >= 1
    assert res.summary.active_customers >= 1
    assert len(res.items) >= 1
    assert res.items[0].customer_name == "Acme Global"


def test_phase_356_inventory_report(reporting_setup, db_session):
    """Phase 356: Verify inventory reporting and ATP."""
    comp_a = reporting_setup["comp_a"]
    filters = ReportFilterParams()
    res = ReportingService.get_inventory_report(db_session, comp_a.id, filters)
    assert res.summary.total_warehouses >= 1
    assert res.summary.total_physical_quantity == 100
    assert res.summary.total_reserved_quantity == 20
    assert res.summary.total_atp_quantity == 80


def test_phase_358_approval_report(reporting_setup, db_session):
    """Phase 358: Verify approval reporting."""
    comp_a = reporting_setup["comp_a"]
    filters = ReportFilterParams()
    res = ReportingService.get_approval_report(db_session, comp_a.id, filters)
    assert res.summary.total_requests >= 1
    assert res.summary.approved_requests >= 1
    assert res.summary.approval_rate == 100.0


def test_phase_359_deal_health_report(reporting_setup, db_session):
    """Phase 359: Verify deal health reporting."""
    comp_a = reporting_setup["comp_a"]
    filters = ReportFilterParams()
    res = ReportingService.get_deal_health_report(db_session, comp_a.id, filters)
    assert res.summary.total_monitored_deals >= 1
    assert res.summary.healthy_deals_count >= 1
    assert res.summary.average_health_score == 85.0


def test_phase_360_361_revenue_and_conversion_analytics(reporting_setup, db_session):
    """Phases 360 & 361: Verify revenue & conversion analytics."""
    comp_a = reporting_setup["comp_a"]
    filters = ReportFilterParams()
    rev = ReportingService.get_revenue_analytics(db_session, comp_a.id, filters)
    assert rev.total_revenue == Decimal("50000.00")
    assert rev.collected_revenue == Decimal("50000.00")
    assert len(rev.time_series) >= 1

    conv = ReportingService.get_conversion_analytics(db_session, comp_a.id, filters)
    assert len(conv.funnel) == 4
    assert conv.deal_to_won_rate == 50.0  # 1 won out of 2 deals


def test_phase_368_executive_dashboard(reporting_setup, db_session):
    """Phase 368: Consolidated executive dashboard analytics."""
    comp_a = reporting_setup["comp_a"]
    filters = ReportFilterParams()
    dash = ReportingService.get_executive_dashboard(db_session, comp_a.id, filters)
    assert dash.sales_summary.total_deals == 2
    assert dash.revenue_summary.total_revenue == Decimal("50000.00")
    assert dash.inventory_summary.total_physical_quantity == 100
    assert dash.approval_summary.total_requests >= 1


def test_phase_369_export_csv_and_scheduling(reporting_setup, db_session):
    """Phase 369: Verify CSV exporter and scheduled report execution."""
    client = TestClient(app)
    headers_a = {"Authorization": f"Bearer {reporting_setup['token_a']}"}

    # CSV export endpoint
    resp = client.get("/api/v1/reports/sales/export?format=csv", headers=headers_a)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "deal_code,deal_name" in resp.text

    # Schedule creation
    sched_resp = client.post(
        "/api/v1/reports/schedules",
        headers=headers_a,
        json={
            "name": "Weekly Executive Sales Summary",
            "report_type": "sales",
            "frequency": "WEEKLY",
            "format": "CSV",
        },
    )
    assert sched_resp.status_code == 200
    sched_data = sched_resp.json()
    assert sched_data["name"] == "Weekly Executive Sales Summary"
    sched_id = sched_data["id"]

    # Trigger run
    run_resp = client.post(f"/api/v1/reports/schedules/{sched_id}/run", headers=headers_a)
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["row_count"] == 2


def test_phase_370_multi_tenant_security_isolation(reporting_setup, db_session):
    """Phase 370: Ensure Company B cannot see Company A's data or reports."""
    client = TestClient(app)
    headers_b = {"Authorization": f"Bearer {reporting_setup['token_b']}"}

    # Company B queries sales report
    resp_b = client.get("/api/v1/reports/sales", headers=headers_b)
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert data_b["summary"]["total_deals"] == 0
    assert len(data_b["items"]) == 0

    # Company B queries inventory report
    resp_inv_b = client.get("/api/v1/reports/inventory", headers=headers_b)
    assert resp_inv_b.status_code == 200
    assert resp_inv_b.json()["summary"]["total_stock_items"] == 0
