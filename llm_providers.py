# llm_providers.py （修复版）
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages, temperature=0.1):
        pass

# 通义千问
class DashScopeProvider(LLMProvider):
    def __init__(self, api_key, model='qwen-turbo'):
        import dashscope
        dashscope.api_key = api_key
        self.model = model

    def chat(self, messages, temperature=0.1):
        from dashscope import Generation
        response = Generation.call(
            model=self.model,
            messages=messages,
            result_format='message',
            temperature=temperature
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"DashScope API error: {response.code}")

# OpenAI 修复版
class OpenAIProvider(LLMProvider):
    def __init__(self, api_key, model='gpt-3.5-turbo'):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def chat(self, messages, temperature=0.1):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

def create_llm_provider(provider_type, api_key, model=None):
    if provider_type == "dashscope":
        return DashScopeProvider(api_key, model=model or "qwen-turbo")
    elif provider_type == "openai":
        return OpenAIProvider(api_key, model=model or "gpt-3.5-turbo")
    else:
        raise ValueError(f"Unsupported provider: {provider_type}")
