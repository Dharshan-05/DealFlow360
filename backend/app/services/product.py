"""Product, Category, Units, Variants, and Attributes Service Layer (Phases 071–080).

Handles business logic for:
- Phase 071: Product CRUD
- Phase 072: Product Categories
- Phase 073: Product Pricing (Decimal currency precision, price >= 0)
- Phase 074: Product Cost (Product cost validation, cost >= 0)
- Phase 075: Product Margin (Gross margin calculations, zero-division safety)
- Phase 076: Product Tax (Decimal percentage precision, tax_rate >= 0)
- Phase 077: Product Units (Catalog of units of measure)
- Phase 078: Product Variants (Parent-child product variations, price/cost overrides, SKU uniqueness)
- Phase 079: Product Attributes (Attribute definitions, attribute values, variant links)
- Phase 080: Subscription Products (is_subscription boolean flag validation)
"""
import uuid
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.errors import ApplicationError
from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.models.product import Product
from app.models.product_attribute import ProductAttribute, ProductAttributeValue
from app.models.product_category import ProductCategory
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.schemas.product import (
    ProductAttributeCreate,
    ProductAttributeUpdate,
    ProductAttributeValueCreate,
    ProductCategoryCreate,
    ProductCategoryUpdate,
    ProductCreate,
    ProductUnitCreate,
    ProductUnitUpdate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantUpdate,
)


# ===========================================================================
# Phase 072: Product Categories Service
# ===========================================================================

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

        product_count = db.scalar(
            select(func.count(Product.id)).where(Product.category_id == category_id)
        ) or 0

        if soft:
            category.is_active = False
            action_type = "DEACTIVATE"
        else:
            if product_count > 0:
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


# ===========================================================================
# Phase 077: Product Units Service
# ===========================================================================

class ProductUnitService:
    """Service layer for Product Units (Phase 077)."""

    @classmethod
    def get_units(
        cls,
        db: Session,
        include_inactive: bool = False,
    ) -> List[ProductUnit]:
        """List all product units."""
        stmt = select(ProductUnit).order_by(ProductUnit.name.asc())
        if not include_inactive:
            stmt = stmt.where(ProductUnit.is_active == True)
        return list(db.scalars(stmt).all())

    @classmethod
    def get_unit_by_id(cls, db: Session, unit_id: uuid.UUID) -> ProductUnit:
        """Get product unit by ID or raise 404."""
        unit = db.get(ProductUnit, unit_id)
        if not unit:
            raise ApplicationError(
                message=f"Product unit with ID '{unit_id}' not found.",
                code="UNIT_NOT_FOUND",
                status_code=404,
            )
        return unit

    @classmethod
    def create_unit(
        cls,
        db: Session,
        data: ProductUnitCreate,
        current_user: User,
    ) -> ProductUnit:
        """Create a new product unit with code uniqueness check."""
        code = data.code.strip().upper()
        name = data.name.strip()

        existing = db.scalars(select(ProductUnit).where(ProductUnit.code == code)).first()
        if existing:
            raise ApplicationError(
                message=f"Product unit with code '{code}' already exists.",
                code="UNIT_CODE_EXISTS",
                status_code=400,
            )

        unit = ProductUnit(
            code=code,
            name=name,
            description=data.description,
            is_active=data.is_active,
        )
        db.add(unit)
        db.flush()

        audit = AuditLog(
            action="CREATE",
            resource_type="product_unit",
            resource_id=unit.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"code": unit.code, "name": unit.name},
        )
        db.add(audit)
        db.commit()
        db.refresh(unit)
        logger.info(f"Created product unit: {unit.code} by user {current_user.id}")
        return unit

    @classmethod
    def update_unit(
        cls,
        db: Session,
        unit_id: uuid.UUID,
        data: ProductUnitUpdate,
        current_user: User,
    ) -> ProductUnit:
        """Update product unit details."""
        unit = cls.get_unit_by_id(db, unit_id)

        if data.name is not None:
            unit.name = data.name.strip()

        if data.description is not None:
            unit.description = data.description

        if data.is_active is not None:
            unit.is_active = data.is_active

        db.flush()

        audit = AuditLog(
            action="UPDATE",
            resource_type="product_unit",
            resource_id=unit.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"code": unit.code, "name": unit.name, "is_active": unit.is_active},
        )
        db.add(audit)
        db.commit()
        db.refresh(unit)
        logger.info(f"Updated product unit: {unit.code} by user {current_user.id}")
        return unit

    @classmethod
    def delete_unit(
        cls,
        db: Session,
        unit_id: uuid.UUID,
        current_user: User,
        soft: bool = True,
    ) -> None:
        """Deactivate or hard delete a product unit."""
        unit = cls.get_unit_by_id(db, unit_id)

        if soft:
            unit.is_active = False
            action_type = "DEACTIVATE"
        else:
            db.delete(unit)
            action_type = "HARD_DELETE"

        audit = AuditLog(
            action=action_type,
            resource_type="product_unit",
            resource_id=unit_id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"code": unit.code},
        )
        db.add(audit)
        db.commit()
        logger.info(f"Product unit {unit_id} ({unit.code}) {action_type} by user {current_user.id}")


