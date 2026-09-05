"""Database Seed System for DealFlow360 (Phase 025).

Seeds master reference data idempotently:
- Product Categories
- Customer Tiers (Bronze, Silver, Gold with baseline discounts, pure data)
- Default Master Company
- Foundational Roles & Permissions (with association mappings)
- Initial Warehouses
- Initial Products

Strictly scoped to master reference data:
- NO user credential creation (no hashing / authentication)
- Deterministic and safe to re-run multiple times
"""
import sys
from decimal import Decimal
from typing import Dict, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.customer_tier import CustomerTier
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_attribute import ProductAttribute, ProductAttributeValue
from app.models.product_category import ProductCategory
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant
from app.models.role import Role
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.models.backorder import Backorder
from app.models.fulfillment import Fulfillment
from app.models.inventory_alert import InventoryAlert


# ---------------------------------------------------------------------------
# Seed Datasets
# ---------------------------------------------------------------------------

CATEGORIES_DATA = [
    {
        "name": "Hardware",
        "code": "CAT-HW",
        "description": "Physical IT equipment, servers, and networking hardware",
    },
    {
        "name": "Software",
        "code": "CAT-SW",
        "description": "Enterprise software licenses, subscriptions, and platforms",
    },
    {
        "name": "Services",
        "code": "CAT-SRV",
        "description": "Professional consulting, implementation, and support services",
    },
]

CUSTOMER_TIERS_DATA = [
    {
        "name": "Bronze",
        "code": "TIER-BRONZE",
        "discount_limit": Decimal("5.00"),
        "description": "Standard entry tier with up to 5% baseline discount limit",
    },
    {
        "name": "Silver",
        "code": "TIER-SILVER",
        "discount_limit": Decimal("10.00"),
        "description": "Preferred partner tier with up to 10% baseline discount limit",
    },
    {
        "name": "Gold",
        "code": "TIER-GOLD",
        "discount_limit": Decimal("15.00"),
        "description": "Strategic VIP tier with up to 15% baseline discount limit",
    },
]

COMPANIES_DATA = [
    {
        "name": "Acme Corporation",
        "legal_name": "Acme Global Technologies Inc.",
        "email": "contact@acme.example.com",
        "phone": "+1-800-555-0100",
        "address": "100 Innovation Way",
        "city": "San Francisco",
        "state": "CA",
        "country": "United States",
        "postal_code": "94105",
        "tax_identifier": "US-EIN-998877665",
    },
]

PERMISSIONS_DATA = [
    # Customer permissions
    {"name": "customers:read", "resource": "customers", "action": "read", "description": "View customer records"},
    {"name": "customers:write", "resource": "customers", "action": "write", "description": "Create and update customer records"},
    {"name": "customers:delete", "resource": "customers", "action": "delete", "description": "Delete customer records"},
    # Product permissions
    {"name": "products:read", "resource": "products", "action": "read", "description": "View product catalog"},
    {"name": "products:write", "resource": "products", "action": "write", "description": "Create and update products"},
    # Warehouse permissions
    {"name": "warehouses:read", "resource": "warehouses", "action": "read", "description": "View warehouse information"},
    {"name": "warehouses:write", "resource": "warehouses", "action": "write", "description": "Manage warehouse facilities"},
    # Quotation permissions (Foundational permission catalog definition)
    {"name": "quotations:read", "resource": "quotations", "action": "read", "description": "View quotations"},
    {"name": "quotations:write", "resource": "quotations", "action": "write", "description": "Create and edit quotations"},
    {"name": "quotations:approve", "resource": "quotations", "action": "approve", "description": "Approve quotation discounts"},
    # Audit log permissions
    {"name": "audit_logs:read", "resource": "audit_logs", "action": "read", "description": "View system audit logs"},
]

