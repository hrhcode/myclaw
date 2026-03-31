"""
浏览器配置模块

定义浏览器配置和默认值
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class BrowserConfig:
    """
    浏览器配置
    
    Attributes:
        enabled: 是否启用浏览器工具
        default_type: 默认浏览器类型（chromium、firefox、webkit）
        headless: 是否无头模式
        viewport_width: 默认视口宽度
        viewport_height: 默认视口高度
        timeout_ms: 默认超时时间（毫秒）
        ssrf_allow_private: 是否允许访问内网地址
        ssrf_whitelist: URL 白名单（逗号分隔）
        max_instances: 最大浏览器实例数
        idle_timeout_ms: 空闲超时时间（毫秒）
    """
    enabled: bool = False
    default_type: str = "chromium"
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 720
    timeout_ms: int = 30000
    ssrf_allow_private: bool = False
    ssrf_whitelist: str = ""
    max_instances: int = 1
    idle_timeout_ms: int = 300000  # 5分钟
    
    # 新增：使用系统浏览器配置
    use_system_browser: bool = True  # 默认使用系统浏览器
    system_browser_channel: str = "chrome"  # 默认使用 Chrome
    
    def get_whitelist(self) -> List[str]:
        """
        获取白名单列表
        
        Returns:
            白名单 URL 列表
        """
        if not self.ssrf_whitelist:
            return []
        return [url.strip() for url in self.ssrf_whitelist.split(",") if url.strip()]
    
    def validate_browser_type(self, browser_type: str) -> bool:
        """
        验证浏览器类型
        
        Args:
            browser_type: 浏览器类型
            
        Returns:
            是否有效
        """
        return browser_type in ["chromium", "firefox", "webkit", "chrome", "msedge"]
    
    def get_timeout_ms(self) -> int:
        """
        获取超时时间
        
        Returns:
            超时时间（毫秒）
        """
        return max(1000, self.timeout_ms)
    
    def get_launch_channel(self, browser_type: str) -> str:
        """
        获取浏览器启动 channel
        
        Args:
            browser_type: 浏览器类型
            
        Returns:
            channel 名称
        """
        # 浏览器类型到 channel 的映射
        channel_map = {
            "chromium": "chrome",
            "chrome": "chrome",
            "msedge": "msedge",
            "firefox": "firefox"
        }
        return channel_map.get(browser_type.lower(), "chrome")
