"""
页面截图模块

提供页面和元素截图功能
"""
import logging
import base64
from typing import Dict, Any, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def take_screenshot(
    page: Page,
    selector: Optional[str] = None,
    full_page: bool = False
) -> Dict[str, Any]:
    """
    截图
    
    Args:
        page: 页面实例
        selector: 元素选择器（可选）
        full_page: 是否截取全页
        
    Returns:
        截图结果
    """
    try:
        screenshot_options = {
            "type": "png",
            "full_page": full_page
        }
        
        if selector:
            element = await page.query_selector(selector)
            if not element:
                return {
                    "success": False,
                    "message": f"未找到元素: {selector}"
                }
            screenshot_bytes = await element.screenshot(**screenshot_options)
        else:
            screenshot_bytes = await page.screenshot(**screenshot_options)
        
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        
        return {
            "success": True,
            "screenshot": screenshot_base64,
            "format": "png",
            "size": len(screenshot_bytes)
        }
    
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return {
            "success": False,
            "message": f"截图失败: {str(e)}"
        }