# Role to permission mapping by permission name
ROLE_PERMISSIONS_MAP: Dict[str, List[str]] = {
    "Admin": [
        "customers:read", "customers:write", "customers:delete",
        "products:read", "products:write",
        "warehouses:read", "warehouses:write",
        "quotations:read", "quotations:write", "quotations:approve",
        "audit_logs:read",
    ],
    "Sales Representative": [
        "customers:read", "customers:write",
        "products:read",
        "warehouses:read",
        "quotations:read", "quotations:write",
    ],
    "Sales Manager": [
        "customers:read", "customers:write",
        "products:read",
        "warehouses:read",
        "quotations:read", "quotations:write", "quotations:approve",
        "audit_logs:read",
    ],
    "Finance": [
        "customers:read",
        "products:read",
        "quotations:read", "quotations:approve",
        "audit_logs:read",
    ],
    "Operations": [
        "products:read",
        "warehouses:read", "warehouses:write",
    ],
    "Customer Portal": [
        "customers:read",
        "quotations:read",
        "products:read",
    ],
}

ROLES_DATA = [
    {"name": "Admin", "description": "Full system administrator access"},
    {"name": "Sales Representative", "description": "Handles deal creation and quotation drafting"},
    {"name": "Sales Manager", "description": "Supervises sales reps and reviews quotation discounts"},
    {"name": "Finance", "description": "Oversees billing, margins, and financial compliance"},
    {"name": "Operations", "description": "Manages logistics, warehouses, and fulfillment"},
    {"name": "Customer Portal", "description": "External customer access for viewing organization quotes and products"},
]

WAREHOUSES_DATA = [
    {
        "code": "WH-CENTRAL",
        "name": "Central Distribution Hub",
        "city": "Chicago",
        "state": "IL",
        "country": "United States",
        "postal_code": "60601",
        "address": "100 Logistics Blvd",
        "priority": 1,
    },
    {
        "code": "WH-EAST",
        "name": "East Coast Fulfillment Center",
        "city": "Newark",
        "state": "NJ",
        "country": "United States",
        "postal_code": "07101",
        "address": "250 Atlantic Way",
        "priority": 2,
    },
    {
        "code": "WH-WEST",
        "name": "West Coast Logistics Depot",
        "city": "Reno",
        "state": "NV",
        "country": "United States",
        "postal_code": "89501",
        "address": "500 Pacific Highway",
        "priority": 3,
    },
]

PRODUCTS_DATA = [
    {
        "category_code": "CAT-HW",
        "sku": "HW-SRV-001",
        "name": "Enterprise Rack Server R750",
        "description": "High-density 2U dual-socket enterprise rack server",
        "cost": Decimal("4500.00"),
        "base_price": Decimal("6800.00"),
        "unit": "unit",
        "tax_rate": Decimal("8.50"),
        "is_subscription": False,
        "recurring_frequency": None,
        "inventory_quantity": 18,
        "low_stock_threshold": 5,
    },
    {
        "category_code": "CAT-HW",
        "sku": "HW-SWT-002",
        "name": "48-Port Managed Gigabit Switch",
        "description": "Enterprise L3 managed network switch with 10G SFP+ uplinks",
        "cost": Decimal("1200.00"),
        "base_price": Decimal("1950.00"),
        "unit": "unit",
        "tax_rate": Decimal("8.50"),
        "is_subscription": False,
        "recurring_frequency": None,
        "inventory_quantity": 4,
        "low_stock_threshold": 5,
    },
    {
        "category_code": "CAT-SW",
        "sku": "SW-ERP-LIC-001",
        "name": "DealFlow Enterprise Platform License",
        "description": "Annual enterprise license for core DealFlow360 platform",
        "cost": Decimal("5000.00"),
        "base_price": Decimal("15000.00"),
        "unit": "license",
        "tax_rate": Decimal("0.00"),
        "is_subscription": True,
        "recurring_frequency": "yearly",
        "inventory_quantity": 100,
        "low_stock_threshold": 10,
    },
    {
        "category_code": "CAT-SW",
        "sku": "SW-ANL-ADD-002",
        "name": "AI Analytics & Anomaly Module Addon",
        "description": "Annual subscription for advanced AI risk scoring and analytics",
        "cost": Decimal("2000.00"),
        "base_price": Decimal("6000.00"),
        "unit": "license",
        "tax_rate": Decimal("0.00"),
        "is_subscription": True,
        "recurring_frequency": "monthly",
        "inventory_quantity": 0,
        "low_stock_threshold": 5,
    },
    {
        "category_code": "CAT-SRV",
        "sku": "SRV-IMP-001",
        "name": "Standard Enterprise Implementation",
        "description": "End-to-end configuration, setup, and deployment package",
        "cost": Decimal("8000.00"),
        "base_price": Decimal("12000.00"),
        "unit": "package",
        "tax_rate": Decimal("0.00"),
        "is_subscription": False,
        "recurring_frequency": None,
        "inventory_quantity": 25,
        "low_stock_threshold": 5,
    },
    {
        "category_code": "CAT-SRV",
        "sku": "SRV-SUP-002",
        "name": "24/7 Premium Platinum Support (Annual)",
        "description": "Round-the-clock priority technical support with 1-hour SLA",
        "cost": Decimal("3000.00"),
        "base_price": Decimal("7500.00"),
        "unit": "year",
        "tax_rate": Decimal("0.00"),
        "is_subscription": True,
        "recurring_frequency": "yearly",
        "inventory_quantity": 50,
        "low_stock_threshold": 10,
    },
]

