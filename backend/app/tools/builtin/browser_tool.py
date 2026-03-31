"""
浏览器工具主模块

定义所有浏览器自动化工具
"""
import logging
from typing import Dict, Any, Optional
from app.tools.base import ToolDefinition, create_tool
from app.tools.builtin.browser.manager import BrowserManager
from app.tools.builtin.browser.snapshot import get_aria_snapshot
from app.tools.builtin.browser.screenshot import take_screenshot
from app.tools.builtin.browser.actions import (
    click_element,
    type_text,
    hover_element,
    wait_for
)
from app.tools.builtin.browser.ssrf_guard import SSRFGuard
from app.tools.builtin.browser.config import BrowserConfig

logger = logging.getLogger(__name__)

# 全局浏览器管理器实例（用于保持浏览器会话）
_global_browser_manager: Optional[BrowserManager] = None
_global_browser_config: Optional[BrowserConfig] = None


def _get_or_create_manager(config: Dict[str, Any], force_new: bool = False) -> BrowserManager:
    """
    获取或创建浏览器管理器
    
    如果全局管理器已存在且浏览器仍在运行，则返回全局管理器
    否则创建新的管理器
    
    Args:
        config: 配置字典
        force_new: 是否强制创建新的管理器
        
    Returns:
        BrowserManager 实例
    """
    global _global_browser_manager, _global_browser_config
    
    # 从配置字典创建 BrowserConfig
    new_config = BrowserConfig(
        default_type=config.get("default_type", "chromium"),
        headless=config.get("headless", False),
        viewport_width=config.get("viewport_width", 1280),
        viewport_height=config.get("viewport_height", 720),
        timeout_ms=config.get("timeout_ms", 30000),
        ssrf_allow_private=config.get("ssrf_allow_private", False),
        ssrf_whitelist=config.get("ssrf_whitelist", ""),
        max_instances=config.get("max_instances", 1),
        idle_timeout_ms=config.get("idle_timeout_ms", 300000),
        use_system_browser=config.get("use_system_browser", True),
        system_browser_channel=config.get("system_browser_channel", "chrome")
    )
    
    # 检查是否需要创建新的管理器
    if _global_browser_manager is not None:
        # 检查浏览器是否真的在运行
        try:
            is_running = False
            if _global_browser_manager.page is not None:
                # 检查 page 是否仍然有效
                try:
                    # 尝试获取 URL 来验证 page 是否仍然有效
                    _ = _global_browser_manager.page.url
                    is_running = True
                except Exception:
                    # page 已经关闭或无效
                    is_running = False
            
            if is_running and not force_new:
                logger.info("[浏览器工具] 复用已存在的浏览器管理器")
                return _global_browser_manager
            else:
                logger.info("[浏览器工具] 浏览器已关闭或不存在，清理旧管理器")
                _global_browser_manager = None
        except Exception as e:
            logger.warning(f"[浏览器工具] 检查浏览器状态时出错: {e}，创建新的管理器")
            _global_browser_manager = None
    
    # 创建新的管理器
    logger.info("[浏览器工具] 创建新的浏览器管理器")
    _global_browser_manager = BrowserManager(new_config)
    _global_browser_config = new_config
    
    return _global_browser_manager


def _create_ssrf_guard(config: Dict[str, Any]) -> SSRFGuard:
    """
    创建 SSRF 防护
    
    Args:
        config: 配置字典
        
    Returns:
        SSRFGuard 实例
    """
    return SSRFGuard(
        allow_private=config.get("ssrf_allow_private", False),
        whitelist=config.get("ssrf_whitelist", "").split(",") if config.get("ssrf_whitelist") else []
    )


