"""
嵌入向量生成服务
使用 OpenRouter API 调用配置的 embedding 模型生成向量嵌入
"""
import httpx
import logging
import struct
from typing import Optional, List
from app.api.config import get_config_value

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_KEY = "openrouter_api_key"
EMBEDDING_MODEL_KEY = "embedding_model"
EMBEDDING_PROVIDER_KEY = "embedding_provider"


class EmbeddingService:
    """
    嵌入向量生成服务
    """
    
    def __init__(self, api_key: str, model: str = DEFAULT_EMBEDDING_MODEL):
        """
        初始化嵌入服务
        
        Args:
            api_key: OpenRouter API Key
            model: 使用的 embedding 模型
        """
        self.api_key = api_key
        self.base_url = OPENROUTER_BASE_URL
        self.model = model
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            向量嵌入列表，失败返回 None
        """
        if not text or not text.strip():
            return None
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://myclaw.local",
                        "X-Title": "MyClaw Chat"
                    },
                    json={
                        "model": self.model,
                        "input": text.strip()
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"嵌入API调用失败: {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                
                if "data" in data and len(data["data"]) > 0:
                    embedding = data["data"][0].get("embedding")
                    if embedding:
                        logger.debug(f"成功生成嵌入向量，维度: {len(embedding)}")
                        return embedding
                
                logger.error(f"嵌入响应格式错误: {data}")
                return None
                
        except httpx.TimeoutException:
            logger.error("嵌入API调用超时")
            return None
        except Exception as e:
            logger.error(f"嵌入API调用异常: {str(e)}")
            return None
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        批量获取文本的向量嵌入
        
        Args:
            texts: 要嵌入的文本列表
            
        Returns:
            向量嵌入列表
        """
        results = []
        for text in texts:
            embedding = await self.get_embedding(text)
            results.append(embedding)
        return results


def embedding_to_bytes(embedding: List[float]) -> bytes:
    """
    将向量嵌入列表转换为字节存储
    
    Args:
        embedding: 向量嵌入列表
        
    Returns:
        字节表示
    """
    return struct.pack(f'{len(embedding)}f', *embedding)


def bytes_to_embedding(data: bytes) -> List[float]:
    """
    将字节转换回向量嵌入列表
    
    Args:
        data: 字节数据
        
    Returns:
        向量嵌入列表
    """
    if not data:
        return []
    count = len(data) // 4
    return list(struct.unpack(f'{count}f', data))


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的余弦相似度
    
    Args:
        vec1: 向量1
        vec2: 向量2
        
    Returns:
        余弦相似度 (0-1)
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


embedding_service_instance: Optional[EmbeddingService] = None


async def get_embedding_service(db) -> Optional[EmbeddingService]:
    """
    获取嵌入服务实例（单例模式）
    
    Args:
        db: 数据库会话
        
    Returns:
        EmbeddingService 实例，未配置返回 None
    """
    global embedding_service_instance
    
    api_key = await get_config_value(db, OPENROUTER_API_KEY_KEY)
    if not api_key:
        logger.warning("OpenRouter API Key 未配置")
        return None
    
    model = await get_config_value(db, EMBEDDING_MODEL_KEY)
    if not model:
        model = DEFAULT_EMBEDDING_MODEL
    
    if embedding_service_instance is None:
        embedding_service_instance = EmbeddingService(api_key=api_key, model=model)
    else:
        embedding_service_instance.api_key = api_key
        embedding_service_instance.model = model
    
    return embedding_service_instance
