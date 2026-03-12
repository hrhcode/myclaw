"""
工具系统模块
提供工具注册、执行和管理功能
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Optional

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class Tool:
    """
    工具类
    定义一个可被 LLM 调用的工具
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        func: Callable,
    ):
        """
        初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数定义（JSON Schema 格式）
            func: 执行函数
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    def to_openai_format(self) -> dict[str, Any]:
        """
        转换为 OpenAI Function Calling 格式
        
        Returns:
            OpenAI 格式的工具定义
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """
    工具注册表
    管理所有可用工具
    """

    def __init__(self):
        """初始化工具注册表"""
        self._tools: dict[str, Tool] = {}
        self._enabled: dict[str, bool] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """注册内置工具"""
        self.register(
            Tool(
                name="web_search",
                description="搜索互联网获取信息。当需要查找最新信息、新闻或特定主题时使用。",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词",
                        }
                    },
                    "required": ["query"],
                },
                func=self._web_search,
            )
        )

        self.register(
            Tool(
                name="web_fetch",
                description="获取网页内容。当需要读取特定网页的详细内容时使用。",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "要获取的网页 URL",
                        }
                    },
                    "required": ["url"],
                },
                func=self._web_fetch,
            )
        )

        self.register(
            Tool(
                name="current_time",
                description="获取当前日期和时间。当用户询问时间相关问题时使用。",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                func=self._current_time,
            )
        )

    def register(self, tool: Tool) -> None:
        """
        注册工具
        
        Args:
            tool: 工具实例
        """
        self._tools[tool.name] = tool
        self._enabled[tool.name] = True
        logger.debug(f"注册工具: {tool.name}")

    def get(self, name: str) -> Optional[Tool]:
        """
        获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，不存在则返回 None
        """
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """
        获取所有工具列表
        
        Returns:
            工具列表
        """
        return list(self._tools.values())

    def is_enabled(self, name: str) -> bool:
        """
        检查工具是否启用
        
        Args:
            name: 工具名称
            
        Returns:
            是否启用
        """
        return self._enabled.get(name, True)

    def set_enabled(self, name: str, enabled: bool) -> None:
        """
        设置工具启用状态
        
        Args:
            name: 工具名称
            enabled: 是否启用
        """
        if name in self._tools:
            self._enabled[name] = enabled
            logger.info(f"工具 {name} {'启用' if enabled else '禁用'}")

    def get_openai_tools(self) -> list[dict[str, Any]]:
        """
        获取 OpenAI 格式的工具定义列表（仅返回启用的工具）
        
        Returns:
            OpenAI 格式的工具列表
        """
        return [
            tool.to_openai_format() 
            for name, tool in self._tools.items() 
            if self._enabled.get(name, True)
        ]

    async def execute(self, name: str, arguments: dict[str, Any]) -> str:
        """
        执行工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            执行结果
        """
        tool = self.get(name)
        if not tool:
            return f"错误: 未找到工具 '{name}'"

        try:
            if asyncio.iscoroutinefunction(tool.func):
                result = await tool.func(**arguments)
            else:
                result = tool.func(**arguments)
            logger.info(f"工具执行成功: {name}")
            return str(result)
        except Exception as e:
            error_msg = f"工具执行失败: {name} - {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def _web_search(self, query: str, max_results: int = 5) -> str:
        """
        网络搜索工具
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
            
        Returns:
            搜索结果
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                return f"未找到关于 '{query}' 的搜索结果"
            
            output = []
            for i, r in enumerate(results, 1):
                output.append(f"{i}. {r['title']}")
                output.append(f"   链接: {r['href']}")
                output.append(f"   摘要: {r['body'][:200]}...")
                output.append("")
            
            return "\n".join(output)
        except Exception as e:
            return f"搜索失败: {str(e)}"

    async def _web_fetch(self, url: str, max_length: int = 5000) -> str:
        """
        网页抓取工具
        
        Args:
            url: 网页 URL
            max_length: 最大内容长度
            
        Returns:
            网页内容
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            text = soup.get_text(separator="\n", strip=True)
            
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = "\n".join(lines)
            
            if len(content) > max_length:
                content = content[:max_length] + "...(内容已截断)"
            
            return content
        except Exception as e:
            return f"抓取失败: {str(e)}"

    def _current_time(self) -> str:
        """
        获取当前时间工具
        
        Returns:
            当前时间字符串
        """
        now = datetime.now()
        return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}"


_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册表实例（单例模式）
    
    Returns:
        ToolRegistry 实例
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
