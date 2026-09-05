from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    customer_tiers,
    customers,
    health,
    product_categories,
    products,
)

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(customer_tiers.router, prefix="/customer-tiers", tags=["Customer Tiers"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(product_categories.router, prefix="/product-categories", tags=["Product Categories"])

