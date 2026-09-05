import uuid
from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_tier import CustomerTier
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


# ==========================================
# PHASE 016: ROLE MODEL TESTS
# ==========================================

def test_role_model_import_and_metadata():
    """Verify Role model is registered in Base.metadata."""
    assert "roles" in Base.metadata.tables
    table = Base.metadata.tables["roles"]
    assert table.name == "roles"


def test_role_columns_definition():
    """Verify Role columns and constraints."""
    cols = {col.name: col for col in Role.__table__.columns}
    assert "id" in cols
    assert "name" in cols
    assert "description" in cols
    assert "is_active" in cols
    assert "created_at" in cols
    assert "updated_at" in cols

    assert cols["id"].primary_key is True
    assert cols["name"].unique is True
    assert cols["name"].nullable is False
    assert cols["is_active"].nullable is False


def test_role_persistence_and_uniqueness():
    """Verify Role creation, persistence, and name uniqueness enforcement."""
    session = SessionLocal()
    role_name = f"ROLE_{uuid.uuid4().hex[:8].upper()}"

    role1 = Role(name=role_name, description="Test sales representative role")
    try:
        session.add(role1)
        session.commit()
        session.refresh(role1)

        assert role1.id is not None
        assert role1.name == role_name
        assert role1.is_active is True

        # Uniqueness test
        role2 = Role(name=role_name, description="Duplicate role")
        session.add(role2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Clean up
        session.delete(role1)
        session.commit()
    finally:
        session.close()


# ==========================================
# PHASE 017: PERMISSION MODEL TESTS
# ==========================================

def test_permission_model_import_and_metadata():
    """Verify Permission model is registered in Base.metadata."""
    assert "permissions" in Base.metadata.tables
    table = Base.metadata.tables["permissions"]
    assert table.name == "permissions"


def test_permission_columns_definition():
    """Verify Permission columns and constraints."""
    cols = {col.name: col for col in Permission.__table__.columns}
    assert "id" in cols
    assert "name" in cols
    assert "description" in cols
    assert "resource" in cols
    assert "action" in cols
    assert "created_at" in cols
    assert "updated_at" in cols

    assert cols["id"].primary_key is True
    assert cols["name"].unique is True
    assert cols["resource"].nullable is False
    assert cols["action"].nullable is False


def test_permission_persistence_and_uniqueness():
    """Verify Permission creation, persistence, and uniqueness constraints."""
    session = SessionLocal()
    perm_name = f"perm.{uuid.uuid4().hex[:8]}"

    perm1 = Permission(
        name=perm_name,
        resource="quotation",
        action="approve",
        description="Permission to approve discount",
    )
    try:
        session.add(perm1)
        session.commit()
        session.refresh(perm1)

        assert perm1.id is not None
        assert perm1.name == perm_name

        # Duplicate name
        perm2 = Permission(
            name=perm_name,
            resource="quotation",
            action="submit",
        )
        session.add(perm2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Duplicate (resource, action)
        perm3 = Permission(
            name=f"other.{uuid.uuid4().hex[:8]}",
            resource="quotation",
            action="approve",
        )
        session.add(perm3)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Clean up
        session.delete(perm1)
        session.commit()
    finally:
        session.close()


# ==========================================
# PHASE 018: COMPANY MODEL TESTS
# ==========================================

def test_company_model_import_and_metadata():
    """Verify Company model is registered in Base.metadata."""
    assert "companies" in Base.metadata.tables
    table = Base.metadata.tables["companies"]
    assert table.name == "companies"


def test_company_columns_definition():
    """Verify Company columns and constraints."""
    cols = {col.name: col for col in Company.__table__.columns}
    assert "id" in cols
    assert "name" in cols
    assert "legal_name" in cols
    assert "email" in cols
    assert "phone" in cols
    assert "address" in cols
    assert "city" in cols
    assert "state" in cols
    assert "country" in cols
    assert "postal_code" in cols
    assert "tax_identifier" in cols
    assert "is_active" in cols
    assert "created_at" in cols
    assert "updated_at" in cols

    assert cols["id"].primary_key is True
    assert cols["name"].nullable is False


def test_company_persistence_and_retrieval():
    """Verify Company creation and retrieval."""
    session = SessionLocal()
    comp_name = f"Acme Corp {uuid.uuid4().hex[:6]}"

    company = Company(
        name=comp_name,
        legal_name="Acme Corporation Ltd.",
        email="billing@acme.com",
        city="Bengaluru",
        country="India",
        tax_identifier="GSTIN12345XYZ",
    )
    try:
        session.add(company)
        session.commit()
        session.refresh(company)

        assert company.id is not None
        assert company.name == comp_name
        assert company.is_active is True

        queried = session.scalars(select(Company).where(Company.id == company.id)).first()
        assert queried is not None
        assert queried.legal_name == "Acme Corporation Ltd."

        # Clean up
        session.delete(company)
        session.commit()
    finally:
        session.close()


# ==========================================
# PHASE 020: CUSTOMER TIER MODEL TESTS
# ==========================================

def test_customer_tier_model_import_and_metadata():
    """Verify CustomerTier model is registered in Base.metadata."""
    assert "customer_tiers" in Base.metadata.tables
    table = Base.metadata.tables["customer_tiers"]
    assert table.name == "customer_tiers"


def test_customer_tier_columns_and_constraint():
    """Verify CustomerTier columns and discount limit check constraint."""
    cols = {col.name: col for col in CustomerTier.__table__.columns}
    assert "id" in cols
    assert "name" in cols
    assert "code" in cols
    assert "description" in cols
    assert "discount_limit" in cols
    assert "is_active" in cols

    assert cols["id"].primary_key is True
    assert cols["name"].unique is True
    assert cols["code"].unique is True


def test_customer_tier_persistence_and_validation():
    """Verify CustomerTier persistence and discount limit range constraint."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]
    tier_code = f"GOLD_{suffix}".upper()

    tier = CustomerTier(
        name=f"Gold Tier {suffix}",
        code=tier_code,
        discount_limit=Decimal("15.00"),
        description="Standard Gold Tier with 15% discount limit",
    )
    try:
        session.add(tier)
        session.commit()
        session.refresh(tier)

        assert tier.id is not None
        assert tier.discount_limit == Decimal("15.00")

        # Violate check constraint (> 100% discount limit)
        invalid_tier = CustomerTier(
            name=f"Invalid Tier {suffix}",
            code=f"INV_{suffix}".upper(),
            discount_limit=Decimal("150.00"),
        )
        session.add(invalid_tier)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Clean up
        session.delete(tier)
        session.commit()
    finally:
        session.close()


# ==========================================
# PHASE 019: CUSTOMER MODEL TESTS
# ==========================================

def test_customer_model_import_and_metadata():
    """Verify Customer model is registered in Base.metadata."""
    assert "customers" in Base.metadata.tables
    table = Base.metadata.tables["customers"]
    assert table.name == "customers"


def test_customer_columns_and_foreign_keys():
    """Verify Customer column definitions and foreign key constraints."""
    cols = {col.name: col for col in Customer.__table__.columns}
    assert "id" in cols
    assert "company_id" in cols
    assert "tier_id" in cols
    assert "customer_code" in cols
    assert "name" in cols
    assert "email" in cols
    assert "is_active" in cols

    assert cols["id"].primary_key is True
    assert cols["name"].nullable is False
    assert cols["customer_code"].nullable is False


def test_customer_persistence_and_code_uniqueness():
    """Verify Customer persistence and scoped customer_code uniqueness."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    company = Company(name=f"Parent Corp {suffix}")
    tier = CustomerTier(name=f"Tier {suffix}", code=f"T_{suffix}".upper(), discount_limit=Decimal("10.00"))
    session.add_all([company, tier])
    session.commit()

    customer = Customer(
        company_id=company.id,
        tier_id=tier.id,
        customer_code=f"CUST-{suffix}",
        name=f"Global Buyer {suffix}",
        email=f"buyer_{suffix}@example.com",
    )
    try:
        session.add(customer)
        session.commit()
        session.refresh(customer)

        assert customer.id is not None
        assert customer.company_id == company.id
        assert customer.tier_id == tier.id

        # Duplicate customer code in the SAME company must fail
        dup_customer = Customer(
            company_id=company.id,
            tier_id=tier.id,
            customer_code=f"CUST-{suffix}",
            name="Another Name",
        )
        session.add(dup_customer)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Clean up
        session.delete(customer)
        session.delete(company)
        session.delete(tier)
        session.commit()
    finally:
        session.close()


# ==========================================
# RELATIONSHIP INTEGRATION TESTS
# ==========================================

def test_user_role_permission_relationships():
    """Verify User <-> Role <-> Permission many-to-many relationship mapping."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    perm = Permission(name=f"deal.approve.{suffix}", resource="deal", action=f"app_{suffix}")
    role = Role(name=f"FINANCE_MANAGER_{suffix}")
    user = User(
        email=f"finance_{suffix}@dealflow360.com",
        first_name="Finance",
        last_name="Officer",
    )

    try:
        role.permissions.append(perm)
        user.roles.append(role)
        session.add_all([perm, role, user])
        session.commit()

        # Query user and inspect populated relations
        loaded_user = session.scalars(select(User).where(User.id == user.id)).first()
        assert loaded_user is not None
        assert len(loaded_user.roles) == 1
        assert loaded_user.roles[0].name == f"FINANCE_MANAGER_{suffix}"
        assert len(loaded_user.roles[0].permissions) == 1
        assert loaded_user.roles[0].permissions[0].action == f"app_{suffix}"

        # Clean up
        session.delete(user)
        session.delete(role)
        session.delete(perm)
        session.commit()
    finally:
        session.close()


def test_company_customer_tier_relationship():
    """Verify Company -> Customer -> CustomerTier ORM navigation."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    company = Company(name=f"Enterprise Corp {suffix}")
    tier = CustomerTier(name=f"Enterprise Tier {suffix}", code=f"ENT_{suffix}".upper(), discount_limit=Decimal("20.00"))
    session.add_all([company, tier])
    session.commit()

    customer = Customer(
        company_id=company.id,
        tier_id=tier.id,
        customer_code=f"ENT-CUST-{suffix}",
        name=f"Mega Enterprise {suffix}",
    )
    session.add(customer)
    session.commit()

    try:
        loaded_company = session.scalars(select(Company).where(Company.id == company.id)).first()
        assert loaded_company is not None
        assert len(loaded_company.customers) == 1
        assert loaded_company.customers[0].name == f"Mega Enterprise {suffix}"
        assert loaded_company.customers[0].tier is not None
        assert loaded_company.customers[0].tier.discount_limit == Decimal("20.00")

        # Clean up
        session.delete(customer)
        session.delete(company)
        session.delete(tier)
        session.commit()
    finally:
        session.close()
