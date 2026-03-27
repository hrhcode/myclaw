"""
嵌入向量生成服务
使用 OpenRouter API 调用配置的 embedding 模型生成向量嵌入
"""
import httpx
import logging
import struct
import hashlib
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.config import get_config_value
from app.models import EmbeddingCache

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_KEY = "openrouter_api_key"
EMBEDDING_MODEL_KEY = "embedding_model"
EMBEDDING_PROVIDER_KEY = "embedding_provider"
CACHE_ENABLED_KEY = "embedding_cache_enabled"
CACHE_MAX_ENTRIES_KEY = "embedding_cache_max_entries"
EMBEDDING_PROVIDER_LOCAL = "local"
EMBEDDING_PROVIDER_OPENROUTER = "openrouter"


class EmbeddingService:
    """
    嵌入向量生成服务
    """
    
    def __init__(self, api_key: str, model: str = DEFAULT_EMBEDDING_MODEL, cache_enabled: bool = True, cache_max_entries: int = 50000):
        """
        初始化嵌入服务
        
        Args:
            api_key: OpenRouter API Key
            model: 使用的 embedding 模型
            cache_enabled: 是否启用缓存
            cache_max_entries: 缓存最大条目数
        """
        self.api_key = api_key
        self.base_url = OPENROUTER_BASE_URL
        self.model = model
        self.cache_enabled = cache_enabled
        self.cache_max_entries = cache_max_entries
    
    def _compute_content_hash(self, content: str) -> str:
        """
        计算内容的SHA256哈希值
        
        Args:
            content: 要哈希的内容
            
        Returns:
            SHA256哈希字符串
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def _get_from_cache(self, db: AsyncSession, content_hash: str) -> Optional[bytes]:
        """
        从缓存中获取嵌入
        
        Args:
            db: 数据库会话
            content_hash: 内容哈希
            
        Returns:
            缓存的嵌入字节数据，未命中返回None
        """
        if not self.cache_enabled:
            return None
        
        try:
            result = await db.execute(
                select(EmbeddingCache).where(EmbeddingCache.content_hash == content_hash)
            )
            cache_entry = result.scalar_one_or_none()
            
            if cache_entry:
                cache_entry.last_accessed_at = datetime.now()
                cache_entry.access_count += 1
                await db.commit()
                logger.debug(f"缓存命中: {content_hash[:16]}...")
                return cache_entry.embedding
            
            return None
        except Exception as e:
            logger.warning(f"缓存查询失败: {str(e)}")
            return None
    
    async def _save_to_cache(self, db: AsyncSession, content_hash: str, embedding: bytes) -> None:
        """
        保存嵌入到缓存
        
        Args:
            db: 数据库会话
            content_hash: 内容哈希
            embedding: 嵌入字节数据
        """
        if not self.cache_enabled:
            return None
        
        try:
            await self._cleanup_cache_if_needed(db)
            
            result = await db.execute(
                select(EmbeddingCache).where(EmbeddingCache.content_hash == content_hash)
            )
            existing_entry = result.scalar_one_or_none()
            
            if existing_entry:
                existing_entry.embedding = embedding
                existing_entry.model = self.model
                existing_entry.last_accessed_at = datetime.now()
                existing_entry.access_count += 1
                logger.debug(f"缓存更新: {content_hash[:16]}...")
            else:
                cache_entry = EmbeddingCache(
                    content_hash=content_hash,
                    embedding=embedding,
                    model=self.model,
                    created_at=datetime.now(),
                    last_accessed_at=datetime.now(),
                    access_count=1
                )
                db.add(cache_entry)
                logger.debug(f"缓存保存: {content_hash[:16]}...")
            
            await db.commit()
        except Exception as e:
            logger.warning(f"缓存保存失败: {str(e)}")
    
    async def _cleanup_cache_if_needed(self, db: AsyncSession) -> None:
        """
        如果缓存超过最大条目数，清理最旧的条目
        
        Args:
            db: 数据库会话
        """
        try:
            from sqlalchemy import func
            
            result = await db.execute(
                select(func.count()).select_from(EmbeddingCache)
            )
            count = result.scalar()
            
            if count and count >= self.cache_max_entries:
                await db.execute(
                    delete(EmbeddingCache).where(
                        EmbeddingCache.id.in_(
                            select(EmbeddingCache.id)
                            .order_by(EmbeddingCache.last_accessed_at.asc())
                            .limit(count - self.cache_max_entries + 100)
                        )
                    )
                )
                await db.commit()
                logger.info(f"清理缓存，删除 {count - self.cache_max_entries} 条旧记录")
        except Exception as e:
            logger.warning(f"缓存清理失败: {str(e)}")
    
    async def get_embedding(self, db: AsyncSession, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """
        获取文本的向量嵌入
        
        Args:
            db: 数据库会话
            text: 要嵌入的文本
            use_cache: 是否使用缓存
            
        Returns:
            向量嵌入列表，失败返回 None
        """
        if not text or not text.strip():
            return None
        
        content_hash = self._compute_content_hash(text.strip())
        
        if use_cache:
            cached_embedding = await self._get_from_cache(db, content_hash)
            if cached_embedding:
                return bytes_to_embedding(cached_embedding)
        
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
                        
                        if use_cache:
                            await self._save_to_cache(db, content_hash, embedding_to_bytes(embedding))
                        
                        return embedding
                
                logger.error(f"嵌入响应格式错误: {data}")
                return None
                
        except httpx.TimeoutException:
            logger.error("嵌入API调用超时")
            return None
        except Exception as e:
            logger.error(f"嵌入API调用异常: {str(e)}")
            return None
    
    async def get_embeddings_batch(self, db: AsyncSession, texts: List[str], use_cache: bool = True) -> List[Optional[List[float]]]:
        """
        批量获取文本的向量嵌入
        
        Args:
            db: 数据库会话
            texts: 要嵌入的文本列表
            use_cache: 是否使用缓存
            
        Returns:
            向量嵌入列表
        """
        if not texts:
            return []
        
        valid_texts = [text.strip() for text in texts if text and text.strip()]
        if not valid_texts:
            return []
        
        content_hashes = [self._compute_content_hash(text) for text in valid_texts]
        
        cached_results = {}
        if use_cache:
            for i, (text, content_hash) in enumerate(zip(valid_texts, content_hashes)):
                cached_embedding = await self._get_from_cache(db, content_hash)
                if cached_embedding:
                    cached_results[i] = bytes_to_embedding(cached_embedding)
        
        uncached_texts = []
        uncached_indices = []
        for i, (text, content_hash) in enumerate(zip(valid_texts, content_hashes)):
            if i not in cached_results:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        if uncached_texts:
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
                            "input": uncached_texts
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"批量嵌入API调用失败: {response.status_code} - {response.text}")
                        for i in uncached_indices:
                            cached_results[i] = None
                    else:
                        data = response.json()
                        
                        if "data" in data and len(data["data"]) == len(uncached_texts):
                            for idx, embedding_data in enumerate(data["data"]):
                                embedding = embedding_data.get("embedding")
                                if embedding:
                                    i = uncached_indices[idx]
                                    cached_results[i] = embedding
                                    
                                    if use_cache:
                                        await self._save_to_cache(db, content_hashes[i], embedding)
                                    logger.debug(f"成功生成嵌入向量 {i+1}/{len(uncached_texts)}，维度: {len(embedding)}")
                                else:
                                    logger.error(f"批量嵌入响应格式错误: {data}")
                                    for i in uncached_indices:
                                        cached_results[i] = None
            except httpx.TimeoutException:
                logger.error("批量嵌入API调用超时")
                for i in uncached_indices:
                    cached_results[i] = None
            except Exception as e:
                logger.error(f"批量嵌入API调用异常: {str(e)}")
                for i in uncached_indices:
                    cached_results[i] = None
        
        results = []
        for i in range(len(texts)):
            if i < len(valid_texts):
                results.append(cached_results.get(i))
            else:
                results.append(None)
        
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
local_embedding_service_instance: Optional['LocalEmbeddingService'] = None


class LocalEmbeddingService:
    """
    本地嵌入向量生成服务
    使用 sentence-transformers 模型生成嵌入
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", cache_enabled: bool = True, cache_max_entries: int = 50000):
        """
        初始化本地嵌入服务
        
        Args:
            model_name: 使用的模型名称
            cache_enabled: 是否启用缓存
            cache_max_entries: 缓存最大条目数
        """
        self.model_name = model_name
        self.cache_enabled = cache_enabled
        self.cache_max_entries = cache_max_entries
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """
        加载本地嵌入模型
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"成功加载本地嵌入模型: {self.model_name}")
        except Exception as e:
            logger.error(f"加载本地嵌入模型失败: {str(e)}")
            raise
    
    def _compute_content_hash(self, content: str) -> str:
        """
        计算内容的SHA256哈希值
        
        Args:
            content: 要哈希的内容
            
        Returns:
            SHA256哈希字符串
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def _get_from_cache(self, db: AsyncSession, content_hash: str) -> Optional[bytes]:
        """
        从缓存中获取嵌入
        
        Args:
            db: 数据库会话
            content_hash: 内容哈希
            
        Returns:
            缓存的嵌入字节数据，未命中返回None
        """
        if not self.cache_enabled:
            return None
        
        try:
            result = await db.execute(
                select(EmbeddingCache).where(EmbeddingCache.content_hash == content_hash)
            )
            cache_entry = result.scalar_one_or_none()
            
            if cache_entry:
                await db.execute(
                    delete(EmbeddingCache).where(EmbeddingCache.id == cache_entry.id)
                )
                cache_entry.last_accessed_at = datetime.now()
                cache_entry.access_count += 1
                db.add(cache_entry)
                await db.commit()
                logger.debug(f"缓存命中: {content_hash[:16]}...")
                return cache_entry.embedding
            
            return None
        except Exception as e:
            logger.warning(f"缓存查询失败: {str(e)}")
            return None
    
    async def _save_to_cache(self, db: AsyncSession, content_hash: str, embedding: List[float]) -> None:
        """
        保存嵌入到缓存
        
        Args:
            db: 数据库会话
            content_hash: 内容哈希
            embedding: 嵌入列表
        """
        if not self.cache_enabled:
            return None
        
        try:
            await self._cleanup_cache_if_needed(db)
            
            cache_entry = EmbeddingCache(
                content_hash=content_hash,
                embedding=embedding_to_bytes(embedding),
                model=self.model_name,
                created_at=datetime.now(),
                last_accessed_at=datetime.now(),
                access_count=1
            )
            db.add(cache_entry)
            await db.commit()
            logger.debug(f"缓存保存: {content_hash[:16]}...")
        except Exception as e:
            logger.warning(f"缓存保存失败: {str(e)}")
    
    async def _cleanup_cache_if_needed(self, db: AsyncSession) -> None:
        """
        如果缓存超过最大条目数，清理最旧的条目
        
        Args:
            db: 数据库会话
        """
        try:
            result = await db.execute(
                select(EmbeddingCache).count()
            )
            count = result.scalar()
            
            if count and count >= self.cache_max_entries:
                await db.execute(
                    delete(EmbeddingCache).where(
                        EmbeddingCache.id.in_(
                            select(EmbeddingCache.id)
                            .order_by(EmbeddingCache.last_accessed_at.asc())
                            .limit(count - self.cache_max_entries + 100)
                        )
                    )
                )
                await db.commit()
                logger.info(f"清理缓存，删除 {count - self.cache_max_entries} 条旧记录")
        except Exception as e:
            logger.warning(f"缓存清理失败: {str(e)}")
    
    async def get_embedding(self, db: AsyncSession, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """
        获取文本的向量嵌入
        
        Args:
            db: 数据库会话
            text: 要嵌入的文本
            use_cache: 是否使用缓存
            
        Returns:
            向量嵌入列表，失败返回 None
        """
        if not text or not text.strip():
            return None
        
        if not self.model:
            logger.error("本地嵌入模型未加载")
            return None
        
        content_hash = self._compute_content_hash(text.strip())
        
        if use_cache:
            cached_embedding = await self._get_from_cache(db, content_hash)
            if cached_embedding:
                return bytes_to_embedding(cached_embedding)
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.model.encode,
                text.strip()
            )
            
            if embedding is not None:
                embedding_list = embedding.tolist()
                logger.debug(f"成功生成嵌入向量，维度: {len(embedding_list)}")
                
                if use_cache:
                    await self._save_to_cache(db, content_hash, embedding_list)
                
                return embedding_list
            
            logger.error("嵌入生成返回None")
            return None
        except Exception as e:
            logger.error(f"本地嵌入生成失败: {str(e)}")
            return None
    
    async def get_embeddings_batch(self, db: AsyncSession, texts: List[str], use_cache: bool = True) -> List[Optional[List[float]]]:
        """
        批量获取文本的向量嵌入
        
        Args:
            db: 数据库会话
            texts: 要嵌入的文本列表
            use_cache: 是否使用缓存
            
        Returns:
            向量嵌入列表
        """
        results = []
        for text in texts:
            embedding = await self.get_embedding(db, text, use_cache)
            results.append(embedding)
        return results