# Phase 077: Product Units seed dataset
PRODUCT_UNITS_DATA = [
    {"code": "UNIT", "name": "Item / Piece", "description": "Individual unit or piece"},
    {"code": "LICENSE", "name": "Software License", "description": "Seat or platform software license"},
    {"code": "PACKAGE", "name": "Service Package", "description": "Bundled implementation or service pack"},
    {"code": "YEAR", "name": "Annual Service", "description": "Annual recurring service term"},
    {"code": "MONTH", "name": "Monthly Term", "description": "Monthly subscription term"},
    {"code": "HOUR", "name": "Consulting Hour", "description": "Hourly professional service rate"},
    {"code": "BOX", "name": "Hardware Box", "description": "Box packaging of hardware items"},
    {"code": "KG", "name": "Kilogram", "description": "Weight measurement in kilograms"},
]

# Phase 079: Product Attributes seed dataset
PRODUCT_ATTRIBUTES_DATA = [
    {
        "code": "SERVER_CHASSIS",
        "name": "Server Chassis Type",
        "description": "Form factor and mounting specification",
        "values": ["1U Rackmount", "2U Rackmount", "4U Tower"],
    },
    {
        "code": "SUPPORT_TIER",
        "name": "Support Level",
        "description": "Support response time and SLA tier",
        "values": ["Standard 8x5", "Silver 24x7", "Platinum 1-Hour SLA"],
    },
    {
        "code": "EDITION",
        "name": "Software Edition",
        "description": "Feature packaging edition",
        "values": ["Standard Edition", "Professional Edition", "Enterprise Edition"],
    },
]

# Phase 078: Sample Product Variants
PRODUCT_VARIANTS_DATA = [
    {
        "parent_sku": "HW-SRV-001",
        "sku": "HW-SRV-001-2U",
        "name": "Enterprise Rack Server R750 (2U 64GB)",
        "cost": Decimal("4800.00"),
        "base_price": Decimal("7200.00"),
    },
    {
        "parent_sku": "HW-SRV-001",
        "sku": "HW-SRV-001-4U",
        "name": "Enterprise Rack Server R750 (4U 128GB High-Perf)",
        "cost": Decimal("6200.00"),
        "base_price": Decimal("9400.00"),
    },
]


# ---------------------------------------------------------------------------
# Seeding Functions
# ---------------------------------------------------------------------------

def seed_categories(db: Session) -> Dict[str, ProductCategory]:
    """Seed product categories idempotently."""
    categories_by_code: Dict[str, ProductCategory] = {}
    for data in CATEGORIES_DATA:
        existing = db.scalars(
            select(ProductCategory).where(ProductCategory.code == data["code"])
        ).first()
        if not existing:
            cat = ProductCategory(**data)
            db.add(cat)
            db.flush()
            logger.info(f"Seeded ProductCategory: {cat.code} - {cat.name}")
            categories_by_code[data["code"]] = cat
        else:
            categories_by_code[data["code"]] = existing
    return categories_by_code


