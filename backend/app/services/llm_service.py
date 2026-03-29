from zai import ZhipuAiClient
from typing import List, Dict, AsyncIterator, Optional, Any
import logging
import json

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, api_key: str):
        self.client = ZhipuAiClient(api_key=api_key)
        self.model = "glm-4-flash"

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        thinking: bool = True
    ) -> AsyncIterator[str]:
        """
        流式聊天对话

        Args:
            messages: 消息历史列表
            model: 模型名称
            thinking: 是否启用思考模式

        Yields:
            AI回复的每个片段
        """
        try:
            use_model = model or self.model

            logger.info(f"调用智谱AI模型(流式): {use_model}, thinking={thinking}")

            response = self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                stream=True,
                thinking={"type": "enabled"} if thinking else {"type": "disabled"}
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
        thinking: bool = True
    ) -> Dict[str, Any]:
        """
        带工具调用的聊天（非流式）

        Args:
            messages: 消息历史列表
            tools: 工具定义列表
            model: 模型名称
            thinking: 是否启用思考模式

        Returns:
            包含 content 和 tool_calls 的响应字典
        """
        try:
            use_model = model or self.model

            logger.info(f"调用智谱AI模型(工具调用): {use_model}, 工具数量: {len(tools)}")

            response = self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                thinking={"type": "enabled"} if thinking else {"type": "disabled"}
            )

            message = response.choices[0].message

            result = {
                "content": message.content if hasattr(message, 'content') else None,
                "tool_calls": []
            }

            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    })

            logger.info(f"工具调用响应: content长度={len(result['content'] or '')}, tool_calls数量={len(result['tool_calls'])}")

            return result

        except Exception as e:
            logger.error(f"工具调用AI模型失败: {str(e)}")
            raise

    async def chat_stream_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        thinking: bool = True
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        带工具调用的流式聊天

        Args:
            messages: 消息历史列表
            tools: 工具定义列表
            model: 模型名称
            thinking: 是否启用思考模式

        Yields:
            包含 content、tool_calls 或 reasoning_content 的字典
        """
        try:
            use_model = model or self.model

            logger.info(f"调用智谱AI模型(流式工具调用): {use_model}, 工具数量: {len(tools)}")

            response = self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                stream=True,
                tool_stream=True,
                thinking={"type": "enabled"} if thinking else {"type": "disabled"}
            )

            tool_calls_map: Dict[int, Dict[str, Any]] = {}
            current_content = ""

            for chunk in response:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    yield {"type": "reasoning", "content": delta.reasoning_content}

                if hasattr(delta, 'content') and delta.content:
                    current_content += delta.content
                    yield {"type": "content", "content": delta.content}

                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        index = tool_call.index
                        if index not in tool_calls_map:
                            tool_calls_map[index] = {
                                "id": tool_call.id,
                                "name": tool_call.function.name if hasattr(tool_call.function, 'name') else "",
                                "arguments": ""
                            }
                        if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                            tool_calls_map[index]["arguments"] += tool_call.function.arguments

            if tool_calls_map:
                yield {
                    "type": "tool_calls",
                    "tool_calls": list(tool_calls_map.values())
                }

            logger.info(f"流式工具调用完成, content长度={len(current_content)}, tool_calls数量={len(tool_calls_map)}")

        except Exception as e:
            logger.error(f"流式工具调用AI模型失败: {str(e)}")
            raise

    def set_model(self, model: str):
        """设置默认模型"""
        self.model = model
        logger.info(f"默认模型已设置为: {model}")


llm_service_global: Optional[LLMService] = None


def get_llm_service(api_key: str) -> LLMService:
    """
    获取LLM服务实例（单例模式）

    Args:
        api_key: 智谱AI API密钥

    Returns:
        LLMService实例
    """
    global llm_service_global

    if llm_service_global is None:
        llm_service_global = LLMService(api_key=api_key)
    else:
        llm_service_global.client = ZhipuAiClient(api_key=api_key)

    return llm_service_global
