"""
LLM Service 兼容层

保留此模块以维持向后兼容，实际实现已迁移到 app.services.llm 子模块。
"""
from typing import Optional

from app.services.llm import BaseLLMProvider, ZhipuProvider, get_llm_provider

# 向后兼容：导出 LLMService 作为 ZhipuProvider 的别名
LLMService = ZhipuProvider

llm_service_global: Optional[BaseLLMProvider] = None


def get_llm_service(api_key: str) -> BaseLLMProvider:
    """
    获取 LLM 服务实例（单例模式，兼容旧接口）

    Args:
        api_key: API 密钥

    Returns:
        BaseLLMProvider 实例
    """
    global llm_service_global

    if llm_service_global is None:
        llm_service_global = get_llm_provider("zhipu", api_key)
    else:
        # 更新 api_key（复用实例时智谱 client 需要重建）
        if llm_service_global.api_key != api_key:
            llm_service_global = get_llm_provider("zhipu", api_key)

    return llm_service_global
