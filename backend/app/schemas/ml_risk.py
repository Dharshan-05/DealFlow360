"""ML Risk Dataset & Feature Engineering Schemas (DealFlow360 B01: Phases 121–125).

Defines strongly-typed schemas for:
- Phase 121: ML Dataset Preparation (Dataset metadata, records, filtering parameters, validation results)
- Phase 122: Historical Deal Dataset (Normalized historical deal records composed from verified entities)
- Phase 123: Feature Engineering (Tabular feature vectors, data types, metadata, leakage-safe extraction)
- Phase 124: Discount Features (Discount metrics, ceiling utilization, customer/category behavior, violation signals)
- Phase 125: Margin Features (Cost, price, gross margin, post-discount margin, margin compression)

Zero sensitive credentials/tokens; Decimal-safe financial values converted to deterministic float for ML readiness.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class DatasetType(str, Enum):
    HISTORICAL_DEALS = "HISTORICAL_DEALS"
    APPLIED_DISCOUNTS = "APPLIED_DISCOUNTS"
    COMPOSITE_TRAINING = "COMPOSITE_TRAINING"


class NormalizationStrategy(str, Enum):
    NONE = "NONE"
    STANDARD = "STANDARD"
    MIN_MAX = "MIN_MAX"


class FeatureType(str, Enum):
    NUMERICAL = "NUMERICAL"
    CATEGORICAL = "CATEGORICAL"
    BOOLEAN = "BOOLEAN"


# ==============================================================================
# Phase 122: Historical Deal Raw Dataset Records
# ==============================================================================

class RawDealRecord(BaseModel):
    """Normalized, point-in-time historical deal record extracted from verified entities (Phase 122).
    Excludes sensitive security/auth data. Strictly multi-tenant isolated.
    """
    model_config = ConfigDict(from_attributes=True)

    record_id: str = Field(description="Unique deterministic record key (deal_code or applied_discount ID)")
    deal_reference: str = Field(description="Reference identifier for deal or quotation")
    company_id: uuid.UUID = Field(description="Tenant isolation identifier")
    customer_id: uuid.UUID = Field(description="Customer account identifier")
    customer_code: str = Field(description="Customer account code")
    customer_tier: str = Field(default="NONE", description="Customer loyalty tier code")
    tier_discount_limit: Decimal = Field(default=Decimal("0.00"), description="Tier baseline discount ceiling")
    
    # Financials
    deal_value: Decimal = Field(default=Decimal("0.00"), description="Deal gross value before discounts")
    requested_discount_pct: Decimal = Field(default=Decimal("0.00"), description="Requested discount percentage")
    applied_discount_pct: Decimal = Field(default=Decimal("0.00"), description="Actual granted discount percentage")
    
    # Product context (when linked to line items / products)
    product_id: Optional[uuid.UUID] = Field(default=None, description="Primary product ID if product-level deal")
    product_sku: Optional[str] = Field(default=None, description="Product SKU")
    product_category: Optional[str] = Field(default=None, description="Category code")
    unit_cost: Decimal = Field(default=Decimal("0.00"), description="Unit cost at deal time")
    selling_price: Decimal = Field(default=Decimal("0.00"), description="Base selling price")
    
    # Customer Relationship & Behavioral Context
    prior_purchases_count: int = Field(default=0, description="Count of completed orders prior to deal")
    prior_purchases_total: Decimal = Field(default=Decimal("0.00"), description="Total purchase value prior to deal")
    prior_discounts_count: int = Field(default=0, description="Count of historical discounts awarded")
    prior_discount_avg_pct: Decimal = Field(default=Decimal("0.00"), description="Mean discount percentage awarded in past")
    prior_payments_count: int = Field(default=0, description="Count of historical payments")
    prior_payments_total: Decimal = Field(default=Decimal("0.00"), description="Total settled amount")
    
    # Inventory context
    inventory_signal: str = Field(default="HEALTHY_STOCK", description="Inventory signal at time of deal")
    
    # Governance & Outcome Context
    deal_status: str = Field(default="WON", description="Deal status outcome: WON, LOST, PENDING, APPROVED, REJECTED")
    decision_outcome: str = Field(default="APPROVED", description="Discount decision engine outcome")
    risk_level: str = Field(default="LOW", description="Risk level evaluated: LOW, MEDIUM, HIGH, CRITICAL")
    closed_at: Optional[datetime] = Field(default=None, description="Date deal closed or discount applied")
    created_at: datetime = Field(description="Timestamp record was created")


# ==============================================================================
# Phase 124: Discount Feature Set
# ==============================================================================

class DiscountFeatures(BaseModel):
    """Discount-specific engineered features (Phase 124).
    Derived from verified Discount Governance models and calculations.
    """
    model_config = ConfigDict(from_attributes=True)

    requested_discount_pct: float = Field(description="Normalized requested discount rate [0, 100]")
    effective_ceiling_pct: float = Field(description="Active policy ceiling percentage [0, 100]")
    ceiling_utilization_ratio: float = Field(
        description="Ratio of requested discount to policy ceiling (1.0 = exact ceiling, >1.0 = overrun)"
    )
    is_ceiling_breached: bool = Field(description="True if requested discount exceeds active ceiling")
    customer_historical_avg_discount: float = Field(description="Customer's lifetime average discount %")
    discount_deviation_from_customer_avg: float = Field(
        description="Difference between requested discount and customer's historical average"
    )
    has_prior_discount_history: bool = Field(description="True if customer has received discounts previously")
    tier_discount_limit: float = Field(description="Customer tier baseline discount ceiling")
    tier_utilization_ratio: float = Field(description="Ratio of requested discount to tier limit")
    discount_amount_est: float = Field(description="Estimated absolute discount monetary amount")


# ==============================================================================
# Phase 125: Margin Feature Set
# ==============================================================================

class MarginFeatures(BaseModel):
    """Margin-specific engineered features (Phase 125).
    Calculated using strict Decimal-safe arithmetic then converted to float.
    """
    model_config = ConfigDict(from_attributes=True)

    unit_cost: float = Field(description="Unit cost of product")
    selling_price: float = Field(description="Baseline catalog selling price")
    gross_margin_amount: float = Field(description="Base gross margin (selling_price - unit_cost)")
    gross_margin_pct: float = Field(description="Gross profit margin % (gross_margin / selling_price * 100)")
    discounted_price: float = Field(description="Selling price after applying discount")
    discounted_margin_amount: float = Field(description="Margin amount remaining after discount")
    discounted_margin_pct: float = Field(description="Margin percentage remaining after discount")
    margin_reduction_ratio: float = Field(description="Relative compression of margin from original margin")
    is_negative_margin: bool = Field(description="True if discounted price falls below unit cost")
    is_zero_cost: bool = Field(description="True if unit cost is zero (e.g. digital services/pure license)")
    discount_to_margin_pressure: float = Field(
        description="Ratio of discount amount to original gross margin amount"
    )


# ==============================================================================
# Phase 123: Complete ML Feature Vector
# ==============================================================================

class EngineeredFeatureVector(BaseModel):
    """Complete, leakage-free engineered feature vector for downstream AI/ML Risk modeling (Phase 123)."""
    model_config = ConfigDict(from_attributes=True)

    record_id: str = Field(description="Unique record reference")
    company_id: str = Field(description="Tenant ID")
    customer_id: str = Field(description="Customer ID")
    
    # Categorical Features
    customer_tier: str = Field(description="Categorical tier")
    product_category: str = Field(description="Categorical category")
    inventory_signal: str = Field(description="Categorical inventory condition")
    
    # Generic Numerical Features
    deal_value: float = Field(description="Gross deal value in currency")
    log_deal_value: float = Field(description="Log-transformed deal value for scale invariance")
    prior_purchases_count: int = Field(description="Count of previous completed purchases")
    prior_purchases_total: float = Field(description="Monetary sum of previous purchases")
    prior_payments_count: int = Field(description="Count of settled payments")
    prior_payments_total: float = Field(description="Monetary sum of settled payments")
    customer_tenure_days: int = Field(default=0, description="Customer relationship age in days at deal time")
    
    # Sub-feature groups
    discount_features: DiscountFeatures = Field(description="Phase 124 Discount Features")
    margin_features: MarginFeatures = Field(description="Phase 125 Margin Features")
    
    # Outcome / Target (Separated to guard against data leakage)
    target_risk_level: Optional[str] = Field(default=None, description="Observed risk outcome (LOW/MED/HIGH/CRIT)")
    target_deal_outcome: Optional[str] = Field(default=None, description="Observed deal outcome (WON/LOST/APPROVED)")
    
    def to_flat_dict(self, include_targets: bool = False) -> Dict[str, Any]:
        """Convert structured feature vector to flattened dictionary suitable for tabular ML models."""
        flat = {
            "record_id": self.record_id,
            "company_id": self.company_id,
            "customer_tier": self.customer_tier,
            "product_category": self.product_category,
            "inventory_signal": self.inventory_signal,
            "deal_value": self.deal_value,
            "log_deal_value": self.log_deal_value,
            "prior_purchases_count": self.prior_purchases_count,
            "prior_purchases_total": self.prior_purchases_total,
            "prior_payments_count": self.prior_payments_count,
            "prior_payments_total": self.prior_payments_total,
            "customer_tenure_days": self.customer_tenure_days,
            
            # Discount Features (Phase 124)
            "requested_discount_pct": self.discount_features.requested_discount_pct,
            "effective_ceiling_pct": self.discount_features.effective_ceiling_pct,
            "ceiling_utilization_ratio": self.discount_features.ceiling_utilization_ratio,
            "is_ceiling_breached": 1 if self.discount_features.is_ceiling_breached else 0,
            "customer_historical_avg_discount": self.discount_features.customer_historical_avg_discount,
            "discount_deviation_from_customer_avg": self.discount_features.discount_deviation_from_customer_avg,
            "has_prior_discount_history": 1 if self.discount_features.has_prior_discount_history else 0,
            "tier_discount_limit": self.discount_features.tier_discount_limit,
            "tier_utilization_ratio": self.discount_features.tier_utilization_ratio,
            "discount_amount_est": self.discount_features.discount_amount_est,
            
            # Margin Features (Phase 125)
            "unit_cost": self.margin_features.unit_cost,
            "selling_price": self.margin_features.selling_price,
            "gross_margin_amount": self.margin_features.gross_margin_amount,
            "gross_margin_pct": self.margin_features.gross_margin_pct,
            "discounted_price": self.margin_features.discounted_price,
            "discounted_margin_amount": self.margin_features.discounted_margin_amount,
            "discounted_margin_pct": self.margin_features.discounted_margin_pct,
            "margin_reduction_ratio": self.margin_features.margin_reduction_ratio,
            "is_negative_margin": 1 if self.margin_features.is_negative_margin else 0,
            "is_zero_cost": 1 if self.margin_features.is_zero_cost else 0,
            "discount_to_margin_pressure": self.margin_features.discount_to_margin_pressure,
        }
        if include_targets:
            flat["target_risk_level"] = self.target_risk_level
            flat["target_deal_outcome"] = self.target_deal_outcome
        return flat


# ==============================================================================
# Phase 121: Dataset Preparation Manifest & Responses
# ==============================================================================

class DatasetMetadata(BaseModel):
    """Deterministic manifest describing prepared dataset (Phase 121)."""
    dataset_id: str = Field(description="Unique deterministic ID of dataset")
    dataset_type: DatasetType = Field(description="Type of dataset prepared")
    company_id: uuid.UUID = Field(description="Tenant company ID")
    total_records_extracted: int = Field(description="Count of raw records read from DB")
    valid_records_count: int = Field(description="Count of valid records passing validation")
    invalid_records_count: int = Field(description="Count of rejected or incomplete records")
    feature_count: int = Field(description="Number of engineered features per record")
    generated_at: datetime = Field(description="Timestamp of preparation")
    normalization_applied: NormalizationStrategy = Field(default=NormalizationStrategy.NONE)


class DatasetPreparationResponse(BaseModel):
    """API response model for ML dataset preparation."""
    metadata: DatasetMetadata
    features: List[EngineeredFeatureVector]
