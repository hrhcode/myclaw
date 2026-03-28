"""
日志 API 端点 - 提供 WebSocket 实时日志推送和 REST 历史日志查询
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from pydantic import BaseModel

from app.services.log_service import (
    get_ws_log_handler,
    LogService,
    setup_log_handlers,
    cleanup_log_handlers
)
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class CleanupResponse(BaseModel):
    """日志清理响应模型"""
    success: bool
    data: dict


class LogStatsResponse(BaseModel):
    """日志统计响应模型"""
    success: bool
    data: dict


@router.websocket("/logs/stream")
async def logs_stream(websocket: WebSocket):
    """
    WebSocket 端点 - 实时推送日志
    
    客户端连接后可发送以下消息：
    - {"type": "filter", "level": "INFO"} - 设置日志级别过滤
    """
    handler = get_ws_log_handler()
    
    await websocket.accept()
    handler.add_connection(websocket)
    
    logger.info(f"WebSocket 日志客户端已连接，当前连接数: {handler.connection_count}")
    
    try:
        history = handler.get_history(limit=50)
        for log in history:
            await websocket.send_text(json.dumps({
                "type": "log",
                "data": log
            }, ensure_ascii=False))
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "filter":
                    level = message.get("level", "DEBUG")
                    handler.set_level_filter(level)
                    logger.info(f"WebSocket 日志级别过滤已设置为: {level}")
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        handler.remove_connection(websocket)
        logger.info(f"WebSocket 日志客户端已断开，当前连接数: {handler.connection_count}")
    except Exception as e:
        handler.remove_connection(websocket)
        logger.error(f"WebSocket 日志连接异常: {e}")


@router.get("/logs/history")
async def get_logs_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页条数"),
    level: Optional[str] = Query(None, description="日志级别过滤（DEBUG/INFO/WARNING/ERROR/CRITICAL）"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    start_time: Optional[str] = Query(None, description="开始时间（ISO 8601 格式）"),
    end_time: Optional[str] = Query(None, description="结束时间（ISO 8601 格式）"),
    order: str = Query("desc", regex="^(asc|desc)$", description="排序方式"),
    db: AsyncSession = Depends(get_db)
):
    """
    REST 端点 - 获取历史日志（从数据库查询）
    
    Args:
        page: 页码（默认 1）
        page_size: 每页条数（默认 50，最大 200）
        level: 日志级别过滤（可选）
        keyword: 关键词搜索（可选）
        start_time: 开始时间（可选）
        end_time: 结束时间（可选）
        order: 排序方式（默认 desc）
    
    Returns:
        分页日志数据
    """
    result = await LogService.get_logs(
        session=db,
        page=page,
        page_size=page_size,
        level=level,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time,
        order=order
    )
    
    return {
        "success": True,
        "data": result
    }


@router.get("/logs/memory")
async def get_logs_memory(
    level: Optional[str] = Query(None, description="日志级别过滤（DEBUG/INFO/WARNING/ERROR/CRITICAL）"),
    limit: int = Query(100, ge=1, le=1000, description="返回条数限制")
):
    """
    REST 端点 - 获取内存缓冲中的历史日志（实时日志）
    
    Args:
        level: 日志级别过滤（可选）
        limit: 返回条数限制（默认100，最大1000）
    
    Returns:
        日志列表
    """
    handler = get_ws_log_handler()
    logs = handler.get_history(level=level, limit=limit)
    
    return {
        "success": True,
        "data": logs,
        "count": len(logs)
    }


@router.get("/logs/status")
async def get_logs_status(db: AsyncSession = Depends(get_db)):
    """
    REST 端点 - 获取日志服务状态
    
    Returns:
        日志服务状态信息
    """
    handler = get_ws_log_handler()
    
    stats = await LogService.get_log_stats(db)
    
    return {
        "success": True,
        "data": {
            "websocket": {
                "connection_count": handler.connection_count,
                "buffer_size": len(handler._log_buffer),
                "max_buffer_size": 1000
            },
            "database": stats
        }
    }


@router.get("/logs/stats")
async def get_logs_stats(db: AsyncSession = Depends(get_db)):
    """
    REST 端点 - 获取日志统计信息
    
    Returns:
        日志统计信息
    """
    stats = await LogService.get_log_stats(db)
    
    return {
        "success": True,
        "data": stats
    }


@router.post("/logs/cleanup")
async def cleanup_old_logs(
    retention_days: Optional[int] = Query(None, ge=1, le=365, description="日志保留天数"),
    max_records: Optional[int] = Query(None, ge=1000, le=1000000, description="最大日志条数"),
    db: AsyncSession = Depends(get_db)
):
    """
    REST 端点 - 手动触发日志清理（按时间和数量）
    
    Args:
        retention_days: 日志保留天数（可选，默认使用配置值）
        max_records: 最大日志条数（可选，默认使用配置值）
    
    Returns:
        清理结果统计
    """
    result = await LogService.cleanup_old_logs(
        session=db,
        retention_days=retention_days if retention_days else 7,
        max_records=max_records if max_records else 100000
    )
    
    logger.info(f"日志清理完成: {result}")
    
    return {
        "success": True,
        "data": result
    }


@router.post("/logs/cleanup/keep-recent")
async def cleanup_keep_recent_logs(
    keep_count: int = Query(100, ge=1, le=1000000, description="保留最近N条日志"),
    db: AsyncSession = Depends(get_db)
):
    """
    REST 端点 - 保留最近 N 条日志，删除其余所有日志
    
    Args:
        keep_count: 保留的日志条数（默认100）
    
    Returns:
        清理结果统计
    """
    result = await LogService.cleanup_keep_recent(
        session=db,
        keep_count=keep_count
    )
    
    logger.info(f"日志清理（保留最近{keep_count}条）完成: {result}")
    
    return {
        "success": True,
        "data": result
    }


@router.delete("/logs/all")
async def cleanup_all_logs(
    db: AsyncSession = Depends(get_db)
):
    """
    REST 端点 - 清空所有历史日志
    
    Returns:
        清理结果统计
    """
    result = await LogService.cleanup_all(session=db)
    
    logger.info(f"清空所有日志完成: {result}")
    
    return {
        "success": True,
        "data": result
    }
