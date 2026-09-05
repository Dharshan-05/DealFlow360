"""ML Risk Dataset & Feature Engineering Schemas (DealFlow360 B01 & B02: Phases 121–130).

Defines strongly-typed schemas for:
- Phase 121: ML Dataset Preparation (Dataset metadata, records, filtering parameters, validation results)
- Phase 122: Historical Deal Dataset (Normalized historical deal records composed from verified entities)
- Phase 123: Feature Engineering (Tabular feature vectors, data types, metadata, leakage-safe extraction)
- Phase 124: Discount Features (Contextual discount metrics, ceiling utilization, violation signals)
- Phase 125: Margin Features (Current deal unit cost, selling price, gross margin, post-discount margin)
- Phase 126: Customer Features (Customer relationship context, purchase frequency, LTV, payment default rate)
- Phase 127: Deal Value Features (Deal size category, deviation from customer/product mean, relative magnitude)
- Phase 128: Discount Behavior Features (Historical discount volatility, max discount, trend, historical escalation rate)
- Phase 129: Margin Behavior Features (Historical margin volatility, minimum margin, low margin frequency, margin compression)
- Phase 130: Risk Target Definition (Binary classification target, risk category, explainable trigger factors)

Zero sensitive credentials/tokens; Decimal-safe financial values converted to deterministic float for ML readiness.
Strictly leakage-free point-in-time extraction.
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


class DealSizeCategory(str, Enum):
    MICRO = "MICRO"          # < 1,000
    SMALL = "SMALL"          # 1,000 - 10,000
    MEDIUM = "MEDIUM"        # 10,000 - 50,000
    LARGE = "LARGE"          # 50,000 - 250,000
    ENTERPRISE = "ENTERPRISE"# > 250,000


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
    
    # Customer Relationship & Behavioral Context (Computed point-in-time strictly before created_at)
    prior_purchases_count: int = Field(default=0, description="Count of completed orders prior to deal")
    prior_purchases_total: Decimal = Field(default=Decimal("0.00"), description="Total purchase value prior to deal")
    prior_discounts_count: int = Field(default=0, description="Count of historical discounts awarded")
    prior_discount_avg_pct: Decimal = Field(default=Decimal("0.00"), description="Mean discount percentage awarded in past")
    prior_payments_count: int = Field(default=0, description="Count of historical payments")
    prior_payments_total: Decimal = Field(default=Decimal("0.00"), description="Total settled amount")
    prior_failed_payments_count: int = Field(default=0, description="Count of failed/delinquent payments")
    
    # Inventory context
    inventory_signal: str = Field(default="HEALTHY_STOCK", description="Inventory signal at time of deal")
    
    # Governance & Outcome Context
    deal_status: str = Field(default="WON", description="Deal status outcome: WON, LOST, PENDING, APPROVED, REJECTED")
    decision_outcome: str = Field(default="APPROVED", description="Discount decision engine outcome: APPROVED, ADJUSTED, ESCALATION_REQUIRED, REJECTED")
    risk_level: str = Field(default="LOW", description="Risk level evaluated: LOW, MEDIUM, HIGH, CRITICAL")
    reason_code: str = Field(default="STANDARD", description="Reason code associated with governance decision")
    closed_at: Optional[datetime] = Field(default=None, description="Date deal closed or discount applied")
    created_at: datetime = Field(description="Timestamp record was created")


# ==============================================================================
# Phase 124: Discount Feature Set (Contextual Deal-Level)
# ==============================================================================

class DiscountFeatures(BaseModel):
    """Discount-specific engineered features (Phase 124).
    Derived from verified Discount Governance models and calculations for the CURRENT deal.
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
# Phase 125: Margin Feature Set (Current Deal-Level)
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
# Phase 126: Customer Features
# ==============================================================================

class CustomerFeatures(BaseModel):
    """Customer-level engineered features (Phase 126).
    Synthesized point-in-time from Customer profile, tier, purchase and payment histories.
    """
    model_config = ConfigDict(from_attributes=True)

    customer_tenure_days: int = Field(description="Relationship age in days strictly at deal time")
    customer_tier: str = Field(description="Loyalty tier code (e.g., BRONZE, SILVER, GOLD, NONE)")
    tier_discount_limit: float = Field(description="Tier baseline maximum discount ceiling %")
    is_established_customer: bool = Field(description="True if customer has >= 3 completed orders or tenure > 90 days")
    lifetime_orders_count: int = Field(description="Prior completed purchases count before deal")
    lifetime_revenue: float = Field(description="Prior completed purchases monetary sum before deal")
    lifetime_settled_amount: float = Field(description="Prior settled payment monetary sum before deal")
    average_order_value: float = Field(description="Prior historical Average Order Value (AOV)")
    payment_default_ratio: float = Field(description="Ratio of failed/refunded payments to total payments [0.0, 1.0]")
    payment_reliability_score: float = Field(description="Payment reliability index [0, 100] where 100 is perfect")
    has_payment_history: bool = Field(description="True if customer has prior recorded payments")
    price_sensitivity_score: float = Field(description="Estimated price sensitivity index [0, 100]")


