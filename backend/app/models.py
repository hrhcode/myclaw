from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, LargeBinary, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


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
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(LargeBinary, nullable=True)
    embedding_model = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    conversation = relationship("Conversation", back_populates="messages")

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
