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


async def scroll_page(
    page: Page,
    x: int = 0,
    y: int = 600
) -> Dict[str, Any]:
    """
    滚动页面

    Args:
        page: 页面实例
        x: 横向滚动像素
        y: 纵向滚动像素

    Returns:
        滚动结果
    """
    try:
        await page.evaluate(
            "(coords) => window.scrollBy(coords.x, coords.y)",
            {"x": x, "y": y},
        )
        return {
            "success": True,
            "x": x,
            "y": y
        }
    except Exception as e:
        logger.error(f"滚动页面失败: {e}")
        return {
            "success": False,
            "message": f"滚动页面失败: {str(e)}"
        }


async def press_key(
    page: Page,
    key: str
) -> Dict[str, Any]:
    """
    模拟键盘按键

    Args:
        page: 页面实例
        key: 键名（如 Enter, Tab, ArrowDown）

    Returns:
        按键结果
    """
    try:
        await page.keyboard.press(key)
        return {
            "success": True,
            "key": key
        }
    except Exception as e:
        logger.error(f"键盘按键失败: {e}")
        return {
            "success": False,
            "message": f"键盘按键失败: {str(e)}"
        }


async def select_option(
    page: Page,
    selector: str,
    value: str
) -> Dict[str, Any]:
    """
    选择下拉框选项

    Args:
        page: 页面实例
        selector: 下拉框选择器
        value: 选项值

    Returns:
        选择结果
    """
    try:
        selected = await page.select_option(selector, value=value)
        return {
            "success": True,
            "selector": selector,
            "value": value,
            "selected": selected
        }
    except Exception as e:
        logger.error(f"选择下拉选项失败: {e}")
        return {
            "success": False,
            "message": f"选择下拉选项失败: {str(e)}"
        }


async def history_go(
    page: Page,
    direction: str = "back"
) -> Dict[str, Any]:
    """
    浏览器历史前进/后退

    Args:
        page: 页面实例
        direction: back 或 forward

    Returns:
        跳转结果
    """
    try:
        if direction == "forward":
            response = await page.go_forward()
        else:
            response = await page.go_back()

        return {
            "success": True,
            "direction": direction,
            "url": page.url,
            "status": response.status if response else None
        }
    except Exception as e:
        logger.error(f"历史跳转失败: {e}")
        return {
            "success": False,
            "message": f"历史跳转失败: {str(e)}"
        }