# ==============================================================================
# Phase 127: Deal Value Features
# ==============================================================================

class DealValueFeatures(BaseModel):
    """Deal-value-related engineered features (Phase 127).
    Derives monetary scale, log transforms, deal size classification, and comparison to historical baseline.
    """
    model_config = ConfigDict(from_attributes=True)

    deal_value: float = Field(description="Nominal gross deal value")
    log_deal_value: float = Field(description="Natural logarithm ln(1 + deal_value) for variance stabilization")
    deal_size_category: str = Field(description="Categorical size band: MICRO, SMALL, MEDIUM, LARGE, ENTERPRISE")
    deal_to_aov_ratio: float = Field(description="Ratio of current deal value to customer's historical AOV (1.0 = equal)")
    is_deal_value_outlier: bool = Field(description="True if deal value > 3x customer's historical AOV")
    deal_value_deviation_from_aov: float = Field(description="Difference (deal_value - customer_aov)")
    has_prior_aov_benchmark: bool = Field(description="True if customer has historical orders to establish AOV")


# ==============================================================================
# Phase 128: Approval Features (Authoritative Roadmap)
# ==============================================================================

class ApprovalFeatures(BaseModel):
    """Approval-related engineered features (Phase 128).
    Evaluates prior customer and deal governance approval requests, escalations, rejections,
    approval rates, and exception indicators strictly point-in-time before deal creation.
    """
    model_config = ConfigDict(from_attributes=True)

    approval_request_count: int = Field(description="Total count of prior discount/deal approval requests evaluated")
    approval_approved_count: int = Field(description="Total count of prior approved proposals")
    approval_escalation_count: int = Field(description="Total count of prior proposals requiring supervisor/finance escalation")
    approval_rejection_count: int = Field(description="Total count of prior rejected proposals")
    approval_rate: float = Field(description="Historical approval rate [0.0, 1.0]")
    rejection_rate: float = Field(description="Historical rejection rate [0.0, 1.0]")
    escalation_rate: float = Field(description="Historical escalation rate [0.0, 1.0]")
    approval_threshold_proximity: float = Field(description="Proximity of requested discount to active approval ceiling ratio")
    approval_required_indicator: int = Field(description="1 if current proposal requires approval escalation, 0 if auto-approved")
    has_prior_approval_history: bool = Field(description="True if customer has prior evaluated governance records")


# ==============================================================================
# Phase 129: Negotiation Features (Authoritative Roadmap)
# ==============================================================================

class NegotiationFeatures(BaseModel):
    """Negotiation-related engineered features (Phase 129).
    Quantifies customer historical negotiation intensity, discount concession frequency, concession magnitude,
    and deal negotiation indicators strictly point-in-time before deal creation.
    """
    model_config = ConfigDict(from_attributes=True)

    negotiation_deal_count: int = Field(description="Total count of prior deals that underwent active negotiation")
    negotiation_frequency: float = Field(description="Percentage of prior deals that involved active negotiation [0.0, 100.0]")
    concession_deal_count: int = Field(description="Count of prior deals where customer secured discount concessions (>0%)")
    concession_frequency: float = Field(description="Percentage of prior orders that received discount concessions [0.0, 100.0]")
    avg_concession_magnitude: float = Field(description="Average discount percentage concession secured by customer")
    max_concession_magnitude: float = Field(description="Maximum discount percentage concession achieved in customer history")
    concession_volatility: float = Field(description="Standard deviation of concessions across prior deals")
    concession_trend_slope: float = Field(description="Trend indicator (+1 expanding concessions, -1 contracting, 0 stable)")
    repeated_negotiation_indicator: int = Field(description="1 if customer repeatedly negotiates discounts (>30% frequency), 0 otherwise")
    has_prior_negotiation_history: bool = Field(description="True if customer has prior recorded deal negotiation history")


# ==============================================================================
# Phase 130: Fulfillment Features (Authoritative Roadmap)
# ==============================================================================

