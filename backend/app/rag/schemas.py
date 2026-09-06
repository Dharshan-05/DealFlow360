from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class KnowledgeSourceCreate(BaseModel):
    name: str
    source_type: str
    metadata_: Optional[Dict[str, Any]] = Field(default_factory=dict)

class KnowledgeSourceResponse(KnowledgeSourceCreate):
    id: uuid.UUID
    company_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    source_id: Optional[uuid.UUID] = None

class RAGCitation(BaseModel):
    source_id: uuid.UUID
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    score: float
    text: str
    page_number: Optional[int] = None

class RAGQueryResponse(BaseModel):
    answer: str
    citations: List[RAGCitation]
    insufficient_knowledge: bool = False
