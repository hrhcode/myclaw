"""
智谱 AI Provider 实现
"""
from zai import ZhipuAiClient
from typing import Any, AsyncIterator, Dict, List, Optional
import logging

from app.services.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class ZhipuProvider(BaseLLMProvider):
    """智谱 AI LLM Provider"""

    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        super().__init__(api_key, model)
        self.client = ZhipuAiClient(api_key=api_key)

    @staticmethod
    def _sanitize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗消息以适配智谱AI的格式要求。

        智谱AI不接受 content 为 null 的消息，也不识别 reasoning_content 等字段。
        """
        sanitized = []
        for msg in messages:
            clean = dict(msg)
            # content 不能为 null，空值改为 ""
            if clean.get("content") is None:
                clean["content"] = ""
            # 移除智谱不支持的字段
            clean.pop("reasoning_content", None)
            # 清理 tool_calls 中的 null arguments
            if "tool_calls" in clean and clean["tool_calls"]:
                clean_tool_calls = []
                for tc in clean["tool_calls"]:
                    tc_copy = dict(tc)
                    func = dict(tc_copy.get("function", {}))
                    if func.get("arguments") is None:
                        func["arguments"] = "{}"
                    tc_copy["function"] = func
                    clean_tool_calls.append(tc_copy)
                clean["tool_calls"] = clean_tool_calls
            sanitized.append(clean)
        return sanitized

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        thinking: bool = True,
    ) -> AsyncIterator[str]:
        try:
            use_model = model or self.model
            logger.info(f"调用智谱AI模型(流式): {use_model}, thinking={thinking}")

            clean_messages = self._sanitize_messages(messages)
            response = self.client.chat.completions.create(
                model=use_model,
                messages=clean_messages,
                stream=True,
                thinking={"type": "enabled"} if thinking else {"type": "disabled"},
            )

            full_content = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield content

            logger.info(f"流式回复完成, 总长度: {len(full_content)}")

        except Exception as e:
            logger.error(f"流式AI模型调用失败: {str(e)}")
            raise

    async def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        thinking: bool = True,
    ) -> Dict[str, Any]:
        try:
            use_model = model or self.model
            logger.info(f"调用智谱AI模型(工具调用): {use_model}, 工具数量: {len(tools)}")

            clean_messages = self._sanitize_messages(messages)
            response = self.client.chat.completions.create(
                model=use_model,
                messages=clean_messages,
                tools=tools,
                tool_choice="auto",
                thinking={"type": "enabled"} if thinking else {"type": "disabled"},
            )

            message = response.choices[0].message

            result = {
                "content": message.content if hasattr(message, "content") else None,
                "tool_calls": [],
            }

            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    result["tool_calls"].append(
                        {
                            "id": tool_call.id,
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        }
                    )

            logger.info(
                f"工具调用响应: content长度={len(result['content'] or '')}, tool_calls数量={len(result['tool_calls'])}"
            )

            return result

        except Exception as e:
            logger.error(f"工具调用AI模型失败: {str(e)}")
            raise

    async def chat_stream_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        thinking: bool = True,
    ) -> AsyncIterator[Dict[str, Any]]:
        try:
            use_model = model or self.model
            logger.info(
                f"调用智谱AI模型(流式工具调用): {use_model}, 工具数量: {len(tools)}"
            )

            clean_messages = self._sanitize_messages(messages)
            response = self.client.chat.completions.create(
                model=use_model,
                messages=clean_messages,
                tools=tools,
                tool_choice="auto",
                stream=True,
                tool_stream=True,
                thinking={"type": "enabled"} if thinking else {"type": "disabled"},
            )

            tool_calls_map: Dict[int, Dict[str, Any]] = {}
            current_content = ""

            for chunk in response:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    yield {"type": "reasoning", "content": delta.reasoning_content}

                if hasattr(delta, "content") and delta.content:
                    current_content += delta.content
                    yield {"type": "content", "content": delta.content}

                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        index = tool_call.index
                        if index not in tool_calls_map:
                            tool_calls_map[index] = {
                                "id": tool_call.id,
                                "name": (
                                    tool_call.function.name
                                    if hasattr(tool_call.function, "name")
                                    else ""
                                ),
                                "arguments": "",
                            }
                        if (
                            hasattr(tool_call.function, "arguments")
                            and tool_call.function.arguments
                        ):
                            tool_calls_map[index][
                                "arguments"
                            ] += tool_call.function.arguments

            if tool_calls_map:
                yield {
                    "type": "tool_calls",
                    "tool_calls": list(tool_calls_map.values()),
                }

            logger.info(
                f"流式工具调用完成, content长度={len(current_content)}, tool_calls数量={len(tool_calls_map)}"
            )

        except Exception as e:
            logger.error(f"流式工具调用AI模型失败: {str(e)}")
            raise
