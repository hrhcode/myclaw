from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, LargeBinary, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    mode = Column(String, nullable=False, default="personal")
    workspace_path = Column(String, nullable=True)
    model = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    tool_profile = Column(String, nullable=False, default="full")
    tool_allow = Column(Text, nullable=True)
    tool_deny = Column(Text, nullable=True)
    max_iterations = Column(Integer, nullable=False, default=5)
    context_summary = Column(Text, nullable=True)
    memory_auto_extract = Column(Boolean, nullable=False, default=False)
    memory_threshold = Column(Integer, nullable=False, default=8)
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    conversations = relationship("Conversation", back_populates="session")
    enabled_skills = relationship("SessionSkill", back_populates="session", cascade="all, delete-orphan")
    automations = relationship("Automation", back_populates="session", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="session", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    session = relationship("Session", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
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
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
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
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
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
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
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


class SessionSkill(Base):
    __tablename__ = "session_skills"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String, nullable=False, index=True)
    skill_path = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    session = relationship("Session", back_populates="enabled_skills")


class Automation(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    schedule_type = Column(String, nullable=False)
    schedule_value = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    session = relationship("Session", back_populates="automations")
    runs = relationship("AutomationRun", back_populates="automation", cascade="all, delete-orphan")


class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id = Column(Integer, primary_key=True, index=True)
    automation_id = Column(Integer, ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    run_id = Column(String, nullable=True, index=True)

    automation = relationship("Automation", back_populates="runs")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, nullable=False, unique=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    stop_reason = Column(String, nullable=True)
    compacted_summary = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("Session", back_populates="agent_runs")
