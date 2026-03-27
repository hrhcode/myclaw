"""
数据库迁移脚本：添加嵌入缓存、长期记忆扩展字段和FTS5全文搜索
运行方式：python -m migrations.add_embedding_cache
"""
import asyncio
from sqlalchemy import text
from app.database import engine, Base


async def migrate():
    """
    执行数据库迁移
    """
    async with engine.begin() as conn:
        # 为long_term_memory表添加新字段
        print("添加长期记忆扩展字段...")
        await conn.execute(text("""
            ALTER TABLE long_term_memory 
            ADD COLUMN IF NOT EXISTS content_hash VARCHAR(255) UNIQUE
        """))
        await conn.execute(text("""
            ALTER TABLE long_term_memory 
            ADD COLUMN IF NOT EXISTS is_evergreen BOOLEAN DEFAULT 0
        """))
        await conn.execute(text("""
            ALTER TABLE long_term_memory 
            ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMP
        """))
        
        # 创建嵌入缓存表
        print("创建嵌入缓存表...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS embedding_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash VARCHAR(255) NOT NULL UNIQUE,
                embedding BLOB NOT NULL,
                model VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """))
        
        # 创建索引
        print("创建索引...")
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_embedding_cache_content_hash 
            ON embedding_cache(content_hash)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_embedding_cache_last_accessed 
            ON embedding_cache(last_accessed_at)
        """))
        
        # 为Message表添加FTS5全文搜索
        print("为Message表添加FTS5全文搜索...")
        await conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                content, 
                content='messages', 
                content_rowid='id'
            )
        """))
        
        # 为LongTermMemory表添加FTS5全文搜索
        print("为LongTermMemory表添加FTS5全文搜索...")
        await conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS long_term_memory_fts USING fts5(
                content, 
                content='long_term_memory', 
                content_rowid='id'
            )
        """))
        
        # 创建FTS5触发器以保持索引同步
        print("创建FTS5触发器...")
        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
            END
        """))
        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
                UPDATE messages_fts SET content = new.content WHERE rowid = new.id;
            END
        """))
        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
                DELETE FROM messages_fts WHERE rowid = old.id;
            END
        """))
        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS long_term_memory_fts_insert AFTER INSERT ON long_term_memory BEGIN
                INSERT INTO long_term_memory_fts(rowid, content) VALUES (new.id, new.content);
            END
        """))
        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS long_term_memory_fts_update AFTER UPDATE ON long_term_memory BEGIN
                UPDATE long_term_memory_fts SET content = new.content WHERE rowid = new.id;
            END
        """))
        await conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS long_term_memory_fts_delete AFTER DELETE ON long_term_memory BEGIN
                DELETE FROM long_term_memory_fts WHERE rowid = old.id;
            END
        """))
        
        print("迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
