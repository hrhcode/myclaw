"""
Web 搜索工具

支持多搜索引擎 API（Brave、Perplexity、自定义）进行网络搜索
"""
import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

import aiohttp

from app.tools.base import BaseTool, ToolDefinition, create_tool

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    搜索结果项
    
    Attributes:
        title: 结果标题
        url: 结果链接
        snippet: 摘要片段
        source: 来源
    """
    title: str
    url: str
    snippet: str = ""
    source: str = ""


@dataclass
class SearchResponse:
    """
    搜索响应
    
    Attributes:
        query: 搜索查询
        results: 搜索结果列表
        provider: 搜索提供商
        cached: 是否来自缓存
        latency_ms: 响应延迟（毫秒）
    """
    query: str
    results: List[SearchResult] = field(default_factory=list)
    provider: str = ""
    cached: bool = False
    latency_ms: int = 0


class SearchCache:
    """
    简单的内存搜索缓存
    
    使用 TTL 过期机制缓存搜索结果
    """
    
    def __init__(self, ttl_seconds: int = 900):
        """
        初始化缓存
        
        Args:
            ttl_seconds: 缓存过期时间（秒），默认15分钟
        """
        self._cache: Dict[str, tuple] = {}
        self._ttl = ttl_seconds
    
    def _make_key(self, query: str, provider: str, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            query: 搜索查询
            provider: 搜索提供商
            **kwargs: 其他参数
            
        Returns:
            缓存键
        """
        params = f"{query}:{provider}:{sorted(kwargs.items())}"
        return hashlib.md5(params.encode()).hexdigest()
    
    def get(self, query: str, provider: str, **kwargs) -> Optional[SearchResponse]:
        """
        获取缓存的搜索结果
        
        Args:
            query: 搜索查询
            provider: 搜索提供商
            **kwargs: 其他参数
            
        Returns:
            缓存的搜索响应，不存在或已过期返回 None
        """
        key = self._make_key(query, provider, **kwargs)
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                data.cached = True
                return data
            del self._cache[key]
        return None
    
    def set(self, response: SearchResponse, **kwargs) -> None:
        """
        缓存搜索结果
        
        Args:
            response: 搜索响应
            **kwargs: 其他参数
        """
        key = self._make_key(response.query, response.provider, **kwargs)
        self._cache[key] = (response, time.time())
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()


class SearchProvider(ABC):
    """搜索提供商基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        count: int = 5,
        **kwargs
    ) -> SearchResponse:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            count: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            搜索响应
        """
        pass


class BraveSearchProvider(SearchProvider):
    """Brave Search API 提供商"""
    
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(self, api_key: str):
        """
        初始化 Brave Search
        
        Args:
            api_key: Brave API Key
        """
        self._api_key = api_key
    
    @property
    def name(self) -> str:
        return "brave"
    
    async def search(
        self,
        query: str,
        count: int = 5,
        country: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs
    ) -> SearchResponse:
        """
        执行 Brave 搜索
        
        Args:
            query: 搜索查询
            count: 返回结果数量
            country: 国家代码
            language: 语言代码
            **kwargs: 其他参数
            
        Returns:
            搜索响应
        """
        start_time = time.time()
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._api_key
        }
        
        params = {
            "q": query,
            "count": min(count, 20)
        }
        
        if country:
            params["country"] = country
        if language:
            params["search_lang"] = language
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.BASE_URL,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Brave API error: {response.status} - {error_text}")
                    
                    data = await response.json()
                    
            results = []
            web_results = data.get("web", {}).get("results", [])
            
            for item in web_results[:count]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source="brave"
                ))
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return SearchResponse(
                query=query,
                results=results,
                provider=self.name,
                latency_ms=latency_ms
            )
            
        except asyncio.TimeoutError:
            raise Exception("Brave Search API 请求超时")
        except Exception as e:
            logger.error(f"[WebSearch] Brave 搜索失败: {e}")
            raise


