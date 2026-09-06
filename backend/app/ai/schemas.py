from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AIQueryRequest(BaseModel):
    message: str
    context_type: Optional[str] = None  # deal, customer, quote
    context_id: Optional[str] = None
    conversation_id: Optional[str] = None

class AIActionConfirmation(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class AIQueryResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    requires_confirmation: bool = False
    action_preview: Optional[AIActionConfirmation] = None

class AnalyticsQuery(BaseModel):
    metric: str
    dimensions: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    date_range: Optional[str] = None
    aggregation: Optional[str] = None
    limit: Optional[int] = 10
    sorting: Optional[str] = None

class GuardedActionRequest(BaseModel):
    conversation_id: str
    tool_name: str
    arguments: Dict[str, Any]
    confirmed: bool
