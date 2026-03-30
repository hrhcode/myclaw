"""
工具组定义

提供工具分组机制，简化工具权限管理
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


@dataclass
class ToolGroup:
    """
    工具组
    
    Attributes:
        id: 组 ID（如 group:fs）
        label: 显示标签
        description: 描述
        tools: 包含的工具列表
    """
    id: str
    label: str
    description: str
    tools: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "tools": self.tools
        }


CORE_TOOL_GROUPS: Dict[str, ToolGroup] = {
    "group:fs": ToolGroup(
        id="group:fs",
        label="文件系统",
        description="文件读写和编辑工具",
        tools=[
            "read",
            "write",
            "edit",
            "apply_patch"
        ]
    ),
    "group:runtime": ToolGroup(
        id="group:runtime",
        label="运行时",
        description="命令执行和进程管理工具",
        tools=[
            "exec",
            "process"
        ]
    ),
    "group:web": ToolGroup(
        id="group:web",
        label="网络",
        description="网络搜索和获取工具",
        tools=[
            "web_search",
            "web_fetch"
        ]
    ),
    "group:sessions": ToolGroup(
        id="group:sessions",
        label="会话",
        description="会话管理工具",
        tools=[
            "sessions_list",
            "sessions_history",
            "sessions_send",
            "sessions_spawn",
            "session_status"
        ]
    ),
    "group:ui": ToolGroup(
        id="group:ui",
        label="界面",
        description="浏览器和画布控制工具",
        tools=[
            "browser",
            "canvas"
        ]
    ),
    "group:messaging": ToolGroup(
        id="group:messaging",
        label="消息",
        description="消息发送工具",
        tools=[
            "message"
        ]
    ),
    "group:automation": ToolGroup(
        id="group:automation",
        label="自动化",
        description="定时任务和网关控制工具",
        tools=[
            "cron",
            "gateway"
        ]
    ),
    "group:nodes": ToolGroup(
        id="group:nodes",
        label="节点",
        description="设备节点管理工具",
        tools=[
            "nodes"
        ]
    ),
    "group:media": ToolGroup(
        id="group:media",
        label="媒体",
        description="图像和文档处理工具",
        tools=[
            "image",
            "pdf",
            "tts"
        ]
    ),
    "group:builtin": ToolGroup(
        id="group:builtin",
        label="已实现工具",
        description="当前项目已实现的内置工具",
        tools=[
            "get_current_time",
            "web_search",
            "web_fetch",
            "exec",
            "process"
        ]
    ),
}


def get_group(group_id: str) -> Optional[ToolGroup]:
    """
    获取工具组
    
    Args:
        group_id: 组 ID
        
    Returns:
        工具组，不存在返回 None
    """
    return CORE_TOOL_GROUPS.get(group_id)


def get_group_tools(group_id: str) -> Optional[List[str]]:
    """
    获取工具组包含的工具列表
    
    Args:
        group_id: 组 ID
        
    Returns:
        工具列表，不存在返回 None
    """
    group = get_group(group_id)
    return group.tools if group else None


def list_groups() -> List[ToolGroup]:
    """
    列出所有工具组
    
    Returns:
        工具组列表
    """
    return list(CORE_TOOL_GROUPS.values())


def is_group_id(name: str) -> bool:
    """
    检查是否为组 ID
    
    Args:
        name: 名称
        
    Returns:
        是否为组 ID
    """
    return name.startswith("group:")


def expand_groups(tool_names: List[str]) -> Set[str]:
    """
    展开工具组引用
    
    将 group:* 引用展开为具体的工具名称
    
    Args:
        tool_names: 工具名称列表
        
    Returns:
        展开后的工具名称集合
    """
    expanded: Set[str] = set()
    
    for name in tool_names:
        if is_group_id(name):
            group_tools = get_group_tools(name)
            if group_tools:
                expanded.update(group_tools)
        else:
            expanded.add(name)
    
    return expanded


def expand_groups_dict(tool_dict: Dict[str, List[str]]) -> Dict[str, Set[str]]:
    """
    展开工具字典中的组引用
    
    Args:
        tool_dict: 包含 allow 和 deny 列表的字典
        
    Returns:
        展开后的字典
    """
    return {
        "allow": expand_groups(tool_dict.get("allow", [])),
        "deny": expand_groups(tool_dict.get("deny", []))
    }


def get_group_options() -> List[Dict[str, str]]:
    """
    获取工具组选项列表（用于 UI 展示）
    
    Returns:
        选项列表
    """
    return [
        {
            "id": g.id,
            "label": g.label,
            "description": g.description,
            "tools": ", ".join(g.tools)
        }
        for g in CORE_TOOL_GROUPS.values()
    ]


def resolve_tool_policy(
    profile_allow: Optional[List[str]] = None,
    profile_deny: Optional[List[str]] = None,
    custom_allow: Optional[List[str]] = None,
    custom_deny: Optional[List[str]] = None
) -> Dict[str, Set[str]]:
    """
    解析工具策略
    
    合并配置文件和自定义策略，展开组引用
    
    Args:
        profile_allow: 配置文件允许列表
        profile_deny: 配置文件禁止列表
        custom_allow: 自定义允许列表
        custom_deny: 自定义禁止列表
        
    Returns:
        包含 allow 和 deny 集合的字典
    """
    allow: Set[str] = set()
    deny: Set[str] = set()
    
    if profile_allow:
        allow.update(expand_groups(profile_allow))
    
    if profile_deny:
        deny.update(expand_groups(profile_deny))
    
    if custom_allow:
        allow.update(expand_groups(custom_allow))
    
    if custom_deny:
        deny.update(expand_groups(custom_deny))
    
    return {
        "allow": allow,
        "deny": deny
    }


class ToolGroupManager:
    """
    工具组管理器
    
    提供工具组的注册、查询和扩展功能
    """
    
    def __init__(self):
        """初始化管理器"""
        self._groups: Dict[str, ToolGroup] = dict(CORE_TOOL_GROUPS)
    
    def register_group(self, group: ToolGroup) -> None:
        """
        注册工具组
        
        Args:
            group: 工具组
        """
        self._groups[group.id] = group
    
    def unregister_group(self, group_id: str) -> bool:
        """
        注销工具组
        
        Args:
            group_id: 组 ID
            
        Returns:
            是否成功注销
        """
        if group_id in self._groups:
            del self._groups[group_id]
            return True
        return False
    
    def get_group(self, group_id: str) -> Optional[ToolGroup]:
        """获取工具组"""
        return self._groups.get(group_id)
    
    def get_group_tools(self, group_id: str) -> Optional[List[str]]:
        """获取工具组包含的工具"""
        group = self.get_group(group_id)
        return group.tools if group else None
    
    def list_groups(self) -> List[ToolGroup]:
        """列出所有工具组"""
        return list(self._groups.values())
    
    def expand_groups(self, tool_names: List[str]) -> Set[str]:
        """展开工具组引用"""
        expanded: Set[str] = set()
        
        for name in tool_names:
            if is_group_id(name):
                group_tools = self.get_group_tools(name)
                if group_tools:
                    expanded.update(group_tools)
            else:
                expanded.add(name)
        
        return expanded


tool_group_manager = ToolGroupManager()
