"""
[已弃用] 此迁移脚本的逻辑已全部吸收至 app/core/bootstrap.py。

启动时 bootstrap.ensure_runtime_schema() 会自动处理：
- embedding_cache 表及索引创建
- long_term_memory 新列（content_hash, is_evergreen, embedding_generated_at）
- FTS5 虚拟表（messages_fts, long_term_memory_fts）及同步触发器

此脚本保留仅供调试参考，不再需要手动执行。
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


async def migrate():
    """
    执行数据库迁移
    """
    async with engine.begin() as conn:
        try:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='embedding_cache'"))
            if result.fetchone():
                print("嵌入缓存表已存在，跳过创建")
            else:
                print("创建嵌入缓存表...")
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
                
                print("创建索引...")
                await conn.execute(text("""
                    CREATE INDEX idx_embedding_cache_content_hash 
                    ON embedding_cache(content_hash)
                """))
                await conn.execute(text("""
                    CREATE INDEX idx_embedding_cache_last_accessed 
                    ON embedding_cache(last_accessed_at)
                """))
        except Exception as e:
            print(f"创建嵌入缓存表时出错: {e}")
        
        try:
            result = await conn.execute(text("PRAGMA table_info(long_term_memory)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'content_hash' not in columns:
                print("添加长期记忆content_hash字段...")
                await conn.execute(text("""
                    ALTER TABLE long_term_memory 
                    ADD COLUMN content_hash VARCHAR(255)
                """))
            
            if 'is_evergreen' not in columns:
                print("添加长期记忆is_evergreen字段...")
                await conn.execute(text("""
                    ALTER TABLE long_term_memory 
                    ADD COLUMN is_evergreen BOOLEAN DEFAULT 0
                """))
            
            if 'embedding_generated_at' not in columns:
                print("添加长期记忆embedding_generated_at字段...")
                await conn.execute(text("""
                    ALTER TABLE long_term_memory 
                    ADD COLUMN embedding_generated_at TIMESTAMP
                """))
        except Exception as e:
            print(f"添加长期记忆字段时出错: {e}")
        
        try:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'"))
            if result.fetchone():
                print("messages_fts表已存在，跳过创建")
            else:
                print("为Message表添加FTS5全文搜索...")
                await conn.execute(text("""
                    CREATE VIRTUAL TABLE messages_fts USING fts5(
                        content, 
                        content='messages', 
                        content_rowid='id'
                    )
                """))
        except Exception as e:
            print(f"创建messages_fts表时出错: {e}")
        
        try:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='long_term_memory_fts'"))
            if result.fetchone():
                print("long_term_memory_fts表已存在，跳过创建")
            else:
                print("为LongTermMemory表添加FTS5全文搜索...")
                await conn.execute(text("""
                    CREATE VIRTUAL TABLE long_term_memory_fts USING fts5(
                        content, 
                        content='long_term_memory', 
                        content_rowid='id'
                    )
                """))
        except Exception as e:
            print(f"创建long_term_memory_fts表时出错: {e}")
        
        try:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='trigger' AND name='messages_fts_insert'"))
            if result.fetchone():
                print("messages_fts_insert触发器已存在，跳过创建")
            else:
                print("创建FTS5触发器...")
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
        except Exception as e:
            print(f"创建messages FTS5触发器时出错: {e}")
        
        try:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='trigger' AND name='long_term_memory_fts_insert'"))
            if result.fetchone():
                print("long_term_memory_fts_insert触发器已存在，跳过创建")
            else:
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
        except Exception as e:
            print(f"创建long_term_memory FTS5触发器时出错: {e}")
        
        print("\n迁移完成！")
        
        print("\n验证迁移结果...")
        
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='embedding_cache'"))
        print(f"✓ embedding_cache表: {'存在' if result.fetchone() else '不存在'}")
        
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts'"))
        print(f"✓ messages_fts表: {'存在' if result.fetchone() else '不存在'}")
        
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='long_term_memory_fts'"))
        print(f"✓ long_term_memory_fts表: {'存在' if result.fetchone() else '不存在'}")
        
        result = await conn.execute(text("PRAGMA table_info(long_term_memory)"))
        columns = [row[1] for row in result.fetchall()]
        print(f"✓ long_term_memory新字段: content_hash={('存在' if 'content_hash' in columns else '不存在')}, is_evergreen={('存在' if 'is_evergreen' in columns else '不存在')}, embedding_generated_at={('存在' if 'embedding_generated_at' in columns else '不存在')}")


if __name__ == "__main__":
    asyncio.run(migrate())
