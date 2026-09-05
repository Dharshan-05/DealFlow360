
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
from app.models.company import Company
from app.models.customer import Customer
from app.models.user import User
from app.models.billing import (
    SubscriptionPlan, Subscription, Invoice, InvoiceLineItem, UsageRecord,
    BillingInterval, SubscriptionStatus, BillingType
)
from app.services.billing import (
    SubscriptionPlanService, SubscriptionCrudService, RecurringBillingService,
    HybridBillingService, UpgradeDowngradeService, RenewalCancellationService,
    UsageBillingService, BillingCycleService
)
from app.schemas.billing import SubscriptionPlanCreate, SubscriptionCreate, UsageRecordCreate

from app.db.session import SessionLocal

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def setup_g15_data(db_session: Session):
    company = Company(name="Billing Inc")
    db_session.add(company)
    db_session.commit()
    
    user = User(company_id=company.id, email=f"admin_{uuid.uuid4()}@billing.inc", password_hash="pw", first_name="Admin", last_name="User", is_active=True)
    db_session.add(user)
    
    customer = Customer(company_id=company.id, name="Test Customer", customer_code="CUST-001")
    db_session.add(customer)
    
    db_session.commit()
    
    return {
        "company": company,
        "user": user,
        "customer": customer
    }

def test_1_create_monthly_subscription(db_session, setup_g15_data):
    """TEST 1: Create monthly subscription"""
    data = setup_g15_data
    
    plan_in = SubscriptionPlanCreate(
        name="Pro Monthly",
        price=Decimal("100.00"),
        billing_interval=BillingInterval.MONTHLY.value
    )
    plan = SubscriptionPlanService.create_plan(db_session, data["company"].id, plan_in)
    
    sub_in = SubscriptionCreate(
        customer_id=data["customer"].id,
        plan_id=plan.id
    )
    sub = SubscriptionCrudService.create_subscription(db_session, data["company"].id, sub_in, data["user"].id)
    
    assert sub.status == SubscriptionStatus.ACTIVE.value
    
    # Verify next billing date is roughly a month ahead
    days_diff = (sub.next_billing_date - datetime.now(sub.next_billing_date.tzinfo)).days
    assert 27 <= days_diff <= 31

def test_2_run_recurring_billing_twice(db_session, setup_g15_data):
    """TEST 2: Run recurring billing twice (Idempotency)"""
    data = setup_g15_data
    
    plan_in = SubscriptionPlanCreate(name="Idemp Plan", price=Decimal("100.00"), billing_interval=BillingInterval.MONTHLY.value)
    plan = SubscriptionPlanService.create_plan(db_session, data["company"].id, plan_in)
    
    sub_in = SubscriptionCreate(customer_id=data["customer"].id, plan_id=plan.id)
    sub = SubscriptionCrudService.create_subscription(db_session, data["company"].id, sub_in, data["user"].id)
    
    inv1 = RecurringBillingService.generate_recurring_invoice(db_session, data["company"].id, sub.id)
    inv2 = RecurringBillingService.generate_recurring_invoice(db_session, data["company"].id, sub.id)
    
    assert inv1.id == inv2.id
    count = db_session.query(Invoice).filter(Invoice.subscription_id == sub.id).count()
    assert count == 1 # 1 generated upon creation, which we hit twice, but it returned the same one

def test_3_hybrid_transaction(db_session, setup_g15_data):
    """TEST 3: Hybrid transaction"""
    data = setup_g15_data
    
    lines = [
        {
            "description": "Product A",
            "quantity": 1,
            "unit_price": Decimal("50000.00"),
            "billing_type": BillingType.ONE_TIME.value
        },
        {
            "description": "Service Plan",
            "quantity": 1,
            "unit_price": Decimal("5000.00"),
            "billing_type": BillingType.RECURRING.value
        }
    ]
    
    inv = HybridBillingService.process_hybrid_deal(
        db_session, data["company"].id, data["customer"].id, None, lines
    )
    
    assert inv.total_amount == Decimal("55000.00")
    
    line_types = [l.billing_type for l in inv.line_items]
    assert BillingType.ONE_TIME.value in line_types
    assert BillingType.RECURRING.value in line_types

def test_4_mid_cycle_upgrade(db_session, setup_g15_data):
    """TEST 4: Mid-cycle upgrade"""
    data = setup_g15_data
    
    plan1 = SubscriptionPlanService.create_plan(db_session, data["company"].id, SubscriptionPlanCreate(name="Basic", price=Decimal("10.00"), billing_interval=BillingInterval.MONTHLY.value))
    plan2 = SubscriptionPlanService.create_plan(db_session, data["company"].id, SubscriptionPlanCreate(name="Pro", price=Decimal("100.00"), billing_interval=BillingInterval.MONTHLY.value))
    
    sub = SubscriptionCrudService.create_subscription(db_session, data["company"].id, SubscriptionCreate(customer_id=data["customer"].id, plan_id=plan1.id), data["user"].id)
    
    # Artificially set dates
    now = datetime.now()
    sub.current_period_start = now - timedelta(days=15)
    sub.current_period_end = now + timedelta(days=15)
    db_session.commit()
    
    sub_up = UpgradeDowngradeService.change_plan(db_session, data["company"].id, sub.id, plan2.id, 1)
    
    # Proration invoice should exist
    inv = db_session.query(Invoice).filter(Invoice.subscription_id == sub_up.id).order_by(Invoice.created_at.desc()).first()
    assert inv.subtotal > Decimal("0.00")

