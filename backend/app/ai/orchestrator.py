import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from app.models.user import User
from app.models.ai import AIConversation, AIMessage, AIAuditEvent, AIUsage
from app.ai.providers import get_provider
from app.ai.schemas import AIQueryRequest, AIQueryResponse, AIActionConfirmation
from app.ai.tools import TOOL_REGISTRY
from app.ai.security import sanitize_untrusted_input, check_permission_for_tool, PromptInjectionError, UnauthorizedAIActionError

class AIOrchestrator:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.provider = get_provider()
    
    def process_query(self, request: AIQueryRequest) -> AIQueryResponse:
        try:
            safe_message = sanitize_untrusted_input(request.message)
        except PromptInjectionError as e:
            self._log_audit("PROMPT_INJECTION_BLOCKED", error_message=str(e), success=False)
            return AIQueryResponse(answer="I cannot safely process that request due to restricted keywords.")

        conversation = self._get_or_create_conversation(request.conversation_id)
        
        system_prompt = "You are DealFlow360 AI Copilot. You explain data from tools and provide verified business insights."
        
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in conversation.messages[-5:]:
            m = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            messages.append(m)
            
        messages.append({"role": "user", "content": safe_message})
        
        tools = [
            {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
            for t in TOOL_REGISTRY.values()
        ]

        # Phase 318: AI Error Handling
        try:
            response = self.provider.generate(messages=messages, tools=tools)
        except TimeoutError as e:
            self._log_audit("PROVIDER_TIMEOUT", error_message=str(e), success=False)
            return AIQueryResponse(answer="AI Provider timed out.")
        except Exception as e:
            if "rate limit" in str(e).lower():
                self._log_audit("RATE_LIMIT_ERROR", error_message=str(e), success=False)
                return AIQueryResponse(answer="Rate limit exceeded.")
            self._log_audit("PROVIDER_ERROR", error_message=str(e), success=False)
            return AIQueryResponse(answer="AI Provider is currently unavailable.")
            
        self._record_usage(response)
        self._save_message(conversation.id, "user", safe_message)
        
        if response.tool_calls:
            self._save_message(conversation.id, "assistant", response.content, tool_calls=response.tool_calls)
            
            tool_call = response.tool_calls[0]
            func_data = tool_call["function"]
            name = func_data["name"]
            
            try:
                args = json.loads(func_data.get("arguments", "{}"))
            except json.JSONDecodeError:
                self._log_audit("MALFORMED_TOOL_OUTPUT", error_message="Invalid JSON from LLM", success=False)
                return AIQueryResponse(answer="The AI generated a malformed request. Please try again.")
            
            tool_instance = TOOL_REGISTRY.get(name)
            if not tool_instance:
                return AIQueryResponse(answer="Requested tool not found.")
                
            try:
                check_permission_for_tool(self.user, name)
            except UnauthorizedAIActionError as e:
                self._log_audit("PERMISSION_DENIED", tool_name=name, error_message=str(e), success=False)
                return AIQueryResponse(answer=f"Permission denied: {str(e)}")
            
            if tool_instance.requires_confirmation:
                self._log_audit("GUARDED_MUTATION_REQUESTED", tool_name=name, action_payload=args)
                return AIQueryResponse(
                    answer="This action requires your confirmation.",
                    requires_confirmation=True,
                    action_preview=AIActionConfirmation(tool_name=name, arguments=args)
                )
                
            start_time = datetime.utcnow()
            try:
                result = tool_instance.execute(self.db, self.user, args)
                latency = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                self._log_audit("TOOL_EXECUTION", tool_name=name, action_payload=args, action_result=result, latency_ms=latency)
                
                self._save_message(conversation.id, "tool", json.dumps(result), tool_call_id=tool_call["id"])
                messages.append({"role": "assistant", "tool_calls": response.tool_calls})
                messages.append({"role": "tool", "tool_call_id": tool_call["id"], "content": json.dumps(result)})
                
                final_response = self.provider.generate(messages=messages)
                self._save_message(conversation.id, "assistant", final_response.content)
                self._record_usage(final_response)
                
                citations = []
                if isinstance(result, dict) and "citations" in result:
                    citations = result["citations"]

                return AIQueryResponse(answer=final_response.content or "Tool executed.", citations=citations)
                
            except Exception as e:
                self._log_audit("TOOL_EXECUTION_FAILED", tool_name=name, action_payload=args, success=False, error_message=str(e))
                return AIQueryResponse(answer=f"Error executing business validation: {str(e)}")

        self._save_message(conversation.id, "assistant", response.content)
        return AIQueryResponse(answer=response.content or "I couldn't generate a response.")

    def execute_guarded_action(self, conversation_id: str, tool_name: str, arguments: Dict[str, Any]) -> AIQueryResponse:
        tool_instance = TOOL_REGISTRY.get(tool_name)
        if not tool_instance:
            return AIQueryResponse(answer="Invalid action.")
            
        start_time = datetime.utcnow()
        try:
            result = tool_instance.execute(self.db, self.user, arguments)
            latency = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._log_audit("GUARDED_MUTATION_EXECUTED", tool_name=tool_name, action_payload=arguments, action_result=result, latency_ms=latency)
            return AIQueryResponse(answer=result.get("message", "Action completed successfully."))
        except Exception as e:
            self._log_audit("GUARDED_MUTATION_FAILED", tool_name=tool_name, action_payload=arguments, success=False, error_message=str(e))
            return AIQueryResponse(answer=f"Action failed: {str(e)}")

    def _get_or_create_conversation(self, conversation_id: Optional[str]) -> AIConversation:
        if conversation_id:
            conv = self.db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.company_id == self.user.company_id
            ).first()
            if conv:
                return conv
        conv = AIConversation(company_id=self.user.company_id, user_id=self.user.id)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def _save_message(self, conversation_id, role, content, tool_calls=None, tool_call_id=None):
        msg = AIMessage(
            conversation_id=conversation_id, role=role, content=content,
            tool_calls=tool_calls, tool_call_id=tool_call_id
        )
        self.db.add(msg)
        self.db.commit()

    def _record_usage(self, response):
        usage = AIUsage(
            company_id=self.user.company_id, user_id=self.user.id,
            provider="openai", model=response.model,
            prompt_tokens=response.usage.prompt_tokens, completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )
        self.db.add(usage)
        self.db.commit()

    def _log_audit(self, action_type, tool_name=None, action_payload=None, action_result=None, success=True, error_message=None, latency_ms=None):
        audit = AIAuditEvent(
            company_id=self.user.company_id, user_id=self.user.id, action_type=action_type,
            tool_name=tool_name, action_payload=action_payload, action_result=action_result,
            success=success, error_message=error_message, latency_ms=latency_ms
        )
        self.db.add(audit)
        self.db.commit()
