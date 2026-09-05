"""Product and Product Category Service Layer (Phases 071–075).

Handles business logic for:
- Phase 071: Product CRUD (Create, Read, List, Update, Delete)
- Phase 072: Product Categories (Create, Read, List, Update, Delete with reference safety)
- Phase 073: Product Pricing (Explicit selling price, Decimal currency precision, price >= 0)
- Phase 074: Product Cost (Product cost validation, cost >= 0)
- Phase 075: Product Margin (Basic gross margin calculations, zero-division safety)
"""
import uuid
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import ApplicationError
from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.models.product import Product
from app.models.product_category import ProductCategory
from app.models.user import User
from app.schemas.product import (
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCreate,
    ProductUpdate,
)


class ProductCategoryService:
    """Service layer for Product Categories (Phase 072)."""

    @classmethod
    def get_categories(
        cls,
        db: Session,
        include_inactive: bool = False,
    ) -> List[ProductCategory]:
        """List product categories."""
        stmt = select(ProductCategory).order_by(ProductCategory.name.asc())
        if not include_inactive:
            stmt = stmt.where(ProductCategory.is_active == True)
        return list(db.scalars(stmt).all())

    @classmethod
    def get_category_by_id(cls, db: Session, category_id: uuid.UUID) -> ProductCategory:
        """Get product category by ID or raise 404."""
        category = db.get(ProductCategory, category_id)
        if not category:
            raise ApplicationError(
                message=f"Product category with ID '{category_id}' not found.",
                code="CATEGORY_NOT_FOUND",
                status_code=404,
            )
        return category

    @classmethod
    def create_category(
        cls,
        db: Session,
        data: ProductCategoryCreate,
        current_user: User,
    ) -> ProductCategory:
        """Create a new product category with code/name uniqueness validation."""
        code = data.code.strip().upper()
        name = data.name.strip()

        # Check code uniqueness
        existing_code = db.scalars(
            select(ProductCategory).where(ProductCategory.code == code)
        ).first()
        if existing_code:
            raise ApplicationError(
                message=f"Product category with code '{code}' already exists.",
                code="CATEGORY_CODE_EXISTS",
                status_code=400,
            )

        # Check name uniqueness
        existing_name = db.scalars(
            select(ProductCategory).where(ProductCategory.name == name)
        ).first()
        if existing_name:
            raise ApplicationError(
                message=f"Product category with name '{name}' already exists.",
                code="CATEGORY_NAME_EXISTS",
                status_code=400,
            )

        category = ProductCategory(
            name=name,
            code=code,
            description=data.description,
            is_active=data.is_active,
        )
        db.add(category)
        db.flush()

        audit = AuditLog(
            action="CREATE",
            resource_type="product_category",
            resource_id=category.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"code": category.code, "name": category.name},
        )
        db.add(audit)
        db.commit()
        db.refresh(category)
        logger.info(f"Created product category: {category.code} by user {current_user.id}")
        return category

    @classmethod
    def update_category(
        cls,
        db: Session,
        category_id: uuid.UUID,
        data: ProductCategoryUpdate,
        current_user: User,
    ) -> ProductCategory:
        """Update an existing product category."""
        category = cls.get_category_by_id(db, category_id)

        if data.name is not None and data.name.strip() != category.name:
            new_name = data.name.strip()
            existing_name = db.scalars(
                select(ProductCategory).where(
                    ProductCategory.name == new_name,
                    ProductCategory.id != category.id,
                )
            ).first()
            if existing_name:
                raise ApplicationError(
                    message=f"Product category with name '{new_name}' already exists.",
                    code="CATEGORY_NAME_EXISTS",
                    status_code=400,
                )
            category.name = new_name

        if data.description is not None:
            category.description = data.description

        if data.is_active is not None:
            category.is_active = data.is_active

        db.flush()

        audit = AuditLog(
            action="UPDATE",
            resource_type="product_category",
            resource_id=category.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"name": category.name, "is_active": category.is_active},
        )
        db.add(audit)
        db.commit()
        db.refresh(category)
        logger.info(f"Updated product category: {category.code} by user {current_user.id}")
        return category

    @classmethod
    def delete_category(
        cls,
        db: Session,
        category_id: uuid.UUID,
        current_user: User,
        soft: bool = True,
    ) -> None:
        """Delete or deactivate product category safely without corrupting products."""
        category = cls.get_category_by_id(db, category_id)

        # Check referencing products count
        product_count = db.scalar(
            select(func.count(Product.id)).where(Product.category_id == category_id)
        ) or 0

        if soft:
            category.is_active = False
            action_type = "DEACTIVATE"
        else:
            if product_count > 0:
                # If products reference it, either detach category or reject hard delete
                # Our schema specifies ondelete="SET NULL", but business logic can detach explicitly
                db.query(Product).filter(Product.category_id == category_id).update({"category_id": None})
            db.delete(category)
            action_type = "HARD_DELETE"

        audit = AuditLog(
            action=action_type,
            resource_type="product_category",
            resource_id=category_id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"code": category.code, "affected_products": product_count},
        )
        db.add(audit)
        db.commit()
        logger.info(f"Product category {category_id} ({category.code}) {action_type} by user {current_user.id}")