class FulfillmentFeatures(BaseModel):
    """Fulfillment-related engineered features (Phase 130).
    Derives fulfillment success, warehouse stock availability, backorder incidence, and delivery reliability
    from verified domain models strictly point-in-time before deal creation.
    """
    model_config = ConfigDict(from_attributes=True)

    fulfillment_history_count: int = Field(description="Total prior customer purchase fulfillment records evaluated")
    fulfilled_order_count: int = Field(description="Count of successfully completed prior orders")
    fulfillment_success_rate: float = Field(description="Ratio of completed orders to total orders [0.0, 1.0]")
    fulfillment_exception_count: int = Field(description="Count of prior canceled, delayed, or problematic orders")
    backorder_indicator: int = Field(description="1 if current product has backorders or inventory scarcity, 0 if healthy")
    stock_availability_ratio: float = Field(description="Available stock ratio for product (1.0 = healthy/excess, 0.0 = stockout)")
    fulfillment_completion_ratio: float = Field(description="Customer historical purchase fulfillment completion ratio [0.0, 1.0]")
    has_fulfillment_history: bool = Field(description="True if customer has prior fulfillment/purchase records")


# ==============================================================================
# ML Target Infrastructure (Separated from Phase 130 to prevent roadmap confusion)
# ==============================================================================

class RiskTarget(BaseModel):
    """Deterministic, explainable risk target label for ML risk models.
    Derived from verified historical governance outcomes and margin thresholds.
    Separated from Phase 130 (Fulfillment Features) to guarantee zero target leakage into feature vectors.
    """
    model_config = ConfigDict(from_attributes=True)

    is_high_risk: int = Field(description="Binary classification target: 1 if high risk / deal breach, 0 if safe")
    risk_level: str = Field(description="Categorical risk tier: LOW, MEDIUM, HIGH, CRITICAL")
    risk_category: str = Field(description="Primary failure mode: GOVERNANCE_BREACH, MARGIN_EROSION, PAYMENT_DEFAULT, NONE")
    is_governance_breached: bool = Field(description="True if requested discount breached active policy ceiling")
    is_margin_breached: bool = Field(description="True if discounted margin fell below minimum threshold (15%)")
    is_escalation_triggered: bool = Field(description="True if deal required supervisor or finance escalation")
    is_rejected: bool = Field(description="True if discount proposal was rejected")
    trigger_reasons: List[str] = Field(default_factory=list, description="Explicit deterministic reasons for risk classification")


# ==============================================================================
# Legacy / Internal Behavioral Helpers (Retained for backwards compatibility)
# ==============================================================================

class DiscountBehaviorFeatures(BaseModel):
    """Internal helper: discount behavior features. Retained for compatibility."""
    model_config = ConfigDict(from_attributes=True)

    historical_discount_count: int = Field(description="Total count of prior discounts awarded")
    historical_discount_frequency_pct: float = Field(description="Percentage of prior orders that received discounts [0, 100]")
    historical_avg_discount_pct: float = Field(description="Average discount percentage across prior awards")
    historical_max_discount_pct: float = Field(description="Maximum discount percentage awarded in prior history")
    historical_discount_volatility: float = Field(description="Standard deviation of prior discounts awarded")
    discount_trend_slope: float = Field(description="Trend indicator (+1 expanding discounts, -1 contracting, 0 stable)")
    historical_escalation_count: int = Field(description="Prior deals that required managerial/finance escalation")
    historical_rejection_count: int = Field(description="Prior discount proposals rejected by governance")
    historical_escalation_rate: float = Field(description="Ratio of escalations to total prior discount requests")


class MarginBehaviorFeatures(BaseModel):
    """Internal helper: margin behavior features. Retained for compatibility."""
    model_config = ConfigDict(from_attributes=True)

    historical_avg_margin_pct: float = Field(description="Average post-discount gross margin realized in prior deals")
    historical_min_margin_pct: float = Field(description="Lowest post-discount gross margin recorded in prior deals")
    historical_max_margin_pct: float = Field(description="Highest post-discount gross margin recorded in prior deals")
    historical_margin_volatility: float = Field(description="Standard deviation of margins in prior deals")
    historical_low_margin_deal_count: int = Field(description="Prior deals realized with margin below threshold (<20%)")
    low_margin_frequency_pct: float = Field(description="Percentage of prior deals with margin below threshold")
    margin_erosion_trend: float = Field(description="Margin trend (+1 improving margins, -1 degrading margins, 0 neutral)")
    has_prior_margin_history: bool = Field(description="True if prior realized margin data exists")


# ==============================================================================
# Phase 123 / Extended B02: Complete Engineered Feature Vector
# ==============================================================================