class PerplexitySearchProvider(SearchProvider):
    """Perplexity Search API 提供商"""
    
    BASE_URL = "https://api.perplexity.ai/chat/completions"
    
    def __init__(self, api_key: str, model: str = "sonar"):
        """
        初始化 Perplexity Search
        
        Args:
            api_key: Perplexity API Key
            model: 模型名称
        """
        self._api_key = api_key
        self._model = model
    
    @property
    def name(self) -> str:
        return "perplexity"
    
    async def search(
        self,
        query: str,
        count: int = 5,
        **kwargs
    ) -> SearchResponse:
        """
        执行 Perplexity 搜索
        
        Args:
            query: 搜索查询
            count: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            搜索响应
        """
        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": "Be precise and concise. Provide citations when possible."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Perplexity API error: {response.status} - {error_text}")
                    
                    data = await response.json()
            
            results = []
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            
            for i, citation in enumerate(citations[:count]):
                results.append(SearchResult(
                    title=f"来源 {i + 1}",
                    url=citation,
                    snippet=content[:500] if i == 0 else "",
                    source="perplexity"
                ))
            
            if not results and content:
                results.append(SearchResult(
                    title="AI 回答",
                    url="",
                    snippet=content[:1000],
                    source="perplexity"
                ))
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return SearchResponse(
                query=query,
                results=results,
                provider=self.name,
                latency_ms=latency_ms
            )
            
        except asyncio.TimeoutError:
            raise Exception("Perplexity Search API 请求超时")
        except Exception as e:
            logger.error(f"[WebSearch] Perplexity 搜索失败: {e}")
            raise


class TavilySearchProvider(SearchProvider):
    """Tavily Search API 提供商"""
    
    BASE_URL = "https://api.tavily.com/search"
    
    def __init__(self, api_key: str):
        """
        初始化 Tavily Search
        
        Args:
            api_key: Tavily API Key
        """
        self._api_key = api_key
    
    @property
    def name(self) -> str:
        return "tavily"
    
    async def search(
        self,
        query: str,
        count: int = 5,
        search_depth: str = "basic",
        include_answer: bool = True,
        include_raw_content: bool = False,
        **kwargs
    ) -> SearchResponse:
        """
        执行 Tavily 搜索

        Args:
            query: 搜索查询
            count: 返回结果数量
            search_depth: 搜索深度（basic 或 advanced）
            include_answer: 是否包含 AI 生成的答案
            include_raw_content: 是否包含原始内容
            **kwargs: 其他参数

        Returns:
            搜索响应
        """
        start_time = time.time()

        safe_headers = {"Authorization": "Bearer ***", "Content-Type": "application/json"}
        payload = {
            "query": query,
            "max_results": min(count, 10),
            "search_depth": search_depth,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content
        }

        logger.info(f"[WebSearch-Tavily] ════════════════════════════════════════════")
        logger.info(f"[WebSearch-Tavily] 准备发起 Tavily API 请求")
        logger.info(f"[WebSearch-Tavily] 端点: {self.BASE_URL}")
        logger.info(f"[WebSearch-Tavily] 请求头: {safe_headers}")
        logger.info(f"[WebSearch-Tavily] 搜索查询: {query}")
        logger.info(f"[WebSearch-Tavily] 最大结果数: {count}")
        logger.info(f"[WebSearch-Tavily] 搜索深度: {search_depth}")
        logger.info(f"[WebSearch-Tavily] 包含AI答案: {include_answer}")
        logger.info(f"[WebSearch-Tavily] 包含原始内容: {include_raw_content}")
        logger.info(f"[WebSearch-Tavily] ────────────────────────────────────────────")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.BASE_URL,
                    headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    logger.info(f"[WebSearch-Tavily] 响应状态码: {response.status}")

                    if response.status != 200:
                        logger.error(f"[WebSearch-Tavily] ✗ API 请求失败")
                        logger.error(f"[WebSearch-Tavily]   状态码: {response.status}")
                        logger.error(f"[WebSearch-Tavily]   错误内容: {response_text[:500]}")
                        raise Exception(f"Tavily API error: {response.status} - {response_text[:500]}")

                    data = await response.json()
                    logger.info(f"[WebSearch-Tavily] ✓ API 请求成功")

                    response_time = data.get("response_time", "N/A")
                    logger.info(f"[WebSearch-Tavily]   API响应时间: {response_time}秒")
                    logger.info(f"[WebSearch-Tavily]   请求ID: {data.get('request_id', 'N/A')}")
                    logger.info(f"[WebSearch-Tavily]   消耗积分: {data.get('usage', {}).get('credits', 'N/A')}")

            results = []
            answer = data.get("answer", "")

            if answer and include_answer:
                logger.info(f"[WebSearch-Tavily]   AI答案: {answer[:100]}...")
                results.append(SearchResult(
                    title="AI 回答",
                    url="",
                    snippet=answer,
                    source="tavily"
                ))
            else:
                logger.info(f"[WebSearch-Tavily]   AI答案: 无")

            raw_results = data.get("results", [])
            logger.info(f"[WebSearch-Tavily]   搜索结果数: {len(raw_results)}")

            for i, item in enumerate(raw_results[:count], 1):
                title = item.get("title", "")[:60]
                url = item.get("url", "")[:80]
                score = item.get("score", 0)
                content_preview = item.get("content", "")[:80]
                logger.info(f"[WebSearch-Tavily]   结果{i}:")
                logger.info(f"[WebSearch-Tavily]     标题: {title}")
                logger.info(f"[WebSearch-Tavily]     URL: {url}")
                logger.info(f"[WebSearch-Tavily]     相关度: {score:.4f}")
                logger.info(f"[WebSearch-Tavily]     内容: {content_preview}...")

                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source="tavily"
                ))

            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"[WebSearch-Tavily] 总耗时: {latency_ms}ms")
            logger.info(f"[WebSearch-Tavily] ════════════════════════════════════════════")

            return SearchResponse(
                query=query,
                results=results,
                provider=self.name,
                latency_ms=latency_ms
            )

        except asyncio.TimeoutError:
            logger.error(f"[WebSearch-Tavily] ✗ 请求超时")
            logger.error(f"[WebSearch-Tavily]   超时时间: 30秒")
            logger.error(f"[WebSearch-Tavily] ════════════════════════════════════════════")
            raise Exception("Tavily Search API 请求超时")
        except Exception as e:
            logger.error(f"[WebSearch-Tavily] ✗ 请求异常")
            logger.error(f"[WebSearch-Tavily]   错误类型: {type(e).__name__}")
            logger.error(f"[WebSearch-Tavily]   错误信息: {str(e)}")
            logger.error(f"[WebSearch-Tavily] ════════════════════════════════════════════")
            raise