def seed_customer_tiers(db: Session) -> Dict[str, CustomerTier]:
    """Seed customer tiers idempotently."""
    tiers_by_code: Dict[str, CustomerTier] = {}
    for data in CUSTOMER_TIERS_DATA:
        existing = db.scalars(
            select(CustomerTier).where(CustomerTier.code == data["code"])
        ).first()
        if not existing:
            tier = CustomerTier(**data)
            db.add(tier)
            db.flush()
            logger.info(f"Seeded CustomerTier: {tier.code} ({tier.discount_limit}%)")
            tiers_by_code[data["code"]] = tier
        else:
            tiers_by_code[data["code"]] = existing
    return tiers_by_code


def seed_companies(db: Session) -> Company:
    """Seed default master company idempotently."""
    first_company_data = COMPANIES_DATA[0]
    existing = db.scalars(
        select(Company).where(Company.name == first_company_data["name"])
    ).first()
    if not existing:
        company = Company(**first_company_data)
        db.add(company)
        db.flush()
        logger.info(f"Seeded Company: {company.name}")
        return company
    return existing


def seed_permissions(db: Session) -> Dict[str, Permission]:
    """Seed permissions idempotently."""
    permissions_by_name: Dict[str, Permission] = {}
    for data in PERMISSIONS_DATA:
        existing = db.scalars(
            select(Permission).where(Permission.name == data["name"])
        ).first()
        if not existing:
            perm = Permission(**data)
            db.add(perm)
            db.flush()
            logger.info(f"Seeded Permission: {perm.name}")
            permissions_by_name[data["name"]] = perm
        else:
            permissions_by_name[data["name"]] = existing
    return permissions_by_name


def seed_roles(db: Session, permissions_by_name: Dict[str, Permission]) -> Dict[str, Role]:
    """Seed roles and link permissions idempotently."""
    roles_by_name: Dict[str, Role] = {}
    for data in ROLES_DATA:
        existing = db.scalars(
            select(Role).where(Role.name == data["name"])
        ).first()
        if not existing:
            role = Role(**data)
            db.add(role)
            db.flush()
            logger.info(f"Seeded Role: {role.name}")
            roles_by_name[data["name"]] = role
        else:
            roles_by_name[data["name"]] = existing

    # Assign permissions to roles
    for role_name, perm_names in ROLE_PERMISSIONS_MAP.items():
        role = roles_by_name[role_name]
        existing_perm_ids = {p.id for p in role.permissions}
        for p_name in perm_names:
            perm = permissions_by_name.get(p_name)
            if perm and perm.id not in existing_perm_ids:
                role.permissions.append(perm)
                existing_perm_ids.add(perm.id)
    db.flush()
    return roles_by_name


def seed_warehouses(db: Session, company: Company) -> List[Warehouse]:
    """Seed initial warehouses under company idempotently."""
    warehouses: List[Warehouse] = []
    for data in WAREHOUSES_DATA:
        existing = db.scalars(
            select(Warehouse).where(
                Warehouse.company_id == company.id,
                Warehouse.code == data["code"],
            )
        ).first()
        if not existing:
            wh = Warehouse(company_id=company.id, **data)
            db.add(wh)
            db.flush()
            logger.info(f"Seeded Warehouse: {wh.code} under {company.name}")
            warehouses.append(wh)
        else:
            if "priority" in data:
                existing.priority = data["priority"]
            db.flush()
            warehouses.append(existing)
    return warehouses