class EngineeredFeatureVector(BaseModel):
    """Complete, leakage-free engineered feature vector for downstream AI/ML Risk modeling (Phases 123–130)."""
    model_config = ConfigDict(from_attributes=True)

    record_id: str = Field(description="Unique record reference")
    company_id: str = Field(description="Tenant ID")
    customer_id: str = Field(description="Customer ID")
    
    # Context Categoricals
    customer_tier: str = Field(description="Categorical tier")
    product_category: str = Field(description="Categorical category")
    inventory_signal: str = Field(description="Categorical inventory condition")
    
    # Generic Point-in-Time Metrics
    deal_value: float = Field(description="Gross deal value in currency")
    log_deal_value: float = Field(description="Log-transformed deal value")
    prior_purchases_count: int = Field(description="Count of previous completed purchases")
    prior_purchases_total: float = Field(description="Monetary sum of previous purchases")
    prior_payments_count: int = Field(description="Count of settled payments")
    prior_payments_total: float = Field(description="Monetary sum of settled payments")
    customer_tenure_days: int = Field(default=0, description="Customer relationship age in days at deal time")
    
    # Specialized Feature Subsets (Phases 124–130)
    discount_features: DiscountFeatures = Field(description="Phase 124 Contextual Discount Features")
    margin_features: MarginFeatures = Field(description="Phase 125 Contextual Margin Features")
    customer_features: CustomerFeatures = Field(description="Phase 126 Customer Features")
    deal_value_features: DealValueFeatures = Field(description="Phase 127 Deal Value Features")
    approval_features: Optional[ApprovalFeatures] = Field(default=None, description="Phase 128 Approval Features")
    negotiation_features: Optional[NegotiationFeatures] = Field(default=None, description="Phase 129 Negotiation Features")
    fulfillment_features: Optional[FulfillmentFeatures] = Field(default=None, description="Phase 130 Fulfillment Features")

    # Internal behavioral helpers (retained for backwards compatibility)
    discount_behavior_features: DiscountBehaviorFeatures = Field(description="Internal Discount Behavior Features")
    margin_behavior_features: MarginBehaviorFeatures = Field(description="Internal Margin Behavior Features")
    
    # Outcome / Target (Separated from feature matrices to guarantee zero future data leakage)
    target: RiskTarget = Field(description="Risk Target Definition")
    target_risk_level: Optional[str] = Field(default=None, description="Observed risk level string")
    target_deal_outcome: Optional[str] = Field(default=None, description="Observed deal outcome string")
    
    def to_flat_dict(self, include_targets: bool = False) -> Dict[str, Any]:
        """Convert structured feature vector to flattened dictionary suitable for tabular ML models."""
        flat: Dict[str, Any] = {
            "record_id": self.record_id,
            "company_id": self.company_id,
            "customer_id": self.customer_id,
            "customer_tier": self.customer_tier,
            "product_category": self.product_category,
            "inventory_signal": self.inventory_signal,
            
            # Phase 124: Discount Features
            "requested_discount_pct": self.discount_features.requested_discount_pct,
            "effective_ceiling_pct": self.discount_features.effective_ceiling_pct,
            "ceiling_utilization_ratio": self.discount_features.ceiling_utilization_ratio,
            "is_ceiling_breached": 1 if self.discount_features.is_ceiling_breached else 0,
            "tier_discount_limit": self.discount_features.tier_discount_limit,
            "tier_utilization_ratio": self.discount_features.tier_utilization_ratio,
            "discount_amount_est": self.discount_features.discount_amount_est,
            
            # Phase 125: Margin Features
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
            
            # Phase 126: Customer Features
            "customer_tenure_days": self.customer_features.customer_tenure_days,
            "is_established_customer": 1 if self.customer_features.is_established_customer else 0,
            "lifetime_orders_count": self.customer_features.lifetime_orders_count,
            "lifetime_revenue": self.customer_features.lifetime_revenue,
            "lifetime_settled_amount": self.customer_features.lifetime_settled_amount,
            "average_order_value": self.customer_features.average_order_value,
            "payment_default_ratio": self.customer_features.payment_default_ratio,
            "payment_reliability_score": self.customer_features.payment_reliability_score,
            "price_sensitivity_score": self.customer_features.price_sensitivity_score,
            
            # Phase 127: Deal Value Features
            "deal_value": self.deal_value_features.deal_value,
            "log_deal_value": self.deal_value_features.log_deal_value,
            "deal_size_category": self.deal_value_features.deal_size_category,
            "deal_to_aov_ratio": self.deal_value_features.deal_to_aov_ratio,
            "is_deal_value_outlier": 1 if self.deal_value_features.is_deal_value_outlier else 0,
            "deal_value_deviation_from_aov": self.deal_value_features.deal_value_deviation_from_aov,
            
            # Internal helpers (retained for backward compatibility)
            "historical_discount_count": self.discount_behavior_features.historical_discount_count,
            "historical_discount_frequency_pct": self.discount_behavior_features.historical_discount_frequency_pct,
            "historical_avg_discount_pct": self.discount_behavior_features.historical_avg_discount_pct,
            "historical_max_discount_pct": self.discount_behavior_features.historical_max_discount_pct,
            "historical_discount_volatility": self.discount_behavior_features.historical_discount_volatility,
            "discount_trend_slope": self.discount_behavior_features.discount_trend_slope,
            "historical_escalation_rate": self.discount_behavior_features.historical_escalation_rate,
            "historical_avg_margin_pct": self.margin_behavior_features.historical_avg_margin_pct,
            "historical_min_margin_pct": self.margin_behavior_features.historical_min_margin_pct,
            "historical_max_margin_pct": self.margin_behavior_features.historical_max_margin_pct,
            "historical_margin_volatility": self.margin_behavior_features.historical_margin_volatility,
            "historical_low_margin_deal_count": self.margin_behavior_features.historical_low_margin_deal_count,
            "low_margin_frequency_pct": self.margin_behavior_features.low_margin_frequency_pct,
            "margin_erosion_trend": self.margin_behavior_features.margin_erosion_trend,
        }

        # Phase 128: Approval Features
        if self.approval_features is not None:
            flat["approval_request_count"] = self.approval_features.approval_request_count
            flat["approval_approved_count"] = self.approval_features.approval_approved_count
            flat["approval_escalation_count"] = self.approval_features.approval_escalation_count
            flat["approval_rejection_count"] = self.approval_features.approval_rejection_count
            flat["approval_rate"] = self.approval_features.approval_rate
            flat["rejection_rate"] = self.approval_features.rejection_rate
            flat["escalation_rate"] = self.approval_features.escalation_rate
            flat["approval_threshold_proximity"] = self.approval_features.approval_threshold_proximity
            flat["approval_required_indicator"] = self.approval_features.approval_required_indicator

        # Phase 129: Negotiation Features
        if self.negotiation_features is not None:
            flat["negotiation_deal_count"] = self.negotiation_features.negotiation_deal_count
            flat["negotiation_frequency"] = self.negotiation_features.negotiation_frequency
            flat["concession_deal_count"] = self.negotiation_features.concession_deal_count
            flat["concession_frequency"] = self.negotiation_features.concession_frequency
            flat["avg_concession_magnitude"] = self.negotiation_features.avg_concession_magnitude
            flat["max_concession_magnitude"] = self.negotiation_features.max_concession_magnitude
            flat["concession_volatility"] = self.negotiation_features.concession_volatility
            flat["concession_trend_slope"] = self.negotiation_features.concession_trend_slope
            flat["repeated_negotiation_indicator"] = self.negotiation_features.repeated_negotiation_indicator

        # Phase 130: Fulfillment Features
        if self.fulfillment_features is not None:
            flat["fulfillment_history_count"] = self.fulfillment_features.fulfillment_history_count
            flat["fulfilled_order_count"] = self.fulfillment_features.fulfilled_order_count
            flat["fulfillment_success_rate"] = self.fulfillment_features.fulfillment_success_rate
            flat["fulfillment_exception_count"] = self.fulfillment_features.fulfillment_exception_count
            flat["backorder_indicator"] = self.fulfillment_features.backorder_indicator
            flat["stock_availability_ratio"] = self.fulfillment_features.stock_availability_ratio
            flat["fulfillment_completion_ratio"] = self.fulfillment_features.fulfillment_completion_ratio

        if include_targets:
            flat["target_is_high_risk"] = self.target.is_high_risk
            flat["target_risk_level"] = self.target.risk_level
            flat["target_risk_category"] = self.target.risk_category
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


