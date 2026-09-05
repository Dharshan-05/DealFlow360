"""ORM Models registry for DealFlow360 (G04–G16: Phases 015–080)"""
from app.models.associations import role_permissions, user_roles
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.customer import Customer
from app.models.customer_deal_history import CustomerDealHistory
from app.models.customer_discount_history import CustomerDiscountHistory
from app.models.customer_payment_history import CustomerPaymentHistory
from app.models.customer_purchase_history import CustomerPurchaseHistory
from app.models.customer_tier import CustomerTier
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_attribute import ProductAttribute, ProductAttributeValue
from app.models.product_category import ProductCategory
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant, product_variant_attribute_values
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_stock import WarehouseStock
from app.models.backorder import Backorder
from app.models.fulfillment import Fulfillment
from app.models.inventory_alert import InventoryAlert
from app.models.discount_configuration import DiscountConfiguration
from app.models.customer_discount_ceiling import CustomerDiscountCeiling
from app.models.category_discount_ceiling import CategoryDiscountCeiling
from app.models.product_discount_ceiling import ProductDiscountCeiling
from app.models.sales_rep_authority_limit import SalesRepAuthorityLimit
from app.models.manager_authority_limit import ManagerAuthorityLimit
from app.models.finance_authority_limit import FinanceAuthorityLimit
from app.models.applied_discount import AppliedDiscount
from app.models.approval_policy import ApprovalPolicy
from app.models.approval_execution import (
    ApprovalAuditLog,
    ApprovalNotification,
    ApprovalRequest,
    ApprovalStep,
)
from app.models.recommendation_event import RecommendationEvent
from app.models.quotation import Quotation, QuotationSendLog, QuotationStatus, QuotationVersion
from app.models.quotation_line_item import QuotationLineItem
from app.models.deal import DealActivity, DealActivityType, DealProduct, DealStage
from app.models.billing import (
    SubscriptionPlan,
    Subscription,
    Invoice,
    InvoiceLineItem,
    UsageRecord,
    BillingEvent,
    BillingInterval,
    SubscriptionStatus,
    InvoiceStatus,
    BillingType,
    PaymentStatus
)

from app.models.deal_health import (
    DealHealthAlert,
    DealHealthAlertSeverity,
    DealHealthAlertStatus,
    DealHealthAlertType,
    DealHealthClassification,
    DealHealthEscalation,
    DealHealthEscalationStatus,
    DealHealthModelMetadata,
    DealHealthNudge,
    DealHealthNudgeStatus,
    DealHealthRecommendation,
    DealHealthSnapshot,
)

__all__ = [
    "SubscriptionPlan",
    "Subscription",
    "Invoice",
    "InvoiceLineItem",
    "UsageRecord",
    "BillingEvent",
    "User",
    "Role",
    "Permission",
    "Company",
    "Customer",
    "CustomerTier",
    "CustomerPurchaseHistory",
    "CustomerDealHistory",
    "CustomerDiscountHistory",
    "CustomerPaymentHistory",
    "user_roles",
    "role_permissions",
    "ProductCategory",
    "Product",
    "ProductUnit",
    "ProductAttribute",
    "ProductAttributeValue",
    "ProductVariant",
    "product_variant_attribute_values",
    "Warehouse",
    "WarehouseStock",
    "Backorder",
    "Fulfillment",
    "InventoryAlert",
    "DiscountConfiguration",
    "CustomerDiscountCeiling",
    "CategoryDiscountCeiling",
    "ProductDiscountCeiling",
    "SalesRepAuthorityLimit",
    "ManagerAuthorityLimit",
    "FinanceAuthorityLimit",
    "AppliedDiscount",
    "ApprovalPolicy",
    "ApprovalRequest",
    "ApprovalStep",
    "ApprovalAuditLog",
    "ApprovalNotification",
    "RecommendationEvent",
    "Quotation",
    "QuotationStatus",
    "QuotationVersion",
    "QuotationSendLog",
    "QuotationLineItem",
    "AuditLog",
    "RefreshToken",
    "DealProduct",
    "DealActivity",
    "DealStage",
    "DealActivityType",
    "DealHealthSnapshot",
    "DealHealthAlert",
    "DealHealthRecommendation",
    "DealHealthNudge",
    "DealHealthEscalation",
    "DealHealthModelMetadata",
    "DealHealthClassification",
    "DealHealthAlertType",
    "DealHealthAlertSeverity",
    "DealHealthAlertStatus",
    "DealHealthNudgeStatus",
    "DealHealthEscalationStatus",
]



