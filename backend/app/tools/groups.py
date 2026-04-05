"""
工具组定义

提供工具分组机制，简化工具权限管理
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    "group:browser": ToolGroup(
        id="group:browser",
        label="浏览器自动化",
        description="浏览器启动、导航与页面交互工具",
        tools=[
            "browser_start",
            "browser_stop",
            "browser_navigate",
            "browser_snapshot",
            "browser_screenshot",
            "browser_click",
            "browser_type",
            "browser_hover",
            "browser_wait",
            "browser_scroll",
            "browser_press",
            "browser_select",
            "browser_history",
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
            "browser_start",
            "browser_stop",
            "browser_navigate",
            "browser_snapshot",
            "browser_screenshot",
            "browser_click",
            "browser_type",
            "browser_hover",
            "browser_wait",
            "browser_scroll",
            "browser_press",
            "browser_select",
            "browser_history",
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
            "process",
            "browser_start",
            "browser_stop",
            "browser_navigate",
            "browser_snapshot",
            "browser_screenshot",
            "browser_click",
            "browser_type",
            "browser_hover",
            "browser_wait",
            "browser_scroll",
            "browser_press",
            "browser_select",
            "browser_history",
        ]
    ),
}


def get_group(group_id: str) -> Optional[ToolGroup]:
    """获取工具组"""
    return CORE_TOOL_GROUPS.get(group_id)


def get_group_tools(group_id: str) -> Optional[List[str]]:
    """获取工具组包含的工具列表"""
    group = get_group(group_id)
    return group.tools if group else None


def list_groups() -> List[ToolGroup]:
    """列出所有工具组"""
    return list(CORE_TOOL_GROUPS.values())


def is_group_id(name: str) -> bool:
    """检查是否为组 ID"""
    return name.startswith("group:")