# ===========================================================================
# Phase 079: Product Attributes Service
# ===========================================================================

class ProductAttributeService:
    """Service layer for Product Attributes and Values (Phase 079)."""

    @classmethod
    def get_attributes(
        cls,
        db: Session,
        include_inactive: bool = False,
    ) -> List[ProductAttribute]:
        """List attributes with their options/values."""
        stmt = select(ProductAttribute).options(selectinload(ProductAttribute.values)).order_by(ProductAttribute.name.asc())
        if not include_inactive:
            stmt = stmt.where(ProductAttribute.is_active == True)
        return list(db.scalars(stmt).all())

    @classmethod
    def get_attribute_by_id(cls, db: Session, attr_id: uuid.UUID) -> ProductAttribute:
        """Get product attribute definition by ID or raise 404."""
        attr = db.scalars(
            select(ProductAttribute)
            .options(selectinload(ProductAttribute.values))
            .where(ProductAttribute.id == attr_id)
        ).first()
        if not attr:
            raise ApplicationError(
                message=f"Product attribute with ID '{attr_id}' not found.",
                code="ATTRIBUTE_NOT_FOUND",
                status_code=404,
            )
        return attr

    @classmethod
    def create_attribute(
        cls,
        db: Session,
        data: ProductAttributeCreate,
        current_user: User,
    ) -> ProductAttribute:
        """Create a new product attribute."""
        code = data.code.strip().upper()
        name = data.name.strip()

        existing = db.scalars(select(ProductAttribute).where(ProductAttribute.code == code)).first()
        if existing:
            raise ApplicationError(
                message=f"Product attribute with code '{code}' already exists.",
                code="ATTRIBUTE_CODE_EXISTS",
                status_code=400,
            )

        attr = ProductAttribute(
            code=code,
            name=name,
            description=data.description,
            is_active=data.is_active,
        )
        db.add(attr)
        db.flush()

        audit = AuditLog(
            action="CREATE",
            resource_type="product_attribute",
            resource_id=attr.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"code": attr.code, "name": attr.name},
        )
        db.add(audit)
        db.commit()
        db.refresh(attr)
        logger.info(f"Created product attribute: {attr.code} by user {current_user.id}")
        return cls.get_attribute_by_id(db, attr.id)

    @classmethod
    def update_attribute(
        cls,
        db: Session,
        attr_id: uuid.UUID,
        data: ProductAttributeUpdate,
        current_user: User,
    ) -> ProductAttribute:
        """Update a product attribute."""
        attr = cls.get_attribute_by_id(db, attr_id)

        if data.name is not None:
            attr.name = data.name.strip()

        if data.description is not None:
            attr.description = data.description

        if data.is_active is not None:
            attr.is_active = data.is_active

        db.flush()

        audit = AuditLog(
            action="UPDATE",
            resource_type="product_attribute",
            resource_id=attr.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"code": attr.code, "name": attr.name, "is_active": attr.is_active},
        )
        db.add(audit)
        db.commit()
        db.refresh(attr)
        logger.info(f"Updated product attribute: {attr.code} by user {current_user.id}")
        return cls.get_attribute_by_id(db, attr.id)

    @classmethod
    def delete_attribute(
        cls,
        db: Session,
        attr_id: uuid.UUID,
        current_user: User,
    ) -> None:
        """Delete a product attribute and its associated values."""
        attr = cls.get_attribute_by_id(db, attr_id)
        db.delete(attr)
        audit = AuditLog(
            action="DELETE",
            resource_type="product_attribute",
            resource_id=attr_id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"code": attr.code},
        )
        db.add(audit)
        db.commit()
        logger.info(f"Deleted product attribute {attr_id} ({attr.code}) by user {current_user.id}")

    @classmethod
    def add_attribute_value(
        cls,
        db: Session,
        attr_id: uuid.UUID,
        data: ProductAttributeValueCreate,
        current_user: User,
    ) -> ProductAttributeValue:
        """Add an option/value to an attribute."""
        attr = cls.get_attribute_by_id(db, attr_id)
        val_str = data.value.strip()

        # Check existing value under this attribute
        existing = db.scalars(
            select(ProductAttributeValue).where(
                ProductAttributeValue.attribute_id == attr.id,
                func.lower(ProductAttributeValue.value) == val_str.lower(),
            )
        ).first()
        if existing:
            raise ApplicationError(
                message=f"Value '{val_str}' already exists for attribute '{attr.name}'.",
                code="ATTRIBUTE_VALUE_EXISTS",
                status_code=400,
            )

        val = ProductAttributeValue(
            attribute_id=attr.id,
            value=val_str,
            display_order=data.display_order,
        )
        db.add(val)
        db.flush()

        audit = AuditLog(
            action="CREATE",
            resource_type="product_attribute_value",
            resource_id=val.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"attribute_code": attr.code, "value": val.value},
        )
        db.add(audit)
        db.commit()
        db.refresh(val)
        return val

    @classmethod
    def delete_attribute_value(
        cls,
        db: Session,
        attr_id: uuid.UUID,
        val_id: uuid.UUID,
        current_user: User,
    ) -> None:
        """Delete an option/value from an attribute."""
        val = db.scalars(
            select(ProductAttributeValue).where(
                ProductAttributeValue.id == val_id,
                ProductAttributeValue.attribute_id == attr_id,
            )
        ).first()
        if not val:
            raise ApplicationError(
                message=f"Attribute value with ID '{val_id}' not found.",
                code="ATTRIBUTE_VALUE_NOT_FOUND",
                status_code=404,
            )

        db.delete(val)
        audit = AuditLog(
            action="DELETE",
            resource_type="product_attribute_value",
            resource_id=val_id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"value": val.value},
        )
        db.add(audit)
        db.commit()


