"""
SSRF 防护模块

防止服务器端请求伪造攻击
"""
import logging
import ipaddress
from urllib.parse import urlparse
from typing import List, Optional

logger = logging.getLogger(__name__)


class SSRFGuard:
    """
    SSRF 防护
    
    防止访问内网地址和恶意 URL
    """
    
    def __init__(
        self,
        allow_private: bool = False,
        whitelist: Optional[List[str]] = None
    ):
        """
        初始化 SSRF 防护
        
        Args:
            allow_private: 是否允许访问内网地址
            whitelist: URL 白名单
        """
        self.allow_private = allow_private
        self.whitelist = whitelist or []
    
    def validate_url(self, url: str) -> tuple[bool, Optional[str]]:
        """
        验证 URL 是否安全
        
        Args:
            url: 要验证的 URL
            
        Returns:
            (是否安全, 错误信息)
        """
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme or parsed.scheme not in ["http", "https"]:
                return False, f"不支持的协议: {parsed.scheme}"
            
            if not parsed.netloc:
                return False, "无效的 URL"
            
            hostname = parsed.hostname
            if not hostname:
                return False, "无效的主机名"
            
            if self._is_in_whitelist(url):
                return True, None
            
            if not self.allow_private and self._is_private_address(hostname):
                return False, f"不允许访问内网地址: {hostname}"
            
            return True, None
        
        except Exception as e:
            logger.error(f"验证 URL 失败: {e}")
            return False, f"验证 URL 失败: {str(e)}"
    
    def _is_private_address(self, hostname: str) -> bool:
        """
        检查是否为内网地址
        
        Args:
            hostname: 主机名
            
        Returns:
            是否为内网地址
        """
        try:
            ip = ipaddress.ip_address(hostname)
            
            if ip.is_private:
                return True
            
            if ip.is_loopback:
                return True
            
            if ip.is_link_local:
                return True
            
            return False
        
        except ValueError:
            pass
        
        private_domains = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1"
        ]
        
        return hostname.lower() in private_domains
    
    def _is_in_whitelist(self, url: str) -> bool:
        """
        检查 URL 是否在白名单中
        
        Args:
            url: URL
            
        Returns:
            是否在白名单中
        """
        if not self.whitelist:
            return False
        
        for whitelist_url in self.whitelist:
            if url.startswith(whitelist_url):
                return True
        
        return False
