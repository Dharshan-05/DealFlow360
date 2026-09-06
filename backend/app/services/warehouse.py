import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.product import Product
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseListResponse,
    WarehouseResponse,
    WarehouseStockCreate,
    WarehouseStockListResponse,
    WarehouseStockResponse,
    WarehouseUpdate,
)
from app.services.atp import AvailableToPromiseService


class WarehouseService:
    """Foundational Warehouse and Stock management service (Phases 086, 087, 089)."""

    # --------------------------------------------------------------------------
    # Phase 086 — Warehouse CRUD
    # --------------------------------------------------------------------------

    @staticmethod
    def _compute_warehouse_totals(db: Session, warehouse_id: uuid.UUID) -> Tuple[int, int, int, int]:
        """Compute aggregate stock counts for a warehouse."""
        stocks = db.query(WarehouseStock).filter(WarehouseStock.warehouse_id == warehouse_id).all()
        total_items = len(stocks)
        total_physical = sum(s.quantity for s in stocks)
        total_reserved = sum(s.reserved_quantity for s in stocks)
        total_atp = sum(s.available_to_promise for s in stocks)
        return total_items, total_physical, total_reserved, total_atp

    @classmethod
    def get_warehouses(
        cls,
        db: Session,
        company_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> WarehouseListResponse:
        """List warehouses for a company with optional filters."""
        query = db.query(Warehouse).filter(Warehouse.company_id == company_id)

        if is_active is not None:
            query = query.filter(Warehouse.is_active == is_active)

        if search and search.strip():
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Warehouse.code.ilike(search_pattern),
                    Warehouse.name.ilike(search_pattern),
                    Warehouse.city.ilike(search_pattern),
                    Warehouse.state.ilike(search_pattern),
                )
            )

        total = query.count()
        warehouses = query.order_by(Warehouse.priority.asc(), Warehouse.code.asc()).offset(skip).limit(limit).all()

        items = []
        for w in warehouses:
            tot_items, tot_phys, tot_res, tot_atp = cls._compute_warehouse_totals(db, w.id)
            items.append(
                WarehouseResponse(
                    id=w.id,
                    company_id=w.company_id,
                    code=w.code,
                    name=w.name,
                    description=w.description,
                    address=w.address,
                    city=w.city,
                    state=w.state,
                    country=w.country,
                    postal_code=w.postal_code,
                    is_active=w.is_active,
                    priority=w.priority,
                    created_at=w.created_at,
                    updated_at=w.updated_at,
                    total_stock_items=tot_items,
                    total_physical_stock=tot_phys,
                    total_reserved_stock=tot_res,
                    total_atp=tot_atp,
                )
            )

        pages = (total + limit - 1) // limit if limit > 0 else 1
        page = (skip // limit) + 1 if limit > 0 else 1

        return WarehouseListResponse(
            items=items,
            total=total,
            page=page,
            size=limit,
            pages=pages,
        )

    @classmethod
    def get_warehouse(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        company_id: Optional[uuid.UUID] = None,
    ) -> WarehouseResponse:
        """Retrieve warehouse details including aggregate stock totals."""
        query = db.query(Warehouse).filter(Warehouse.id == warehouse_id)
        if company_id:
            query = query.filter(Warehouse.company_id == company_id)

        warehouse = query.first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        tot_items, tot_phys, tot_res, tot_atp = cls._compute_warehouse_totals(db, warehouse.id)

        return WarehouseResponse(
            id=warehouse.id,
            company_id=warehouse.company_id,
            code=warehouse.code,
            name=warehouse.name,
            description=warehouse.description,
            address=warehouse.address,
            city=warehouse.city,
            state=warehouse.state,
            country=warehouse.country,
            postal_code=warehouse.postal_code,
            is_active=warehouse.is_active,
            priority=warehouse.priority,
            created_at=warehouse.created_at,
            updated_at=warehouse.updated_at,
            total_stock_items=tot_items,
            total_physical_stock=tot_phys,
            total_reserved_stock=tot_res,
            total_atp=tot_atp,
        )

    @classmethod
    def create_warehouse(
        cls,
        db: Session,
        company_id: uuid.UUID,
        warehouse_in: WarehouseCreate,
        current_user: Optional[User] = None,
    ) -> WarehouseResponse:
        """Create a new warehouse record with code uniqueness check."""
        code_normalized = warehouse_in.code.strip().upper()

        existing = (
            db.query(Warehouse)
            .filter(
                Warehouse.company_id == company_id,
                Warehouse.code == code_normalized,
            )
            .first()
        )
        if existing:
            raise ConflictError(f"Warehouse with code '{code_normalized}' already exists.")

        warehouse = Warehouse(
            company_id=company_id,
            code=code_normalized,
            name=warehouse_in.name.strip(),
            description=warehouse_in.description.strip() if warehouse_in.description else None,
            address=warehouse_in.address.strip() if warehouse_in.address else None,
            city=warehouse_in.city.strip() if warehouse_in.city else None,
            state=warehouse_in.state.strip() if warehouse_in.state else None,
            country=warehouse_in.country.strip() if warehouse_in.country else None,
            postal_code=warehouse_in.postal_code.strip() if warehouse_in.postal_code else None,
            is_active=warehouse_in.is_active,
            priority=warehouse_in.priority,
        )
        db.add(warehouse)
        db.flush()

        if current_user:
            audit = AuditLog(
                action="CREATE",
                resource_type="warehouse",
                resource_id=warehouse.id,
                user_id=current_user.id,
                company_id=company_id,
                context_metadata={"code": warehouse.code, "name": warehouse.name},
            )
            db.add(audit)

        db.commit()
        db.refresh(warehouse)
        return cls.get_warehouse(db, warehouse.id)

    @classmethod
    def update_warehouse(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        warehouse_in: WarehouseUpdate,
        company_id: Optional[uuid.UUID] = None,
        current_user: Optional[User] = None,
    ) -> WarehouseResponse:
        """Update warehouse details."""
        query = db.query(Warehouse).filter(Warehouse.id == warehouse_id)
        if company_id:
            query = query.filter(Warehouse.company_id == company_id)

        warehouse = query.first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        update_data = warehouse_in.model_dump(exclude_unset=True)
        changes = {}

        for field, value in update_data.items():
            if hasattr(warehouse, field):
                old_val = getattr(warehouse, field)
                if old_val != value:
                    setattr(warehouse, field, value)
                    changes[field] = {"old": old_val, "new": value}

        db.flush()

        if current_user and changes:
            audit = AuditLog(
                action="UPDATE",
                resource_type="warehouse",
                resource_id=warehouse.id,
                user_id=current_user.id,
                company_id=warehouse.company_id,
                context_metadata={"changes": changes},
            )
            db.add(audit)

        db.commit()
        db.refresh(warehouse)
        return cls.get_warehouse(db, warehouse.id)

    @classmethod
    def deactivate_warehouse(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        company_id: Optional[uuid.UUID] = None,
        current_user: Optional[User] = None,
    ) -> WarehouseResponse:
        """Soft-deactivate warehouse without destroying historical records."""
        query = db.query(Warehouse).filter(Warehouse.id == warehouse_id)
        if company_id:
            query = query.filter(Warehouse.company_id == company_id)

        warehouse = query.first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        warehouse.is_active = False
        db.flush()

        if current_user:
            audit = AuditLog(
                action="DEACTIVATE",
                resource_type="warehouse",
                resource_id=warehouse.id,
                user_id=current_user.id,
                company_id=warehouse.company_id,
                context_metadata={"action": "soft_deactivate", "code": warehouse.code},
            )
            db.add(audit)

        db.commit()
        db.refresh(warehouse)
        return cls.get_warehouse(db, warehouse.id)

    # --------------------------------------------------------------------------
    # Phase 087 — Warehouse Stock Operations
    # --------------------------------------------------------------------------

    @classmethod
    def get_warehouse_stocks(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
    ) -> WarehouseStockListResponse:
        """List all stock records in a warehouse with product details and ATP."""
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        stocks = (
            db.query(WarehouseStock)
            .options(joinedload(WarehouseStock.product).joinedload(Product.category))
            .filter(WarehouseStock.warehouse_id == warehouse_id)
            .all()
        )

        items = []
        for s in stocks:
            items.append(
                WarehouseStockResponse(
                    id=s.id,
                    warehouse_id=s.warehouse_id,
                    product_id=s.product_id,
                    quantity=s.quantity,
                    reserved_quantity=s.reserved_quantity,
                    available_to_promise=s.available_to_promise,
                    is_available=s.is_available,
                    product_sku=s.product.sku if s.product else None,
                    product_name=s.product.name if s.product else None,
                    product_unit=s.product.unit if s.product else None,
                    category_name=s.product.category.name if (s.product and s.product.category) else None,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )

        total_phys = sum(s.quantity for s in stocks)
        total_res = sum(s.reserved_quantity for s in stocks)
        total_atp = sum(s.available_to_promise for s in stocks)

        return WarehouseStockListResponse(
            warehouse_id=warehouse.id,
            warehouse_code=warehouse.code,
            warehouse_name=warehouse.name,
            items=items,
            total=len(items),
            total_physical=total_phys,
            total_reserved=total_res,
            total_atp=total_atp,
        )

    @classmethod
    def get_stock(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> Optional[WarehouseStock]:
        """Fetch stock record for a specific warehouse and product."""
        return (
            db.query(WarehouseStock)
            .filter(
                WarehouseStock.warehouse_id == warehouse_id,
                WarehouseStock.product_id == product_id,
            )
            .first()
        )

    @classmethod
    def set_stock(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        stock_in: WarehouseStockCreate,
        current_user: Optional[User] = None,
    ) -> WarehouseStockResponse:
        """Create or set physical and reserved stock for a product in a warehouse."""
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        product = db.query(Product).filter(Product.id == stock_in.product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {stock_in.product_id} not found.")

        if stock_in.quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        if stock_in.reserved_quantity < 0:
            raise ValidationError("Reserved quantity cannot be negative.")
        if stock_in.reserved_quantity > stock_in.quantity:
            raise ValidationError(
                f"Reserved quantity ({stock_in.reserved_quantity}) cannot exceed physical stock ({stock_in.quantity})."
            )

        stock = cls.get_stock(db, warehouse_id, stock_in.product_id)
        action = "UPDATE" if stock else "CREATE"

        if stock:
            stock.quantity = stock_in.quantity
            stock.reserved_quantity = stock_in.reserved_quantity
        else:
            stock = WarehouseStock(
                warehouse_id=warehouse_id,
                product_id=stock_in.product_id,
                quantity=stock_in.quantity,
                reserved_quantity=stock_in.reserved_quantity,
            )
            db.add(stock)

        db.flush()

        if current_user:
            audit = AuditLog(
                action=action,
                resource_type="warehouse_stock",
                resource_id=stock.id,
                user_id=current_user.id,
                company_id=warehouse.company_id,
                context_metadata={
                    "warehouse_code": warehouse.code,
                    "product_sku": product.sku,
                    "quantity": stock.quantity,
                    "reserved_quantity": stock.reserved_quantity,
                    "atp": stock.available_to_promise,
                },
            )
            db.add(audit)

        db.commit()
        db.refresh(stock)

        return WarehouseStockResponse(
            id=stock.id,
            warehouse_id=stock.warehouse_id,
            product_id=stock.product_id,
            quantity=stock.quantity,
            reserved_quantity=stock.reserved_quantity,
            available_to_promise=stock.available_to_promise,
            is_available=stock.is_available,
            product_sku=product.sku,
            product_name=product.name,
            product_unit=product.unit,
            category_name=product.category.name if product.category else None,
            created_at=stock.created_at,
            updated_at=stock.updated_at,
        )

    @classmethod
    def update_stock_quantity(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        product_id: uuid.UUID,
        new_quantity: int,
        current_user: Optional[User] = None,
    ) -> WarehouseStockResponse:
        """Update physical stock quantity ensuring it remains >= reserved_quantity."""
        if new_quantity < 0:
            raise ValidationError("Physical stock quantity cannot be negative.")

        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        stock = cls.get_stock(db, warehouse_id, product_id)
        if not stock:
            # If no record exists, create one with 0 reserved
            stock = WarehouseStock(
                warehouse_id=warehouse_id,
                product_id=product_id,
                quantity=new_quantity,
                reserved_quantity=0,
            )
            db.add(stock)
        else:
            if new_quantity < stock.reserved_quantity:
                raise ValidationError(
                    f"Cannot reduce physical stock to {new_quantity} below currently reserved quantity ({stock.reserved_quantity})."
                )
            stock.quantity = new_quantity

        db.flush()

        if current_user:
            audit = AuditLog(
                action="UPDATE_STOCK",
                resource_type="warehouse_stock",
                resource_id=stock.id,
                user_id=current_user.id,
                company_id=warehouse.company_id,
                context_metadata={
                    "product_sku": product.sku,
                    "new_quantity": stock.quantity,
                    "reserved_quantity": stock.reserved_quantity,
                    "atp": stock.available_to_promise,
                },
            )
            db.add(audit)

        db.commit()
        db.refresh(stock)

        try:
            from app.services.event_bus import event_bus
            from app.schemas.realtime import EventEnvelope
            event_bus.publish_sync(
                EventEnvelope(
                    event_type="inventory.updated",
                    company_id=warehouse.company_id,
                    actor_id=current_user.id if current_user else None,
                    entity_type="warehouse_stock",
                    entity_id=str(stock.id),
                    payload={
                        "warehouse_id": str(warehouse.id),
                        "product_id": str(product.id),
                        "product_sku": product.sku,
                        "quantity": stock.quantity,
                        "reserved_quantity": stock.reserved_quantity,
                        "atp": stock.available_to_promise,
                    },
                )
            )
        except Exception:
            pass

        return WarehouseStockResponse(
            id=stock.id,
            warehouse_id=stock.warehouse_id,
            product_id=stock.product_id,
            quantity=stock.quantity,
            reserved_quantity=stock.reserved_quantity,
            available_to_promise=stock.available_to_promise,
            is_available=stock.is_available,
            product_sku=product.sku,
            product_name=product.name,
            product_unit=product.unit,
            category_name=product.category.name if product.category else None,
            created_at=stock.created_at,
            updated_at=stock.updated_at,
        )

    # --------------------------------------------------------------------------
    # Phase 089 — Reserved Stock Operations
    # --------------------------------------------------------------------------

    @classmethod
    def reserve_stock(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        product_id: uuid.UUID,
        amount: int,
        current_user: Optional[User] = None,
    ) -> WarehouseStockResponse:
        """Foundational reservation: increment reserved_quantity by amount (Phase 089)."""
        if amount <= 0:
            raise ValidationError("Reservation amount must be strictly positive.")

        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        stock = cls.get_stock(db, warehouse_id, product_id)
        if not stock:
            raise ValidationError(
                f"Cannot reserve stock for product '{product.sku}': no physical stock record in warehouse '{warehouse.code}'."
            )

        new_reserved = stock.reserved_quantity + amount
        if new_reserved > stock.quantity:
            available = max(stock.quantity - stock.reserved_quantity, 0)
            raise ValidationError(
                f"Cannot reserve {amount} units. Only {available} units available to promise (Physical: {stock.quantity}, Already Reserved: {stock.reserved_quantity})."
            )

        stock.reserved_quantity = new_reserved
        db.flush()

        if current_user:
            audit = AuditLog(
                action="RESERVE_STOCK",
                resource_type="warehouse_stock",
                resource_id=stock.id,
                user_id=current_user.id,
                company_id=warehouse.company_id,
                context_metadata={
                    "reserved_amount": amount,
                    "new_reserved_total": stock.reserved_quantity,
                    "atp": stock.available_to_promise,
                },
            )
            db.add(audit)

        db.commit()
        db.refresh(stock)

        return WarehouseStockResponse(
            id=stock.id,
            warehouse_id=stock.warehouse_id,
            product_id=stock.product_id,
            quantity=stock.quantity,
            reserved_quantity=stock.reserved_quantity,
            available_to_promise=stock.available_to_promise,
            is_available=stock.is_available,
            product_sku=product.sku,
            product_name=product.name,
            product_unit=product.unit,
            category_name=product.category.name if product.category else None,
            created_at=stock.created_at,
            updated_at=stock.updated_at,
        )

    @classmethod
    def release_stock(
        cls,
        db: Session,
        warehouse_id: uuid.UUID,
        product_id: uuid.UUID,
        amount: int,
        current_user: Optional[User] = None,
    ) -> WarehouseStockResponse:
        """Foundational release: decrement reserved_quantity by amount (Phase 089)."""
        if amount <= 0:
            raise ValidationError("Release amount must be strictly positive.")

        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        if not warehouse:
            raise NotFoundError(f"Warehouse with id {warehouse_id} not found.")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {product_id} not found.")

        stock = cls.get_stock(db, warehouse_id, product_id)
        if not stock:
            raise ValidationError(
                f"Cannot release stock for product '{product.sku}': no stock record in warehouse '{warehouse.code}'."
            )

        if amount > stock.reserved_quantity:
            raise ValidationError(
                f"Cannot release {amount} units. Current reserved quantity is only {stock.reserved_quantity}."
            )

        stock.reserved_quantity -= amount
        db.flush()

        if current_user:
            audit = AuditLog(
                action="RELEASE_STOCK",
                resource_type="warehouse_stock",
                resource_id=stock.id,
                user_id=current_user.id,
                company_id=warehouse.company_id,
                context_metadata={
                    "released_amount": amount,
                    "new_reserved_total": stock.reserved_quantity,
                    "atp": stock.available_to_promise,
                },
            )
            db.add(audit)

        db.commit()
        db.refresh(stock)

        return WarehouseStockResponse(
            id=stock.id,
            warehouse_id=stock.warehouse_id,
            product_id=stock.product_id,
            quantity=stock.quantity,
            reserved_quantity=stock.reserved_quantity,
            available_to_promise=stock.available_to_promise,
            is_available=stock.is_available,
            product_sku=product.sku,
            product_name=product.name,
            product_unit=product.unit,
            category_name=product.category.name if product.category else None,
            created_at=stock.created_at,
            updated_at=stock.updated_at,
        )
