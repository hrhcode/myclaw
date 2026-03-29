"""
日志服务模块 - 提供 WebSocket 日志推送和数据库持久化功能
"""
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional
from collections import deque
from fastapi import WebSocket
from sqlalchemy import select, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.models import Log
from app.common.constants import (
    MAX_LOG_BUFFER_SIZE,
    LOG_RETENTION_DAYS,
    LOG_MAX_RECORDS,
    LOG_CLEANUP_INTERVAL_HOURS,
)


class LogEntry:
    """
    日志条目数据结构
    用于内存缓冲和 WebSocket 推送
    """
    
    def __init__(self, timestamp: str, level: str, logger: str, message: str, extra: Optional[dict] = None):
        self.timestamp = timestamp
        self.level = level
        self.logger = logger
        self.message = message
        self.extra = extra or {}
    
    def to_dict(self) -> dict:
        """
        转换为字典格式
        
        Returns:
            包含日志信息的字典
        """
        result = {
            "timestamp": self.timestamp,
            "level": self.level,
            "logger": self.logger,
            "message": self.message,
        }
        if self.extra:
            result["extra"] = self.extra
        return result
    
    def to_json(self) -> str:
        """
        转换为 JSON 字符串
        
        Returns:
            JSON 格式的日志字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)


class WebSocketLogHandler(logging.Handler):
    """
    WebSocket 日志处理器
    将日志推送到所有连接的 WebSocket 客户端
    """
    
    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)
        self._connections: set[WebSocket] = set()
        self._log_buffer: deque[LogEntry] = deque(maxlen=MAX_LOG_BUFFER_SIZE)
        self._level_filter: int = logging.DEBUG
        self._lock = asyncio.Lock()
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        处理日志记录
        
        Args:
            record: Python 标准日志记录对象
        """
        if record.levelno < self._level_filter:
            return
        
        try:
            timestamp = datetime.fromtimestamp(record.created).isoformat()
            level = record.levelname
            logger = record.name
            message = self.format(record)
            
            extra = {}
            if hasattr(record, 'user_id'):
                extra['user_id'] = record.user_id
            if hasattr(record, 'conversation_id'):
                extra['conversation_id'] = record.conversation_id
            
            log_entry = LogEntry(timestamp, level, logger, message, extra if extra else None)
            
            self._log_buffer.append(log_entry)
            
            asyncio.create_task(self._broadcast_log(log_entry))
            
        except Exception:
            self.handleError(record)
    
    async def _broadcast_log(self, log_entry: LogEntry) -> None:
        """
        广播日志到所有连接的 WebSocket 客户端
        
        Args:
            log_entry: 日志条目
        """
        if not self._connections:
            return
        
        message = json.dumps({
            "type": "log",
            "data": log_entry.to_dict()
        }, ensure_ascii=False)
        
        disconnected = set()
        for websocket in self._connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.add(websocket)
        
        for ws in disconnected:
            self._connections.discard(ws)
    
    def add_connection(self, websocket: WebSocket) -> None:
        """
        添加 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接对象
        """
        self._connections.add(websocket)
    
    def remove_connection(self, websocket: WebSocket) -> None:
        """
        移除 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接对象
        """
        self._connections.discard(websocket)
    
    def get_history(self, level: Optional[str] = None, limit: int = 100) -> list[dict]:
        """
        获取内存缓冲中的历史日志
        
        Args:
            level: 日志级别过滤（可选）
            limit: 返回条数限制
        
        Returns:
            日志列表
        """
        logs = list(self._log_buffer)
        
        if level:
            level_upper = level.upper()
            logs = [log for log in logs if log.level == level_upper]
        
        return [log.to_dict() for log in logs[-limit:]]
    
    def set_level_filter(self, level: str) -> None:
        """
        设置日志级别过滤
        
        Args:
            level: 日志级别名称（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        self._level_filter = level_map.get(level.upper(), logging.DEBUG)
    
    @property
    def connection_count(self) -> int:
        """
        当前连接数
        
        Returns:
            WebSocket 连接数量
        """
        return len(self._connections)


class DatabaseLogHandler(logging.Handler):
    """
    数据库日志处理器
    将日志持久化存储到 SQLite 数据库
    """
    
    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)
        self._log_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        处理日志记录，添加到队列等待写入数据库
        
        Args:
            record: Python 标准日志记录对象
        """
        try:
            timestamp = datetime.fromtimestamp(record.created).isoformat()
            level = record.levelname
            logger = record.name
            message = self.format(record)
            
            extra = {}
            if hasattr(record, 'user_id'):
                extra['user_id'] = record.user_id
            if hasattr(record, 'conversation_id'):
                extra['conversation_id'] = record.conversation_id
            
            log_data = {
                "timestamp": timestamp,
                "level": level,
                "logger": logger,
                "message": message,
                "extra": json.dumps(extra, ensure_ascii=False) if extra else None
            }
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._log_queue.put(log_data))
            except RuntimeError:
                pass
            
        except Exception:
            self.handleError(record)
    
    async def start(self) -> None:
        """
        启动日志写入任务
        """
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
    
    async def stop(self) -> None:
        """
        停止日志写入任务
        """
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
    
    async def _process_queue(self) -> None:
        """
        处理日志队列，批量写入数据库
        """
        while self._running:
            try:
                batch = []
                try:
                    log_data = await asyncio.wait_for(self._log_queue.get(), timeout=1.0)
                    batch.append(log_data)
                    
                    while not self._log_queue.empty() and len(batch) < 100:
                        batch.append(await self._log_queue.get())
                    
                except asyncio.TimeoutError:
                    continue
                
                if batch:
                    await self._write_batch(batch)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"日志写入队列处理错误: {e}")
    
    async def _write_batch(self, batch: list[dict]) -> None:
        """
        批量写入日志到数据库
        
        Args:
            batch: 日志数据列表
        """
        try:
            async with AsyncSessionLocal() as session:
                for log_data in batch:
                    log_entry = Log(
                        timestamp=log_data["timestamp"],
                        level=log_data["level"],
                        logger=log_data["logger"],
                        message=log_data["message"],
                        extra=log_data["extra"]
                    )
                    session.add(log_entry)
                await session.commit()
        except Exception as e:
            logging.error(f"日志批量写入数据库失败: {e}")