# ==============================================================================
# Phase 131: Risk Dataset Pipeline Schemas
# ==============================================================================

class DatasetSplitManifest(BaseModel):
    """Deterministic train/validation/test split summary (Phase 131)."""
    model_config = ConfigDict(from_attributes=True)

    total_samples: int = Field(description="Total usable samples in pipeline")
    train_samples: int = Field(description="Number of samples in training partition")
    val_samples: int = Field(description="Number of samples in validation partition")
    test_samples: int = Field(description="Number of samples in test partition")
    positive_ratio_train: float = Field(description="High-risk positive prevalence in train partition [0.0, 1.0]")
    positive_ratio_val: float = Field(description="High-risk positive prevalence in validation partition [0.0, 1.0]")
    positive_ratio_test: float = Field(description="High-risk positive prevalence in test partition [0.0, 1.0]")
    feature_names: List[str] = Field(description="Ordered list of feature column names")
    target_name: str = Field(default="target_is_high_risk", description="Target column name")
    categorical_encodings: Dict[str, Dict[str, int]] = Field(
        default_factory=dict, description="Deterministic category-to-integer mappings"
    )
    is_stratified: bool = Field(description="Whether split preserved target class ratio")
    random_seed: int = Field(description="Deterministic random seed used for partition")


class RiskDatasetPipelineResult(BaseModel):
    """Result of executing the Phase 131 Risk Dataset Pipeline."""
    model_config = ConfigDict(from_attributes=True)

    pipeline_id: str = Field(description="Deterministic pipeline execution identifier")
    company_id: uuid.UUID = Field(description="Tenant isolation identifier")
    split_manifest: DatasetSplitManifest = Field(description="Split metadata and feature schema")
    train_feature_matrix: List[List[float]] = Field(description="Deterministic X_train matrix")
    train_target_vector: List[int] = Field(description="Deterministic y_train vector")
    val_feature_matrix: List[List[float]] = Field(description="Deterministic X_val matrix")
    val_target_vector: List[int] = Field(description="Deterministic y_val vector")
    test_feature_matrix: List[List[float]] = Field(description="Deterministic X_test matrix")
    test_target_vector: List[int] = Field(description="Deterministic y_test vector")
    validation_errors: List[str] = Field(default_factory=list, description="Integrity check messages")
    created_at: datetime = Field(description="Timestamp of pipeline generation")


