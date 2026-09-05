"""Customer Tiers API Endpoints (Phase 058).

Provides:
- GET /customer-tiers: List available discount tiers for assignment.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.customer_tier import CustomerTier
from app.models.user import User
from app.schemas.customer import CustomerTierResponse
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[List[CustomerTierResponse]],
    dependencies=[Depends(require_permission("customers:read"))],
    summary="List active customer tiers (Phase 058)",
)
def list_customer_tiers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all active customer tiers with discount limits."""
    tiers = db.scalars(
        select(CustomerTier)
        .where(CustomerTier.is_active == True)
        .order_by(CustomerTier.discount_limit.asc())
    ).all()
    items = [CustomerTierResponse.model_validate(t) for t in tiers]
    return ApiResponse(
        success=True,
        data=items,
    )
