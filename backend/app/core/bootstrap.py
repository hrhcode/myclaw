from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.models.models import Session


async def ensure_runtime_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL UNIQUE,
                    mode VARCHAR NOT NULL DEFAULT 'personal',
                    workspace_path VARCHAR,
                    model VARCHAR,
                    provider VARCHAR,
                    tool_profile VARCHAR NOT NULL DEFAULT 'full',
                    tool_allow TEXT,
                    tool_deny TEXT,
                    max_iterations INTEGER NOT NULL DEFAULT 5,
                    context_summary TEXT,
                    memory_auto_extract BOOLEAN NOT NULL DEFAULT 0,
                    memory_threshold INTEGER NOT NULL DEFAULT 8,
                    is_default BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        await _ensure_column(conn, "conversations", "session_id", "INTEGER")
        await _ensure_column(conn, "messages", "session_id", "INTEGER")
        await _ensure_column(conn, "long_term_memory", "session_id", "INTEGER")
        await _ensure_column(conn, "tool_calls", "session_id", "INTEGER")
        await _ensure_column(conn, "agent_events", "session_id", "INTEGER")
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS session_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    skill_name VARCHAR NOT NULL,
                    skill_path VARCHAR NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS automations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL,
                    session_id INTEGER NOT NULL,
                    prompt TEXT NOT NULL,
                    schedule_type VARCHAR NOT NULL,
                    schedule_value VARCHAR NOT NULL,
                    timezone VARCHAR NOT NULL DEFAULT 'UTC',
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    last_run_at DATETIME,
                    next_run_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS automation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    automation_id INTEGER NOT NULL,
                    session_id INTEGER NOT NULL,
                    status VARCHAR NOT NULL DEFAULT 'pending',
                    trigger_mode VARCHAR NOT NULL DEFAULT 'scheduled',
                    triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    error TEXT,
                    run_id VARCHAR,
                    FOREIGN KEY(automation_id) REFERENCES automations(id) ON DELETE CASCADE,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )
        )
        await _ensure_column(conn, "automations", "timezone", "VARCHAR NOT NULL DEFAULT 'UTC'")
        await _ensure_column(conn, "automation_runs", "trigger_mode", "VARCHAR NOT NULL DEFAULT 'scheduled'")
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id VARCHAR NOT NULL UNIQUE,
                    session_id INTEGER NOT NULL,
                    conversation_id INTEGER NOT NULL,
                    user_message TEXT NOT NULL,
                    stop_reason VARCHAR,
                    compacted_summary TEXT,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
                """
            )
        )


async def ensure_default_session(db: AsyncSession) -> Session:
    result = await db.execute(text("SELECT id, name FROM sessions WHERE is_default = 1 ORDER BY id LIMIT 1"))
    row = result.first()
    if row:
        return await db.get(Session, row.id)

    workspace_path = os.getenv("MYCLAW_DEFAULT_WORKSPACE", str(Path.cwd()))
    session = Session(
        name="main",
        mode="personal",
        workspace_path=workspace_path,
        tool_profile="full",
        max_iterations=5,
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
