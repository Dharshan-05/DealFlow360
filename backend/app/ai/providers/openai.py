import os
import time
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.ai.providers.base import LLMProvider, LLMResponse, LLMUsage

logger = logging.getLogger("dealflow360.ai")

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        
        # Auto-detect provider base URL and default model
        configured_base_url = os.getenv("LLM_BASE_URL")
        if configured_base_url:
            self.base_url = configured_base_url.rstrip("/")
        elif self.api_key and self.api_key.startswith("xai-"):
            self.base_url = "https://api.x.ai/v1"
        else:
            self.base_url = "https://api.openai.com/v1"

        configured_model = os.getenv("LLM_MODEL")
        if configured_model:
            self.model = configured_model
        elif self.api_key and self.api_key.startswith("xai-"):
            self.model = "grok-2-latest"
        else:
            self.model = "gpt-4o-mini"
        
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[type[BaseModel]] = None,
        temperature: float = 0.0
    ) -> LLMResponse:
        start_time = time.time()
        
        # If no API key or in testing mode, return simulated response
        if not self.api_key or self.api_key == "test":
            return self._generate_simulation(messages, tools, response_format, start_time)

        # Real OpenAI / xAI Grok API call
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Format messages cleanly
        cleaned_messages = []
        for m in messages:
            msg_dict: Dict[str, Any] = {"role": m.get("role", "user")}
            if m.get("content") is not None:
                msg_dict["content"] = m["content"]
            if m.get("tool_calls"):
                msg_dict["tool_calls"] = m["tool_calls"]
            if m.get("tool_call_id"):
                msg_dict["tool_call_id"] = m["tool_call_id"]
            cleaned_messages.append(msg_dict)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": cleaned_messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

                latency = int((time.time() - start_time) * 1000)

                # Handle insufficient quota or permission error gracefully
                if response.status_code == 403 or response.status_code == 429:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_msg = error_data.get("error") or response.text
                    logger.warning(f"AI API quota/spending limit notice ({response.status_code}): {error_msg}")
                    
                    # If xAI credits are exhausted, return clear message and fallback
                    sim = self._generate_simulation(messages, tools, response_format, start_time)
                    sim.content = (
                        f"[Notice: xAI Grok API Key is connected, but the team account has reached its spending limit or used available credits. "
                        f"Please top up credits at console.x.ai.]\n\n"
                        f"{sim.content}"
                    )
                    return sim

                response.raise_for_status()
                data = response.json()
                
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content")
                tool_calls = message.get("tool_calls")

                usage_data = data.get("usage", {})
                usage = LLMUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )

                return LLMResponse(
                    content=content,
                    tool_calls=tool_calls,
                    usage=usage,
                    model=data.get("model", self.model),
                    latency_ms=latency
                )

        except Exception as e:
            logger.error(f"Error calling LLM provider ({self.base_url}): {e}")
            latency = int((time.time() - start_time) * 1000)
            sim = self._generate_simulation(messages, tools, response_format, start_time)
            sim.content = f"[AI Provider notice: {str(e)}]\n\n{sim.content}"
            return sim

    def _generate_simulation(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        response_format: Optional[type[BaseModel]],
        start_time: float
    ) -> LLMResponse:
        latency = int((time.time() - start_time) * 1000)
        content = "This is DealFlow360 AI Copilot. I can assist you with deal health, approval workflows, discount governance, and revenue analytics."
        tool_calls = None
        
        last_msg = messages[-1].get("content", "") if messages else ""
        if isinstance(last_msg, str):
            if "get_deal_summary" in last_msg and tools:
                tool_calls = [{"id": "call_123", "type": "function", "function": {"name": "get_deal_summary", "arguments": "{}"}}]
            if "explain risk" in last_msg.lower() and tools:
                tool_calls = [{"id": "call_124", "type": "function", "function": {"name": "get_risk_explanation", "arguments": "{}"}}]
            if "analytics" in last_msg.lower() and tools:
                tool_calls = [{"id": "call_125", "type": "function", "function": {"name": "analytics_query", "arguments": '{"metric":"deals", "limit":10}'}}]
        
        if response_format and not tool_calls:
            content = response_format().model_dump_json()
            
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            model=f"{self.model} (fallback)",
            latency_ms=latency
        )
