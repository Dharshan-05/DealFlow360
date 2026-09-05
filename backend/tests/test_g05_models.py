"""Unit and integration tests for G05 models (Phases 021–024):
- Phase 021: Product Model
- Phase 022: ProductCategory Model
- Phase 023: Warehouse Model
- Phase 024: AuditLog Model
"""
import uuid
from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User
from app.models.warehouse import Warehouse


# ===========================================================================
# PHASE 022: PRODUCT CATEGORY MODEL TESTS
# ===========================================================================

def test_product_category_metadata_and_columns():
    """Verify ProductCategory metadata registration and schema columns."""
    assert "product_categories" in Base.metadata.tables
    table = Base.metadata.tables["product_categories"]
    assert table.name == "product_categories"

    cols = {col.name: col for col in ProductCategory.__table__.columns}
    assert "id" in cols
    assert "name" in cols
    assert "code" in cols
    assert "description" in cols
    assert "is_active" in cols
    assert "created_at" in cols
    assert "updated_at" in cols

    assert cols["id"].primary_key is True
    assert cols["name"].unique is True
    assert cols["code"].unique is True
    assert cols["name"].nullable is False
    assert cols["code"].nullable is False


def test_product_category_crud_and_uniqueness():
    """Test ProductCategory persistence and uniqueness on code and name."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]
    cat = ProductCategory(
        name=f"Category {suffix}",
        code=f"CAT-{suffix}",
        description="Test Category Description",
    )
    try:
        session.add(cat)
        session.commit()
        session.refresh(cat)

        assert cat.id is not None
        assert cat.is_active is True
        assert cat.created_at is not None
        assert cat.updated_at is not None

        # Duplicate code violation
        dup_code_cat = ProductCategory(
            name=f"Other Category {suffix}",
            code=f"CAT-{suffix}",
        )
        session.add(dup_code_cat)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # Duplicate name violation
        dup_name_cat = ProductCategory(
            name=f"Category {suffix}",
            code=f"OTHER-{suffix}",
        )
        session.add(dup_name_cat)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.rollback()
        # Clean up
        existing = session.scalars(select(ProductCategory).where(ProductCategory.code == f"CAT-{suffix}")).first()
        if existing:
            session.delete(existing)
            session.commit()
        session.close()


# ===========================================================================
# PHASE 021: PRODUCT MODEL TESTS
# ===========================================================================

def test_product_metadata_and_columns():
    """Verify Product metadata registration and schema columns."""
    assert "products" in Base.metadata.tables
    table = Base.metadata.tables["products"]
    assert table.name == "products"

    cols = {col.name: col for col in Product.__table__.columns}
    assert "id" in cols
    assert "category_id" in cols
    assert "sku" in cols
    assert "name" in cols
    assert "description" in cols
    assert "cost" in cols
    assert "base_price" in cols
    assert "unit" in cols
    assert "tax_rate" in cols
    assert "is_active" in cols
    assert "created_at" in cols
    assert "updated_at" in cols

    assert cols["id"].primary_key is True
    assert cols["sku"].unique is True
    assert cols["sku"].nullable is False
    assert cols["name"].nullable is False
    assert cols["cost"].nullable is False
    assert cols["base_price"].nullable is False


def test_product_crud_and_relationship():
    """Test Product creation, category relationship, and SKU uniqueness."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    category = ProductCategory(
        name=f"Hardware {suffix}",
        code=f"HW-{suffix}",
    )
    session.add(category)
    session.commit()
    session.refresh(category)

    product = Product(
        category_id=category.id,
        sku=f"SKU-{suffix}",
        name=f"Server Model {suffix}",
        description="High performance rack server",
        cost=Decimal("1500.00"),
        base_price=Decimal("2500.00"),
        unit="unit",
        tax_rate=Decimal("18.00"),
    )
    try:
        session.add(product)
        session.commit()
        session.refresh(product)

        assert product.id is not None
        assert product.category_id == category.id
        assert product.category is not None
        assert product.category.code == f"HW-{suffix}"
        assert product in category.products
        assert product.cost == Decimal("1500.00")
        assert product.base_price == Decimal("2500.00")

        # Duplicate SKU violation
        dup_product = Product(
            category_id=category.id,
            sku=f"SKU-{suffix}",
            name=f"Duplicate SKU Server {suffix}",
            cost=Decimal("1000.00"),
            base_price=Decimal("2000.00"),
        )
        session.add(dup_product)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.rollback()
        # Clean up
        p = session.scalars(select(Product).where(Product.sku == f"SKU-{suffix}")).first()
        if p:
            session.delete(p)
        c = session.scalars(select(ProductCategory).where(ProductCategory.code == f"HW-{suffix}")).first()
        if c:
            session.delete(c)
        session.commit()
        session.close()


# ===========================================================================
# PHASE 023: WAREHOUSE MODEL TESTS
# ===========================================================================

