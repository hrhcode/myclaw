"""
存储模块
提供统一的数据库存储管理
"""

from app.storage.database import Database, get_database

__all__ = ["Database", "get_database"]
