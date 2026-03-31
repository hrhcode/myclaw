"""
浏览器自动化工具模块

提供基于 Playwright 的浏览器自动化功能
"""
from app.tools.builtin.browser.config import BrowserConfig
from app.tools.builtin.browser.manager import BrowserManager

__all__ = [
    "BrowserConfig",
    "BrowserManager",
]