# ===========================================================================
# Phase 078: Product Variants Service
# ===========================================================================

class ProductVariantService:
    """Service layer for Product Variants (Phase 078)."""

    @classmethod
    def get_variants_by_product(
        cls,
        db: Session,
        product_id: uuid.UUID,
        include_inactive: bool = False,
    ) -> List[ProductVariant]:
        """List variants of a parent product."""
        stmt = (
            select(ProductVariant)
            .options(joinedload(ProductVariant.attribute_values))
            .where(ProductVariant.product_id == product_id)
            .order_by(ProductVariant.sku.asc())
        )
        if not include_inactive:
            stmt = stmt.where(ProductVariant.is_active == True)
        return list(db.scalars(stmt).unique().all())

    @classmethod
    def get_variant_by_id(cls, db: Session, variant_id: uuid.UUID) -> ProductVariant:
        """Get variant by ID or raise 404."""
        variant = db.scalars(
            select(ProductVariant)
            .options(joinedload(ProductVariant.attribute_values))
            .where(ProductVariant.id == variant_id)
        ).first()
        if not variant:
            raise ApplicationError(
                message=f"Product variant with ID '{variant_id}' not found.",
                code="VARIANT_NOT_FOUND",
                status_code=404,
            )
        return variant

    @classmethod
    def create_variant(
        cls,
        db: Session,
        product_id: uuid.UUID,
        data: ProductVariantCreate,
        current_user: User,
    ) -> ProductVariant:
        """Create a new product variant for a parent product."""
        parent_product = db.get(Product, product_id)
        if not parent_product:
            raise ApplicationError(
                message=f"Parent product with ID '{product_id}' not found.",
                code="PRODUCT_NOT_FOUND",
                status_code=404,
            )

        sku = data.sku.strip().upper()
        # Ensure SKU uniqueness across variants AND products
        existing_variant_sku = db.scalars(select(ProductVariant).where(ProductVariant.sku == sku)).first()
        existing_product_sku = db.scalars(select(Product).where(Product.sku == sku)).first()
        if existing_variant_sku or existing_product_sku:
            raise ApplicationError(
                message=f"SKU '{sku}' is already in use.",
                code="SKU_ALREADY_EXISTS",
                status_code=400,
            )

        # Price and cost validation if provided
        cost = Decimal(str(data.cost)).quantize(Decimal("0.01")) if data.cost is not None else None
        base_price = Decimal(str(data.base_price)).quantize(Decimal("0.01")) if data.base_price is not None else None

        if base_price is not None and base_price < Decimal("0.00"):
            raise ApplicationError(
                message="Variant selling price cannot be negative.",
                code="INVALID_PRICE",
                status_code=422,
            )

        if cost is not None and cost < Decimal("0.00"):
            raise ApplicationError(
                message="Variant cost cannot be negative.",
                code="INVALID_COST",
                status_code=422,
            )

        # Retrieve attribute values
        attr_values: List[ProductAttributeValue] = []
        if data.attribute_value_ids:
            for avid in data.attribute_value_ids:
                val = db.get(ProductAttributeValue, avid)
                if val:
                    attr_values.append(val)

        variant = ProductVariant(
            product_id=product_id,
            sku=sku,
            name=data.name.strip(),
            cost=cost,
            base_price=base_price,
            is_active=data.is_active,
            attribute_values=attr_values,
        )
        db.add(variant)
        db.flush()

        audit = AuditLog(
            action="CREATE",
            resource_type="product_variant",
            resource_id=variant.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"product_id": str(product_id), "sku": variant.sku, "name": variant.name},
        )
        db.add(audit)
        db.commit()
        db.refresh(variant)
        logger.info(f"Created variant {variant.sku} for product {product_id} by user {current_user.id}")
        return cls.get_variant_by_id(db, variant.id)

    @classmethod
    def update_variant(
        cls,
        db: Session,
        variant_id: uuid.UUID,
        data: ProductVariantUpdate,
        current_user: User,
    ) -> ProductVariant:
        """Update an existing product variant."""
        variant = cls.get_variant_by_id(db, variant_id)

        if data.sku is not None:
            new_sku = data.sku.strip().upper()
            if new_sku != variant.sku:
                existing_variant = db.scalars(
                    select(ProductVariant).where(ProductVariant.sku == new_sku, ProductVariant.id != variant.id)
                ).first()
                existing_product = db.scalars(select(Product).where(Product.sku == new_sku)).first()
                if existing_variant or existing_product:
                    raise ApplicationError(
                        message=f"SKU '{new_sku}' is already in use.",
                        code="SKU_ALREADY_EXISTS",
                        status_code=400,
                    )
                variant.sku = new_sku

        if data.name is not None:
            variant.name = data.name.strip()

        if data.base_price is not None:
            price = Decimal(str(data.base_price)).quantize(Decimal("0.01"))
            if price < Decimal("0.00"):
                raise ApplicationError(
                    message="Variant selling price cannot be negative.",
                    code="INVALID_PRICE",
                    status_code=422,
                )
            variant.base_price = price

        if data.cost is not None:
            cost = Decimal(str(data.cost)).quantize(Decimal("0.01"))
            if cost < Decimal("0.00"):
                raise ApplicationError(
                    message="Variant cost cannot be negative.",
                    code="INVALID_COST",
                    status_code=422,
                )
            variant.cost = cost

        if data.is_active is not None:
            variant.is_active = data.is_active

        if data.attribute_value_ids is not None:
            attr_values: List[ProductAttributeValue] = []
            for avid in data.attribute_value_ids:
                val = db.get(ProductAttributeValue, avid)
                if val:
                    attr_values.append(val)
            variant.attribute_values = attr_values

        db.flush()

        audit = AuditLog(
            action="UPDATE",
            resource_type="product_variant",
            resource_id=variant.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"sku": variant.sku, "name": variant.name, "is_active": variant.is_active},
        )
        db.add(audit)
        db.commit()
        db.refresh(variant)
        logger.info(f"Updated variant {variant.sku} by user {current_user.id}")
        return cls.get_variant_by_id(db, variant.id)

    @classmethod
    def delete_variant(
        cls,
        db: Session,
        variant_id: uuid.UUID,
        current_user: User,
        soft: bool = True,
    ) -> None:
        """Deactivate or hard delete a variant."""
        variant = cls.get_variant_by_id(db, variant_id)

        if soft:
            variant.is_active = False
            action_type = "DEACTIVATE"
        else:
            db.delete(variant)
            action_type = "HARD_DELETE"

        audit = AuditLog(
            action=action_type,
            resource_type="product_variant",
            resource_id=variant_id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            context_metadata={"sku": variant.sku},
        )
        db.add(audit)
        db.commit()
        logger.info(f"Product variant {variant_id} ({variant.sku}) {action_type} by user {current_user.id}")