# ==============================================================================
# Phases 132–134: Model Evaluation Metrics & Artifact Schemas
# ==============================================================================

class ModelEvaluationMetrics(BaseModel):
    """Comprehensive classification metrics derived from actual predictions (Phases 132–135)."""
    model_config = ConfigDict(from_attributes=True)

    accuracy: float = Field(description="Fraction of correctly classified samples")
    precision: float = Field(description="True Positives / (True Positives + False Positives)")
    recall: float = Field(description="True Positives / (True Positives + False Negatives)")
    f1_score: float = Field(description="Harmonic mean of precision and recall")
    roc_auc: Optional[float] = Field(default=None, description="Area Under the Receiver Operating Characteristic")
    pr_auc: Optional[float] = Field(default=None, description="Area Under the Precision-Recall Curve")
    brier_score: float = Field(description="Mean squared difference between predicted probabilities and outcomes")
    true_positives: int = Field(description="TP count")
    false_positives: int = Field(description="FP count")
    true_negatives: int = Field(description="TN count")
    false_negatives: int = Field(description="FN count")
    sample_count: int = Field(description="Total evaluation samples evaluated")


class ModelType(str, Enum):
    XGBOOST = "XGBOOST"
    LIGHTGBM = "LIGHTGBM"
    RANDOM_FOREST = "RANDOM_FOREST"


class ModelArtifact(BaseModel):
    """Serialized model artifact and metadata (Phases 132–134)."""
    model_config = ConfigDict(from_attributes=True)

    artifact_id: str = Field(description="Unique artifact ID")
    company_id: uuid.UUID = Field(description="Tenant isolation identifier")
    model_type: ModelType = Field(description="Model family: XGBOOST, LIGHTGBM, RANDOM_FOREST")
    feature_names: List[str] = Field(description="Ordered list of input feature names")
    hyperparameters: Dict[str, Any] = Field(description="Explicit hyperparameters used for training")
    train_metrics: ModelEvaluationMetrics = Field(description="Performance on training partition")
    val_metrics: Optional[ModelEvaluationMetrics] = Field(default=None, description="Performance on validation partition")
    test_metrics: ModelEvaluationMetrics = Field(description="Performance on test partition")
    feature_importances: Dict[str, float] = Field(
        default_factory=dict, description="Normalized feature importance scores (sum to 1.0)"
    )
    serialized_model: str = Field(description="Base64 or JSON serialized model structure")
    random_seed: int = Field(description="Random seed used for training")
    trained_at: datetime = Field(description="Training completion timestamp")


# ==============================================================================
# Phase 135: Model Comparison Schemas
# ==============================================================================

class ModelComparisonEntry(BaseModel):
    """Comparison row for a single evaluated model family (Phase 135)."""
    model_config = ConfigDict(from_attributes=True)

    model_type: ModelType = Field(description="Model family")
    artifact_id: str = Field(description="Referenced model artifact ID")
    metrics: ModelEvaluationMetrics = Field(description="Evaluation metrics on common test split")
    rank: int = Field(description="Deterministic ranking (1 = best)")
    selection_score: float = Field(description="Scalar selection score (e.g. combination of F1 and ROC-AUC)")