async def get_embedding_service(db) -> Optional[object]:
    """
    获取嵌入服务实例（单例模式）
    
    Args:
        db: 数据库会话
        
    Returns:
        EmbeddingService 或 LocalEmbeddingService 实例，未配置返回 None
    """
    global embedding_service_instance, local_embedding_service_instance
    
    provider = await get_config_value(db, EMBEDDING_PROVIDER_KEY)
    if not provider:
        provider = EMBEDDING_PROVIDER_OPENROUTER
    
    if provider == EMBEDDING_PROVIDER_LOCAL:
        model = await get_config_value(db, EMBEDDING_MODEL_KEY)
        if not model:
            model = "sentence-transformers/all-MiniLM-L6-v2"
        
        cache_enabled = await get_config_value(db, CACHE_ENABLED_KEY)
        if cache_enabled is None:
            cache_enabled = True
        
        cache_max_entries = await get_config_value(db, CACHE_MAX_ENTRIES_KEY)
        if cache_max_entries is None:
            cache_max_entries = 50000
        
        if local_embedding_service_instance is None:
            try:
                local_embedding_service_instance = LocalEmbeddingService(
                    model_name=model,
                    cache_enabled=cache_enabled,
                    cache_max_entries=cache_max_entries
                )
            except Exception as e:
                logger.error(f"初始化本地嵌入服务失败: {str(e)}，降级到远程API")
                provider = EMBEDDING_PROVIDER_OPENROUTER
        
        if local_embedding_service_instance:
            return local_embedding_service_instance
    
    if provider == EMBEDDING_PROVIDER_OPENROUTER:
        api_key = await get_config_value(db, OPENROUTER_API_KEY_KEY)
        if not api_key:
            logger.warning("OpenRouter API Key 未配置")
            return None
        
        model = await get_config_value(db, EMBEDDING_MODEL_KEY)
        if not model:
            model = DEFAULT_EMBEDDING_MODEL
        
        cache_enabled = await get_config_value(db, CACHE_ENABLED_KEY)
        if cache_enabled is None:
            cache_enabled = True
        
        cache_max_entries = await get_config_value(db, CACHE_MAX_ENTRIES_KEY)
        if cache_max_entries is None:
            cache_max_entries = 50000
        
        if embedding_service_instance is None:
            embedding_service_instance = EmbeddingService(
                api_key=api_key, 
                model=model,
                cache_enabled=cache_enabled,
                cache_max_entries=cache_max_entries
            )
        else:
            embedding_service_instance.api_key = api_key
            embedding_service_instance.model = model
            embedding_service_instance.cache_enabled = cache_enabled
            embedding_service_instance.cache_max_entries = cache_max_entries
        
        return embedding_service_instance
    
    return None