# ===========================================================================
# Phases 071, 073, 074, 075, 076, 077, 080: Product Service
# ===========================================================================

class ProductService:
    """Service layer for Product Management, Pricing, Cost, Margin, Tax, Unit, and Subscription."""

    @classmethod
    def get_products(
        cls,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        category_id: Optional[uuid.UUID] = None,
        is_subscription: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Product], int]:
        """List products with pagination, category, and variants."""
        query = select(Product).options(
            joinedload(Product.category),
            selectinload(Product.variants).joinedload(ProductVariant.attribute_values),
        )

        if category_id is not None:
            query = query.where(Product.category_id == category_id)

        if is_subscription is not None:
            query = query.where(Product.is_subscription == is_subscription)

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
            .options(
                joinedload(Product.category),
                selectinload(Product.variants).joinedload(ProductVariant.attribute_values),
            )
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
        """Create a new product catalog item with tax rate, unit, subscription, and margin."""
        sku = data.sku.strip().upper()

        # SKU uniqueness across products and variants
        existing = db.scalars(select(Product).where(Product.sku == sku)).first()
        existing_variant = db.scalars(select(ProductVariant).where(ProductVariant.sku == sku)).first()
        if existing or existing_variant:
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

        # Phase 076: Tax rate validation
        tax_rate = Decimal(str(data.tax_rate)).quantize(Decimal("0.01"))
        if tax_rate < Decimal("0.00"):
            raise ApplicationError(
                message="Tax rate cannot be negative.",
                code="INVALID_TAX_RATE",
                status_code=422,
            )

        # Phase 077: Unit normalization
        unit = data.unit.strip().lower() if data.unit else "unit"

        product = Product(
            sku=sku,
            name=data.name.strip(),
            description=data.description,
            category_id=data.category_id,
            cost=cost,
            base_price=base_price,
            unit=unit,
            tax_rate=tax_rate,
            is_subscription=data.is_subscription,
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
                "tax_rate": str(product.tax_rate),
                "unit": product.unit,
                "is_subscription": product.is_subscription,
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
        """Update an existing product's fields, pricing, tax, unit, and subscription."""
        product = cls.get_product_by_id(db, product_id)

        if data.name is not None:
            product.name = data.name.strip()

        if data.description is not None:
            product.description = data.description

        if data.category_id is not None:
            cat = db.get(ProductCategory, data.category_id)
            if not cat:
                raise ApplicationError(
                    message=f"Referenced product category '{data.category_id}' does not exist.",
                    code="INVALID_CATEGORY_REFERENCE",
                    status_code=400,
                )
            product.category_id = data.category_id

        if data.base_price is not None:
            price = Decimal(str(data.base_price)).quantize(Decimal("0.01"))
            if price < Decimal("0.00"):
                raise ApplicationError(
                    message="Selling price cannot be negative.",
                    code="INVALID_PRICE",
                    status_code=422,
                )
            product.base_price = price

        if data.cost is not None:
            cost = Decimal(str(data.cost)).quantize(Decimal("0.01"))
            if cost < Decimal("0.00"):
                raise ApplicationError(
                    message="Product cost cannot be negative.",
                    code="INVALID_COST",
                    status_code=422,
                )
            product.cost = cost

        # Phase 076: Product Tax
        if data.tax_rate is not None:
            tax = Decimal(str(data.tax_rate)).quantize(Decimal("0.01"))
            if tax < Decimal("0.00"):
                raise ApplicationError(
                    message="Tax rate cannot be negative.",
                    code="INVALID_TAX_RATE",
                    status_code=422,
                )
            product.tax_rate = tax

        # Phase 077: Product Unit
        if data.unit is not None:
            product.unit = data.unit.strip().lower()

        # Phase 080: Subscription Product
        if data.is_subscription is not None:
            product.is_subscription = data.is_subscription

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
                "tax_rate": str(product.tax_rate),
                "unit": product.unit,
                "is_subscription": product.is_subscription,
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
