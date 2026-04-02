"""
Time tool.

Provides the current date/time in a few simple formats.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from app.tools.base import BaseTool, ToolDefinition, create_tool


WEEKDAYS_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
MONTHS_ZH = [
    "一月",
    "二月",
    "三月",
    "四月",
    "五月",
    "六月",
    "七月",
    "八月",
    "九月",
    "十月",
    "十一月",
    "十二月",
]


class TimeTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return "Get the current date, time, timezone, and timestamp."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Output format for the time value.",
                    "enum": ["iso", "friendly", "timestamp"],
                    "default": "friendly",
                },
                "timezone": {
                    "type": "string",
                    "description": "Timezone name such as Asia/Shanghai or UTC. Defaults to local timezone.",
                    "default": "local",
                },
                "include_date": {
                    "type": "boolean",
                    "description": "Whether to include date information in friendly format.",
                    "default": True,
                },
            },
            "required": [],
        }

    async def execute(
        self,
        format: str = "friendly",
        timezone: str = "local",
        include_date: bool = True,
    ) -> Dict[str, Any]:
        now = datetime.now().astimezone()

        if timezone != "local":
            try:
                import pytz

                tz = pytz.timezone(timezone)
                now = now.astimezone(tz)
            except Exception:
                timezone = "local"

        if format == "iso":
            rendered = now.isoformat(timespec="seconds")
        elif format == "timestamp":
            rendered = str(int(now.timestamp()))
        elif include_date:
            rendered = (
                f"{now.year}年{MONTHS_ZH[now.month - 1]}{now.day}日"
                f" {WEEKDAYS_ZH[now.weekday()]} {now:%H:%M:%S}"
            )
        else:
            rendered = now.strftime("%H:%M:%S")

        return {
            "time": rendered,
            "format": format,
            "timezone": str(now.tzinfo) if now.tzinfo else "local",
            "timestamp": int(now.timestamp()),
            "iso": now.isoformat(timespec="seconds"),
        }


def get_current_time_tool() -> ToolDefinition:
    tool = TimeTool()
    return create_tool(
        name=tool.name,
        description=tool.description,
        parameters=tool.parameters,
        execute=tool.execute,
    )
