from zai import ZhipuAiClient
from typing import List, Dict, AsyncIterator, Optional
import logging

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