# llm_providers.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages, temperature=0.1):
        """发送对话消息并返回模型生成的文本内容"""
        pass
    
# 在 LLMProvider 类定义之后追加

class DashScopeProvider(LLMProvider):
    def __init__(self, api_key, model='qwen-turbo'):
        import dashscope
        dashscope.api_key = api_key
        self.api_key = api_key
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
        
class OpenAIProvider(LLMProvider):
    def __init__(self, api_key, model='gpt-3.5-turbo'):
        import openai
        openai.api_key = api_key
        self.model = model

    def chat(self, messages, temperature=0.1):
        import openai
        response = openai.ChatCompletion.create(
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