def seed_units(db: Session) -> Dict[str, ProductUnit]:
    """Seed product units of measure idempotently (Phase 077)."""
    units_by_code: Dict[str, ProductUnit] = {}
    for data in PRODUCT_UNITS_DATA:
        existing = db.scalars(select(ProductUnit).where(ProductUnit.code == data["code"])).first()
        if not existing:
            unit = ProductUnit(**data)
            db.add(unit)
            db.flush()
            logger.info(f"Seeded ProductUnit: {unit.code} - {unit.name}")
            units_by_code[data["code"]] = unit
        else:
            units_by_code[data["code"]] = existing
    return units_by_code


def seed_attributes(db: Session) -> Dict[str, ProductAttribute]:
    """Seed product attribute definitions and value options idempotently (Phase 079)."""
    attributes_by_code: Dict[str, ProductAttribute] = {}
    for data in PRODUCT_ATTRIBUTES_DATA:
        code = data["code"]
        existing = db.scalars(select(ProductAttribute).where(ProductAttribute.code == code)).first()
        if not existing:
            attr = ProductAttribute(
                code=code,
                name=data["name"],
                description=data["description"],
            )
            db.add(attr)
            db.flush()
            for idx, val_str in enumerate(data["values"]):
                val = ProductAttributeValue(
                    attribute_id=attr.id,
                    value=val_str,
                    display_order=idx,
                )
                db.add(val)
            db.flush()
            logger.info(f"Seeded ProductAttribute: {attr.code} with {len(data['values'])} options")
            attributes_by_code[code] = attr
        else:
            attributes_by_code[code] = existing
    return attributes_by_code


def seed_products(db: Session, categories_by_code: Dict[str, ProductCategory]) -> List[Product]:
    """Seed initial product catalog idempotently."""
    products: List[Product] = []
    for data in PRODUCTS_DATA:
        sku = data["sku"]
        existing = db.scalars(select(Product).where(Product.sku == sku)).first()
        if not existing:
            cat_code = data["category_code"]
            cat = categories_by_code.get(cat_code)
            prod_dict = {k: v for k, v in data.items() if k != "category_code"}
            prod = Product(
                category_id=cat.id if cat else None,
                **prod_dict,
            )
            db.add(prod)
            db.flush()
            logger.info(f"Seeded Product: {prod.sku} - {prod.name}")
            products.append(prod)
        else:
            if "is_subscription" in data:
                existing.is_subscription = data["is_subscription"]
            if "recurring_frequency" in data:
                existing.recurring_frequency = data["recurring_frequency"]
            if "inventory_quantity" in data:
                existing.inventory_quantity = data["inventory_quantity"]
            if "low_stock_threshold" in data:
                existing.low_stock_threshold = data["low_stock_threshold"]
            products.append(existing)
    return products


def seed_variants(db: Session) -> List[ProductVariant]:
    """Seed sample product variants idempotently (Phase 078)."""
    variants: List[ProductVariant] = []
    for data in PRODUCT_VARIANTS_DATA:
        sku = data["sku"]
        existing = db.scalars(select(ProductVariant).where(ProductVariant.sku == sku)).first()
        if not existing:
            parent = db.scalars(select(Product).where(Product.sku == data["parent_sku"])).first()
            if parent:
                variant = ProductVariant(
                    product_id=parent.id,
                    sku=sku,
                    name=data["name"],
                    cost=data.get("cost"),
                    base_price=data.get("base_price"),
                )
                db.add(variant)
                db.flush()
                logger.info(f"Seeded ProductVariant: {variant.sku} under {parent.sku}")
                variants.append(variant)
        else:
            variants.append(existing)
    return variants


