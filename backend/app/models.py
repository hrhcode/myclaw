from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# 会话模型
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关联消息
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

# 消息模型
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联会话
    conversation = relationship("Conversation", back_populates="messages")
