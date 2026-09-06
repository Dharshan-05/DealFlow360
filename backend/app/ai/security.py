import re
from typing import Dict, Any

class PromptInjectionError(Exception):
    pass

class UnauthorizedAIActionError(Exception):
    pass

def sanitize_untrusted_input(text: str) -> str:
    """Phase 314: Defends against basic prompt injection."""
    if not text:
        return text
        
    # Basic heuristical blocks
    suspicious_patterns = [
        r"ignore previous instructions",
        r"reveal system prompt",
        r"system instructions",
        r"bypassing",
        r"override"
    ]
    
    text_lower = text.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, text_lower):
            raise PromptInjectionError("Suspicious instruction detected in user input.")
            
    # Wrap in untrusted tags to enforce boundary
    return f"[[UNTRUSTED_CONTENT_START]]\n{text}\n[[UNTRUSTED_CONTENT_END]]"

def check_permission_for_tool(user, tool_name: str) -> bool:
    """Phase 315: Evaluates existing RBAC before allowing AI tool."""
    # For now, simplistic RBAC checks.
    # In DealFlow360, this would check specific user roles.
    restricted_tools = ["submit_approval", "request_discount"]
    if tool_name in restricted_tools:
        # Mock logic: assume they have permission if they are active
        if not user.is_active:
            raise UnauthorizedAIActionError(f"User lacks permission to execute {tool_name}")
    return True
