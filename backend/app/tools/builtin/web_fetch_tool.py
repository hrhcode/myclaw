"""
Web 获取工具

获取网页内容并提取可读文本，支持 HTML 转 Markdown
包含 SSRF 防护机制
"""
import asyncio
import hashlib
import ipaddress
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import aiohttp

from app.tools.base import BaseTool, ToolDefinition, create_tool

logger = logging.getLogger(__name__)


@dataclass
class FetchCache:
    """
    简单的内存获取缓存
    """
    _cache: Dict[str, tuple] = field(default_factory=dict)
    _ttl: int = 900
    
    def get(self, url: str, extract_mode: str, max_chars: int) -> Optional[Dict[str, Any]]:
        key = hashlib.md5(f"{url}:{extract_mode}:{max_chars}".encode()).hexdigest()
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
            del self._cache[key]
        return None
    
    def set(self, url: str, extract_mode: str, max_chars: int, data: Dict[str, Any]) -> None:
        key = hashlib.md5(f"{url}:{extract_mode}:{max_chars}".encode()).hexdigest()
        self._cache[key] = (data, time.time())


class SSRFProtector:
    """
    SSRF 防护器
    
    防止服务器端请求伪造攻击
    """
    
    PRIVATE_NETWORKS = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
        ipaddress.ip_network('127.0.0.0/8'),
        ipaddress.ip_network('169.254.0.0/16'),
        ipaddress.ip_network('::1/128'),
        ipaddress.ip_network('fc00::/7'),
        ipaddress.ip_network('fe80::/10'),
    ]
    
    BLOCKED_SCHEMES = {'file', 'ftp', 'sftp', 'ssh', 'telnet', 'gopher', 'dict', 'ldap'}
    
    BLOCKED_HOSTS = {
        'localhost',
        'localhost.localdomain',
        'ip6-localhost',
        'ip6-loopback',
    }
    
    def __init__(
        self,
        allow_private_network: bool = False,
        allowed_hosts: Optional[Set[str]] = None,
        blocked_hosts: Optional[Set[str]] = None
    ):
        """
        初始化 SSRF 防护器
        
        Args:
            allow_private_network: 是否允许私有网络访问
            allowed_hosts: 允许的主机白名单
            blocked_hosts: 禁止的主机黑名单
        """
        self._allow_private_network = allow_private_network
        self._allowed_hosts = allowed_hosts or set()
        self._blocked_hosts = blocked_hosts or set()
    
    def is_safe_url(self, url: str) -> tuple[bool, str]:
        """
        检查 URL 是否安全
        
        Args:
            url: 要检查的 URL
            
        Returns:
            (是否安全, 原因)
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"无效的 URL: {e}"
        
        if parsed.scheme.lower() not in {'http', 'https'}:
            return False, f"不允许的协议: {parsed.scheme}"
        
        hostname = parsed.hostname
        if not hostname:
            return False, "缺少主机名"
        
        hostname_lower = hostname.lower()
        
        if hostname_lower in self._blocked_hosts or hostname_lower in self.BLOCKED_HOSTS:
            return False, f"禁止访问的主机: {hostname}"
        
        if self._allowed_hosts and hostname_lower not in self._allowed_hosts:
            if not any(
                hostname_lower.endswith(f".{allowed}")
                for allowed in self._allowed_hosts
                if allowed.startswith(".")
            ):
                return False, f"主机不在白名单中: {hostname}"
        
        if not self._allow_private_network:
            try:
                if self._is_private_host(hostname):
                    return False, f"禁止访问私有网络地址: {hostname}"
            except Exception as e:
                return False, f"主机名解析失败: {e}"
        
        return True, "URL 安全"
    
    def _is_private_host(self, hostname: str) -> bool:
        """
        检查主机是否为私有网络地址
        
        Args:
            hostname: 主机名
            
        Returns:
            是否为私有网络地址
        """
        try:
            import socket
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            
            for network in self.PRIVATE_NETWORKS:
                if ip in network:
                    return True
            return False
        except socket.gaierror:
            return False
        except Exception:
            return False


class HTMLToMarkdownConverter:
    """
    简单的 HTML 转 Markdown 转换器
    
    不依赖外部库，提供基本的转换功能
    """
    
    TAG_MAPPING = {
        'h1': ('# ', '\n\n'),
        'h2': ('## ', '\n\n'),
        'h3': ('### ', '\n\n'),
        'h4': ('#### ', '\n\n'),
        'h5': ('##### ', '\n\n'),
        'h6': ('###### ', '\n\n'),
        'p': ('', '\n\n'),
        'br': ('', '\n'),
        'hr': ('\n---\n', ''),
        'strong': ('**', '**'),
        'b': ('**', '**'),
        'em': ('*', '*'),
        'i': ('*', '*'),
        'code': ('`', '`'),
        'pre': ('\n```\n', '\n```\n'),
        'blockquote': ('> ', '\n'),
        'li': ('- ', '\n'),
    }
    
    @classmethod
    def convert(cls, html: str, max_chars: int = 50000) -> str:
        """
        将 HTML 转换为 Markdown
        
        Args:
            html: HTML 内容
            max_chars: 最大字符数
            
        Returns:
            Markdown 文本
        """
        text = html
        
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<nav[^>]*>.*?</nav>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<footer[^>]*>.*?</footer>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<header[^>]*>.*?</header>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        text = re.sub(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', r'[\2](\1)', text)
        
        text = re.sub(r'<img[^>]*alt=["\']([^"\']+)["\'][^>]*>', r'![\1]', text)
        text = re.sub(r'<img[^>]*>', '', text)
        
        for tag, (prefix, suffix) in cls.TAG_MAPPING.items():
            text = re.sub(
                rf'<{tag}[^>]*>(.*?)</{tag}>',
                rf'{prefix}\1{suffix}',
                text,
                flags=re.DOTALL | re.IGNORECASE
            )
            text = re.sub(rf'<{tag}[^>]*/?>', prefix, text, flags=re.IGNORECASE)
        
        text = re.sub(r'<div[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<span[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'</span>', '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'<[^>]+>', '', text)
        
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&#39;', "'", text)
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()
        
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n... (内容已截断)"
        
        return text
    
    @classmethod
    def extract_text(cls, html: str, max_chars: int = 50000) -> str:
        """
        从 HTML 中提取纯文本
        
        Args:
            html: HTML 内容
            max_chars: 最大字符数
            
        Returns:
            纯文本
        """
        text = html
        
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        text = re.sub(r'<br[^>]*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</tr>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</td>', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'</th>', ' ', text, flags=re.IGNORECASE)
        
        text = re.sub(r'<[^>]+>', '', text)
        
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&#39;', "'", text)
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()
        
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n... (内容已截断)"
        
        return text


class WebFetchTool(BaseTool):
    """Web 获取工具"""
    
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    def __init__(
        self,
        allow_private_network: bool = False,
        allowed_hosts: Optional[Set[str]] = None,
        max_chars: int = 50000,
        max_response_bytes: int = 2000000,
        timeout_seconds: int = 30,
        max_redirects: int = 5,
        cache_ttl_seconds: int = 900,
        user_agent: Optional[str] = None
    ):
        """
        初始化 Web 获取工具
        
        Args:
            allow_private_network: 是否允许私有网络访问
            allowed_hosts: 允许的主机白名单
            max_chars: 最大字符数
            max_response_bytes: 最大响应字节数
            timeout_seconds: 超时时间（秒）
            max_redirects: 最大重定向次数
            cache_ttl_seconds: 缓存过期时间
            user_agent: User-Agent 字符串
        """
        self._ssrf_protector = SSRFProtector(
            allow_private_network=allow_private_network,
            allowed_hosts=allowed_hosts
        )
        self._max_chars = max_chars
        self._max_response_bytes = max_response_bytes
        self._timeout = timeout_seconds
        self._max_redirects = max_redirects
        self._cache = FetchCache(_ttl=cache_ttl_seconds)
        self._user_agent = user_agent or self.DEFAULT_USER_AGENT
    
    @property
    def name(self) -> str:
        return "web_fetch"
    
    @property
    def description(self) -> str:
        return "获取网页内容并提取可读文本。支持 HTML 转 Markdown 或纯文本模式。"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要获取的网页 URL（仅支持 HTTP/HTTPS）"
                },
                "extract_mode": {
                    "type": "string",
                    "description": "提取模式",
                    "enum": ["markdown", "text"],
                    "default": "markdown"
                },
                "max_chars": {
                    "type": "integer",
                    "description": "最大返回字符数",
                    "default": 50000
                },
                "use_cache": {
                    "type": "boolean",
                    "description": "是否使用缓存",
                    "default": True
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒）",
                    "default": 30
                }
            },
            "required": ["url"]
        }
    
    async def execute(
        self,
        url: str,
        extract_mode: str = "markdown",
        max_chars: Optional[int] = None,
        use_cache: bool = True,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行 Web 获取
        
        Args:
            url: 要获取的 URL
            extract_mode: 提取模式（markdown 或 text）
            max_chars: 最大字符数
            use_cache: 是否使用缓存
            timeout: 超时时间
            **kwargs: 其他参数
            
        Returns:
            获取结果字典
        """
        max_chars = min(max_chars or self._max_chars, self._max_chars)
        timeout = timeout or self._timeout
        
        is_safe, reason = self._ssrf_protector.is_safe_url(url)
        if not is_safe:
            return {
                "success": False,
                "error": f"URL 安全检查失败: {reason}",
                "url": url
            }
        
        if use_cache:
            cached = self._cache.get(url, extract_mode, max_chars)
            if cached:
                cached["cached"] = True
                return cached
        
        try:
            html, final_url, content_type = await self._fetch_url(url, timeout)
            
            if not html:
                return {
                    "success": False,
                    "error": "获取到的内容为空",
                    "url": url
                }
            
            if extract_mode == "markdown":
                content = HTMLToMarkdownConverter.convert(html, max_chars)
            else:
                content = HTMLToMarkdownConverter.extract_text(html, max_chars)
            
            result = {
                "success": True,
                "url": url,
                "final_url": final_url,
                "content": content,
                "content_type": content_type,
                "content_length": len(content),
                "extract_mode": extract_mode,
                "cached": False
            }
            
            if use_cache:
                self._cache.set(url, extract_mode, max_chars, result)
            
            return result
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"请求超时（{timeout}秒）",
                "url": url
            }
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": f"HTTP 请求失败: {e}",
                "url": url
            }
        except Exception as e:
            logger.error(f"[WebFetch] 获取失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    async def _fetch_url(
        self,
        url: str,
        timeout: int
    ) -> tuple[Optional[str], str, str]:
        """
        获取 URL 内容
        
        Args:
            url: URL
            timeout: 超时时间
            
        Returns:
            (HTML内容, 最终URL, 内容类型)
        """
        headers = {
            "User-Agent": self._user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
        }
        
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=2,
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            async with session.get(
                url,
                allow_redirects=True,
                max_redirects=self._max_redirects
            ) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                content_type = response.headers.get("Content-Type", "text/html")
                
                if "text/html" not in content_type and "text/plain" not in content_type:
                    if "application/json" in content_type:
                        data = await response.json()
                        return str(data), str(response.url), content_type
                    return None, str(response.url), content_type
                
                raw_bytes = await response.content.read(self._max_response_bytes + 1)
                
                if len(raw_bytes) > self._max_response_bytes:
                    logger.warning(f"[WebFetch] 响应过大，已截断: {url}")
                    raw_bytes = raw_bytes[:self._max_response_bytes]
                
                encoding = response.charset or "utf-8"
                try:
                    html = raw_bytes.decode(encoding)
                except UnicodeDecodeError:
                    html = raw_bytes.decode("utf-8", errors="ignore")
                
                return html, str(response.url), content_type


def get_web_fetch_tool(
    allow_private_network: bool = False,
    allowed_hosts: Optional[Set[str]] = None,
    max_chars: int = 50000
) -> ToolDefinition:
    """
    获取 Web 获取工具定义
    
    Args:
        allow_private_network: 是否允许私有网络访问
        allowed_hosts: 允许的主机白名单
        max_chars: 最大字符数
        
    Returns:
        工具定义实例
    """
    tool_instance = WebFetchTool(
        allow_private_network=allow_private_network,
        allowed_hosts=allowed_hosts,
        max_chars=max_chars
    )
    
    return create_tool(
        name="web_fetch",
        description="获取网页内容并提取可读文本。支持 HTML 转 Markdown 或纯文本模式。",
        parameters=tool_instance.parameters,
        execute=tool_instance.execute
    )
