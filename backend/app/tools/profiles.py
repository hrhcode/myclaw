"""
工具配置文件系统

提供预设的工具组合配置，简化工具权限管理
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ToolProfileId(str, Enum):
    """
    工具配置文件 ID
    
    Attributes:
        MINIMAL: 最小配置，仅包含基本工具
        STANDARD: 标准配置，包含常用工具
        CODING: 编程配置，包含文件和运行时工具
        MESSAGING: 消息配置，包含消息和会话工具
        FULL: 完整配置，无限制
    """
    MINIMAL = "minimal"
    STANDARD = "standard"
    CODING = "coding"
    MESSAGING = "messaging"
    FULL = "full"


@dataclass
class ToolProfile:
    """
    工具配置文件
    
    Attributes:
        id: 配置文件 ID
        label: 显示标签
        description: 描述
        allow: 允许的工具列表
        deny: 禁止的工具列表
    """
    id: ToolProfileId
    label: str
    description: str
    allow: List[str] = field(default_factory=list)
    deny: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id.value,
            "label": self.label,
            "description": self.description,
            "allow": self.allow,
            "deny": self.deny
        }


CORE_TOOL_PROFILES: Dict[ToolProfileId, ToolProfile] = {
    ToolProfileId.MINIMAL: ToolProfile(
        id=ToolProfileId.MINIMAL,
        label="最小",
        description="仅包含基本工具，适合受限环境",
        allow=[
            "get_current_time",
            "session_status"
        ],
        deny=[]
    ),
    ToolProfileId.STANDARD: ToolProfile(
        id=ToolProfileId.STANDARD,
        label="标准",
        description="包含常用内置能力，适合默认对话任务",
        allow=[
            "group:builtin",
            "group:web",
            "group:browser",
            "get_current_time",
        ],
        deny=[]
    ),
    ToolProfileId.CODING: ToolProfile(
        id=ToolProfileId.CODING,
        label="编程",
        description="包含运行时和网络工具，适合编程任务",
        allow=[
            "group:runtime",
            "group:web",
            "get_current_time"
        ],
        deny=[]
    ),
    ToolProfileId.MESSAGING: ToolProfile(
        id=ToolProfileId.MESSAGING,
        label="消息",
        description="包含消息和会话工具，适合对话任务",
        allow=[
            "group:messaging",
            "sessions_list",
            "sessions_history",
            "sessions_send",
            "session_status",
            "get_current_time"
        ],
        deny=[]
    ),
    ToolProfileId.FULL: ToolProfile(
        id=ToolProfileId.FULL,
        label="完整",
        description="无限制，可以使用所有工具",
        allow=[],
        deny=[]
    ),
}


def get_profile(profile_id: str) -> Optional[ToolProfile]:
    """
    获取工具配置文件
    
    Args:
        profile_id: 配置文件 ID
        
    Returns:
        工具配置文件，不存在返回 None
    """
    try:
        pid = ToolProfileId(profile_id.lower())
        return CORE_TOOL_PROFILES.get(pid)
    except ValueError:
        return None


def list_profiles() -> List[ToolProfile]:
    """
    列出所有工具配置文件
    
    Returns:
        配置文件列表
    """
    return list(CORE_TOOL_PROFILES.values())


def resolve_profile_policy(profile_id: Optional[str]) -> Optional[Dict[str, List[str]]]:
    """
    解析配置文件策略
    
    Args:
        profile_id: 配置文件 ID
        
    Returns:
        策略字典，包含 allow 和 deny 列表
    """
    if not profile_id:
        return None
    
    profile = get_profile(profile_id)
    if not profile:
        return None
    
    return {
        "allow": list(profile.allow),
        "deny": list(profile.deny)
    }


def get_profile_options() -> List[Dict[str, str]]:
    """
    获取配置文件选项列表（用于 UI 展示）
    
    Returns:
        选项列表
    """
    return [
        {"id": p.id.value, "label": p.label, "description": p.description}
        for p in CORE_TOOL_PROFILES.values()
    ]


class ToolProfileResolver:
    """
    工具配置文件解析器
    
    解析和合并多个配置文件
    """
    
    def __init__(self, groups_module: Optional[Any] = None):
        """
        初始化解析器
        
        Args:
            groups_module: 工具组模块（用于展开 group:* 引用）
        """
        self._groups_module = groups_module
    
    def resolve(
        self,
        profile_id: Optional[str] = None,
        custom_allow: Optional[List[str]] = None,
        custom_deny: Optional[List[str]] = None
    ) -> Dict[str, Set[str]]:
        """
        解析工具策略
        
        Args:
            profile_id: 配置文件 ID
            custom_allow: 自定义允许列表
            custom_deny: 自定义禁止列表
            
        Returns:
            包含 allow 和 deny 集合的字典
        """
        allow: Set[str] = set()
        deny: Set[str] = set()
        
        if profile_id:
            profile = get_profile(profile_id)
            if profile:
                allow.update(profile.allow)
                deny.update(profile.deny)
        
        if custom_allow:
            allow.update(custom_allow)
        
        if custom_deny:
            deny.update(custom_deny)
        
        allow = self._expand_groups(allow)
        deny = self._expand_groups(deny)
        
        return {
            "allow": allow,
            "deny": deny
        }
    
    def _expand_groups(self, tool_names: Set[str]) -> Set[str]:
        """
        展开工具组引用
        
        Args:
            tool_names: 工具名称集合
            
        Returns:
            展开后的工具名称集合
        """
        if not self._groups_module:
            return tool_names
        
        expanded: Set[str] = set()
        
        for name in tool_names:
            if name.startswith("group:"):
                group_tools = self._groups_module.get_group_tools(name)
                if group_tools:
                    expanded.update(group_tools)
            else:
                expanded.add(name)
        
        return expanded


def create_profile_resolver(groups_module: Optional[Any] = None) -> ToolProfileResolver:
    """
    创建配置文件解析器
    
    Args:
        groups_module: 工具组模块
        
    Returns:
        解析器实例
    """
    return ToolProfileResolver(groups_module)