class ModelComparisonReport(BaseModel):
    """Comprehensive comparison report across XGBoost, LightGBM, and Random Forest (Phase 135)."""
    model_config = ConfigDict(from_attributes=True)

    comparison_id: str = Field(description="Deterministic comparison ID")
    company_id: uuid.UUID = Field(description="Tenant isolation identifier")
    pipeline_id: str = Field(description="Underlying Phase 131 dataset pipeline ID")
    evaluated_models: List[ModelComparisonEntry] = Field(description="Ranked list of evaluated models")
    winner_model_type: ModelType = Field(description="Best-performing model family")
    winner_artifact_id: str = Field(description="Artifact ID of the winning model")
    selection_criterion: str = Field(
        default="HIGHEST_F1_ROC_AUC",
        description="Explicit rule used to determine the comparison winner"
    )
    comparison_notes: List[str] = Field(default_factory=list, description="Analytical observations")
    compared_at: datetime = Field(description="Timestamp comparison was conducted")


# ==============================================================================
# Phase 136: Model Selection Schemas
# ==============================================================================

class ModelSelectionResult(BaseModel):
    """Deterministic selection summary identifying the champion model (Phase 136)."""
    model_config = ConfigDict(from_attributes=True)

    selection_id: str = Field(description="Deterministic selection identifier")
    company_id: uuid.UUID = Field(description="Tenant isolation identifier")
    selected_model: ModelType = Field(description="Champion model architecture")
    selected_artifact_id: str = Field(description="Artifact ID of champion model")
    selection_criterion: str = Field(description="Rule used to evaluate and select champion")
    selection_rationale: str = Field(description="Detailed explanation of selection decision")
    candidate_metrics: List[ModelComparisonEntry] = Field(description="Metrics of all evaluated candidates")
    selected_at: datetime = Field(description="Selection execution timestamp")


# ==============================================================================
# Phase 139: Probability Calibration Schemas
# ==============================================================================

class CalibrationMethod(str, Enum):
    PLATT_SCALING = "PLATT_SCALING"
    ISOTONIC = "ISOTONIC"
    NONE = "NONE"


class CalibrationMetadata(BaseModel):
    """Probability calibration parameters and validation performance (Phase 139)."""
    model_config = ConfigDict(from_attributes=True)

    calibration_id: str = Field(description="Calibration identifier")
    method: CalibrationMethod = Field(default=CalibrationMethod.PLATT_SCALING)
    pre_calibration_brier: float = Field(description="Validation Brier score before calibration")
    post_calibration_brier: float = Field(description="Validation Brier score after calibration")
    brier_improvement_pct: float = Field(description="Percentage reduction in Brier score")
    sigmoid_a: float = Field(description="Platt scaling logistic slope parameter A")
    sigmoid_b: float = Field(description="Platt scaling logistic intercept parameter B")
    validation_sample_count: int = Field(description="Validation sample count used for calibration fit")
    calibrated_at: datetime = Field(description="Calibration fit timestamp")


# ==============================================================================
# Phase 137 & 138: Pipeline Execution & Evaluation Schemas
# ==============================================================================

class ModelTrainingPipelineResult(BaseModel):
    """Result of end-to-end model training, evaluation, selection, and calibration (Phase 137)."""
    model_config = ConfigDict(from_attributes=True)

    pipeline_run_id: str = Field(description="Training pipeline run identifier")
    company_id: uuid.UUID = Field(description="Tenant isolation identifier")
    dataset_split: DatasetSplitManifest = Field(description="Dataset split manifest")
    model_selection: ModelSelectionResult = Field(description="Champion model selection result")
    champion_artifact: ModelArtifact = Field(description="Champion model artifact")
    calibration: CalibrationMetadata = Field(description="Probability calibration metadata")
    final_test_evaluation: ModelEvaluationMetrics = Field(description="Rigorous out-of-sample test metrics (Phase 138)")
    trained_at: datetime = Field(description="Pipeline execution completion timestamp")


# ==============================================================================
# Phases 141–144: Risk Scoring, Classification, Explainability & Factors
# ==============================================================================

