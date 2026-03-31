"""
浏览器会话管理模块

管理浏览器会话的生命周期
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from playwright.async_api import Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class BrowserSession:
    """
    浏览器会话
    
    管理单个浏览器会话的生命周期
    """
    
    def __init__(self, session_id: str):
        """
        初始化浏览器会话
        
        Args:
            session_id: 会话 ID
        """
        self.session_id = session_id
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.created_at = datetime.now()
        self.last_used_at = datetime.now()
        self._is_active = False
    
    async def initialize(
        self,
        browser: Browser,
        context: BrowserContext,
        page: Page
    ) -> None:
        """
        初始化会话
        
        Args:
            browser: 浏览器实例
            context: 浏览器上下文
            page: 页面实例
        """
        self.browser = browser
        self.context = context
        self.page = page
        self._is_active = True
        self.last_used_at = datetime.now()
        logger.info(f"浏览器会话 {self.session_id} 已初始化")
    
    async def close(self) -> None:
        """
        关闭会话
        """
        if self.page:
            await self.page.close()
            self.page = None
        
        if self.context:
            await self.context.close()
            self.context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        self._is_active = False
        logger.info(f"浏览器会话 {self.session_id} 已关闭")
    
    def update_last_used(self) -> None:
        """
        更新最后使用时间
        """
        self.last_used_at = datetime.now()
    
    def is_idle(self, timeout_ms: int) -> bool:
        """
        检查会话是否空闲
        
        Args:
            timeout_ms: 超时时间（毫秒）
            
        Returns:
            是否空闲
        """
        idle_time = datetime.now() - self.last_used_at
        return idle_time > timedelta(milliseconds=timeout_ms)
    
    @property
    def is_active(self) -> bool:
        """
        会话是否活跃
        
        Returns:
            是否活跃
        """
        return self._is_active and self.browser is not None
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取会话状态
        
        Returns:
            状态字典
        """
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat(),
            "idle_seconds": (datetime.now() - self.last_used_at).total_seconds()
        }
