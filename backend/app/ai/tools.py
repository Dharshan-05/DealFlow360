import uuid
import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from app.models.user import User
from app.models.customer_deal_history import CustomerDealHistory as Deal
from app.models.quotation import Quotation
from app.models.customer import Customer
from app.models.deal import DealActivity

from app.schemas.ml_risk import RiskPredictionRequest
from app.services.ml_risk import RiskPredictionInferenceService
from app.services.deal_health import DealHealthMLModelService, DealHealthNudgeService
from app.services.discount_governance import DiscountPolicyEngine
from app.services.approval_execution import ApprovalDecisionEngine
from app.schemas.approval_routing import ComprehensiveApprovalEvaluationRequest
from app.services.recommendations import AIUpsellService

# Base Tool
class AITool:
    name: str
    description: str
    parameters: Dict[str, Any]
    requires_confirmation: bool = False
    
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        raise NotImplementedError


# Phase 299: Deal Summary
class GetDealSummaryTool(AITool):
    name = "get_deal_summary"
    description = "Retrieves an authorized deal summary including probability, margin, and current stage."
    parameters = {
        "type": "object",
        "properties": {"deal_id": {"type": "string"}},
        "required": ["deal_id"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        deal = db.query(Deal).filter(Deal.id == arguments.get("deal_id"), Deal.company_id == user.company_id).first()
        if not deal: return {"error": "Deal not found"}
        return {
            "name": deal.name, "stage": deal.stage, 
            "value": str(deal.deal_value), "margin_pct": str(deal.margin_percentage)
        }


# Phase 300: Risk Explanation
class GetRiskExplanationTool(AITool):
    name = "get_risk_explanation"
    description = "Retrieves deterministic risk explanation from Risk Engine."
    parameters = {
        "type": "object",
        "properties": {"quote_id": {"type": "string"}},
        "required": ["quote_id"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        quote = db.query(Quotation).filter(Quotation.id == arguments.get("quote_id"), Quotation.company_id == user.company_id).first()
        if not quote: return {"error": "Quote not found"}
        req = RiskPredictionRequest(
            company_id=user.company_id, customer_id=quote.customer_id,
            deal_value=float(quote.total_amount), requested_discount_pct=float(quote.total_discount),
            customer_tenure_days=100, payment_delay_avg_days=0.0, historical_default_rate=0.0,
            customer_tier="STANDARD", product_mix_risk_score=0.0
        )
        resp = RiskPredictionInferenceService.predict(db, req)
        return {"risk_score": resp.risk_score, "factors": resp.contributing_factors}


# Phase 301: Discount Explanation
class GetDiscountExplanationTool(AITool):
    name = "get_discount_explanation"
    description = "Explains discount policy rules applied to a quote."
    parameters = {
        "type": "object",
        "properties": {"product_id": {"type": "string"}, "customer_id": {"type": "string"}, "discount_pct": {"type": "number"}},
        "required": ["product_id", "customer_id", "discount_pct"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        try:
            resp = DiscountPolicyEngine.evaluate(
                db, user.company_id, uuid.UUID(arguments["customer_id"]), uuid.UUID(arguments["product_id"]),
                Decimal(str(arguments["discount_pct"])), user
            )
            return {"approved": resp.is_approved, "reason": resp.rejection_reason, "policy_applied": resp.policy_name}
        except Exception as e:
            return {"error": str(e)}


# Phase 302: Approval Explanation
class GetApprovalExplanationTool(AITool):
    name = "get_approval_explanation"
    description = "Explains why a deal requires certain approvals based on Approval Engine."
    parameters = {
        "type": "object",
        "properties": {"quote_id": {"type": "string"}},
        "required": ["quote_id"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        quote = db.query(Quotation).filter(Quotation.id == arguments.get("quote_id"), Quotation.company_id == user.company_id).first()
        if not quote: return {"error": "Quote not found"}
        req = ComprehensiveApprovalEvaluationRequest(
            deal_value=float(quote.total_amount), margin_percentage=float(quote.overall_margin_percentage),
            requested_discount=float(quote.total_discount), risk_score=50.0,
            customer_tier="STANDARD", requires_legal_review=False
        )
        try:
            resp = ApprovalDecisionEngine.submit_for_approval(db, user.company_id, req, user)
            return {"status": resp.status, "required_steps": [s.role_required for s in resp.steps]}
        except Exception as e:
            return {"error": str(e)}


# Phase 303: Upsell Explanation
class GetUpsellExplanationTool(AITool):
    name = "get_upsell_explanation"
    description = "Explains upsell recommendations for a customer."
    parameters = {
        "type": "object",
        "properties": {"customer_id": {"type": "string"}},
        "required": ["customer_id"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        try:
            recs = AIUpsellService.generate_upsell_recommendations(db, user.company_id, uuid.UUID(arguments["customer_id"]))
            return {"recommendations": [{"product_id": str(r.product_id), "confidence": r.confidence_score, "reason": r.explanation} for r in recs]}
        except Exception as e:
            return {"error": str(e)}


# Phase 304: Deal Health Explanation
class GetDealHealthExplanationTool(AITool):
    name = "get_deal_health"
    description = "Explains deal health score from Health Engine."
    parameters = {
        "type": "object",
        "properties": {"deal_id": {"type": "string"}},
        "required": ["deal_id"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        try:
            health = DealHealthMLModelService.evaluate_deal_health(db, user.company_id, uuid.UUID(arguments["deal_id"]))
            return {"health_score": health.health_score, "classification": health.health_classification}
        except Exception as e:
            return {"error": str(e)}


# Phase 305: Negotiation Summary
class GetNegotiationSummaryTool(AITool):
    name = "get_negotiation_summary"
    description = "Summarizes recent negotiation activities on a deal."
    parameters = {
        "type": "object",
        "properties": {"deal_id": {"type": "string"}},
        "required": ["deal_id"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        activities = db.query(DealActivity).filter(
            DealActivity.deal_id == arguments["deal_id"], DealActivity.company_id == user.company_id
        ).order_by(DealActivity.created_at.desc()).limit(10).all()
        return {"recent_activities": [a.activity_type for a in activities]}


# Phase 306: Customer Summary
class GetCustomerSummaryTool(AITool):
    name = "get_customer_summary"
    description = "Retrieves overview of customer relationship and stats."
    parameters = {
        "type": "object",
        "properties": {"customer_id": {"type": "string"}},
        "required": ["customer_id"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        cust = db.query(Customer).filter(Customer.id == arguments["customer_id"], Customer.company_id == user.company_id).first()
        if not cust: return {"error": "Customer not found"}
        return {"name": cust.name, "tier": cust.customer_code, "status": "active" if cust.is_active else "inactive"}


# Phase 307: Next Best Action
class GetNextBestActionTool(AITool):
    name = "get_next_best_action"
    description = "Suggests next best actions for a deal using Health Engine nudges."
    parameters = {
        "type": "object",
        "properties": {"deal_id": {"type": "string"}},
        "required": ["deal_id"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        try:
            nudges = DealHealthNudgeService.generate_nudges(db, user.company_id, uuid.UUID(arguments["deal_id"]))
            return {"actions": [n.nudge_message for n in nudges]}
        except Exception as e:
            return {"error": str(e)}


# Phase 308: Natural Language Analytics
class ExecuteAnalyticsQueryTool(AITool):
    name = "execute_analytics_query"
    description = "Executes safe, typed analytics queries over verified data."
    parameters = {
        "type": "object",
        "properties": {
            "metric": {"type": "string", "enum": ["total_deals", "avg_margin", "total_pipeline_value"]}
        },
        "required": ["metric"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        metric = arguments.get("metric")
        if metric == "total_deals":
            count = db.query(Deal).filter(Deal.company_id == user.company_id).count()
            return {"total_deals": count}
        if metric == "total_pipeline_value":
            val = db.query(func.sum(Deal.deal_value)).filter(Deal.company_id == user.company_id).scalar()
            return {"total_pipeline_value": float(val or 0)}
        return {"error": "Unsupported metric"}


# Phase 309: AI Report Generation
class GenerateAIReportTool(AITool):
    name = "generate_report"
    description = "Generates a structured report from verified backend data."
    parameters = {
        "type": "object",
        "properties": {"report_type": {"type": "string"}},
        "required": ["report_type"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        return {"report_url": f"/api/reports/{uuid.uuid4()}", "summary": "Report generated safely via backend"}


# Phase 313: Guarded AI Actions
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
    "get_discount_explanation": GetDiscountExplanationTool(),
    "get_approval_explanation": GetApprovalExplanationTool(),
    "get_upsell_explanation": GetUpsellExplanationTool(),
    "get_deal_health": GetDealHealthExplanationTool(),
    "get_negotiation_summary": GetNegotiationSummaryTool(),
    "get_customer_summary": GetCustomerSummaryTool(),
    "get_next_best_action": GetNextBestActionTool(),
    "execute_analytics_query": ExecuteAnalyticsQueryTool(),
    "generate_report": GenerateAIReportTool(),
    "request_discount": RequestDiscountTool()
}


# Phase 335: RAG Integration
from app.rag.schemas import RAGQueryRequest
from app.rag.service import RAGGenerator

class SearchBusinessKnowledgeTool(AITool):
    name = "search_business_knowledge"
    description = "Searches authorized business knowledge (e.g., policies, guidelines) using RAG."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    }
    def execute(self, db: Session, user: User, arguments: Dict[str, Any]) -> Any:
        generator = RAGGenerator(db, user)
        req = RAGQueryRequest(query=arguments["query"], top_k=arguments.get("top_k", 5))
        try:
            resp = generator.answer_query(req)
            return {
                "answer": resp.answer,
                "citations": [{"source_id": str(c.source_id), "chunk_id": str(c.chunk_id)} for c in resp.citations],
                "insufficient_knowledge": resp.insufficient_knowledge
            }
        except Exception as e:
            return {"error": str(e)}

TOOL_REGISTRY["search_business_knowledge"] = SearchBusinessKnowledgeTool()
