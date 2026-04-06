from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.models.models import Session


async def ensure_runtime_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        # ── 列迁移（兼容旧数据库） ──────────────────────────────
        await _ensure_column(conn, "conversations", "session_id", "INTEGER")
        await _ensure_column(conn, "conversations", "rule", "TEXT")
        await _ensure_column(conn, "messages", "session_id", "INTEGER")
        await _ensure_column(conn, "long_term_memory", "session_id", "INTEGER")
        await _ensure_column(conn, "long_term_memory", "title", "VARCHAR")
        await _ensure_column(conn, "long_term_memory", "content_type", "VARCHAR NOT NULL DEFAULT 'note'")
        await _ensure_column(conn, "long_term_memory", "group_id", "VARCHAR")
        await _ensure_column(conn, "long_term_memory", "origin_message_id", "INTEGER")
        await _ensure_column(conn, "long_term_memory", "content_hash", "VARCHAR(255)")
        await _ensure_column(conn, "long_term_memory", "is_evergreen", "BOOLEAN DEFAULT 0")
        await _ensure_column(conn, "long_term_memory", "embedding_generated_at", "TIMESTAMP")
        await _ensure_column(conn, "tool_calls", "session_id", "INTEGER")
        await _ensure_column(conn, "agent_events", "session_id", "INTEGER")
        await _ensure_column(conn, "automations", "conversation_id", "INTEGER")
        await _ensure_column(conn, "automations", "timezone", "VARCHAR NOT NULL DEFAULT 'UTC'")
        await _ensure_column(conn, "automation_runs", "trigger_mode", "VARCHAR NOT NULL DEFAULT 'scheduled'")
        await _ensure_column(conn, "automation_runs", "conversation_id", "INTEGER")

        # ── 数据迁移 ────────────────────────────────────────────
        await _migrate_channel_session_to_conversation(conn)
        await _migrate_channel_chat_session_to_conversation(conn)

        # ── embedding_cache 表（ORM create_all 不处理此表的索引） ─
        await _ensure_embedding_cache(conn)

        # ── FTS5 全文搜索虚拟表 + 触发器 ─────────────────────────
        await _ensure_fts_tables(conn)


async def ensure_default_session(db: AsyncSession) -> Session:
    result = await db.execute(text("SELECT id, name FROM sessions WHERE is_default = 1 ORDER BY id LIMIT 1"))
    row = result.first()
    if row:
        # 迁移：已有 session 的 max_iterations 从旧默认值 5 提升到 30
        await db.execute(
            text("UPDATE sessions SET max_iterations = 30 WHERE max_iterations = 5"),
        )
        await db.commit()
        return await db.get(Session, row.id)

    workspace_path = os.getenv("MYCLAW_DEFAULT_WORKSPACE", str(Path.cwd()))
    session = Session(
        name="main",
        mode="personal",
        workspace_path=workspace_path,
        tool_profile="full",
        max_iterations=30,
        is_default=True,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    await db.execute(
        text("UPDATE conversations SET session_id = :session_id WHERE session_id IS NULL"),
        {"session_id": session.id},
    )
    await db.execute(
        text(
            """
            UPDATE messages
            SET session_id = :session_id
            WHERE session_id IS NULL
            """
        ),
        {"session_id": session.id},
    )
    await db.execute(
        text("UPDATE tool_calls SET session_id = :session_id WHERE session_id IS NULL"),
        {"session_id": session.id},
    )
    await db.execute(
        text("UPDATE agent_events SET session_id = :session_id WHERE session_id IS NULL"),
        {"session_id": session.id},
    )
    await db.execute(
        text("UPDATE long_term_memory SET session_id = :session_id WHERE session_id IS NULL"),
        {"session_id": session.id},
    )
    await db.commit()
    return session


async def _ensure_column(conn, table_name: str, column_name: str, column_sql: str) -> None:
    result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
    columns = {row[1] for row in result.fetchall()}
    if column_name not in columns:
        await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))


