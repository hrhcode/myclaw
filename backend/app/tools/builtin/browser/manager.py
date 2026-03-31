"""
浏览器管理器模块

负责浏览器实例的启动、停止和配置管理
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, BrowserType

from app.tools.builtin.browser.config import BrowserConfig
from app.tools.builtin.browser.session import BrowserSession

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    浏览器管理器
    
    负责浏览器实例的启动、停止和配置管理
    """
    
    _instance_count = 0
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        """
        初始化浏览器管理器
        
        Args:
            config: 浏览器配置
        """
        self._config = config or BrowserConfig()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._session: Optional[BrowserSession] = None
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        viewport: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        启动浏览器
        
        Args:
            browser_type: 浏览器类型（chromium、firefox、webkit）
            headless: 是否无头模式
            viewport: 视口大小
            
        Returns:
            启动结果
        """
        async with self._lock:
            if self._browser:
                logger.warning("浏览器已在运行")
                return {
                    "success": False,
                    "message": "浏览器已在运行"
                }
            
            if BrowserManager._instance_count >= self._config.max_instances:
                logger.warning(f"已达到最大浏览器实例数: {self._config.max_instances}")
                return {
                    "success": False,
                    "message": f"已达到最大浏览器实例数: {self._config.max_instances}"
                }
            
            try:
                self._playwright = await async_playwright().start()
                
                # 根据配置选择启动方式
                if self._config.use_system_browser:
                    return await self._start_system_browser(browser_type, headless, viewport)
                else:
                    return await self._start_playwright_browser(browser_type, headless, viewport)
            
            except Exception as e:
                # 详细的错误日志记录
                logger.error(f"[浏览器启动] ══════════════════════════════════════")
                logger.error(f"[浏览器启动] 错误类型: {type(e).__name__}")
                logger.error(f"[浏览器启动] 错误信息: {str(e)}")
                logger.error(f"[浏览器启动] 浏览器类型: {browser_type}")
                logger.error(f"[浏览器启动] 无头模式: {headless}")
                logger.error(f"[浏览器启动] 使用系统浏览器: {self._config.use_system_browser}")
                logger.error(f"[浏览器启动] ══════════════════════════════════════")
                
                # 详细的错误消息
                error_type = type(e).__name__
                error_msg = str(e)
                
                # 根据错误类型提供更友好的错误消息
                if "Executable doesn't exist" in error_msg:
                    friendly_msg = "浏览器可执行文件不存在，请检查系统是否已安装浏览器"
                elif "NotImplementedError" in error_msg:
                    friendly_msg = "系统不支持子进程，请检查 Windows 事件循环策略设置"
                elif "TimeoutError" in error_msg:
                    friendly_msg = f"浏览器启动超时（{self._config.timeout_ms}ms）"
                elif "Permission denied" in error_msg:
                    friendly_msg = "浏览器启动权限被拒绝，请检查系统权限"
                else:
                    friendly_msg = f"启动浏览器失败: {error_msg}"
                
                logger.error(f"[浏览器启动] 友好错误消息: {friendly_msg}")
                
                await self._cleanup()
                return {
                    "success": False,
                    "message": friendly_msg,
                    "error_type": error_type,
                    "error_detail": error_msg,
                    "browser_type": browser_type,
                    "headless": headless,
                    "use_system_browser": self._config.use_system_browser
                }
    
    async def stop(self) -> Dict[str, Any]:
        """
        停止浏览器
        
        Returns:
            停止结果
        """
        async with self._lock:
            if not self._browser:
                logger.warning("浏览器未运行")
                return {
                    "success": False,
                    "message": "浏览器未运行"
                }
            
            try:
                if self._cleanup_task:
                    self._cleanup_task.cancel()
                    try:
                        await self._cleanup_task
                    except asyncio.CancelledError:
                        pass
                    self._cleanup_task = None
                
                if self._session:
                    await self._session.close()
                    self._session = None
                
                await self._cleanup()
                
                BrowserManager._instance_count = max(0, BrowserManager._instance_count - 1)
                
                logger.info("浏览器已停止")
                
                return {
                    "success": True,
                    "message": "浏览器已停止"
                }
            
            except Exception as e:
                # 详细的错误日志记录
                logger.error(f"[浏览器停止] ══════════════════════════════════")
                logger.error(f"[浏览器停止] 错误类型: {type(e).__name__}")
                logger.error(f"[浏览器停止] 错误信息: {str(e)}")
                logger.error(f"[浏览器停止] ════════════════════════════════════")
                
                # 详细的错误消息
                error_type = type(e).__name__
                error_msg = str(e)
                friendly_msg = f"停止浏览器失败: {error_msg}"
                
                logger.error(f"[浏览器停止] 友好错误消息: {friendly_msg}")
                
                return {
                    "success": False,
                    "message": friendly_msg,
                    "error_type": error_type,
                    "error_detail": error_msg
                }
    
    async def navigate(
        self,
        url: str,
        wait_until: str = "load"
    ) -> Dict[str, Any]:
        """
        导航到 URL
        
        Args:
            url: 目标 URL
            wait_until: 等待条件（load、domcontentloaded、networkidle）
            
        Returns:
            导航结果
        """
        if not self._page:
            return {
                "success": False,
                "message": "浏览器未启动"
            }
        
        try:
            await self._page.goto(url, wait_until=wait_until)
            
            self._session.update_last_used()
            
            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title()
            }
        
        except Exception as e:
            # 详细的错误日志记录
            logger.error(f"[浏览器导航] ════════════════════════════════════")
            logger.error(f"[浏览器导航] 错误类型: {type(e).__name__}")
            logger.error(f"[浏览器导航] 错误信息: {str(e)}")
            logger.error(f"[浏览器导航] 目标 URL: {url}")
            logger.error(f"[浏览器导航] 等待条件: {wait_until}")
            logger.error(f"[浏览器导航] ══════════════════════════════════════")
            
            # 详细的错误消息
            error_type = type(e).__name__
            error_msg = str(e)
            friendly_msg = f"导航到 URL 失败: {error_msg}"
            
            logger.error(f"[浏览器导航] 友好错误消息: {friendly_msg}")
            
            return {
                "success": False,
                "message": friendly_msg,
                "error_type": error_type,
                "error_detail": error_msg,
                "url": url,
                "wait_until": wait_until
            }
    
    async def _cleanup(self) -> None:
        """
        清理资源
        """
        if self._page:
            try:
                await self._page.close()
            except:
                pass
            self._page = None
        
        if self._context:
            try:
                await self._context.close()
            except:
                pass
            self._context = None
        
        if self._browser:
            try:
                await self._browser.close()
            except:
                pass
            self._browser = None
        
        if self._playwright:
            try:
                await self._playwright.stop()
            except:
                pass
            self._playwright = None
    
    async def _cleanup_idle_session(self) -> None:
        """
        清理空闲会话
        
        定期检查会话是否空闲，如果空闲则自动清理
        """
        while True:
            try:
                await asyncio.sleep(60)
                
                if self._session and self._session.is_idle(self._config.idle_timeout_ms):
                    logger.info(f"检测到空闲会话，自动清理: {self._session.session_id}")
                    await self.stop()
                    break
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理空闲会话时出错: {e}")
    
    def _get_browser_type(self, browser_type: str) -> BrowserType:
        """
        获取浏览器类型对象
        
        Args:
            browser_type: 浏览器类型名称
            
        Returns:
            浏览器类型对象
        """
        if browser_type == "chromium":
            return self._playwright.chromium
        elif browser_type == "firefox":
            return self._playwright.firefox
        elif browser_type == "webkit":
            return self._playwright.webkit
        else:
            return self._playwright.chromium
    
    async def _start_system_browser(
        self,
        browser_type: str,
        headless: bool,
        viewport: Optional[Dict[str, int]]
    ) -> Dict[str, Any]:
        """
        启动系统浏览器
        
        Args:
            browser_type: 浏览器类型
            headless: 是否无头模式
            viewport: 视口大小
            
        Returns:
            启动结果
        """
        try:
            # 获取浏览器 channel
            channel = self._config.get_launch_channel(browser_type)
            
            # 准备启动选项
            launch_options = {
                "headless": headless,
                "channel": channel,
            }
            
            # 根据浏览器类型选择 Playwright 浏览器对象
            if browser_type.lower() in ["firefox"]:
                browser_type_obj = self._playwright.firefox
            else:
                browser_type_obj = self._playwright.chromium
            
            # 启动系统浏览器
            self._browser = await browser_type_obj.launch(**launch_options)
            
            # 创建上下文和页面
            self._context = await self._browser.new_context(
                viewport={
                    "width": viewport.get("width", self._config.viewport_width) if viewport else self._config.viewport_width,
                    "height": viewport.get("height", self._config.viewport_height) if viewport else self._config.viewport_height
                }
            )
            
            self._page = await self._context.new_page()
            
            # 初始化会话
            self._session = BrowserSession("default")
            await self._session.initialize(self._browser, self._context, self._page)
            
            BrowserManager._instance_count += 1
            
            # 启动空闲清理任务
            self._cleanup_task = asyncio.create_task(self._cleanup_idle_session())
            
            logger.info(f"系统浏览器已启动: {browser_type}, channel={channel}, headless={headless}")
            
            return {
                "success": True,
                "browser_type": browser_type,
                "headless": headless,
                "viewport": viewport or {
                    "width": self._config.viewport_width,
                    "height": self._config.viewport_height
                },
                "browser_source": "system",
                "channel": channel
            }
        
        except Exception as e:
            logger.error(f"启动系统浏览器失败: {e}")
            await self._cleanup()
            return {
                "success": False,
                "message": f"启动系统浏览器失败: {str(e)}"
            }
    
    async def _start_playwright_browser(
        self,
        browser_type: str,
        headless: bool,
        viewport: Optional[Dict[str, int]]
    ) -> Dict[str, Any]:
        """
        启动 Playwright 下载的浏览器
        
        Args:
            browser_type: 浏览器类型
            headless: 是否无头模式
            viewport: 视口大小
            
        Returns:
            启动结果
        """
        try:
            browser_type_obj = self._get_browser_type(browser_type)
            
            launch_options = {
                "headless": headless,
            }
            
            self._browser = await browser_type_obj.launch(**launch_options)
            
            self._context = await self._browser.new_context(
                viewport={
                    "width": viewport.get("width", self._config.viewport_width) if viewport else self._config.viewport_width,
                    "height": viewport.get("height", self._config.viewport_height) if viewport else self._config.viewport_height
                }
            )
            
            self._page = await self._context.new_page()
            
            self._session = BrowserSession("default")
            await self._session.initialize(self._browser, self._context, self._page)
            
            BrowserManager._instance_count += 1
            
            self._cleanup_task = asyncio.create_task(self._cleanup_idle_session())
            
            logger.info(f"Playwright 浏览器已启动: {browser_type}, headless={headless}")
            
            return {
                "success": True,
                "browser_type": browser_type,
                "headless": headless,
                "viewport": viewport or {
                    "width": self._config.viewport_width,
                    "height": self._config.viewport_height
                },
                "browser_source": "playwright"
            }
        
        except Exception as e:
            logger.error(f"启动 Playwright 浏览器失败: {e}")
            await self._cleanup()
            return {
                "success": False,
                "message": f"启动浏览器失败: {str(e)}"
            }
    
    @property
    def is_running(self) -> bool:
        """
        浏览器是否正在运行
        
        Returns:
            是否运行中
        """
        return self._browser is not None
    
    @property
    def page(self) -> Optional[Page]:
        """
        获取当前页面
        
        Returns:
            页面实例
        """
        return self._page
    
    @property
    def session(self) -> Optional[BrowserSession]:
        """
        获取当前会话
        
        Returns:
            会话实例
        """
        return self._session
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取浏览器状态
        
        Returns:
            状态字典
        """
        return {
            "is_running": self.is_running,
            "session": self._session.get_status() if self._session else None
        }
