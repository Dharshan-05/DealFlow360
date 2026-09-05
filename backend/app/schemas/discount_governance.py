"""Pydantic schemas for Discount Governance (Phases 101–105)."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# Phase 101: Discount Configuration Schemas
# ==============================================================================

class DiscountConfigurationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    default_discount_ceiling: Decimal = Field(..., ge=0, le=100, description="Percentage between 0 and 100")
    is_active: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None

    @field_validator("effective_until")
    @classmethod
    def validate_dates(cls, v, values):
        if v is not None and "effective_from" in values.data:
            if v < values.data["effective_from"]:
                raise ValueError("effective_until cannot precede effective_from")
        return v


class DiscountConfigurationCreate(DiscountConfigurationBase):
    pass


class DiscountConfigurationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    default_discount_ceiling: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class DiscountConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    description: Optional[str] = None
    default_discount_ceiling: Decimal
    is_active: bool
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class DiscountConfigurationListResponse(BaseModel):
    items: List[DiscountConfigurationResponse]
    total: int


# ==============================================================================
# Phase 102: Customer Discount Ceiling Schemas
# ==============================================================================

class CustomerDiscountCeilingBase(BaseModel):
    customer_id: uuid.UUID
    max_discount_percentage: Decimal = Field(..., ge=0, le=100, description="Percentage between 0 and 100")
    is_active: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None

    @field_validator("effective_until")
    @classmethod
    def validate_dates(cls, v, values):
        if v is not None and "effective_from" in values.data:
            if v < values.data["effective_from"]:
                raise ValueError("effective_until cannot precede effective_from")
        return v


class CustomerDiscountCeilingCreate(CustomerDiscountCeilingBase):
    pass


class CustomerDiscountCeilingUpdate(BaseModel):
    max_discount_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class CustomerDiscountCeilingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    customer_id: uuid.UUID
    max_discount_percentage: Decimal
    is_active: bool
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class CustomerDiscountCeilingListResponse(BaseModel):
    items: List[CustomerDiscountCeilingResponse]
    total: int


# ==============================================================================
# Phase 103: Category Discount Ceiling Schemas
# ==============================================================================

class CategoryDiscountCeilingBase(BaseModel):
    category_id: uuid.UUID
    max_discount_percentage: Decimal = Field(..., ge=0, le=100, description="Percentage between 0 and 100")
    is_active: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None

    @field_validator("effective_until")
    @classmethod
    def validate_dates(cls, v, values):
        if v is not None and "effective_from" in values.data:
            if v < values.data["effective_from"]:
                raise ValueError("effective_until cannot precede effective_from")
        return v


class CategoryDiscountCeilingCreate(CategoryDiscountCeilingBase):
    pass


class CategoryDiscountCeilingUpdate(BaseModel):
    max_discount_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class CategoryDiscountCeilingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    category_id: uuid.UUID
    max_discount_percentage: Decimal
    is_active: bool
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class CategoryDiscountCeilingListResponse(BaseModel):
    items: List[CategoryDiscountCeilingResponse]
    total: int


# ==============================================================================
# Phase 104: Product Discount Ceiling Schemas
# ==============================================================================

class ProductDiscountCeilingBase(BaseModel):
    product_id: uuid.UUID
    max_discount_percentage: Decimal = Field(..., ge=0, le=100, description="Percentage between 0 and 100")
    is_active: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None

    @field_validator("effective_until")
    @classmethod
    def validate_dates(cls, v, values):
        if v is not None and "effective_from" in values.data:
            if v < values.data["effective_from"]:
                raise ValueError("effective_until cannot precede effective_from")
        return v


class ProductDiscountCeilingCreate(ProductDiscountCeilingBase):
    pass


class ProductDiscountCeilingUpdate(BaseModel):
    max_discount_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class ProductDiscountCeilingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    product_id: uuid.UUID
    max_discount_percentage: Decimal
    is_active: bool
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class ProductDiscountCeilingListResponse(BaseModel):
    items: List[ProductDiscountCeilingResponse]
    total: int


# ==============================================================================
# Phase 105: Sales Rep Authority Limit Schemas
# ==============================================================================

class SalesRepAuthorityLimitBase(BaseModel):
    user_id: uuid.UUID
    max_authorized_discount: Decimal = Field(..., ge=0, le=100, description="Percentage between 0 and 100")
    is_active: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None

    @field_validator("effective_until")
    @classmethod
    def validate_dates(cls, v, values):
        if v is not None and "effective_from" in values.data:
            if v < values.data["effective_from"]:
                raise ValueError("effective_until cannot precede effective_from")
        return v


class SalesRepAuthorityLimitCreate(SalesRepAuthorityLimitBase):
    pass


class SalesRepAuthorityLimitUpdate(BaseModel):
    max_authorized_discount: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class SalesRepAuthorityLimitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    user_id: uuid.UUID
    max_authorized_discount: Decimal
    is_active: bool
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class SalesRepAuthorityLimitListResponse(BaseModel):
    items: List[SalesRepAuthorityLimitResponse]
    total: int


# ==============================================================================
# Phase 106: Manager Authority Limit Schemas
# ==============================================================================

class ManagerAuthorityLimitBase(BaseModel):
    user_id: uuid.UUID
    max_authorized_discount: Decimal = Field(..., ge=0, le=100, description="Percentage between 0 and 100")
    is_active: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None

    @field_validator("effective_until")
    @classmethod
    def validate_dates(cls, v, values):
        if v is not None and "effective_from" in values.data:
            if v < values.data["effective_from"]:
                raise ValueError("effective_until cannot precede effective_from")
        return v


class ManagerAuthorityLimitCreate(ManagerAuthorityLimitBase):
    pass


class ManagerAuthorityLimitUpdate(BaseModel):
    max_authorized_discount: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class ManagerAuthorityLimitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    user_id: uuid.UUID
    max_authorized_discount: Decimal
    is_active: bool
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class ManagerAuthorityLimitListResponse(BaseModel):
    items: List[ManagerAuthorityLimitResponse]
    total: int


# ==============================================================================
# Phase 107: Finance Authority Limit Schemas
# ==============================================================================

class FinanceAuthorityLimitBase(BaseModel):
    user_id: uuid.UUID
    max_authorized_discount: Decimal = Field(..., ge=0, le=100, description="Percentage between 0 and 100")
    is_active: bool = True
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None

    @field_validator("effective_until")
    @classmethod
    def validate_dates(cls, v, values):
        if v is not None and "effective_from" in values.data:
            if v < values.data["effective_from"]:
                raise ValueError("effective_until cannot precede effective_from")
        return v


class FinanceAuthorityLimitCreate(FinanceAuthorityLimitBase):
    pass


class FinanceAuthorityLimitUpdate(BaseModel):
    max_authorized_discount: Optional[Decimal] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


class FinanceAuthorityLimitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    user_id: uuid.UUID
    max_authorized_discount: Decimal
    is_active: bool
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class FinanceAuthorityLimitListResponse(BaseModel):
    items: List[FinanceAuthorityLimitResponse]
    total: int


# ==============================================================================
# Phases 108–110: Discount Validation & Policy Engine Schemas
# ==============================================================================

class DiscountValidationRequest(BaseModel):
    customer_id: uuid.UUID
    product_id: uuid.UUID
    proposed_discount: Decimal = Field(..., ge=0, le=100, description="Proposed discount percentage (0 to 100)")


class DiscountViolation(BaseModel):
    type: str = Field(..., description="Violation category identifier")
    source: str = Field(..., description="Policy source entity")
    limit: Decimal = Field(..., description="Authorized threshold percentage")
    proposed: Decimal = Field(..., description="Proposed discount percentage")
    message: str = Field(..., description="Human-readable violation description")
    metadata: dict = Field(default_factory=dict, description="Additional context metadata")


class PolicyEvaluationDetail(BaseModel):
    policy_type: str
    limit: Optional[Decimal] = None
    is_active: bool = False
    source_id: Optional[uuid.UUID] = None
    description: Optional[str] = None


class DiscountPolicyEvaluationResponse(BaseModel):
    allowed: bool
    proposed_discount: Decimal
    effective_ceiling: Decimal
    actor_authority_limit: Optional[Decimal] = None
    actor_role: Optional[str] = None
    violations: List[DiscountViolation] = Field(default_factory=list)
    evaluated_policies: dict = Field(default_factory=dict)
    evaluated_at: datetime

