"""
浏览器操作模块

提供元素交互和等待功能
"""
import logging
from typing import Dict, Any, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def click_element(
    page: Page,
    selector: str,
    text: Optional[str] = None
) -> Dict[str, Any]:
    """
    点击元素
    
    Args:
        page: 页面实例
        selector: 元素选择器
        text: 元素文本（可选）
        
    Returns:
        点击结果
    """
    try:
        if text:
            selector = f"{selector}:has-text('{text}')"
        
        await page.click(selector)
        
        return {
            "success": True,
            "selector": selector
        }
    
    except Exception as e:
        logger.error(f"点击元素失败: {e}")
        return {
            "success": False,
            "message": f"点击元素失败: {str(e)}"
        }


async def type_text(
    page: Page,
    selector: str,
    text: str,
    clear: bool = True
) -> Dict[str, Any]:
    """
    输入文本
    
    Args:
        page: 页面实例
        selector: 元素选择器
        text: 输入的文本
        clear: 是否先清空
        
    Returns:
        输入结果
    """
    try:
        element = await page.query_selector(selector)
        if not element:
            return {
                "success": False,
                "message": f"未找到元素: {selector}"
            }
        
        if clear:
            await element.fill("")
        
        await element.fill(text)
        
        return {
            "success": True,
            "selector": selector,
            "text": text
        }
    
    except Exception as e:
        logger.error(f"输入文本失败: {e}")
        return {
            "success": False,
            "message": f"输入文本失败: {str(e)}"
        }


async def hover_element(
    page: Page,
    selector: str
) -> Dict[str, Any]:
    """
    悬停元素
    
    Args:
        page: 页面实例
        selector: 元素选择器
        
    Returns:
        悬停结果
    """
    try:
        await page.hover(selector)
        
        return {
            "success": True,
            "selector": selector
        }
    
    except Exception as e:
        logger.error(f"悬停元素失败: {e}")
        return {
            "success": False,
            "message": f"悬停元素失败: {str(e)}"
        }


async def wait_for(
    page: Page,
    selector: Optional[str] = None,
    text: Optional[str] = None,
    timeout: int = 30000
) -> Dict[str, Any]:
    """
    等待条件
    
    Args:
        page: 页面实例
        selector: 元素选择器（可选）
        text: 等待的文本（可选）
        timeout: 超时时间（毫秒）
        
    Returns:
        等待结果
    """
    try:
        if selector:
            await page.wait_for_selector(selector, timeout=timeout)
            return {
                "success": True,
                "selector": selector
            }
        
        elif text:
            await page.wait_for_function(
                f"() => document.body.innerText.includes('{text}')",
                timeout=timeout
            )
            return {
                "success": True,
                "text": text
            }
        
        else:
            return {
                "success": False,
                "message": "必须指定 selector 或 text"
            }
    
    except Exception as e:
        logger.error(f"等待失败: {e}")
        return {
            "success": False,
            "message": f"等待失败: {str(e)}"
        }
