import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.quotation import Quotation
from app.api.deps import get_current_user
from app.services.portal import (
    PortalAuthenticationService,
    PortalAuthorizationService,
    CustomerCommentService,
    NegotiationService,
    PortalAcceptanceService,
    PortalRejectionService,
    PortalPaymentService
)
from app.schemas.billing import InvoiceResponse

router = APIRouter()

def get_portal_user(current_user: User = Depends(get_current_user)) -> User:
    if not PortalAuthenticationService.verify_portal_user(None, current_user):
        raise HTTPException(status_code=403, detail="Not authorized for Customer Portal")
    return current_user

@router.get("/quotes/{quote_id}")
def get_quote(quote_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_portal_user)):
    try:
        quote = PortalAuthorizationService.get_quotation(db, user.company_id, user.customer_id, quote_id)
        # Strip sensitive info
        return {
            "id": quote.id,
            "quotation_number": quote.quotation_number,
            "status": quote.status,
            "total_amount": quote.total_amount,
            "discount_amount": quote.discount_amount,
            "line_items": [{"id": li.id, "product": li.description, "quantity": li.quantity, "unit_price": li.unit_price, "total": li.total_amount} for li in quote.line_items]
        }
    except ValueError:
        raise HTTPException(status_code=404, detail="Quote not found")

@router.post("/quotes/{quote_id}/comments")
def add_comment(quote_id: uuid.UUID, comment: str, line_id: uuid.UUID = None, db: Session = Depends(get_db), user: User = Depends(get_portal_user)):
    try:
        c = CustomerCommentService.add_comment(db, user.company_id, user.customer_id, user.id, quote_id, comment, line_id)
        return {"status": "success", "id": c.id}
    except ValueError:
        raise HTTPException(status_code=404, detail="Quote not found")

@router.post("/quotes/{quote_id}/negotiations")
def submit_negotiation(quote_id: uuid.UUID, request_type: str, requested_value: str, current_value: str, reason: str, line_id: uuid.UUID = None, db: Session = Depends(get_db), user: User = Depends(get_portal_user)):
    try:
        req = NegotiationService.submit_request(db, user.company_id, user.customer_id, quote_id, request_type, requested_value, current_value, reason, line_id)
        return {"status": "success", "req_id": req.id, "req_status": req.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/quotes/{quote_id}/accept")
def accept_quote(quote_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_portal_user)):
    try:
        q = PortalAcceptanceService.accept_quote(db, user.company_id, user.customer_id, quote_id)
        return {"status": "success", "quote_status": q.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/quotes/{quote_id}/reject")
def reject_quote(quote_id: uuid.UUID, reason: str, db: Session = Depends(get_db), user: User = Depends(get_portal_user)):
    try:
        q = PortalRejectionService.reject_quote(db, user.company_id, user.customer_id, quote_id, reason)
        return {"status": "success", "quote_status": q.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/invoices/{invoice_id}/pay")
def pay_invoice(invoice_id: uuid.UUID, amount: Decimal, db: Session = Depends(get_db), user: User = Depends(get_portal_user)):
    try:
        inv = PortalPaymentService.process_payment(db, user.company_id, user.customer_id, invoice_id, amount)
        return {"status": "success", "payment_status": inv.payment_status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
