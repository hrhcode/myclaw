"""
配置管理模块
负责加载 YAML 配置文件并支持环境变量替换
"""

import os
import re
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """服务器配置"""

    port: int = Field(default=18789, description="服务端口")
    host: str = Field(default="127.0.0.1", description="绑定地址")


class LLMConfig(BaseModel):
    """LLM 配置"""

    provider: str = Field(default="zhipu", description="LLM 提供商")
    model: str = Field(default="glm-4-flash", description="模型名称")
    api_key: str = Field(default="", description="API Key")


class WechatConfig(BaseModel):
    """企业微信配置"""

    enabled: bool = Field(default=False, description="是否启用微信")
    corp_id: str = Field(default="", description="企业ID")
    agent_id: str = Field(default="", description="应用AgentId")
    secret: str = Field(default="", description="应用Secret")
    token: str = Field(default="", description="回调Token")
    encoding_aes_key: str = Field(default="", description="加密Key")


class EmbeddingConfig(BaseModel):
    """Embedding 配置"""

    provider: Literal["zhipu", "openrouter", "none"] = Field(
        default="none", description="Embedding 提供商 (zhipu/openrouter/none)"
    )
    model: str = Field(
        default="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        description="Embedding 模型名称",
    )
    api_key: str = Field(default="", description="Embedding API Key (可选，默认使用 LLM API Key)")
    base_url: str = Field(default="https://openrouter.ai/api/v1", description="API 基础 URL")


class HybridSearchConfig(BaseModel):
    """混合检索配置"""

    enabled: bool = Field(default=True, description="是否启用混合检索")
    vector_weight: float = Field(default=0.7, description="向量检索权重")
    fts_weight: float = Field(default=0.3, description="FTS 检索权重")
    min_score: float = Field(default=0.3, description="最低相似度阈值")


class MemoryConfig(BaseModel):
    """记忆系统配置"""

    enabled: bool = Field(default=True, description="是否启用记忆")
    max_memories: int = Field(default=1000, description="最大记忆数量")
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    hybrid_search: HybridSearchConfig = Field(default_factory=HybridSearchConfig)


class SearchToolConfig(BaseModel):
    """搜索工具配置"""

    provider: str = Field(default="duckduckgo", description="搜索提供商")


class ToolsConfig(BaseModel):
    """工具配置"""

    search: SearchToolConfig = Field(default_factory=SearchToolConfig)


class AgentConfig(BaseModel):
    """Agent 配置"""

    system_prompt: str = Field(
        default="你是一个有用的 AI 助手。你可以使用各种工具来帮助用户解决问题。",
        description="系统提示词"
    )


class AppConfig(BaseModel):
    """应用配置"""

    server: ServerConfig = Field(default_factory=ServerConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    wechat: WechatConfig = Field(default_factory=WechatConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)


ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def resolve_env_vars(value: str) -> str:
    """
    解析字符串中的环境变量引用
    
    Args:
        value: 包含环境变量引用的字符串，如 "${VAR_NAME}"
        
    Returns:
        解析后的字符串
    """
    matches = ENV_VAR_PATTERN.findall(value)
    for match in matches:
        env_value = os.environ.get(match, "")
        value = value.replace(f"${{{match}}}", env_value)
    return value


def resolve_config_env_vars(config: dict) -> dict:
    """
    递归解析配置字典中的环境变量
    
    Args:
        config: 配置字典
        
    Returns:
        解析后的配置字典
    """
    result = {}
    for key, value in config.items():
        if isinstance(value, dict):
            result[key] = resolve_config_env_vars(value)
        elif isinstance(value, str):
            result[key] = resolve_env_vars(value)
        else:
            result[key] = value
    return result


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，默认为当前目录的 config.yaml
        
    Returns:
        AppConfig 配置对象
    """
    if config_path is None:
        config_path = str(Path.cwd() / "config.yaml")

    path = Path(config_path)
    if not path.exists():
        return AppConfig()

    with open(path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f) or {}

    resolved_config = resolve_config_env_vars(raw_config)
    return AppConfig(**resolved_config)


_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    获取全局配置实例（单例模式）
    
    Returns:
        AppConfig 配置对象
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> AppConfig:
    """
    重新加载配置
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        AppConfig 配置对象
    """
    global _config
    _config = load_config(config_path)
    return _config
