"""
自动记忆管理服务
在会话接近上下文压缩时，自动提醒模型保存重要信息到长期记忆
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Message, Conversation, LongTermMemory
from app.common.config import get_config_value
from app.common.constants import (
    AUTO_MEMORY_FLUSH_ENABLED,
    AUTO_MEMORY_FLUSH_THRESHOLD,
    LOG_SEPARATOR_SHORT,
)
from app.common.utils.text import estimate_tokens

logger = logging.getLogger(__name__)


class MemoryFlushService:
    """
    自动记忆刷新服务
    """
    
    def __init__(self, threshold_tokens: int = 4000):
        """
        初始化记忆刷新服务
        
        Args:
            threshold_tokens: 触发记忆刷新的token阈值
        """
        self.threshold_tokens = threshold_tokens
    
    async def get_conversation_tokens(self, db: AsyncSession, conversation_id: int) -> int:
        """
        获取会话的token数量
        
        Args:
            db: 数据库会话
            conversation_id: 会话ID
            
        Returns:
            会话的token数量
        """
        try:
            result = await db.execute(
                select(Message).where(Message.conversation_id == conversation_id)
            )
            messages = result.scalars().all()
            
            total_tokens = 0
            for msg in messages:
                total_tokens += self.estimate_tokens(msg.content)
            
            logger.debug(f"[Token统计] 会话 {conversation_id} 共 {len(messages)} 条消息，约 {total_tokens} tokens")
            return int(total_tokens)
        except Exception as e:
            logger.error(f"[Token统计] 获取会话token数量失败: {str(e)}")
            return 0
    
    async def should_flush_memory(self, db: AsyncSession, conversation_id: int) -> bool:
        """
        判断是否应该触发记忆刷新
        
        Args:
            db: 数据库会话
            conversation_id: 会话ID
            
        Returns:
            是否应该触发记忆刷新
        """
        conversation_tokens = await self.get_conversation_tokens(db, conversation_id)
        should_flush = conversation_tokens >= self.threshold_tokens
        
        if should_flush:
            logger.info(f"[记忆刷新] 触发条件满足！当前: {conversation_tokens} tokens >= 阈值: {self.threshold_tokens}")
        else:
            logger.debug(f"[记忆刷新] 未达阈值，当前: {conversation_tokens} tokens < 阈值: {self.threshold_tokens}")
        
        return should_flush
    
    async def get_recent_messages(self, db: AsyncSession, conversation_id: int, limit: int = 20) -> List[Message]:
        """
        获取最近的消息
        
        Args:
            db: 数据库会话
            conversation_id: 会话ID
            limit: 返回消息数量
            
        Returns:
            最近的消息列表
        """
        try:
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            messages = result.scalars().all()
            logger.debug(f"[消息获取] 获取会话 {conversation_id} 最近 {len(messages)} 条消息")
            return list(messages)
        except Exception as e:
            logger.error(f"[消息获取] 获取最近消息失败: {str(e)}")
            return []
    
    async def create_memory_flush_prompt(self, db: AsyncSession, conversation_id: int) -> Optional[str]:
        """
        创建记忆刷新提示
        
        Args:
            db: 数据库会话
            conversation_id: 会话ID
            
        Returns:
            记忆刷新提示文本
        """
        logger.info(LOG_SEPARATOR)
        logger.info(f"[记忆刷新] 为会话 {conversation_id} 创建记忆刷新提示")
        
        try:
            recent_messages = await self.get_recent_messages(db, conversation_id, limit=20)
            
            if not recent_messages:
                logger.warning("[记忆刷新] 无最近消息，跳过刷新提示")
                return None
            
            context = "\n".join([f"{msg.role}: {msg.content}" for msg in recent_messages])
            
            prompt = f"""<no_reply>
请回顾以下对话历史，识别并保存重要信息到长期记忆。

对话历史：
{context}

请执行以下操作：
1. 识别对话中的关键信息、重要决策、用户偏好等
2. 使用 /memory/create 接口将这些信息保存为长期记忆
3. 为每条记忆设置适当的importance值（0.0-1.0）
4. 使用简洁清晰的语言描述记忆内容

完成后，请忽略此提示，继续正常对话。
</no_reply>"""
            
            logger.info(f"[记忆刷新] 提示创建成功，上下文长度: {len(context)} 字符")
            logger.info(LOG_SEPARATOR)
            
            return prompt
        except Exception as e:
            logger.error(f"[记忆刷新] 创建记忆刷新提示失败: {str(e)}")
            return None


async def get_memory_flush_service(db: AsyncSession) -> Optional[MemoryFlushService]:
    """
    获取记忆刷新服务实例
    
    Args:
        db: 数据库会话
        
    Returns:
        MemoryFlushService 实例，未启用返回 None
    """
    enabled = await get_config_value(db, AUTO_MEMORY_FLUSH_ENABLED)
    if enabled is None:
        enabled = True
    
    if not enabled:
        logger.debug("[记忆刷新服务] 服务未启用")
        return None
    
    threshold = await get_config_value(db, AUTO_MEMORY_FLUSH_THRESHOLD)
    if threshold is None:
        threshold = 4000
    
    logger.debug(f"[记忆刷新服务] 服务已启用，阈值: {threshold} tokens")
    return MemoryFlushService(threshold_tokens=threshold)