async def _ensure_embedding_cache(conn) -> None:
    """确保 embedding_cache 表及其索引存在。"""
    result = await conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='embedding_cache'")
    )
    if result.fetchone():
        return

    await conn.execute(text("""
        CREATE TABLE embedding_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_hash VARCHAR(255) NOT NULL UNIQUE,
            embedding BLOB NOT NULL,
            model VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 0
        )
    """))
    await conn.execute(text("""
        CREATE INDEX idx_embedding_cache_content_hash
        ON embedding_cache(content_hash)
    """))
    await conn.execute(text("""
        CREATE INDEX idx_embedding_cache_last_accessed
        ON embedding_cache(last_accessed_at)
    """))


async def _ensure_fts_tables(conn) -> None:
    """确保 FTS5 全文搜索虚拟表和同步触发器存在。"""
    # messages_fts
    result = await conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'")
    )
    if not result.fetchone():
        await conn.execute(text("""
            CREATE VIRTUAL TABLE messages_fts USING fts5(
                content,
                content='messages',
                content_rowid='id'
            )
        """))

    # long_term_memory_fts
    result = await conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='long_term_memory_fts'")
    )
    if not result.fetchone():
        await conn.execute(text("""
            CREATE VIRTUAL TABLE long_term_memory_fts USING fts5(
                content,
                content='long_term_memory',
                content_rowid='id'
            )
        """))

    # messages FTS5 触发器
    result = await conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='trigger' AND name='messages_fts_insert'")
    )
    if not result.fetchone():
        await conn.execute(text("""
            CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
            END
        """))
        await conn.execute(text("""
            CREATE TRIGGER messages_fts_update AFTER UPDATE ON messages BEGIN
                UPDATE messages_fts SET content = new.content WHERE rowid = new.id;
            END
        """))
        await conn.execute(text("""
            CREATE TRIGGER messages_fts_delete AFTER DELETE ON messages BEGIN
                DELETE FROM messages_fts WHERE rowid = old.id;
            END
        """))

    # long_term_memory FTS5 触发器
    result = await conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='trigger' AND name='long_term_memory_fts_insert'")
    )
    if not result.fetchone():
        await conn.execute(text("""
            CREATE TRIGGER long_term_memory_fts_insert AFTER INSERT ON long_term_memory BEGIN
                INSERT INTO long_term_memory_fts(rowid, content) VALUES (new.id, new.content);
            END
        """))
        await conn.execute(text("""
            CREATE TRIGGER long_term_memory_fts_update AFTER UPDATE ON long_term_memory BEGIN
                UPDATE long_term_memory_fts SET content = new.content WHERE rowid = new.id;
            END
        """))
        await conn.execute(text("""
            CREATE TRIGGER long_term_memory_fts_delete AFTER DELETE ON long_term_memory BEGIN
                DELETE FROM long_term_memory_fts WHERE rowid = old.id;
            END
        """))


async def _migrate_channel_session_to_conversation(conn) -> None:
    """迁移 channels 表的 session_id 列到 conversation_id。

    SQLite 不支持列重命名（含外键约束），所以：
    1. 如果已有 conversation_id 列且无 session_id 列 → 已迁移，跳过
    2. 如果已有 session_id 列且无 conversation_id 列 → 添加 conversation_id，清空 session_id
    3. 如果两者都存在 → 添加 conversation_id（已有），清空 session_id
    4. 如果都不存在 → 新表，由 CREATE TABLE 处理
    """
    result = await conn.execute(text("PRAGMA table_info(channels)"))
    columns = {row[1] for row in result.fetchall()}

    if "conversation_id" not in columns:
        await conn.execute(
            text("ALTER TABLE channels ADD COLUMN conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL")
        )

    if "session_id" in columns:
        # 清除旧列数据（保留列结构以避免 SQLite 重建表的复杂性）
        await conn.execute(text("UPDATE channels SET session_id = NULL"))


async def _migrate_channel_chat_session_to_conversation(conn) -> None:
    """迁移 channel_chats 表，移除 session_id 残留。"""
    result = await conn.execute(text("PRAGMA table_info(channel_chats)"))
    columns = {row[1] for row in result.fetchall()}

    if "session_id" in columns:
        await conn.execute(text("UPDATE channel_chats SET session_id = NULL"))
