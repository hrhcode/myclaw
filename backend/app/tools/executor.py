"""
工具执行器

负责执行工具调用，处理超时和错误
"""
import asyncio
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
from app.tools.base import ToolDefinition, ToolResult
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    工具执行器

    负责执行工具调用，处理超时和错误
    """

    def __init__(self, timeout_seconds: int = 30):
        """
        初始化执行器

        Args:
            timeout_seconds: 单个工具执行超时时间（秒）
        """
        self.timeout_seconds = timeout_seconds

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        message_id: Optional[int] = None
    ) -> ToolResult:
        """
        执行工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            message_id: 关联的消息ID（用于记录）

        Returns:
            工具执行结果
        """
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            logger.error(f"[工具执行] 工具不存在: {tool_name}")
            return ToolResult(
                success=False,
                content=None,
                error=f"工具 '{tool_name}' 不存在"
            )

        if not tool.enabled:
            logger.warning(f"[工具执行] 工具已禁用: {tool_name}")
            return ToolResult(
                success=False,
                content=None,
                error=f"工具 '{tool_name}' 已禁用"
            )

        start_time = datetime.now()

        safe_args = self._sanitize_arguments(arguments)
        logger.info(f"[工具执行] ════════════════════════════════════════════")
        logger.info(f"[工具执行] 开始执行工具: {tool_name}")
        logger.info(f"[工具执行] 参数: {json.dumps(safe_args, ensure_ascii=False, indent=2)}")
        logger.info(f"[工具执行] 超时设置: {self.timeout_seconds}秒")
        logger.info(f"[工具执行] ────────────────────────────────────────────")

        try:
            result = await asyncio.wait_for(
                tool.execute(**arguments),
                timeout=self.timeout_seconds
            )

            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            if result.get("success"):
                logger.info(f"[工具执行] ✓ 工具 '{tool_name}' 执行成功")
                logger.info(f"[工具执行]   耗时: {execution_time_ms}ms")
                results_count = len(result.get("results", []))
                logger.info(f"[工具执行]   返回结果数: {results_count}")
                if results_count > 0:
                    for i, r in enumerate(result.get("results", [])[:3], 1):
                        title = r.get("title", "")[:50]
                        url = r.get("url", "")[:80]
                        logger.info(f"[工具执行]   结果{i}: {title}")
                        logger.info(f"[工具执行]         URL: {url}")
                    if results_count > 3:
                        logger.info(f"[工具执行]   ... 还有 {results_count - 3} 个结果")
            else:
                logger.error(f"[工具执行] ✗ 工具 '{tool_name}' 执行失败")
                logger.error(f"[工具执行]   错误: {result.get('error', '未知错误')}")
                logger.error(f"[工具执行]   耗时: {execution_time_ms}ms")

            logger.info(f"[工具执行] ════════════════════════════════════════════")

            return ToolResult(
                success=result.get("success", False),
                content=result,
                execution_time_ms=execution_time_ms
            )

        except asyncio.TimeoutError:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"[工具执行] ✗ 工具 '{tool_name}' 执行超时")
            logger.error(f"[工具执行]   设置超时: {self.timeout_seconds}秒")
            logger.error(f"[工具执行]   实际耗时: {execution_time_ms}ms")
            logger.error(f"[工具执行] ════════════════════════════════════════════")
            return ToolResult(
                success=False,
                content=None,
                error=f"工具 '{tool_name}' 执行超时（{self.timeout_seconds}秒）",
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"[工具执行] ✗ 工具 '{tool_name}' 执行异常")
            logger.error(f"[工具执行]   错误类型: {type(e).__name__}")
            logger.error(f"[工具执行]   错误信息: {str(e)}")
            logger.error(f"[工具执行]   耗时: {execution_time_ms}ms")
            logger.error(f"[工具执行] ════════════════════════════════════════════")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
                execution_time_ms=execution_time_ms
            )

    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理参数中的敏感信息

        Args:
            arguments: 原始参数

        Returns:
            清理后的参数
        """
        sensitive_keys = ["api_key", "token", "password", "secret", "tavily_api_key"]
        sanitized = {}
        for key, value in arguments.items():
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = "***隐藏***"
            else:
                sanitized[key] = value
        return sanitized

    async def execute_tools(
        self,
        tool_calls: list[Dict[str, Any]],
        message_id: Optional[int] = None
    ) -> list[ToolResult]:
        """
        批量执行多个工具

        Args:
            tool_calls: 工具调用列表，每个包含 name 和 arguments
            message_id: 关联的消息ID

        Returns:
            工具执行结果列表
        """
        results = []
        logger.info(f"[工具执行] 开始批量执行 {len(tool_calls)} 个工具调用")

        for i, call in enumerate(tool_calls, 1):
            tool_name = call.get("name")
            arguments_str = call.get("arguments", "{}")

            try:
                arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
            except json.JSONDecodeError:
                arguments = {}

            logger.info(f"[工具执行] [{i}/{len(tool_calls)}] 准备执行工具: {tool_name}")

            result = await self.execute_tool(tool_name, arguments, message_id)
            results.append(result)

            if not result.success:
                logger.warning(f"[工具执行] [{i}/{len(tool_calls)}] 工具执行失败，停止后续执行")
                break

        logger.info(f"[工具执行] 批量执行完成，成功: {sum(1 for r in results if r.success)}/{len(results)}")
        return results


tool_executor = ToolExecutor()
