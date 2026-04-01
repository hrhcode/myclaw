from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, LargeBinary, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(LargeBinary, nullable=True)
    embedding_model = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    conversation = relationship("Conversation", back_populates="messages")
    tool_calls = relationship("ToolCall", back_populates="message", cascade="all, delete-orphan")
    agent_events = relationship("AgentEvent", back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        {"sqlite_autoincrement": True}
    )


class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(String, nullable=False)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LongTermMemory(Base):
    __tablename__ = "long_term_memory"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=True)
    content = Column(String, nullable=False)
    embedding = Column(LargeBinary, nullable=True)
    embedding_model = Column(String, nullable=True)
    importance = Column(Float, default=0.5)
    source = Column(String, nullable=True)
    content_hash = Column(String, nullable=True, unique=True)
    is_evergreen = Column(Boolean, default=False)
    embedding_generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EmbeddingCache(Base):
    __tablename__ = "embedding_cache"

    id = Column(Integer, primary_key=True, index=True)
    content_hash = Column(String, nullable=False, unique=True, index=True)
    embedding = Column(LargeBinary, nullable=False)
    model = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    access_count = Column(Integer, default=0)


class Log(Base):
    """
    日志记录模型
    用于持久化存储系统日志，支持历史查询和分析
    """
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, nullable=False, index=True)
    level = Column(String, nullable=False, index=True)
    logger = Column(String, nullable=False)
    message = Column(String, nullable=False)
    extra = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        {"sqlite_autoincrement": True}
    )


class ToolCall(Base):
    """
    工具调用记录模型
    用于记录 AI 工具调用的历史，便于调试和分析
    """
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String, nullable=False, index=True)
    tool_call_id = Column(String, nullable=False)
    arguments = Column(String, nullable=False)
    result = Column(String, nullable=True)
    status = Column(String, default="pending", index=True)
    error = Column(String, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    message = relationship("Message", back_populates="tool_calls")
    conversation = relationship("Conversation")

    __table_args__ = (
        {"sqlite_autoincrement": True}
    )


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    payload = Column(String, nullable=False)
    sequence = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    message = relationship("Message", back_populates="agent_events")
    conversation = relationship("Conversation")

    __table_args__ = (
        {"sqlite_autoincrement": True}
    )
