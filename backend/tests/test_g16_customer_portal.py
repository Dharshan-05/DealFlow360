import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.models.customer import Customer
from app.models.role import Role
from app.models.company import Company
from app.models.portal import CustomerComment, NegotiationRequest, NegotiationHistory
from app.models.quotation import Quotation
from app.models.quotation_line_item import QuotationLineItem
from app.models.billing import Invoice, PaymentStatus
from app.main import app

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def setup_data(db_session):
    # Setup test company
    comp = Company(name=f"Comp-{uuid.uuid4().hex[:4]}")
    db_session.add(comp)
    db_session.commit()
    db_session.refresh(comp)

    # Setup customer
    cust = Customer(
        company_id=comp.id, 
        customer_code=f"C-{uuid.uuid4().hex[:4]}", 
        name="Test Cust", 
        email=f"test_{uuid.uuid4()}@example.com", 
        is_active=True
    )
    db_session.add(cust)
    
    # Internal user as author
    internal_user = User(
        email=f"author_{uuid.uuid4()}@example.com",
        first_name="Auth", last_name="User",
        company_id=comp.id,
        is_active=True
    )
    db_session.add(internal_user)
    db_session.commit()
    db_session.refresh(cust)
    db_session.refresh(internal_user)

    return comp, cust, internal_user

# Helper to create a customer portal user
def create_portal_user(db: Session, company: Company, customer: Customer) -> User:
    role = db.query(Role).filter_by(name="Customer Portal").first()
    if not role:
        role = Role(name="Customer Portal", description="Customer Portal Access")
        db.add(role)
        db.commit()

    user = User(
        email=f"portal_{uuid.uuid4()}@example.com",
        first_name="Portal",
        last_name="User",
        company_id=company.id,
        customer_id=customer.id,
        password_hash="test",
        is_active=True
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    return user

def create_mock_quote(db: Session, company: Company, customer: Customer, author: User, status: str = "SENT") -> Quotation:
    q = Quotation(
        quotation_number=f"Q-{uuid.uuid4().hex[:8]}",
        company_id=company.id,
        customer_id=customer.id,
        user_id=author.id,
        status=status,
        version_number=1,
        total_amount=Decimal("1000.00"),
        subtotal=Decimal("1000.00"),
        total_discount=Decimal("0.00"),
        overall_discount_percent=Decimal("0.00"), 
        overall_discount_amount=Decimal("0.00"), 
        line_discount_total=Decimal("0.00"),
        taxable_amount=Decimal("1000.00"), 
        tax_amount=Decimal("0.00"), 
        total_cost=Decimal("0.00"), 
        gross_profit=Decimal("0.00"), 
        margin_percentage=Decimal("0.00")
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

def test_portal_user_auth(db_session, client, setup_data):
    test_company, test_customer, internal_user = setup_data
    # Customer Portal
    p_user = create_portal_user(db_session, test_company, test_customer)
    
    from app.services.portal import PortalAuthenticationService
    assert PortalAuthenticationService.verify_portal_user(db_session, p_user) is True
    assert PortalAuthenticationService.verify_portal_user(db_session, internal_user) is False

def test_tenant_isolation(db_session, client, setup_data):
    test_company, test_customer, internal_user = setup_data
    # Create Company B
    comp2 = Company(name="Comp2")
    db_session.add(comp2)
    db_session.commit()
    db_session.refresh(comp2)

    cust2 = Customer(company_id=comp2.id, customer_code=f"C2-{uuid.uuid4().hex[:4]}", name="Cust2", email=f"c2_{uuid.uuid4()}@test.com", is_active=True)
    db_session.add(cust2)
    
    internal_user2 = User(
        email=f"author2_{uuid.uuid4()}@example.com",
        first_name="Auth", last_name="User",
        company_id=comp2.id,
        is_active=True
    )
    db_session.add(internal_user2)
    db_session.commit()

    q1 = create_mock_quote(db_session, test_company, test_customer, internal_user)
    q2 = create_mock_quote(db_session, comp2, cust2, internal_user2)

    # Portal user for cust2
    p_user2 = create_portal_user(db_session, comp2, cust2)

    from app.services.portal import PortalAuthorizationService
    # p_user2 accessing q2 works
    q = PortalAuthorizationService.get_quotation(db_session, comp2.id, cust2.id, q2.id)
    assert q.id == q2.id
    
    # p_user2 accessing q1 fails
    with pytest.raises(ValueError):
        PortalAuthorizationService.get_quotation(db_session, comp2.id, cust2.id, q1.id)

def test_negotiation_workflow(db_session, client, setup_data):
    test_company, test_customer, internal_user = setup_data
    p_user = create_portal_user(db_session, test_company, test_customer)
    quote = create_mock_quote(db_session, test_company, test_customer, internal_user, "SENT")
    
    # Test comment
    from app.services.portal import CustomerCommentService, NegotiationService
    cmt = CustomerCommentService.add_comment(db_session, test_company.id, test_customer.id, p_user.id, quote.id, "Too expensive")
    assert cmt.id is not None
    
    # Request negotiation
    req = NegotiationService.submit_request(db_session, test_company.id, test_customer.id, quote.id, "REQUEST_DISCOUNT", "15%", "0%", "Lower budget")
    
    assert req.status in ["APPROVED", "PENDING_APPROVAL"] # Should pass intent extraction and enter policy

def test_quote_acceptance_idempotency(db_session, client, setup_data):
    test_company, test_customer, internal_user = setup_data
    quote = create_mock_quote(db_session, test_company, test_customer, internal_user, "SENT")
    from app.services.portal import PortalAcceptanceService
    
    q = PortalAcceptanceService.accept_quote(db_session, test_company.id, test_customer.id, quote.id)
    assert q.status == "ACCEPTED"
    
    # Accept again (should be idempotent)
    q2 = PortalAcceptanceService.accept_quote(db_session, test_company.id, test_customer.id, quote.id)
    assert q2.status == "ACCEPTED"