WAREHOUSE_STOCK_SEED_MAP = [
    # WH-CENTRAL
    {"warehouse_code": "WH-CENTRAL", "sku": "HW-SRV-001", "quantity": 100, "reserved_quantity": 20},
    {"warehouse_code": "WH-CENTRAL", "sku": "HW-NET-001", "quantity": 50, "reserved_quantity": 10},
    {"warehouse_code": "WH-CENTRAL", "sku": "PRD-SW-SEC-001", "quantity": 500, "reserved_quantity": 50},
    {"warehouse_code": "WH-CENTRAL", "sku": "PRD-SRV-001", "quantity": 20, "reserved_quantity": 5},
    # WH-EAST
    {"warehouse_code": "WH-EAST", "sku": "HW-SRV-001", "quantity": 40, "reserved_quantity": 0},
    {"warehouse_code": "WH-EAST", "sku": "HW-NET-001", "quantity": 15, "reserved_quantity": 5},
    {"warehouse_code": "WH-EAST", "sku": "PRD-SW-SEC-001", "quantity": 200, "reserved_quantity": 20},
    {"warehouse_code": "WH-EAST", "sku": "PRD-SRV-001", "quantity": 10, "reserved_quantity": 2},
    # WH-WEST
    {"warehouse_code": "WH-WEST", "sku": "HW-SRV-001", "quantity": 25, "reserved_quantity": 5},
    {"warehouse_code": "WH-WEST", "sku": "HW-NET-001", "quantity": 0, "reserved_quantity": 0},
    {"warehouse_code": "WH-WEST", "sku": "PRD-SW-SEC-001", "quantity": 100, "reserved_quantity": 20},
    {"warehouse_code": "WH-WEST", "sku": "PRD-SRV-001", "quantity": 5, "reserved_quantity": 1},
]


def seed_warehouse_stocks(db: Session, warehouses: List[Warehouse], products: List[Product]) -> List[WarehouseStock]:
    """Seed warehouse-specific product inventory and reserved stock (Phases 087, 089, 090)."""
    wh_map = {w.code: w for w in warehouses}
    prod_map = {p.sku: p for p in products}

    stocks: List[WarehouseStock] = []
    for item in WAREHOUSE_STOCK_SEED_MAP:
        wh = wh_map.get(item["warehouse_code"])
        prod = prod_map.get(item["sku"])
        if not wh or not prod:
            continue

        existing = db.scalars(
            select(WarehouseStock).where(
                WarehouseStock.warehouse_id == wh.id,
                WarehouseStock.product_id == prod.id,
            )
        ).first()

        if not existing:
            stock = WarehouseStock(
                warehouse_id=wh.id,
                product_id=prod.id,
                quantity=item["quantity"],
                reserved_quantity=item["reserved_quantity"],
            )
            db.add(stock)
            db.flush()
            logger.info(
                f"Seeded WarehouseStock: {wh.code} - {prod.sku} (Qty: {stock.quantity}, Reserved: {stock.reserved_quantity}, ATP: {stock.available_to_promise})"
            )
            stocks.append(stock)
        else:
            existing.quantity = item["quantity"]
            existing.reserved_quantity = item["reserved_quantity"]
            db.flush()
            stocks.append(existing)

    return stocks


