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
        
        return min(score, 1.0)
    
    def extract_key_information(self, messages: List[Message]) -> List[Dict]:
        """
        从消息中提取关键信息
        
        Args:
            messages: 消息列表
            
        Returns:
            关键信息列表
        """
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
        
        key_info.sort(key=lambda x: x["importance"], reverse=True)
        
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
            return []
        
        summary = key_info[:max_items]
        
        for item in summary:
            content = item["content"]
            
            if len(content) > 200:
                item["summary"] = content[:200] + "..."
            else:
                item["summary"] = content
            
            item["importance_display"] = f"{item['importance']:.2f}"
        
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
        try:
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(50)
            )
            messages = result.scalars().all()
            
            key_info = self.extract_key_information(messages)
            summary = self.generate_summary(key_info, max_items=max_memories)
            
            return summary
        except Exception as e:
            logger.error(f"提取记忆失败: {str(e)}")
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
