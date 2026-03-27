"""
记忆摘要生成服务
从对话中提取重要信息并生成摘要
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Message, Conversation

logger = logging.getLogger(__name__)

LOG_SEPARATOR = "─" * 40


class MemorySummarizer:
    """
    记忆摘要生成器
    """
    
    def __init__(self):
        """
        初始化记忆摘要生成器
        """
        self.importance_keywords = [
            "重要", "关键", "必须", "记住", "不要忘记",
            "重要信息", "关键信息", "核心", "主要",
            "prefer", "like", "want", "need", "require",
            "设置", "配置", "选项", "参数", "偏好"
        ]
    
    def calculate_importance_score(self, text: str) -> float:
        """
        计算文本的重要性分数
        
        Args:
            text: 文本内容
            
        Returns:
            重要性分数 (0.0-1.0)
        """
        if not text:
            return 0.0
        
        score = 0.0
        text_lower = text.lower()
        
        for keyword in self.importance_keywords:
            if keyword.lower() in text_lower:
                score += 0.1
        
        if "？" in text or "?" in text:
            score += 0.05
        
        if "！" in text or "!" in text:
            score += 0.05
        
        if len(text.split()) > 20:
            score += 0.1
        
        final_score = min(score, 1.0)
        logger.debug(f"[重要性计算] 文本: {text[:30]}... -> 分数: {final_score:.2f}")
        return final_score
    
    def extract_key_information(self, messages: List[Message]) -> List[Dict]:
        """
        从消息中提取关键信息
        
        Args:
            messages: 消息列表
            
        Returns:
            关键信息列表
        """
        logger.info(f"[关键信息提取] 开始从 {len(messages)} 条消息中提取关键信息")
        
        key_info = []
        
        for msg in messages:
            importance = self.calculate_importance_score(msg.content)
            
            if importance > 0.3:
                key_info.append({
                    "content": msg.content,
                    "role": msg.role,
                    "importance": importance,
                    "created_at": msg.created_at,
                    "message_id": msg.id
                })
                logger.debug(f"[关键信息提取] 发现重要信息 (分数: {importance:.2f}): {msg.content[:50]}...")
        
        key_info.sort(key=lambda x: x["importance"], reverse=True)
        
        logger.info(f"[关键信息提取] 完成，提取到 {len(key_info)} 条关键信息")
        return key_info
    
    def generate_summary(self, key_info: List[Dict], max_items: int = 5) -> List[Dict]:
        """
        生成摘要
        
        Args:
            key_info: 关键信息列表
            max_items: 最大摘要项数
            
        Returns:
            摘要列表
        """
        if not key_info:
            logger.debug("[摘要生成] 无关键信息，返回空摘要")
            return []
        
        logger.info(f"[摘要生成] 开始生成摘要，最大项数: {max_items}")
        
        summary = key_info[:max_items]
        
        for item in summary:
            content = item["content"]
            
            if len(content) > 200:
                item["summary"] = content[:200] + "..."
            else:
                item["summary"] = content
            
            item["importance_display"] = f"{item['importance']:.2f}"
        
        logger.info(f"[摘要生成] 完成，生成 {len(summary)} 条摘要")
        for i, item in enumerate(summary, 1):
            logger.debug(f"  #{i}: 分数={item['importance']:.2f}, 内容={item['summary'][:30]}...")
        
        return summary
    
    async def extract_memory_from_conversation(
        self,
        db: AsyncSession,
        conversation_id: int,
        max_memories: int = 5
    ) -> List[Dict]:
        """
        从会话中提取记忆
        
        Args:
            db: 数据库会话
            conversation_id: 会话ID
            max_memories: 最大记忆数量
            
        Returns:
            记忆列表
        """
        logger.info(LOG_SEPARATOR)
        logger.info(f"[记忆提取] 开始从会话 {conversation_id} 提取记忆")
        
        try:
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(50)
            )
            messages = result.scalars().all()
            
            logger.info(f"[记忆提取] 获取到 {len(messages)} 条最近消息")
            
            key_info = self.extract_key_information(messages)
            summary = self.generate_summary(key_info, max_items=max_memories)
            
            logger.info(f"[记忆提取] 完成，提取 {len(summary)} 条记忆")
            logger.info(LOG_SEPARATOR)
            
            return summary
        except Exception as e:
            logger.error(f"[记忆提取] 失败: {str(e)}")
            return []
    
    def format_memory_for_storage(self, summary_item: Dict) -> str:
        """
        格式化记忆用于存储
        
        Args:
            summary_item: 摘要项
            
        Returns:
            格式化的记忆文本
        """
        role = summary_item.get("role", "user")
        content = summary_item.get("summary", "")
        
        if role == "user":
            return f"用户提到: {content}"
        else:
            return f"系统/助手: {content}"


async def get_memory_summarizer() -> MemorySummarizer:
    """
    获取记忆摘要生成器实例
    
    Returns:
        MemorySummarizer 实例
    """
    return MemorySummarizer()
