"""
LLM Provider 模块

提供统一的 LLM 调用抽象层，支持多 provider 扩展。
"""
from typing import Dict, Optional

from app.services.llm.base import BaseLLMProvider
from app.services.llm.zhipu import ZhipuProvider

__all__ = [
    "BaseLLMProvider",
    "ZhipuProvider",
    "get_llm_provider",
]

# Provider 注册表
_PROVIDER_REGISTRY: Dict[str, type] = {
    "zhipu": ZhipuProvider,
}

# Provider 实例缓存（按 provider 名称）
_provider_cache: Dict[str, BaseLLMProvider] = {}


def get_llm_provider(
    provider: str, api_key: str, model: str = ""
) -> BaseLLMProvider:
    """
    根据 provider 名称获取 LLM Provider 实例

    同一 provider 复用实例（更新 api_key）。

    Args:
        provider: provider 名称（如 "zhipu"）
        api_key: API 密钥
        model: 默认模型名称

    Returns:
        BaseLLMProvider 实例
    """
    cls = _PROVIDER_REGISTRY.get(provider, ZhipuProvider)

    cached = _provider_cache.get(provider)
    if cached is not None and cached.api_key == api_key:
        if model:
            cached.model = model
        return cached

    instance = cls(api_key=api_key, model=model) if model else cls(api_key=api_key)
    _provider_cache[provider] = instance
    return instance
