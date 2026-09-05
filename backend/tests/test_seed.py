"""Unit and integration tests for Phase 025 Database Seed System.
Verifies:
1. Seed execution populates master data.
2. Seed execution is strictly idempotent (multiple runs produce no duplicates or errors).
3. Seeded entities have required relations and integrity.
"""
from decimal import Decimal
import pytest
from sqlalchemy import func, select

from app.db.seed import (
    CATEGORIES_DATA,
    COMPANIES_DATA,
    CUSTOMER_TIERS_DATA,
    PERMISSIONS_DATA,
    PRODUCTS_DATA,
    ROLES_DATA,
    WAREHOUSES_DATA,
    run_seed,
)
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.customer_tier import CustomerTier
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.role import Role
from app.models.warehouse import Warehouse


def test_seed_execution_and_idempotency():
    """Verify run_seed populates data and repeat executions do not create duplicates."""
    session = SessionLocal()
    try:
        # Initial run
        run_seed(session)

        # Verify Categories
        for cat_data in CATEGORIES_DATA:
            cat = session.scalars(
                select(ProductCategory).where(ProductCategory.code == cat_data["code"])
            ).first()
            assert cat is not None
            assert cat.name == cat_data["name"]

        # Verify Customer Tiers (Bronze 5%, Silver 10%, Gold 15%)
        for tier_data in CUSTOMER_TIERS_DATA:
            tier = session.scalars(
                select(CustomerTier).where(CustomerTier.code == tier_data["code"])
            ).first()
            assert tier is not None
            assert tier.discount_limit == tier_data["discount_limit"]

        # Verify Master Company
        comp = session.scalars(
            select(Company).where(Company.name == COMPANIES_DATA[0]["name"])
        ).first()
        assert comp is not None

        # Verify Roles and Permissions
        for role_data in ROLES_DATA:
            role = session.scalars(
                select(Role).where(Role.name == role_data["name"])
            ).first()
            assert role is not None
            assert len(role.permissions) > 0

        # Verify Warehouses
        for wh_data in WAREHOUSES_DATA:
            wh = session.scalars(
                select(Warehouse).where(
                    Warehouse.company_id == comp.id,
                    Warehouse.code == wh_data["code"],
                )
            ).first()
            assert wh is not None
            assert wh.name == wh_data["name"]

        # Verify Products
        for prod_data in PRODUCTS_DATA:
            prod = session.scalars(
                select(Product).where(Product.sku == prod_data["sku"])
            ).first()
            assert prod is not None
            assert prod.category is not None
            assert prod.cost == prod_data["cost"]
            assert prod.base_price == prod_data["base_price"]

        # Count records before second seed run
        cat_count_1 = session.scalar(select(func.count(ProductCategory.id)))
        tier_count_1 = session.scalar(select(func.count(CustomerTier.id)))
        role_count_1 = session.scalar(select(func.count(Role.id)))
        perm_count_1 = session.scalar(select(func.count(Permission.id)))
        wh_count_1 = session.scalar(select(func.count(Warehouse.id)))
        prod_count_1 = session.scalar(select(func.count(Product.id)))

        # Run seed SECOND time - IDEMPOTENCY CHECK
        run_seed(session)

        # Count records after second seed run
        cat_count_2 = session.scalar(select(func.count(ProductCategory.id)))
        tier_count_2 = session.scalar(select(func.count(CustomerTier.id)))
        role_count_2 = session.scalar(select(func.count(Role.id)))
        perm_count_2 = session.scalar(select(func.count(Permission.id)))
        wh_count_2 = session.scalar(select(func.count(Warehouse.id)))
        prod_count_2 = session.scalar(select(func.count(Product.id)))

        assert cat_count_1 == cat_count_2
        assert tier_count_1 == tier_count_2
        assert role_count_1 == role_count_2
        assert perm_count_1 == perm_count_2
        assert wh_count_1 == wh_count_2
        assert prod_count_1 == prod_count_2

    finally:
        session.close()
