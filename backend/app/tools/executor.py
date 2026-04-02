from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.tools.base import ToolResult
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        message_id: Optional[int] = None,
    ) -> ToolResult:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            logger.error("[tool_executor] tool not found: %s", tool_name)
            return ToolResult(
                success=False,
                content=None,
                error=f"Tool '{tool_name}' not found.",
            )

        if not tool.enabled:
            logger.warning("[tool_executor] tool disabled: %s", tool_name)
            return ToolResult(
                success=False,
                content=None,
                error=f"Tool '{tool_name}' is disabled.",
            )

        start_time = datetime.now()
        safe_args = self._sanitize_arguments(arguments)
        logger.info("[tool_executor] start tool=%s args=%s", tool_name, json.dumps(safe_args, ensure_ascii=False))

        try:
            raw_result = await asyncio.wait_for(
                tool.execute(**arguments),
                timeout=self.timeout_seconds,
            )
            result = self._normalize_tool_result(raw_result)
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            if result.get("success"):
                logger.info("[tool_executor] tool succeeded: %s (%sms)", tool_name, execution_time_ms)
            else:
                logger.error(
                    "[tool_executor] tool failed: %s (%sms) error=%s",
                    tool_name,
                    execution_time_ms,
                    result.get("error"),
                )

            return ToolResult(
                success=bool(result.get("success", False)),
                content=result.get("content"),
                error=result.get("error"),
                execution_time_ms=execution_time_ms,
            )
        except asyncio.TimeoutError:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error("[tool_executor] tool timed out: %s", tool_name)
            return ToolResult(
                success=False,
                content=None,
                error=f"Tool '{tool_name}' timed out after {self.timeout_seconds} seconds.",
                execution_time_ms=execution_time_ms,
            )
        except Exception as exc:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.exception("[tool_executor] tool raised exception: %s", tool_name)
            return ToolResult(
                success=False,
                content=None,
                error=str(exc),
                execution_time_ms=execution_time_ms,
            )

    async def execute_tools(
        self,
        tool_calls: list[Dict[str, Any]],
        message_id: Optional[int] = None,
    ) -> list[ToolResult]:
        results: list[ToolResult] = []
        logger.info("[tool_executor] batch start: %s call(s)", len(tool_calls))

        for call in tool_calls:
            tool_name = call.get("name")
            arguments_str = call.get("arguments", "{}")
            try:
                arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
            except json.JSONDecodeError:
                arguments = {}

            result = await self.execute_tool(tool_name, arguments, message_id)
            results.append(result)

            if not result.success:
                break

        return results

    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        sensitive_keys = ["api_key", "token", "password", "secret", "tavily_api_key"]
        sanitized: Dict[str, Any] = {}
        for key, value in arguments.items():
            if any(marker in key.lower() for marker in sensitive_keys):
                sanitized[key] = "***hidden***"
            else:
                sanitized[key] = value
        return sanitized

    def _normalize_tool_result(self, result: Any) -> Dict[str, Any]:
        if isinstance(result, ToolResult):
            return result.to_dict()
        if isinstance(result, dict):
            if "success" in result:
                return result
            return {
                "success": True,
                "content": result,
                "error": None,
            }
        return {
            "success": True,
            "content": result,
            "error": None,
        }


tool_executor = ToolExecutor()