class ProductService:
    """Service layer for Product Management, Pricing, Cost, and Margin (Phases 071, 073, 074, 075)."""

    @classmethod
    def get_products(
        cls,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        category_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Product], int]:
        """List products with pagination and category join."""
        query = select(Product).options(joinedload(Product.category))

        if category_id is not None:
            query = query.where(Product.category_id == category_id)

        if is_active is not None:
            query = query.where(Product.is_active == is_active)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

        stmt = query.order_by(Product.name.asc()).offset(skip).limit(limit)
        items = list(db.scalars(stmt).unique().all())
        return items, total

    @classmethod
    def get_product_by_id(cls, db: Session, product_id: uuid.UUID) -> Product:
        """Retrieve single product by ID or raise 404."""
        product = db.scalars(
            select(Product)
            .options(joinedload(Product.category))
            .where(Product.id == product_id)
        ).first()

        if not product:
            raise ApplicationError(
                message=f"Product with ID '{product_id}' not found.",
                code="PRODUCT_NOT_FOUND",
                status_code=404,
            )
        return product

    @classmethod
    def create_product(
        cls,
        db: Session,
        data: ProductCreate,
        current_user: User,
    ) -> Product:
        """Create a new product catalog item with pricing, cost, and SKU uniqueness."""
        sku = data.sku.strip().upper()

        # SKU uniqueness
        existing = db.scalars(select(Product).where(Product.sku == sku)).first()
        if existing:
            raise ApplicationError(
                message=f"Product with SKU '{sku}' already exists.",
                code="PRODUCT_SKU_EXISTS",
                status_code=400,
            )

        # Validate category reference if provided (Phase 072)
        if data.category_id:
            category = db.get(ProductCategory, data.category_id)
            if not category:
                raise ApplicationError(
                    message=f"Referenced product category '{data.category_id}' does not exist.",
                    code="INVALID_CATEGORY_REFERENCE",
                    status_code=400,
                )

        # Price and Cost validation (Phases 073 & 074)
        cost = Decimal(str(data.cost)).quantize(Decimal("0.01"))
        base_price = Decimal(str(data.base_price)).quantize(Decimal("0.01"))

        if base_price < Decimal("0.00"):
            raise ApplicationError(
                message="Selling price cannot be negative.",
                code="INVALID_PRICE",
                status_code=422,
            )

        if cost < Decimal("0.00"):
            raise ApplicationError(
                message="Product cost cannot be negative.",
                code="INVALID_COST",
                status_code=422,
            )

        product = Product(
            sku=sku,
            name=data.name.strip(),
            description=data.description,
            category_id=data.category_id,
            cost=cost,
            base_price=base_price,
            is_active=data.is_active,
        )
        db.add(product)
        db.flush()

        audit = AuditLog(
            action="CREATE",
            resource_type="product",
            resource_id=product.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={
                "sku": product.sku,
                "name": product.name,
                "base_price": str(product.base_price),
                "cost": str(product.cost),
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(product)
        logger.info(f"Created product: {product.sku} by user {current_user.id}")
        return cls.get_product_by_id(db, product.id)

    @classmethod
    def update_product(
        cls,
        db: Session,
        product_id: uuid.UUID,
        data: ProductUpdate,
        current_user: User,
    ) -> Product:
        """Update an existing product's fields, pricing, and cost."""
        product = cls.get_product_by_id(db, product_id)

        if data.name is not None:
            product.name = data.name.strip()

        if data.description is not None:
            product.description = data.description

        if data.category_id is not None:
            # Validate category reference
            cat = db.get(ProductCategory, data.category_id)
            if not cat:
                raise ApplicationError(
                    message=f"Referenced product category '{data.category_id}' does not exist.",
                    code="INVALID_CATEGORY_REFERENCE",
                    status_code=400,
                )
            product.category_id = data.category_id

        # Phase 073: Product Pricing
        if data.base_price is not None:
            price = Decimal(str(data.base_price)).quantize(Decimal("0.01"))
            if price < Decimal("0.00"):
                raise ApplicationError(
                    message="Selling price cannot be negative.",
                    code="INVALID_PRICE",
                    status_code=422,
                )
            product.base_price = price

        # Phase 074: Product Cost
        if data.cost is not None:
            cost = Decimal(str(data.cost)).quantize(Decimal("0.01"))
            if cost < Decimal("0.00"):
                raise ApplicationError(
                    message="Product cost cannot be negative.",
                    code="INVALID_COST",
                    status_code=422,
                )
            product.cost = cost

        if data.is_active is not None:
            product.is_active = data.is_active

        db.flush()

        audit = AuditLog(
            action="UPDATE",
            resource_type="product",
            resource_id=product.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={
                "sku": product.sku,
                "name": product.name,
                "base_price": str(product.base_price),
                "cost": str(product.cost),
                "is_active": product.is_active,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(product)
        logger.info(f"Updated product: {product.sku} by user {current_user.id}")
        return cls.get_product_by_id(db, product.id)

    @classmethod
    def delete_product(
        cls,
        db: Session,
        product_id: uuid.UUID,
        current_user: User,
        soft: bool = True,
    ) -> None:
        """Deactivate or delete a product catalog item safely."""
        product = cls.get_product_by_id(db, product_id)

        if soft:
            product.is_active = False
            action_type = "DEACTIVATE"
        else:
            db.delete(product)
            action_type = "HARD_DELETE"

        audit = AuditLog(
            action=action_type,
            resource_type="product",
            resource_id=product_id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"sku": product.sku, "name": product.name},
        )
        db.add(audit)
        db.commit()
        logger.info(f"Product {product_id} ({product.sku}) {action_type} by user {current_user.id}")
