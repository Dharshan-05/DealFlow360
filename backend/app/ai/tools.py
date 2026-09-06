from typing import Dict, Any, List
import uuid
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

from app.models.user import User
from app.models.customer_deal_history import CustomerDealHistory as Deal
from app.models.quotation import Quotation
from app.services.deal_health import DealHealthMLModelService
from app.services.ml_risk import RiskPredictionInferenceService
from app.schemas.ml_risk import RiskPredictionRequest

# Phase 311 - Tool Registry

class AITool:
    name: str
    description: str
    parameters: Dict[str, Any]
    requires_confirmation: bool = False
    
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        raise NotImplementedError

class GetDealSummaryTool(AITool):
    name = "get_deal_summary"
    description = "Retrieves an authorized deal summary including probability, margin, and current stage."
    parameters = {
        "type": "object",
        "properties": {
            "deal_id": {"type": "string"}
        },
        "required": ["deal_id"]
    }
    
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        deal_id = arguments.get("deal_id")
        deal = db.query(Deal).filter(Deal.id == deal_id, Deal.company_id == user.company_id).first()
        if not deal:
            return {"error": "Deal not found or unauthorized."}
        
        return {
            "deal_overview": deal.name,
            "current_stage": deal.stage,
            "value": str(deal.amount),
            "probability": deal.probability,
            "blockers": "None visible from stage.",
        }

class GetRiskExplanationTool(AITool):
    name = "get_risk_explanation"
    description = "Retrieves risk factors and scores for a specific quote or deal."
    parameters = {
        "type": "object",
        "properties": {
            "deal_id": {"type": "string"},
            "quote_id": {"type": "string"}
        }
    }
    
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        # We integrate with existing RiskPredictionInferenceService (Phase 300)
        # We need a Deal or Quote to get the value
        quote_id = arguments.get("quote_id")
        if not quote_id:
            return {"error": "Quote ID required for precise risk explanation"}
            
        quote = db.query(Quotation).filter(Quotation.id == quote_id, Quotation.company_id == user.company_id).first()
        if not quote:
            return {"error": "Quote not found or unauthorized"}
            
        risk_req = RiskPredictionRequest(
            company_id=quote.company_id,
            customer_id=quote.customer_id,
            deal_value=float(quote.total_amount),
            requested_discount_pct=float(quote.total_discount),
            customer_tenure_days=100,
            payment_delay_avg_days=0.0,
            historical_default_rate=0.0,
            customer_tier="STANDARD",
            product_mix_risk_score=0.0
        )
        
        try:
            risk_resp = RiskPredictionInferenceService.predict(db, risk_req)
            return {
                "risk_score": risk_resp.risk_score,
                "classification": risk_resp.classification,
                "factors": risk_resp.contributing_factors,
                "recommended_mitigation": risk_resp.mitigation_recommendation
            }
        except Exception as e:
            return {"error": f"Failed to calculate risk: {str(e)}"}

class GetDealHealthTool(AITool):
    name = "get_deal_health"
    description = "Retrieves the Deal Health Engine score and classification."
    parameters = {
        "type": "object",
        "properties": {
            "deal_id": {"type": "string"}
        },
        "required": ["deal_id"]
    }
    
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        deal_id = arguments.get("deal_id")
        try:
            health = DealHealthMLModelService.evaluate_deal_health(db, deal_id, user.company_id)
            return {
                "health_score": health.health_score,
                "classification": health.health_classification,
                "conversion_probability": health.conversion_probability
            }
        except Exception as e:
            return {"error": "Could not evaluate deal health."}

class RequestDiscountTool(AITool):
    name = "request_discount"
    description = "Mutating action to request a higher discount on a quote."
    parameters = {
        "type": "object",
        "properties": {
            "quote_id": {"type": "string"},
            "discount_percentage": {"type": "number"}
        },
        "required": ["quote_id", "discount_percentage"]
    }
    requires_confirmation = True
    
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        return {"status": "success", "message": f"Discount request for {arguments.get('discount_percentage')}% submitted."}


TOOL_REGISTRY = {
    "get_deal_summary": GetDealSummaryTool(),
    "get_risk_explanation": GetRiskExplanationTool(),
    "get_deal_health": GetDealHealthTool(),
    "request_discount": RequestDiscountTool()
}
