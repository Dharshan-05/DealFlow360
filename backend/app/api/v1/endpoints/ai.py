from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.session import get_db
from app.api.v1.endpoints.deps import get_current_user
from app.models.user import User
from app.ai.schemas import AIQueryRequest, AIQueryResponse, GuardedActionRequest
from app.ai.orchestrator import AIOrchestrator
from app.models.ai import AIUsage

router = APIRouter()

@router.post("/query", response_model=AIQueryResponse)
def ai_query(
    request: AIQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orchestrator = AIOrchestrator(db, current_user)
    return orchestrator.process_query(request)

@router.post("/action", response_model=AIQueryResponse)
def execute_guarded_action(
    request: GuardedActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not request.confirmed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be confirmed")
        
    orchestrator = AIOrchestrator(db, current_user)
    return orchestrator.execute_guarded_action(
        conversation_id=request.conversation_id,
        tool_name=request.tool_name,
        arguments=request.arguments
    )

@router.get("/status")
def ai_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return {
        "status": "Operational",
        "provider": "Connected",
        "model": "gpt-4o-mini"
    }

@router.get("/usage")
def ai_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Phase 317: Usage Tracking
    from sqlalchemy import func
    total_tokens = db.query(func.sum(AIUsage.total_tokens)).filter(AIUsage.company_id == current_user.company_id).scalar() or 0
    return {
        "total_tokens": total_tokens
    }
