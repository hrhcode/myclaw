from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event

DATABASE_URL = "sqlite+aiosqlite:///./chat.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    在SQLite连接时启用外键约束
    SQLite默认不启用外键约束，需要手动启用
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async_session = AsyncSessionLocal

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