def seed_g20_inventory_records(db: Session, company: Company, products: List[Product]) -> None:
    """Seed sample Backorders, Fulfillments, and Inventory Alerts idempotently (Phases 096-100)."""
    if not products or not company:
        return

    # Find sample products
    prod_map = {p.sku: p for p in products}
    srv_prod = prod_map.get("PROD-SRV-001") or products[0]
    laptop_prod = prod_map.get("PROD-LT-001") or (products[1] if len(products) > 1 else products[0])

    # 1. Seed Backorder
    existing_bo = db.scalars(
        select(Backorder).where(
            Backorder.company_id == company.id,
            Backorder.product_id == srv_prod.id,
            Backorder.status == "OPEN",
        )
    ).first()

    if not existing_bo:
        bo = Backorder(
            company_id=company.id,
            product_id=srv_prod.id,
            requested_quantity=30,
            allocated_quantity=10,
            backordered_quantity=20,
            status="OPEN",
            notes="Initial backlog fulfillment requirement",
        )
        db.add(bo)
        db.flush()
        existing_bo = bo
        logger.info(f"Seeded Backorder for {srv_prod.sku} (Backordered: 20)")

    # 2. Seed Fulfillments with different delivery statuses
    fulfillment_samples = [
        {
            "product_id": srv_prod.id,
            "requested_quantity": 30,
            "fulfilled_quantity": 10,
            "remaining_quantity": 20,
            "status": "PARTIALLY_FULFILLED",
            "delivery_status": "IN_TRANSIT",
            "backorder_id": existing_bo.id if existing_bo else None,
            "tracking_number": "TRK-DF360-001",
            "notes": "Partial dispatch of server nodes",
        },
        {
            "product_id": laptop_prod.id,
            "requested_quantity": 5,
            "fulfilled_quantity": 5,
            "remaining_quantity": 0,
            "status": "FULFILLED",
            "delivery_status": "DELIVERED",
            "backorder_id": None,
            "tracking_number": "TRK-DF360-002",
            "notes": "Delivered to enterprise client headquarters",
        },
        {
            "product_id": laptop_prod.id,
            "requested_quantity": 10,
            "fulfilled_quantity": 10,
            "remaining_quantity": 0,
            "status": "FULFILLED",
            "delivery_status": "READY",
            "backorder_id": None,
            "tracking_number": None,
            "notes": "Ready for courier dispatch",
        },
    ]

    for sample in fulfillment_samples:
        existing_f = db.scalars(
            select(Fulfillment).where(
                Fulfillment.company_id == company.id,
                Fulfillment.product_id == sample["product_id"],
                Fulfillment.notes == sample["notes"],
            )
        ).first()

        if not existing_f:
            f = Fulfillment(
                company_id=company.id,
                product_id=sample["product_id"],
                requested_quantity=sample["requested_quantity"],
                fulfilled_quantity=sample["fulfilled_quantity"],
                remaining_quantity=sample["remaining_quantity"],
                status=sample["status"],
                delivery_status=sample["delivery_status"],
                backorder_id=sample["backorder_id"],
                tracking_number=sample["tracking_number"],
                notes=sample["notes"],
            )
            db.add(f)
            db.flush()
            logger.info(f"Seeded Fulfillment: {sample['delivery_status']} - {sample['status']}")

    # 3. Seed Inventory Alerts
    alert_samples = [
        {
            "product_id": srv_prod.id,
            "alert_type": "BACKORDER",
            "severity": "WARNING",
            "message": f"Product '{srv_prod.sku}' has open backorder for 20 units.",
        },
        {
            "product_id": laptop_prod.id,
            "alert_type": "LOW_STOCK",
            "severity": "WARNING",
            "message": f"Product '{laptop_prod.sku}' ATP is approaching threshold.",
        },
    ]

    for asample in alert_samples:
        existing_alert = db.scalars(
            select(InventoryAlert).where(
                InventoryAlert.company_id == company.id,
                InventoryAlert.product_id == asample["product_id"],
                InventoryAlert.alert_type == asample["alert_type"],
                InventoryAlert.is_active == True,
            )
        ).first()

        if not existing_alert:
            al = InventoryAlert(
                company_id=company.id,
                product_id=asample["product_id"],
                warehouse_id=None,
                alert_type=asample["alert_type"],
                severity=asample["severity"],
                message=asample["message"],
                is_active=True,
            )
            db.add(al)
            db.flush()
            logger.info(f"Seeded InventoryAlert: {asample['alert_type']} ({asample['severity']})")


def run_seed(db: Session) -> None:
    """Execute complete master database seeding in strict dependency order."""
    logger.info("Starting DealFlow360 database master seeding...")
    categories = seed_categories(db)
    seed_units(db)
    seed_attributes(db)
    seed_customer_tiers(db)
    company = seed_companies(db)
    permissions = seed_permissions(db)
    seed_roles(db, permissions)
    warehouses = seed_warehouses(db, company)
    products = seed_products(db, categories)
    seed_variants(db)
    seed_warehouse_stocks(db, warehouses, products)
    seed_g20_inventory_records(db, company, products)
    db.commit()
    logger.info("DealFlow360 database master seeding completed successfully.")



def run_seed_cli() -> None:
    """Entrypoint for CLI execution: python -m app.db.seed"""
    db = SessionLocal()
    try:
        run_seed(db)
    except Exception as exc:
        db.rollback()
        logger.error(f"Seeding failed: {exc}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed_cli()
