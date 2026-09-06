import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import relationship

from app.db.base import Base

class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(pgUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIMessage.created_at")
    company = relationship("Company")
    user = relationship("User")


class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(pgUUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system, tool
    content = Column(String, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    tool_call_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("AIConversation", back_populates="messages")


class AIAuditEvent(Base):
    __tablename__ = "ai_audit_events"

    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(pgUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(pgUUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True)
    
    action_type = Column(String(100), nullable=False)  # e.g., 'TOOL_EXECUTION', 'GUARDED_MUTATION', 'PROMPT_INJECTION_BLOCKED'
    tool_name = Column(String(100), nullable=True)
    action_payload = Column(JSON, nullable=True)
    action_result = Column(JSON, nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(String, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AIUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(pgUUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(pgUUID(as_uuid=True), ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True)
    
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

