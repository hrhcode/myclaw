"""
页面快照模块

获取页面的可访问性树结构
"""
import logging
from typing import Dict, Any, List, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def get_aria_snapshot(page: Page, format: str = "aria") -> Dict[str, Any]:
    """
    获取页面快照
    
    Args:
        page: 页面实例
        format: 快照格式（aria、compact）
        
    Returns:
        快照结果
    """
    try:
        snapshot = await page.accessibility.snapshot()
        
        if format == "compact":
            result = await _format_compact_snapshot(snapshot, page.url)
        else:
            result = await _format_aria_snapshot(snapshot, page.url)
        
        return {
            "success": True,
            "format": format,
            "url": page.url,
            "snapshot": result
        }
    
    except Exception as e:
        logger.error(f"获取快照失败: {e}")
        return {
            "success": False,
            "message": f"获取快照失败: {str(e)}"
        }


async def _format_aria_snapshot(snapshot: Dict[str, Any], url: str) -> str:
    """
    格式化 ARIA 快照
    
    Args:
        snapshot: 可访问性树
        url: 页面 URL
        
    Returns:
        格式化的快照字符串
    """
    lines = [f"页面快照: {url}"]
    lines.append("=" * 80)
    
    if snapshot:
        lines.extend(_format_node(snapshot, depth=0))
    
    return "\n".join(lines)


async def _format_compact_snapshot(snapshot: Dict[str, Any], url: str) -> str:
    """
    格式化紧凑快照
    
    Args:
        snapshot: 可访问性树
        url: 页面 URL
        
    Returns:
        格式化的紧凑快照字符串
    """
    lines = [f"紧凑快照: {url}"]
    
    if snapshot:
        interactive_nodes = _collect_interactive_nodes(snapshot)
        
        for i, node in enumerate(interactive_nodes, 1):
            role = node.get("role", "unknown")
            name = node.get("name", "")
            description = node.get("description", "")
            
            line = f"[{i}] {role}"
            if name:
                line += f": {name}"
            if description:
                line += f" ({description})"
            
            lines.append(line)
    
    return "\n".join(lines)


def _format_node(node: Dict[str, Any], depth: int = 0) -> List[str]:
    """
    格式化节点
    
    Args:
        node: 可访问性节点
        depth: 深度
        
    Returns:
        格式化的节点行列表
    """
    lines = []
    indent = "  " * depth
    
    role = node.get("role", "unknown")
    name = node.get("name", "")
    description = node.get("description", "")
    
    line = f"{indent}{role}"
    if name:
        line += f": {name}"
    if description:
        line += f" ({description})"
    
    lines.append(line)
    
    children = node.get("children", [])
    if children:
        for child in children:
            lines.extend(_format_node(child, depth + 1))
    
    return lines


def _collect_interactive_nodes(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    收集可交互节点
    
    Args:
        node: 可访问性节点
        
    Returns:
        可交互节点列表
    """
    interactive_roles = {
        "button", "link", "textbox", "checkbox", "radio", "combobox",
        "listbox", "menuitem", "tab", "slider", "spinbutton"
    }
    
    nodes = []
    
    if node.get("role") in interactive_roles:
        nodes.append(node)
    
    children = node.get("children", [])
    for child in children:
        nodes.extend(_collect_interactive_nodes(child))
    
    return nodes
