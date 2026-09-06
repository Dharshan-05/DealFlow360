from app.api.v1.endpoints import knowledge
from fastapi import APIRouter
from app.api.v1.endpoints import (
    ai,
    billing,
    auth,
    customer_tiers,
    customers,
    health,
    product_attributes,
    product_categories,
    product_units,
    products,
    warehouses,
    backorders,
    fulfillments,
    inventory,
    discount_governance,
    discount_intelligence,
    discount_automation,
    ml_risk,
    approval_routing,
    approval_execution,
    recommendations,
    quotations,
    deals,
    deal_health,
)

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(customer_tiers.router, prefix="/customer-tiers", tags=["Customer Tiers"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(product_categories.router, prefix="/product-categories", tags=["Product Categories"])
api_router.include_router(product_units.router, prefix="/product-units", tags=["Product Units"])
api_router.include_router(product_attributes.router, prefix="/product-attributes", tags=["Product Attributes"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouses"])
api_router.include_router(backorders.router)
api_router.include_router(fulfillments.router)
api_router.include_router(inventory.router)
api_router.include_router(discount_governance.router)
api_router.include_router(discount_intelligence.router)
api_router.include_router(discount_automation.router)
api_router.include_router(ml_risk.router)
api_router.include_router(approval_routing.router)
api_router.include_router(approval_execution.router)
api_router.include_router(recommendations.router)
api_router.include_router(quotations.router)
api_router.include_router(deals.router)
api_router.include_router(deal_health.router, prefix="/deal-health", tags=["Deal Health Engine"])




api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Copilot"])

api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
