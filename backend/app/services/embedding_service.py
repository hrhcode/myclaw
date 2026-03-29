"""
嵌入向量生成服务
使用 OpenRouter API 调用配置的 embedding 模型生成向量嵌入
"""
import httpx
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.config import get_config_value
from app.models.models import EmbeddingCache
from app.common.constants import (
    DEFAULT_EMBEDDING_MODEL,
    OPENROUTER_BASE_URL,
    OPENROUTER_API_KEY_KEY,
    EMBEDDING_MODEL_KEY,
    EMBEDDING_PROVIDER_KEY,
    CACHE_ENABLED_KEY,
    CACHE_MAX_ENTRIES_KEY,
    EMBEDDING_PROVIDER_LOCAL,
    EMBEDDING_PROVIDER_OPENROUTER,
    LOG_SEPARATOR_SHORT,
)
from app.common.utils.embedding import (
    embedding_to_bytes,
    bytes_to_embedding,
    cosine_similarity,
    compute_content_hash,
)

logger = logging.getLogger(__name__)


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
    
    async def _get_from_cache(self, db: AsyncSession, content_hash: str) -> Optional[bytes]:
        """
        从缓存中获取嵌入（使用独立数据库会话）
        
        Args:
            db: 数据库会话（未使用，保留参数兼容性）
            content_hash: 内容哈希
            
        Returns:
            缓存的嵌入字节数据，未命中返回None
        """
        if not self.cache_enabled:
            return None
        
        from app.core.database import AsyncSessionLocal
        
        try:
            async with AsyncSessionLocal() as cache_db:
                result = await cache_db.execute(
                    select(EmbeddingCache).where(EmbeddingCache.content_hash == content_hash)
                )
                cache_entry = result.scalar_one_or_none()
                
                if cache_entry:
                    embedding_data = cache_entry.embedding
                    cache_entry.last_accessed_at = datetime.now()
                    cache_entry.access_count += 1
                    await cache_db.commit()
                    logger.debug(f"缓存命中: {content_hash[:16]}...")
                    return embedding_data
                
                return None
        except Exception as e:
            logger.warning(f"缓存查询失败: {str(e)}")
            return None
    
    async def _save_to_cache(self, db: AsyncSession, content_hash: str, embedding: bytes) -> None:
        """
        保存嵌入到缓存（使用独立数据库会话）
        
        Args:
            db: 数据库会话
            content_hash: 内容哈希
            embedding: 嵌入字节数据
        """
        if not self.cache_enabled:
            return
        
        from app.core.database import AsyncSessionLocal
        
        try:
            async with AsyncSessionLocal() as cache_db:
                await self._cleanup_cache_if_needed(cache_db)
                
                result = await cache_db.execute(
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
                    cache_db.add(cache_entry)
                    logger.debug(f"缓存保存: {content_hash[:16]}...")
                
                await cache_db.commit()
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
            logger.warning("[嵌入生成] 输入文本为空，跳过嵌入生成")
            return None
        
        content_hash = self._compute_content_hash(text.strip())
        logger.debug(f"[嵌入生成] 开始处理，文本长度: {len(text)}, 哈希: {content_hash[:16]}...")
        
        if use_cache:
            cached_embedding = await self._get_from_cache(db, content_hash)
            if cached_embedding:
                embedding_list = bytes_to_embedding(cached_embedding)
                logger.info(f"[嵌入生成] 缓存命中，维度: {len(embedding_list)}")
                return embedding_list
            else:
                logger.debug("[嵌入生成] 缓存未命中，调用API生成")
        
        try:
            logger.info(f"[嵌入生成] 调用OpenRouter API，模型: {self.model}")
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
                    logger.error(f"[嵌入生成] API调用失败: HTTP {response.status_code} - {response.text[:200]}")
                    return None
                
                data = response.json()
                
                if "data" in data and len(data["data"]) > 0:
                    embedding = data["data"][0].get("embedding")
                    if embedding:
                        logger.info(f"[嵌入生成] 成功，维度: {len(embedding)}")
                        
                        if use_cache:
                            await self._save_to_cache(db, content_hash, embedding_to_bytes(embedding))
                            logger.debug(f"[嵌入生成] 已缓存，哈希: {content_hash[:16]}...")
                        
                        return embedding
                
                logger.error(f"[嵌入生成] 响应格式错误: {str(data)[:200]}")
                return None
                
        except httpx.TimeoutException:
            logger.error("[嵌入生成] API调用超时 (60s)")
            return None
        except Exception as e:
            logger.error(f"[嵌入生成] 异常: {str(e)}")
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
            logger.info(f"[本地嵌入] 开始加载模型: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"[本地嵌入] 模型加载成功: {self.model_name}")
        except Exception as e:
            logger.error(f"[本地嵌入] 模型加载失败: {str(e)}")
            raise
    
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
        
        from app.core.database import AsyncSessionLocal
        
        try:
            async with AsyncSessionLocal() as cache_db:
                result = await cache_db.execute(
                    select(EmbeddingCache).where(EmbeddingCache.content_hash == content_hash)
                )
                cache_entry = result.scalar_one_or_none()
                
                if cache_entry:
                    embedding_data = cache_entry.embedding
                    cache_entry.last_accessed_at = datetime.now()
                    cache_entry.access_count += 1
                    await cache_db.commit()
                    logger.debug(f"缓存命中: {content_hash[:16]}...")
                    return embedding_data
                
                return None
        except Exception as e:
            logger.warning(f"缓存查询失败: {str(e)}")
            return None
    
    async def _save_to_cache(self, db: AsyncSession, content_hash: str, embedding: List[float]) -> None:
        """
        保存嵌入到缓存（使用独立数据库会话）
        
        Args:
            db: 数据库会话（未使用，保留参数兼容性）
            content_hash: 内容哈希
            embedding: 嵌入列表
        """
        if not self.cache_enabled:
            return
        
        from app.core.database import AsyncSessionLocal
        
        try:
            async with AsyncSessionLocal() as cache_db:
                await self._cleanup_cache_if_needed(cache_db)
                
                cache_entry = EmbeddingCache(
                    content_hash=content_hash,
                    embedding=embedding_to_bytes(embedding),
                    model=self.model_name,
                    created_at=datetime.now(),
                    last_accessed_at=datetime.now(),
                    access_count=1
                )
                cache_db.add(cache_entry)
                await cache_db.commit()
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
            logger.warning("[本地嵌入] 输入文本为空，跳过嵌入生成")
            return None
        
        if not self.model:
            logger.error("[本地嵌入] 模型未加载")
            return None
        
        content_hash = self._compute_content_hash(text.strip())
        logger.debug(f"[本地嵌入] 开始处理，文本长度: {len(text)}, 哈希: {content_hash[:16]}...")
        
        if use_cache:
            cached_embedding = await self._get_from_cache(db, content_hash)
            if cached_embedding:
                embedding_list = bytes_to_embedding(cached_embedding)
                logger.info(f"[本地嵌入] 缓存命中，维度: {len(embedding_list)}")
                return embedding_list
            else:
                logger.debug("[本地嵌入] 缓存未命中，开始生成")
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            logger.debug(f"[本地嵌入] 开始生成嵌入向量...")
            embedding = await loop.run_in_executor(
                None,
                self.model.encode,
                text.strip()
            )
            
            if embedding is not None:
                embedding_list = embedding.tolist()
                logger.info(f"[本地嵌入] 成功，维度: {len(embedding_list)}")
                
                if use_cache:
                    await self._save_to_cache(db, content_hash, embedding_list)
                    logger.debug(f"[本地嵌入] 已缓存，哈希: {content_hash[:16]}...")
                
                return embedding_list
            
            logger.error("[本地嵌入] 嵌入生成返回None")
            return None
        except Exception as e:
            logger.error(f"[本地嵌入] 生成失败: {str(e)}")
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
    
    logger.debug(f"[嵌入服务] 初始化嵌入服务，提供商: {provider}")
    
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
                logger.info(f"[嵌入服务] 创建本地嵌入服务实例，模型: {model}")
                local_embedding_service_instance = LocalEmbeddingService(
                    model_name=model,
                    cache_enabled=cache_enabled,
                    cache_max_entries=cache_max_entries
                )
                logger.info("[嵌入服务] 本地嵌入服务初始化成功")
            except Exception as e:
                logger.error(f"[嵌入服务] 初始化本地嵌入服务失败: {str(e)}，降级到远程API")
                provider = EMBEDDING_PROVIDER_OPENROUTER
        
        if local_embedding_service_instance:
            return local_embedding_service_instance
    
    if provider == EMBEDDING_PROVIDER_OPENROUTER:
        api_key = await get_config_value(db, OPENROUTER_API_KEY_KEY)
        if not api_key:
            logger.warning("[嵌入服务] OpenRouter API Key 未配置")
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
            logger.info(f"[嵌入服务] 创建OpenRouter嵌入服务实例，模型: {model}")
            embedding_service_instance = EmbeddingService(
                api_key=api_key, 
                model=model,
                cache_enabled=cache_enabled,
                cache_max_entries=cache_max_entries
            )
            logger.info("[嵌入服务] OpenRouter嵌入服务初始化成功")
        else:
            embedding_service_instance.api_key = api_key
            embedding_service_instance.model = model
            embedding_service_instance.cache_enabled = cache_enabled
            embedding_service_instance.cache_max_entries = cache_max_entries
            logger.debug(f"[嵌入服务] 更新现有实例配置，模型: {model}")
        
        return embedding_service_instance
    
    logger.warning("[嵌入服务] 未找到可用的嵌入服务提供商")
    return None
