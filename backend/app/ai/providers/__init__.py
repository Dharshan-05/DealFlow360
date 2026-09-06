from .base import LLMProvider, LLMResponse, LLMUsage
from .openai import OpenAIProvider

def get_provider() -> LLMProvider:
    return OpenAIProvider()