def test_warehouse_metadata_and_columns():
    """Verify Warehouse metadata registration and schema columns."""
    assert "warehouses" in Base.metadata.tables
    table = Base.metadata.tables["warehouses"]
    assert table.name == "warehouses"

    cols = {col.name: col for col in Warehouse.__table__.columns}
    assert "id" in cols
    assert "company_id" in cols
    assert "code" in cols
    assert "name" in cols
    assert "city" in cols
    assert "state" in cols
    assert "country" in cols
    assert "is_active" in cols

    assert cols["id"].primary_key is True
    assert cols["company_id"].nullable is False
    assert cols["code"].nullable is False
    assert cols["name"].nullable is False


def test_warehouse_company_scoped_uniqueness():
    """Test Warehouse uniqueness is scoped per company (company_id, code)."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    company1 = Company(name=f"Company A {suffix}")
    company2 = Company(name=f"Company B {suffix}")
    session.add_all([company1, company2])
    session.commit()
    session.refresh(company1)
    session.refresh(company2)

    wh_code = f"WH-{suffix}"
    wh1 = Warehouse(company_id=company1.id, code=wh_code, name="Warehouse 1")
    wh2 = Warehouse(company_id=company2.id, code=wh_code, name="Warehouse 2 (Diff Company)")

    try:
        session.add_all([wh1, wh2])
        session.commit()
        session.refresh(wh1)
        session.refresh(wh2)

        # Same code in different companies should SUCCEED
        assert wh1.id != wh2.id
        assert wh1.code == wh2.code
        assert wh1.company_id != wh2.company_id
        assert wh1 in company1.warehouses

        # Duplicate code within same company should FAIL
        wh_dup = Warehouse(company_id=company1.id, code=wh_code, name="Warehouse Duplicate")
        session.add(wh_dup)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.rollback()
        # Clean up
        for comp_id in [company1.id, company2.id]:
            c = session.get(Company, comp_id)
            if c:
                session.delete(c)
        session.commit()
        session.close()


# ===========================================================================
# PHASE 024: AUDIT LOG MODEL TESTS
# ===========================================================================

def test_audit_log_metadata_and_columns():
    """Verify AuditLog metadata registration, append-only nature, and schema columns."""
    assert "audit_logs" in Base.metadata.tables
    table = Base.metadata.tables["audit_logs"]
    assert table.name == "audit_logs"

    cols = {col.name: col for col in AuditLog.__table__.columns}
    assert "id" in cols
    assert "user_id" in cols
    assert "company_id" in cols
    assert "action" in cols
    assert "resource_type" in cols
    assert "resource_id" in cols
    assert "details" in cols
    assert "context_metadata" in cols
    assert "created_at" in cols
    # Crucial append-only verification: NO updated_at column
    assert "updated_at" not in cols

    assert cols["id"].primary_key is True
    assert cols["action"].nullable is False
    assert cols["resource_type"].nullable is False
    assert cols["user_id"].nullable is True
    assert cols["company_id"].nullable is True


def test_audit_log_crud_and_jsonb_metadata():
    """Test AuditLog persistence with JSONB metadata and user/company relationships."""
    session = SessionLocal()
    suffix = uuid.uuid4().hex[:6]

    company = Company(name=f"Audit Test Co {suffix}")
    user = User(
        email=f"auditor_{suffix}@example.com",
        first_name="Audit",
        last_name="User",
    )
    session.add_all([company, user])
    session.commit()
    session.refresh(company)
    session.refresh(user)

    audit = AuditLog(
        user_id=user.id,
        company_id=company.id,
        action="quotation:approved",
        resource_type="quotation",
        resource_id=str(uuid.uuid4()),
        details="Approved discount of 12.5% for customer deal",
        context_metadata={
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "discount_percentage": 12.5,
            "policy_rule_id": "RULE-001",
        },
    )

    # System audit log without user (system-generated event)
    system_audit = AuditLog(
        user_id=None,
        company_id=company.id,
        action="system:backup",
        resource_type="database",
        resource_id=None,
        details="Automated database backup completed",
        context_metadata={"status": "success", "duration_ms": 1240},
    )

    try:
        session.add_all([audit, system_audit])
        session.commit()
        session.refresh(audit)
        session.refresh(system_audit)

        assert audit.id is not None
        assert audit.created_at is not None
        assert audit.user_id == user.id
        assert audit.company_id == company.id
        assert audit.context_metadata["discount_percentage"] == 12.5
        assert audit in user.audit_logs
        assert audit in company.audit_logs

        assert system_audit.id is not None
        assert system_audit.user is None
        assert system_audit.company_id == company.id
        assert system_audit.context_metadata["status"] == "success"
    finally:
        session.rollback()
        # Clean up
        session.delete(audit)
        session.delete(system_audit)
        session.delete(user)
        session.delete(company)
        session.commit()
        session.close()
