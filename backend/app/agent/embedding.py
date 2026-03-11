"""
Embedding 客户端模块
支持多种 Embedding 提供商：智谱 AI、OpenRouter
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

import httpx

if TYPE_CHECKING:
    from app.config import AppConfig

logger = logging.getLogger(__name__)


class EmbeddingClient(ABC):
    """Embedding 客户端抽象基类"""

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
        """
        pass

    @abstractmethod
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        批量获取文本的向量嵌入
        
        Args:
            texts: 输入文本列表
            
        Returns:
            嵌入向量列表
        """
        pass


class ZhipuEmbeddingClient(EmbeddingClient):
    """智谱 AI Embedding 客户端"""

    def __init__(self, api_key: str, model: str = "embedding-3"):
        """
        初始化智谱 AI Embedding 客户端
        
        Args:
            api_key: 智谱 AI API Key
            model: Embedding 模型名称
        """
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        """获取智谱 AI 客户端"""
        if self._client is None:
            from zhipuai import ZhipuAI
            self._client = ZhipuAI(api_key=self.api_key)
        return self._client

    async def get_embedding(self, text: str) -> list[float]:
        """获取单个文本的向量嵌入"""
        client = self._get_client()
        response = client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """批量获取文本的向量嵌入"""
        client = self._get_client()
        response = client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [item.embedding for item in response.data]


class OpenRouterEmbeddingClient(EmbeddingClient):
    """OpenRouter Embedding 客户端"""

    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/llama-nemotron-embed-vl-1b-v2:free",
        base_url: str = "https://openrouter.ai/api/v1",
    ):
        """
        初始化 OpenRouter Embedding 客户端
        
        Args:
            api_key: OpenRouter API Key
            model: Embedding 模型名称
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def get_embedding(self, text: str) -> list[float]:
        """获取单个文本的向量嵌入"""
        embeddings = await self.get_embeddings([text])
        return embeddings[0] if embeddings else []

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """批量获取文本的向量嵌入"""
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json={
                    "model": self.model,
                    "input": texts,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return [item["embedding"] for item in data["data"]]


class NoneEmbeddingClient(EmbeddingClient):
    """空 Embedding 客户端（禁用向量检索）"""

    async def get_embedding(self, text: str) -> list[float]:
        """返回空向量"""
        return []

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """返回空向量列表"""
        return [[] for _ in texts]


_embedding_client: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """
    获取全局 Embedding 客户端实例（单例模式）
    
    Returns:
        EmbeddingClient 实例
    """
    global _embedding_client
    if _embedding_client is None:
        from app.config import get_config
        config = get_config()
        embedding_config = config.memory.embedding
        
        if embedding_config.provider == "none":
            logger.info("Embedding 提供商已禁用，将使用 FTS-only 模式")
            _embedding_client = NoneEmbeddingClient()
        elif embedding_config.provider == "openrouter":
            api_key = embedding_config.api_key or config.llm.api_key
            if not api_key:
                logger.warning("OpenRouter API Key 未配置，将使用 FTS-only 模式")
                _embedding_client = NoneEmbeddingClient()
            else:
                logger.info(f"使用 OpenRouter Embedding: {embedding_config.model}")
                _embedding_client = OpenRouterEmbeddingClient(
                    api_key=api_key,
                    model=embedding_config.model,
                    base_url=embedding_config.base_url,
                )
        elif embedding_config.provider == "zhipu":
            api_key = config.llm.api_key
            if not api_key:
                logger.warning("智谱 AI API Key 未配置，将使用 FTS-only 模式")
                _embedding_client = NoneEmbeddingClient()
            else:
                logger.info(f"使用智谱 AI Embedding: {embedding_config.model}")
                _embedding_client = ZhipuEmbeddingClient(
                    api_key=api_key,
                    model=embedding_config.model,
                )
        else:
            logger.warning(f"未知的 Embedding 提供商: {embedding_config.provider}，将使用 FTS-only 模式")
            _embedding_client = NoneEmbeddingClient()
    
    return _embedding_client


def reset_embedding_client() -> None:
    """重置 Embedding 客户端（用于配置重新加载）"""
    global _embedding_client
    _embedding_client = None
