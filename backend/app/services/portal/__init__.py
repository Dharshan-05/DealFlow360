import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.customer import Customer
from app.models.quotation import Quotation
from app.models.quotation_line_item import QuotationLineItem
from app.models.billing import Invoice, PaymentStatus
from app.models.portal import CustomerComment, NegotiationRequest, NegotiationHistory, CustomerNotification
from app.models.role import Role

from app.services.quotation import QuotationService
from app.services.discount_governance import DiscountPolicyEngine
from app.schemas.ml_risk import RiskPredictionRequest
from app.services.ml_risk import RiskPredictionInferenceService
from app.services.approval_execution import ApprovalDecisionEngine
from app.schemas.approval_routing import ComprehensiveApprovalEvaluationRequest
from app.models.user import User





from app.services.billing import PaymentStatusService


class PortalAuthenticationService:
    @staticmethod
    def verify_portal_user(db: Session, user: User) -> bool:
        # User must have customer_id
        if not user.customer_id:
            return False
            
        # Must have "Customer Portal" role
        has_role = any(r.name == "Customer Portal" for r in user.roles)
        return has_role


class PortalAuthorizationService:
    @staticmethod
    def get_quotation(db: Session, company_id: uuid.UUID, customer_id: uuid.UUID, quotation_id: uuid.UUID) -> Quotation:
        quote = db.scalar(select(Quotation).where(
            Quotation.id == quotation_id,
            Quotation.company_id == company_id,
            Quotation.customer_id == customer_id
        ))
        if not quote:
            raise ValueError("Quotation not found or access denied")
        return quote
        
    @staticmethod
    def get_invoice(db: Session, company_id: uuid.UUID, customer_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
        inv = db.scalar(select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.company_id == company_id,
            Invoice.customer_id == customer_id
        ))
        if not inv:
            raise ValueError("Invoice not found or access denied")
        return inv