class RiskScoreCategory(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FeatureContribution(BaseModel):
    """Individual feature contribution derived from tree structure (Phase 143)."""
    model_config = ConfigDict(from_attributes=True)

    feature_name: str = Field(description="Internal feature name")
    feature_value: float = Field(description="Raw numerical or encoded feature value")
    contribution: float = Field(description="Signed logit/log-odds contribution")
    direction: str = Field(description="'risk_increasing' or 'risk_reducing'")
    relative_impact_pct: float = Field(description="Relative absolute share of explanation [0.0, 100.0]")


class RiskFactorDetail(BaseModel):
    """Human-readable risk factor explanation (Phase 144)."""
    model_config = ConfigDict(from_attributes=True)

    feature_name: str = Field(description="Internal feature name")
    display_name: str = Field(description="Human-friendly label")
    feature_value: float = Field(description="Observed value")
    contribution: float = Field(description="Attribution weight")
    direction: str = Field(description="'risk_increasing' or 'risk_reducing'")
    severity: str = Field(description="'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'BENEFICIAL'")
    description: str = Field(description="Actionable business description of factor impact")


class RiskPredictionRequest(BaseModel):
    """Payload for requesting deal risk inference (Phase 140)."""
    model_config = ConfigDict(from_attributes=True)

    deal_value: float = Field(description="Total proposed deal value in currency units", ge=0.0)
    requested_discount_pct: float = Field(description="Proposed discount percentage", ge=0.0, le=100.0)
    selling_price: float = Field(description="Unit selling price", ge=0.0)
    unit_cost: float = Field(description="Unit cost", ge=0.0)
    customer_tenure_days: int = Field(default=90, description="Customer relationship tenure in days", ge=0)
    customer_tier: str = Field(default="STANDARD", description="Customer tier: BRONZE, SILVER, GOLD, PLATINUM, ENTERPRISE, STANDARD")
    product_category: str = Field(default="GENERAL", description="Product category code")
    inventory_signal: str = Field(default="HEALTHY_STOCK", description="Inventory signal: HEALTHY_STOCK, LOW_STOCK, EXCESS_AVAILABLE, OUT_OF_STOCK")
    lifetime_orders: int = Field(default=5, description="Prior customer order count", ge=0)
    lifetime_revenue: float = Field(default=50000.0, description="Customer cumulative lifetime revenue", ge=0.0)
    payment_default_ratio: float = Field(default=0.0, description="Customer historical payment default ratio", ge=0.0, le=1.0)
    historical_avg_discount_pct: float = Field(default=10.0, description="Customer historical average discount %", ge=0.0, le=100.0)
    historical_avg_margin_pct: float = Field(default=45.0, description="Customer historical average margin %")
    deal_reference: Optional[str] = Field(default=None, description="Optional deal reference identifier")


class RiskPredictionResponse(BaseModel):
    """Full risk inference response (Phases 140–144)."""
    model_config = ConfigDict(from_attributes=True)

    prediction_id: str = Field(description="Deterministic prediction execution identifier")
    company_id: uuid.UUID = Field(description="Tenant isolation identifier")
    deal_reference: Optional[str] = Field(default=None, description="Deal reference")
    raw_probability: float = Field(description="Raw model probability [0.0, 1.0]")
    risk_probability: float = Field(description="Calibrated probability of high risk [0.0, 1.0] (Phase 139)")
    risk_score: int = Field(description="Deterministic scalar risk score [0, 100] (Phase 141)")
    risk_classification: RiskScoreCategory = Field(description="Risk classification tier (Phase 142)")
    model_type: ModelType = Field(description="Champion model architecture")
    artifact_id: str = Field(description="Champion model artifact ID")
    is_calibrated: bool = Field(description="Whether probability calibration was applied")
    top_risk_increasing_factors: List[RiskFactorDetail] = Field(description="Top factors driving risk up (Phase 144)")
    top_risk_reducing_factors: List[RiskFactorDetail] = Field(description="Top factors reducing risk (Phase 144)")
    feature_contributions: List[FeatureContribution] = Field(description="All feature contributions (Phase 143)")
    evaluated_at: datetime = Field(description="Inference timestamp")


# ==============================================================================
# Phase 145: AI Risk Dashboard Schemas
# ==============================================================================

class RiskDistributionBucket(BaseModel):
    """Risk score distribution bin for charts (Phase 145)."""
    model_config = ConfigDict(from_attributes=True)

    score_range: str = Field(description="Bin range, e.g. '0-20', '21-40'")
    count: int = Field(description="Deals falling into this bin")
    percentage: float = Field(description="Percentage of total evaluated deals")


class AIRiskDashboardSummary(BaseModel):
    """Comprehensive AI Risk Dashboard response (Phase 145)."""
    model_config = ConfigDict(from_attributes=True)

    company_id: uuid.UUID = Field(description="Tenant isolation identifier")
    total_evaluated_deals: int = Field(description="Count of evaluated deals")
    low_risk_count: int = Field(description="Count of LOW risk deals")
    medium_risk_count: int = Field(description="Count of MEDIUM risk deals")
    high_risk_count: int = Field(description="Count of HIGH risk deals")
    critical_risk_count: int = Field(description="Count of CRITICAL risk deals")
    average_risk_score: float = Field(description="Mean risk score across deals")
    risk_distribution: List[RiskDistributionBucket] = Field(description="Histogram distribution of scores")
    champion_model: Optional[ModelArtifact] = Field(default=None, description="Active champion model details")
    calibration_status: Optional[CalibrationMetadata] = Field(default=None, description="Active calibration metadata")
    recent_evaluated_deals: List[RiskPredictionResponse] = Field(default_factory=list, description="Recent deal evaluations")
    generated_at: datetime = Field(description="Dashboard generation timestamp")