class LogService:
    """
    日志服务
    提供日志查询、清理等功能
    """
    
    @staticmethod
    async def get_logs(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        level: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        order: str = "desc"
    ) -> dict:
        """
        查询历史日志
        
        Args:
            session: 数据库会话
            page: 页码
            page_size: 每页条数
            level: 日志级别过滤
            keyword: 关键词搜索
            start_time: 开始时间
            end_time: 结束时间
            order: 排序方式（asc/desc）
        
        Returns:
            包含分页日志数据的字典
        """
        query = select(Log)
        count_query = select(func.count(Log.id))
        
        if level:
            query = query.where(Log.level == level.upper())
            count_query = count_query.where(Log.level == level.upper())
        
        if keyword:
            keyword_filter = or_(
                Log.message.contains(keyword),
                Log.logger.contains(keyword)
            )
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)
        
        if start_time:
            query = query.where(Log.timestamp >= start_time)
            count_query = count_query.where(Log.timestamp >= start_time)
        
        if end_time:
            query = query.where(Log.timestamp <= end_time)
            count_query = count_query.where(Log.timestamp <= end_time)
        
        if order == "desc":
            query = query.order_by(Log.timestamp.desc())
        else:
            query = query.order_by(Log.timestamp.asc())
        
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await session.execute(query)
        logs = result.scalars().all()
        
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0
        
        items = []
        for log in logs:
            items.append({
                "id": log.id,
                "timestamp": log.timestamp,
                "level": log.level,
                "logger": log.logger,
                "message": log.message,
                "extra": json.loads(log.extra) if log.extra else None,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    @staticmethod
    async def cleanup_old_logs(
        session: AsyncSession,
        retention_days: int = LOG_RETENTION_DAYS,
        max_records: int = LOG_MAX_RECORDS
    ) -> dict:
        """
        清理过期日志
        
        Args:
            session: 数据库会话
            retention_days: 日志保留天数
            max_records: 最大日志条数
        
        Returns:
            清理结果统计
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cutoff_str = cutoff_date.isoformat()
        
        delete_stmt = delete(Log).where(Log.timestamp < cutoff_str)
        result = await session.execute(delete_stmt)
        deleted_by_date = result.rowcount
        
        count_result = await session.execute(select(func.count(Log.id)))
        current_count = count_result.scalar() or 0
        
        deleted_by_count = 0
        if current_count > max_records:
            excess = current_count - max_records
            
            oldest_query = select(Log.id).order_by(Log.timestamp.asc()).limit(excess)
            oldest_result = await session.execute(oldest_query)
            oldest_ids = [row[0] for row in oldest_result.fetchall()]
            
            if oldest_ids:
                delete_excess_stmt = delete(Log).where(Log.id.in_(oldest_ids))
                excess_result = await session.execute(delete_excess_stmt)
                deleted_by_count = excess_result.rowcount
        
        await session.commit()
        
        return {
            "deleted_by_date": deleted_by_date,
            "deleted_by_count": deleted_by_count,
            "total_deleted": deleted_by_date + deleted_by_count,
            "retention_days": retention_days,
            "max_records": max_records
        }
    
    @staticmethod
    async def cleanup_keep_recent(
        session: AsyncSession,
        keep_count: int
    ) -> dict:
        """
        保留最近 N 条日志，删除其余所有日志
        
        Args:
            session: 数据库会话
            keep_count: 保留的日志条数
        
        Returns:
            清理结果统计
        """
        count_result = await session.execute(select(func.count(Log.id)))
        total_count = count_result.scalar() or 0
        
        if total_count <= keep_count:
            await session.commit()
            return {
                "total_before": total_count,
                "total_after": total_count,
                "deleted_count": 0,
                "keep_count": keep_count,
                "message": f"当前日志总数 ({total_count}) 不超过保留数量 ({keep_count})，无需清理"
            }
        
        keep_query = select(Log.id).order_by(Log.timestamp.desc()).limit(keep_count)
        keep_result = await session.execute(keep_query)
        keep_ids = [row[0] for row in keep_result.fetchall()]
        
        delete_stmt = delete(Log).where(Log.id.notin_(keep_ids))
        delete_result = await session.execute(delete_stmt)
        deleted_count = delete_result.rowcount
        
        await session.commit()
        
        return {
            "total_before": total_count,
            "total_after": keep_count,
            "deleted_count": deleted_count,
            "keep_count": keep_count,
            "message": f"已删除 {deleted_count} 条日志，保留最近 {keep_count} 条"
        }
    
    @staticmethod
    async def cleanup_all(session: AsyncSession) -> dict:
        """
        清空所有日志
        
        Args:
            session: 数据库会话
        
        Returns:
            清理结果统计
        """
        count_result = await session.execute(select(func.count(Log.id)))
        total_count = count_result.scalar() or 0
        
        delete_stmt = delete(Log)
        await session.execute(delete_stmt)
        await session.commit()
        
        return {
            "total_before": total_count,
            "total_after": 0,
            "deleted_count": total_count,
            "message": f"已清空所有日志，共删除 {total_count} 条"
        }
    
    @staticmethod
    async def get_log_stats(session: AsyncSession) -> dict:
        """
        获取日志统计信息
        
        Args:
            session: 数据库会话
        
        Returns:
            日志统计信息
        """
        total_result = await session.execute(select(func.count(Log.id)))
        total = total_result.scalar() or 0
        
        level_result = await session.execute(
            select(Log.level, func.count(Log.id)).group_by(Log.level)
        )
        level_counts = {row[0]: row[1] for row in level_result.fetchall()}
        
        oldest_result = await session.execute(
            select(Log.timestamp).order_by(Log.timestamp.asc()).limit(1)
        )
        oldest = oldest_result.scalar()
        
        newest_result = await session.execute(
            select(Log.timestamp).order_by(Log.timestamp.desc()).limit(1)
        )
        newest = newest_result.scalar()
        
        return {
            "total": total,
            "level_counts": level_counts,
            "oldest_log": oldest,
            "newest_log": newest,
            "retention_days": LOG_RETENTION_DAYS,
            "max_records": LOG_MAX_RECORDS
        }


ws_log_handler: Optional[WebSocketLogHandler] = None
db_log_handler: Optional[DatabaseLogHandler] = None


def get_ws_log_handler() -> WebSocketLogHandler:
    """
    获取全局 WebSocket 日志处理器实例
    
    Returns:
        WebSocketLogHandler 实例
    """
    global ws_log_handler
    if ws_log_handler is None:
        ws_log_handler = WebSocketLogHandler()
    return ws_log_handler


def get_db_log_handler() -> DatabaseLogHandler:
    """
    获取全局数据库日志处理器实例
    
    Returns:
        DatabaseLogHandler 实例
    """
    global db_log_handler
    if db_log_handler is None:
        db_log_handler = DatabaseLogHandler()
    return db_log_handler


async def setup_log_handlers() -> tuple[WebSocketLogHandler, DatabaseLogHandler]:
    """
    初始化并注册所有日志处理器
    
    Returns:
        WebSocket 和数据库日志处理器元组
    """
    ws_handler = get_ws_log_handler()
    ws_handler.setFormatter(logging.Formatter('%(message)s'))
    
    db_handler = get_db_log_handler()
    db_handler.setFormatter(logging.Formatter('%(message)s'))
    
    root_logger = logging.getLogger()
    root_logger.addHandler(ws_handler)
    root_logger.addHandler(db_handler)
    
    await db_handler.start()
    
    return ws_handler, db_handler


async def cleanup_log_handlers() -> None:
    """
    清理日志处理器资源
    """
    db_handler = get_db_log_handler()
    await db_handler.stop()