async def browser_start(
    browser_type: Optional[str] = None,
    headless: Optional[bool] = None,
    viewport: Optional[Dict[str, int]] = None,
    _config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    启动浏览器

    Args:
        browser_type: 浏览器类型（chromium、firefox、webkit），如果为 None 则使用配置中的默认值
        headless: 是否无头模式，如果为 None 则使用配置中的默认值
        viewport: 视口大小，如果为 None 则使用配置中的默认值
        _config: 配置字典（内部使用）

    Returns:
        启动结果
    """
    if not _config:
        logger.warning("[浏览器配置] 未提供配置，使用默认配置")
        _config = {}

    # 强制创建新的管理器，确保能重新启动已关闭的浏览器
    manager = _get_or_create_manager(_config, force_new=True)

    # 如果参数为 None，使用配置中的默认值
    if browser_type is None:
        browser_type = _config.get("default_type", "chromium")
    if headless is None:
        headless = _config.get("headless", False)
    if viewport is None:
        viewport = {
            "width": _config.get("viewport_width", 1280),
            "height": _config.get("viewport_height", 720)
        }

    return await manager.start(
        browser_type=browser_type,
        headless=headless,
        viewport=viewport
    )


async def browser_stop(
    _config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    停止浏览器

    Args:
        _config: 配置字典（内部使用）

    Returns:
        停止结果
    """
    global _global_browser_manager
    
    if _global_browser_manager is None:
        return {
            "success": False,
            "message": "浏览器未启动"
        }

    result = await _global_browser_manager.stop()
    _global_browser_manager = None
    return result


async def browser_navigate(
    url: str,
    wait_until: str = "load",
    _config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    导航到 URL

    Args:
        url: 目标 URL
        wait_until: 等待条件（load、domcontentloaded、networkidle）
        _config: 配置字典（内部使用）

    Returns:
        导航结果
    """
    if not _config:
        _config = {}

    manager = _get_or_create_manager(_config)
    
    if manager.page is None:
        logger.warning("[浏览器工具] 浏览器未启动，无法导航")
        return {
            "success": False,
            "message": "浏览器未启动"
        }
    
    ssrf_guard = _create_ssrf_guard(_config)
    is_safe, error = ssrf_guard.validate_url(url)

    if not is_safe:
        logger.warning(f"SSRF 防护阻止访问: {url}, 原因: {error}")
        return {
            "success": False,
            "message": f"SSRF 防护阻止访问: {error}"
        }

    return await manager.navigate(url, wait_until)


async def browser_snapshot(
    format: str = "aria",
    _config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    获取页面快照

    Args:
        format: 快照格式（aria、compact）
        _config: 配置字典（内部使用）

    Returns:
        快照结果
    """
    if not _config:
        _config = {}

    manager = _get_or_create_manager(_config)

    if manager.page is None:
        return {
            "success": False,
            "message": "浏览器未启动"
        }

    return await get_aria_snapshot(manager.page, format)


async def browser_screenshot(
    selector: Optional[str] = None,
    full_page: bool = False,
    _config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    截图

    Args:
        selector: 元素选择器（可选）
        full_page: 是否截取全页
        _config: 配置字典（内部使用）

    Returns:
        截图结果
    """
    if not _config:
        _config = {}

    manager = _get_or_create_manager(_config)

    if manager.page is None:
        return {
            "success": False,
            "message": "浏览器未启动"
        }

    return await take_screenshot(manager.page, selector, full_page)


async def browser_click(
    selector: str,
    text: Optional[str] = None,
    _config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    点击元素

    Args:
        selector: 元素选择器
        text: 元素文本（可选）
        _config: 配置字典（内部使用）

    Returns:
        点击结果
    """
    if not _config:
        _config = {}

    manager = _get_or_create_manager(_config)

    if manager.page is None:
        return {
            "success": False,
            "message": "浏览器未启动"
        }

    result = await click_element(manager.page, selector, text)

    if result.get("success"):
        manager.session.update_last_used()

    return result


async def browser_type(
    selector: str,
    text: str,
    clear: bool = True,
    _config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    输入文本

    Args:
        selector: 元素选择器
        text: 输入的文本
        clear: 是否先清空
        _config: 配置字典（内部使用）

    Returns:
        输入结果
    """
    if not _config:
        _config = {}

    manager = _get_or_create_manager(_config)

    if manager.page is None:
        return {
            "success": False,
            "message": "浏览器未启动"
        }

    result = await type_text(manager.page, selector, text, clear)

    if result.get("success"):
        manager.session.update_last_used()

    return result


async def browser_hover(
    selector: str,
    _config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    悬停元素

    Args:
        selector: 元素选择器
        _config: 配置字典（内部使用）

    Returns:
        悬停结果
    """
    if not _config:
        _config = {}

    manager = _get_or_create_manager(_config)

    if manager.page is None:
        return {
            "success": False,
            "message": "浏览器未启动"
        }

    result = await hover_element(manager.page, selector)

    if result.get("success"):
        manager.session.update_last_used()

    return result


async def browser_wait(
    selector: Optional[str] = None,
    text: Optional[str] = None,
    timeout: Optional[int] = None,
    _config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    等待条件

    Args:
        selector: 元素选择器（可选）
        text: 等待的文本（可选）
        timeout: 超时时间（毫秒），如果为 None 则使用配置中的默认值
        _config: 配置字典（内部使用）

    Returns:
        等待结果
    """
    if not _config:
        _config = {}

    manager = _get_or_create_manager(_config)

    if manager.page is None:
        return {
            "success": False,
            "message": "浏览器未启动"
        }

    # 如果 timeout 为 None，使用配置中的默认值
    if timeout is None:
        timeout = _config.get("timeout_ms", 30000)

    result = await wait_for(manager.page, selector, text, timeout)

    if result.get("success"):
        manager.session.update_last_used()

    return result


def get_browser_tools() -> list[ToolDefinition]:
    """
    获取所有浏览器工具

    Returns:
        浏览器工具列表（默认禁用，需要用户明确启用）
    """
    tools = [
        create_tool(
            name="browser_start",
            description="启动浏览器实例（使用配置中的默认值）",
            parameters={
                "type": "object",
                "properties": {
                    "browser_type": {
                        "type": "string",
                        "enum": ["chromium", "firefox", "webkit"],
                        "description": "浏览器类型（可选，不指定则使用配置中的默认值）"
                    },
                    "headless": {
                        "type": "boolean",
                        "description": "是否无头模式（可选，不指定则使用配置中的默认值）"
                    },
                    "viewport": {
                        "type": "object",
                        "properties": {
                            "width": {"type": "number"},
                            "height": {"type": "number"}
                        },
                        "description": "视口大小（可选，不指定则使用配置中的默认值）"
                    }
                },
                "required": []
            },
            execute=browser_start,
            enabled=True
        ),
        create_tool(
            name="browser_stop",
            description="停止浏览器实例",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            execute=browser_stop,
            enabled=True
        ),
        create_tool(
            name="browser_navigate",
            description="导航到指定 URL",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "目标 URL"
                    },
                    "wait_until": {
                        "type": "string",
                        "enum": ["load", "domcontentloaded", "networkidle"],
                        "description": "等待条件"
                    }
                },
                "required": ["url"]
            },
            execute=browser_navigate,
            enabled=True
        ),
        create_tool(
            name="browser_snapshot",
            description="获取页面快照（可访问性树）",
            parameters={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["aria", "compact"],
                        "description": "快照格式"
                    }
                },
                "required": []
            },
            execute=browser_snapshot,
            enabled=True
        ),
        create_tool(
            name="browser_screenshot",
            description="截图页面或元素",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "元素选择器（可选，不指定则截取全页）"
                    },
                    "full_page": {
                        "type": "boolean",
                        "description": "是否截取全页",
                        "default": False
                    }
                },
                "required": []
            },
            execute=browser_screenshot,
            enabled=True
        ),
        create_tool(
            name="browser_click",
            description="点击页面元素",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "元素选择器"
                    },
                    "text": {
                        "type": "string",
                        "description": "元素文本（可选）"
                    }
                },
                "required": ["selector"]
            },
            execute=browser_click,
            enabled=True
        ),
        create_tool(
            name="browser_type",
            description="在元素中输入文本",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "元素选择器"
                    },
                    "text": {
                        "type": "string",
                        "description": "输入的文本"
                    },
                    "clear": {
                        "type": "boolean",
                        "description": "是否先清空输入框",
                        "default": True
                    }
                },
                "required": ["selector", "text"]
            },
            execute=browser_type,
            enabled=True
        ),
        create_tool(
            name="browser_hover",
            description="悬停页面元素",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "元素选择器"
                    }
                },
                "required": ["selector"]
            },
            execute=browser_hover,
            enabled=True
        ),
        create_tool(
            name="browser_wait",
            description="等待条件满足（使用配置中的默认超时时间）",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "元素选择器"
                    },
                    "text": {
                        "type": "string",
                        "description": "等待的文本"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "超时时间（毫秒，可选，不指定则使用配置中的默认值）"
                    }
                },
                "required": []
            },
            execute=browser_wait,
            enabled=True
        )
    ]

    return tools