class CustomerCommentService:
    @staticmethod
    def add_comment(db: Session, company_id: uuid.UUID, customer_id: uuid.UUID, user_id: uuid.UUID, quotation_id: uuid.UUID, comment: str, line_id: Optional[uuid.UUID] = None) -> CustomerComment:
        quote = PortalAuthorizationService.get_quotation(db, company_id, customer_id, quotation_id)
        
        c = CustomerComment(
            company_id=company_id,
            quotation_id=quote.id,
            quotation_line_id=line_id,
            customer_id=customer_id,
            author_id=user_id,
            comment=comment
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return c


class NegotiationService:
    @staticmethod
    def submit_request(db: Session, company_id: uuid.UUID, customer_id: uuid.UUID, quotation_id: uuid.UUID, 
                       request_type: str, requested_value: str, current_value: str, reason: str, line_id: Optional[uuid.UUID] = None) -> NegotiationRequest:
        quote = PortalAuthorizationService.get_quotation(db, company_id, customer_id, quotation_id)
        
        if quote.status not in ["SENT", "NEGOTIATION"]:
            raise ValueError("Quote is not in a negotiable state")
            
        # Create request
        req = NegotiationRequest(
            company_id=company_id,
            quotation_id=quote.id,
            quotation_line_id=line_id,
            customer_id=customer_id,
            request_type=request_type,
            requested_value=requested_value,
            current_value=current_value,
            reason=reason,
            status="SUBMITTED"
        )
        db.add(req)
        
        # Log History
        hist = NegotiationHistory(
            company_id=company_id,
            quotation_id=quote.id,
            customer_id=customer_id,
            event_type="NEGOTIATION_REQUESTED",
            description=f"Requested {request_type} from {current_value} to {requested_value}",
            metadata_data={"reason": reason, "line_id": str(line_id) if line_id else None}
        )
        db.add(hist)
        
        # Trigger intent/validation/policy flow
        NegotiationService._process_request(db, req, quote)
        
        db.commit()
        db.refresh(req)
        return req
        


    @staticmethod
    def _process_request(db: Session, req: NegotiationRequest, quote: Quotation):
        # 1. Intent Extraction (Deterministic Phase 284)
        intent = NegotiationIntentService.extract_intent(req.request_type, req.requested_value)
        if not intent:
            req.status = "REJECTED"
            return
            
        # 2. Validation (Phase 285)
        if not NegotiationValidationService.validate(req, intent):
            req.status = "REJECTED"
            return
            
        # 3. Policy Recheck (Phase 286)
        if intent["type"] == "DISCOUNT":
            new_discount = Decimal(intent["value"])
            # Temporarily simulate the change for policy evaluation
            original_discount = quote.total_discount
            quote.total_discount = new_discount
            
            policy_result = {"auto_approved": True}
            
            try:
                actor = db.query(User).filter(User.id == quote.user_id).first()
                if actor:
                    first_line = db.query(QuotationLineItem).filter(QuotationLineItem.quotation_id == quote.id).first()
                    if first_line:
                        res = DiscountPolicyEngine.evaluate(
                            db=db,
                            company_id=quote.company_id,
                            customer_id=quote.customer_id,
                            product_id=first_line.product_id,
                            proposed_discount=new_discount,
                            actor=actor
                        )
                        if not res.allowed:
                            policy_result["auto_approved"] = False
            except Exception as e:
                policy_result["auto_approved"] = False
            
            # 4. Risk Recalculation (Phase 287)
            try:
                risk_req = RiskPredictionRequest(
                    company_id=quote.company_id,
                    customer_id=quote.customer_id,
                    deal_value=float(quote.total_amount),
                    requested_discount_pct=float(new_discount),
                    customer_tenure_days=100,
                    payment_delay_avg_days=0.0,
                    historical_default_rate=0.0,
                    customer_tier="STANDARD",
                    product_mix_risk_score=0.0
                )
                risk_resp = RiskPredictionInferenceService.predict(db, risk_req)
                if risk_resp.risk_score > 70:
                    policy_result["auto_approved"] = False
            except Exception:
                pass
            
            # 5. Automatic Reapproval (Phase 288)
            if not policy_result.get("auto_approved", False):
                req.status = "PENDING_APPROVAL"
                quote.status = "AWAITING_APPROVAL"
                try:
                    actor = db.query(User).filter(User.id == quote.user_id).first()
                    if actor:
                        comp_req = ComprehensiveApprovalEvaluationRequest(
                            deal_reference=quote.quotation_number,
                            deal_value=quote.total_amount,
                            selling_price=quote.subtotal,
                            unit_cost=quote.subtotal * Decimal("0.5"),
                            requested_discount_pct=new_discount,
                            customer_id=quote.customer_id
                        )
                        ApprovalDecisionEngine.submit_for_approval(
                            db=db,
                            company_id=quote.company_id,
                            request_payload=comp_req,
                            actor=actor
                        )
                except Exception:
                    pass
            else:
                req.status = "APPROVED"
                req.resolved_at = datetime.now()
            
            quote.total_discount = original_discount
            
        elif intent["type"] == "DELIVERY":
            req.status = "PENDING_APPROVAL"
            quote.status = "AWAITING_APPROVAL"
            try:
                actor = db.query(User).filter(User.id == quote.user_id).first()
                if actor:
                    comp_req = ComprehensiveApprovalEvaluationRequest(
                        deal_reference=quote.quotation_number,
                        deal_value=quote.total_amount,
                        selling_price=quote.subtotal,
                        unit_cost=quote.subtotal * Decimal("0.5"),
                        requested_discount_pct=quote.total_discount,
                        customer_id=quote.customer_id
                    )
                    ApprovalDecisionEngine.submit_for_approval(
                        db=db,
                        company_id=quote.company_id,
                        request_payload=comp_req,
                        actor=actor
                    )
            except Exception:
                pass
        
        # Phase 290 Customer Notifications
        PortalNotificationService.notify(db, quote.company_id, quote.customer_id, "NEGOTIATION_SUBMITTED", "Negotiation Submitted", f"Your request for {intent['type']} has been submitted.")


class NegotiationIntentService:
    @staticmethod
    def extract_intent(req_type: str, req_value: str) -> dict:
        if req_type == "REQUEST_DISCOUNT":
            try:
                # Strip % and parse
                val = req_value.replace("%", "").strip()
                return {"type": "DISCOUNT", "value": val}
            except:
                return None
        elif req_type == "CHANGE_DELIVERY":
            return {"type": "DELIVERY", "value": req_value}
        return {"type": "UNKNOWN"}


class NegotiationValidationService:
    @staticmethod
    def validate(req: NegotiationRequest, intent: dict) -> bool:
        if intent["type"] == "DISCOUNT":
            try:
                val = Decimal(intent["value"])
                if val < 0 or val > 100: return False
                return True
            except:
                return False
        return True


class PortalAcceptanceService:
    @staticmethod
    def accept_quote(db: Session, company_id: uuid.UUID, customer_id: uuid.UUID, quotation_id: uuid.UUID) -> Quotation:
        quote = PortalAuthorizationService.get_quotation(db, company_id, customer_id, quotation_id)
        
        if quote.status in ["ACCEPTED", "CONFIRMED", "CONVERTED"]:
            return quote # Idempotent
            
        if quote.status not in ["SENT", "NEGOTIATION", "APPROVED"]:
            raise ValueError("Quote cannot be accepted in current state")
            
        quote.status = "ACCEPTED"
        quote.accepted_at = datetime.now()
        
        # Log History
        hist = NegotiationHistory(
            company_id=company_id,
            quotation_id=quote.id,
            customer_id=customer_id,
            event_type="QUOTE_ACCEPTED",
            description="Customer accepted the quotation"
        )
        db.add(hist)
        
        PortalNotificationService.notify(db, company_id, customer_id, "QUOTE_ACCEPTED", "Quote Accepted", f"You have accepted quote {quote.quotation_number}")
        
        db.commit()
        db.refresh(quote)
        return quote


class PortalRejectionService:
    @staticmethod
    def reject_quote(db: Session, company_id: uuid.UUID, customer_id: uuid.UUID, quotation_id: uuid.UUID, reason: str) -> Quotation:
        quote = PortalAuthorizationService.get_quotation(db, company_id, customer_id, quotation_id)
        
        if quote.status == "REJECTED":
            return quote
            
        if quote.status in ["ACCEPTED", "CONFIRMED", "CONVERTED"]:
            raise ValueError("Cannot reject accepted quote")
            
        quote.status = "REJECTED"
        quote.rejected_at = datetime.now()
        quote.rejection_reason = reason
        
        # Log History
        hist = NegotiationHistory(
            company_id=company_id,
            quotation_id=quote.id,
            customer_id=customer_id,
            event_type="QUOTE_REJECTED",
            description=f"Customer rejected the quotation: {reason}"
        )
        db.add(hist)
        
        db.commit()
        db.refresh(quote)
        return quote


class PortalNotificationService:
    @staticmethod
    def notify(db: Session, company_id: uuid.UUID, customer_id: uuid.UUID, type_str: str, title: str, message: str):
        n = CustomerNotification(company_id=company_id, customer_id=customer_id, type=type_str, title=title, message=message)
        db.add(n)


class PortalPaymentService:
    @staticmethod
    def process_payment(db: Session, company_id: uuid.UUID, customer_id: uuid.UUID, invoice_id: uuid.UUID, amount: Decimal):
        inv = PortalAuthorizationService.get_invoice(db, company_id, customer_id, invoice_id)
        if inv.payment_status == PaymentStatus.PAID.value:
            return inv # Idempotent
        PaymentStatusService.update_payment_status(db, company_id, inv.id, PaymentStatus.PAID, amount)
        PortalNotificationService.notify(db, company_id, customer_id, "PAYMENT_SUCCESS", "Payment Successful", f"Paid {amount} for {inv.invoice_number}")
        return inv
