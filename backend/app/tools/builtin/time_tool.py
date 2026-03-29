"""
时间查询工具

提供获取当前时间的功能
"""
from datetime import datetime
from typing import Dict, Any
from app.tools.base import BaseTool, ToolDefinition, create_tool


class TimeTool(BaseTool):
    """时间查询工具"""
    
    @property
    def name(self) -> str:
        return "get_current_time"
    
    @property
    def description(self) -> str:
        return "获取当前的日期、时间、时区信息"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "时间格式",
                    "enum": ["iso", "friendly", "timestamp"]
                },
                "timezone": {
                    "type": "string",
                    "description": "时区，例如：Asia/Shanghai、UTC。默认为本地时区",
                    "default": "local"
                },
                "include_date": {
                    "type": "boolean",
                    "description": "是否包含日期信息",
                    "default": True
                }
            },
            "required": []
        }
    
    async def execute(
        self,
        format: str = "friendly",
        timezone: str = "local",
        include_date: bool = True
    ) -> Dict[str, Any]:
        """
        执行时间查询
        
        Args:
            format: 时间格式
                - iso: ISO 格式 (YYYY-MM-DD HH:MM:SS)
                - friendly: 友好格式 (2024年1月1日 12:00:00)
                - timestamp: Unix 时间戳
            timezone: 时区
            include_date: 是否包含日期
            
        Returns:
            时间信息字典
        """
        now = datetime.now()
        
        if timezone != "local":
            try:
                import pytz
                tz = pytz.timezone(timezone)
                now = now.astimezone(tz)
            except Exception:
                pass
        
        result = {}
        
        if format == "iso":
            result["time"] = now.strftime("%Y-%m-%d %H:%M:%S")
        elif format == "timestamp":
            result["time"] = int(now.timestamp())
        else:
            if include_date:
                weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                months = ["一月", "二月", "三月", "四月", "五月", "六月", 
                            "七月", "八月", "九月", "十月", "十一月", "十二月"]
                
                result["time"] = now.strftime(f"%Y年{months[now.month-1]}{now.day}日 {weekdays[now.weekday]} {now.hour:02d}:{now.minute:02d}")
            else:
                result["time"] = now.strftime("%H:%M:%S")
        
        result["format"] = format
        result["timezone"] = str(now.tzinfo) if now.tzinfo else "UTC"
        result["timestamp"] = int(now.timestamp())
        
        return result


def get_current_time_tool() -> ToolDefinition:
    """
    获取时间查询工具定义
    
    Returns:
        工具定义实例
    """
    tool_instance = TimeTool()
    return create_tool(
        name="get_current_time",
        description="获取当前的日期、时间、时区信息",
        parameters={
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "时间格式",
                    "enum": ["iso", "friendly", "timestamp"]
                },
                "timezone": {
                    "type": "string",
                    "description": "时区，例如：Asia/Shanghai、UTC。默认为本地时区",
                    "default": "local"
                },
                "include_date": {
                    "type": "boolean",
                    "description": "是否包含日期信息",
                    "default": True
                }
            },
            "required": []
        },
        execute=tool_instance.execute
    )