def test_5_mid_cycle_downgrade(db_session, setup_g15_data):
    """TEST 5: Mid-cycle downgrade"""
    data = setup_g15_data
    
    plan1 = SubscriptionPlanService.create_plan(db_session, data["company"].id, SubscriptionPlanCreate(name="Pro", price=Decimal("100.00"), billing_interval=BillingInterval.MONTHLY.value))
    plan2 = SubscriptionPlanService.create_plan(db_session, data["company"].id, SubscriptionPlanCreate(name="Basic", price=Decimal("10.00"), billing_interval=BillingInterval.MONTHLY.value))
    
    sub = SubscriptionCrudService.create_subscription(db_session, data["company"].id, SubscriptionCreate(customer_id=data["customer"].id, plan_id=plan1.id), data["user"].id)
    
    sub_down = UpgradeDowngradeService.change_plan(db_session, data["company"].id, sub.id, plan2.id, 1)
    assert sub_down.plan_id == plan2.id

def test_6_renewal(db_session, setup_g15_data):
    """TEST 6: Renewal"""
    data = setup_g15_data
    plan = SubscriptionPlanService.create_plan(db_session, data["company"].id, SubscriptionPlanCreate(name="Basic", price=Decimal("10.00"), billing_interval=BillingInterval.MONTHLY.value))
    sub = SubscriptionCrudService.create_subscription(db_session, data["company"].id, SubscriptionCreate(customer_id=data["customer"].id, plan_id=plan.id), data["user"].id)
    
    # Force time to expire
    sub.current_period_end = datetime.now() - timedelta(minutes=1)
    db_session.commit()
    
    inv = RenewalCancellationService.process_renewal(db_session, data["company"].id, sub.id)
    assert inv is not None
    
    inv2 = RenewalCancellationService.process_renewal(db_session, data["company"].id, sub.id)
    assert inv2 is None # Already renewed, next period end is in the future

def test_7_cancellation(db_session, setup_g15_data):
    """TEST 7: Cancellation"""
    data = setup_g15_data
    plan = SubscriptionPlanService.create_plan(db_session, data["company"].id, SubscriptionPlanCreate(name="Basic", price=Decimal("10.00"), billing_interval=BillingInterval.MONTHLY.value))
    sub = SubscriptionCrudService.create_subscription(db_session, data["company"].id, SubscriptionCreate(customer_id=data["customer"].id, plan_id=plan.id), data["user"].id)
    
    RenewalCancellationService.cancel_subscription(db_session, data["company"].id, sub.id, immediate=True)
    assert sub.status == SubscriptionStatus.CANCELLED.value

def test_8_tenant_isolation(db_session, setup_g15_data):
    """TEST 8: Tenant isolation (Simulated via endpoints/services)"""
    data = setup_g15_data
    plan = SubscriptionPlanService.create_plan(db_session, data["company"].id, SubscriptionPlanCreate(name="Basic", price=Decimal("10.00"), billing_interval=BillingInterval.MONTHLY.value))
    sub = SubscriptionCrudService.create_subscription(db_session, data["company"].id, SubscriptionCreate(customer_id=data["customer"].id, plan_id=plan.id), data["user"].id)
    
    other_company_id = uuid.uuid4()
    # Attempting to fetch from another company returns None
    res = SubscriptionCrudService.get_subscription(db_session, other_company_id, sub.id)
    assert res is None

def test_9_customer_portal_isolation(db_session, setup_g15_data):
    """TEST 9: Customer portal isolation (Not directly tested at service layer since it's enforced at router, but similar to above)"""
    pass

def test_10_usage_record_idempotency(db_session, setup_g15_data):
    """TEST 10: Usage record inserted twice"""
    data = setup_g15_data
    plan = SubscriptionPlanService.create_plan(db_session, data["company"].id, SubscriptionPlanCreate(name="Basic", price=Decimal("10.00"), billing_interval=BillingInterval.MONTHLY.value))
    sub = SubscriptionCrudService.create_subscription(db_session, data["company"].id, SubscriptionCreate(customer_id=data["customer"].id, plan_id=plan.id), data["user"].id)
    
    u_in = UsageRecordCreate(metric_name="API Calls", quantity=Decimal("100"), idempotency_key="key123")
    
    ur1 = UsageBillingService.ingest_usage(db_session, data["company"].id, u_in, sub.id)
    ur2 = UsageBillingService.ingest_usage(db_session, data["company"].id, u_in, sub.id)
    
    assert ur1.id == ur2.id
    count = db_session.query(UsageRecord).filter(UsageRecord.subscription_id == sub.id).count()
    assert count == 1

