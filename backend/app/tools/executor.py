"""
工具执行器

负责执行工具调用，处理超时和错误
"""
import asyncio
import logging
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
            return ToolResult(
                success=False,
                content=None,
                error=f"工具 '{tool_name}' 不存在"
            )
        
        if not tool.enabled:
            return ToolResult(
                success=False,
                content=None,
                error=f"工具 '{tool_name}' 已禁用"
            )
        
        start_time = datetime.now()
        
        try:
            logger.info(f"开始执行工具 '{tool_name}'，参数: {arguments}")
            
            result = await asyncio.wait_for(
                tool.execute(**arguments),
                timeout=self.timeout_seconds
            )
            
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(f"工具 '{tool_name}' 执行成功，耗时: {execution_time_ms}ms")
            
            return ToolResult(
                success=True,
                content=result,
                execution_time_ms=execution_time_ms
            )
            
        except asyncio.TimeoutError:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"工具 '{tool_name}' 执行超时，耗时: {execution_time_ms}ms")
            return ToolResult(
                success=False,
                content=None,
                error=f"工具 '{tool_name}' 执行超时（{self.timeout_seconds}秒）",
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"工具 '{tool_name}' 执行失败: {str(e)}")
            return ToolResult(
                success=False,
                content=None,
                error=str(e),
                execution_time_ms=execution_time_ms
            )
    
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
        for call in tool_calls:
            tool_name = call.get("name")
            arguments = call.get("arguments", {})
            if isinstance(arguments, str):
                import json
                try:
                    arguments = json.loads(arguments)
                except:
                    arguments = {}
            result = await self.execute_tool(tool_name, arguments, message_id)
            results.append(result)
        return results


tool_executor = ToolExecutor()