class WebSearchTool(BaseTool):
    """Web 搜索工具"""

    def __init__(
        self,
        brave_api_key: Optional[str] = None,
        perplexity_api_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
        default_provider: str = "tavily",
        cache_ttl_seconds: int = 900,
        max_results: int = 10
    ):
        """
        初始化 Web 搜索工具

        Args:
            brave_api_key: Brave Search API Key
            perplexity_api_key: Perplexity Search API Key
            tavily_api_key: Tavily Search API Key
            default_provider: 默认搜索提供商
            cache_ttl_seconds: 缓存过期时间
            max_results: 最大返回结果数
        """
        self._providers: Dict[str, SearchProvider] = {}
        self._cache = SearchCache(cache_ttl_seconds)
        self._default_provider = default_provider
        self._max_results = max_results

        if brave_api_key:
            self._providers["brave"] = BraveSearchProvider(brave_api_key)
        if perplexity_api_key:
            self._providers["perplexity"] = PerplexitySearchProvider(perplexity_api_key)
        if tavily_api_key:
            self._providers["tavily"] = TavilySearchProvider(tavily_api_key)
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "使用搜索引擎搜索互联网信息。支持 Tavily、Brave 和 Perplexity 搜索引擎。"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询内容"
                },
                "count": {
                    "type": "integer",
                    "description": "返回结果数量（1-10）",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                },
                "provider": {
                    "type": "string",
                    "description": "搜索引擎提供商",
                    "enum": ["tavily", "brave", "perplexity"],
                    "default": "tavily"
                },
                "search_depth": {
                    "type": "string",
                    "description": "搜索深度（仅 Tavily 支持）",
                    "enum": ["basic", "advanced"],
                    "default": "basic"
                },
                "include_answer": {
                    "type": "boolean",
                    "description": "是否包含 AI 生成的答案（仅 Tavily 支持）",
                    "default": True
                },
                "country": {
                    "type": "string",
                    "description": "国家代码（如 CN、US）"
                },
                "language": {
                    "type": "string",
                    "description": "语言代码（如 zh、en）"
                },
                "freshness": {
                    "type": "string",
                    "description": "时间过滤：day（一天内）、week（一周内）、month（一月内）",
                    "enum": ["day", "week", "month"]
                },
                "use_cache": {
                    "type": "boolean",
                    "description": "是否使用缓存",
                    "default": True
                }
            },
            "required": ["query"]
        }
    
    async def execute(
        self,
        query: str,
        count: int = 5,
        provider: Optional[str] = None,
        search_depth: str = "basic",
        include_answer: bool = True,
        country: Optional[str] = None,
        language: Optional[str] = None,
        freshness: Optional[str] = None,
        use_cache: bool = True,
        tavily_api_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行 Web 搜索

        Args:
            query: 搜索查询
            count: 返回结果数量
            provider: 搜索提供商
            search_depth: 搜索深度（仅 Tavily）
            include_answer: 是否包含 AI 答案（仅 Tavily）
            country: 国家代码
            language: 语言代码
            freshness: 时间过滤
            use_cache: 是否使用缓存
            tavily_api_key: Tavily API Key（可选，如果未在初始化时提供）
            **kwargs: 其他参数

        Returns:
            搜索结果字典
        """
        provider_name = provider or self._default_provider

        if provider_name not in self._providers:
            if provider_name == "tavily" and tavily_api_key:
                self._providers["tavily"] = TavilySearchProvider(tavily_api_key)
                logger.info("[WebSearch] 已通过传入参数获取 Tavily API Key")

        if provider_name not in self._providers:
            available = list(self._providers.keys())
            return {
                "success": False,
                "error": f"搜索提供商 '{provider_name}' 不可用。可用提供商: {available}",
                "results": []
            }
        
        search_provider = self._providers[provider_name]
        count = min(count, self._max_results)
        
        cache_params = {
            "count": count,
            "country": country,
            "language": language,
            "freshness": freshness,
            "search_depth": search_depth,
            "include_answer": include_answer
        }
        
        if use_cache:
            cached = self._cache.get(query, provider_name, **cache_params)
            if cached:
                logger.info(f"[WebSearch] 命中缓存: {query}")
                return self._format_response(cached)
        
        try:
            if provider_name == "tavily":
                response = await search_provider.search(
                    query=query,
                    count=count,
                    search_depth=search_depth,
                    include_answer=include_answer
                )
            else:
                response = await search_provider.search(
                    query=query,
                    count=count,
                    country=country,
                    language=language,
                    freshness=freshness
                )
            
            if use_cache:
                self._cache.set(response, **cache_params)
            
            return self._format_response(response)
            
        except Exception as e:
            logger.error(f"[WebSearch] 搜索失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _format_response(self, response: SearchResponse) -> Dict[str, Any]:
        """
        格式化搜索响应
        
        Args:
            response: 搜索响应
            
        Returns:
            格式化后的字典
        """
        return {
            "success": True,
            "query": response.query,
            "provider": response.provider,
            "cached": response.cached,
            "latency_ms": response.latency_ms,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "source": r.source
                }
                for r in response.results
            ],
            "count": len(response.results)
        }


def get_web_search_tool(
    brave_api_key: Optional[str] = None,
    perplexity_api_key: Optional[str] = None,
    tavily_api_key: Optional[str] = None,
    default_provider: str = "tavily"
) -> ToolDefinition:
    """
    获取 Web 搜索工具定义
    
    Args:
        brave_api_key: Brave Search API Key
        perplexity_api_key: Perplexity Search API Key
        tavily_api_key: Tavily Search API Key
        default_provider: 默认搜索提供商
        
    Returns:
        工具定义实例
    """
    import os
    
    brave_key = brave_api_key or os.environ.get("BRAVE_API_KEY")
    perplexity_key = perplexity_api_key or os.environ.get("PERPLEXITY_API_KEY")
    tavily_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
    
    tool_instance = WebSearchTool(
        brave_api_key=brave_key,
        perplexity_api_key=perplexity_key,
        tavily_api_key=tavily_key,
        default_provider=default_provider
    )
    
    return create_tool(
        name="web_search",
        description="使用搜索引擎搜索互联网信息。支持 Tavily、Brave 和 Perplexity 搜索引擎。",
        parameters=tool_instance.parameters,
        execute=tool_instance.execute
    )
