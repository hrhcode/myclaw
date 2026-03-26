from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库URL
DATABASE_URL = "sqlite+aiosqlite:///./chat.db"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 创建基类
Base = declarative_base()

# 获取数据库会话的依赖项
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
