"""
进程管理工具

提供后台进程管理能力，支持进程列表、轮询、日志、终止等操作
"""
import asyncio
import logging
import platform
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.tools.base import BaseTool, ToolDefinition, create_tool

logger = logging.getLogger(__name__)


class ProcessStatus(str, Enum):
    """进程状态"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"


@dataclass
class ProcessSession:
    """
    进程会话
    
    Attributes:
        id: 会话 ID
        command: 执行的命令
        status: 进程状态
        pid: 进程 ID（如果可用）
        started_at: 启动时间
        completed_at: 完成时间
        exit_code: 退出码
        stdout_buffer: 标准输出缓冲
        stderr_buffer: 标准错误缓冲
        scope_key: 作用域键（用于隔离）
    """
    id: str
    command: str
    status: ProcessStatus = ProcessStatus.RUNNING
    pid: Optional[int] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout_buffer: List[str] = field(default_factory=list)
    stderr_buffer: List[str] = field(default_factory=list)
    scope_key: Optional[str] = None
    _process: Optional[asyncio.subprocess.Process] = field(default=None, repr=False)
    _task: Optional[asyncio.Task] = field(default=None, repr=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "command": self.command,
            "status": self.status.value,
            "pid": self.pid,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "exit_code": self.exit_code,
            "runtime_seconds": self._calculate_runtime(),
            "scope_key": self.scope_key
        }
    
    def _calculate_runtime(self) -> int:
        """计算运行时间（秒）"""
        end = self.completed_at or datetime.now()
        return int((end - self.started_at).total_seconds())


class ProcessManager:
    """
    进程管理器
    
    管理所有后台进程会话
    """
    
    def __init__(self, max_sessions: int = 100, cleanup_interval: int = 300):
        """
        初始化进程管理器
        
        Args:
            max_sessions: 最大会话数
            cleanup_interval: 清理间隔（秒）
        """
        self._sessions: Dict[str, ProcessSession] = {}
        self._max_sessions = max_sessions
        self._cleanup_interval = cleanup_interval
        self._lock = asyncio.Lock()
    
    async def create_session(
        self,
        command: str,
        scope_key: Optional[str] = None
    ) -> ProcessSession:
        """
        创建新的进程会话
        
        Args:
            command: 要执行的命令
            scope_key: 作用域键
            
        Returns:
            进程会话
        """
        async with self._lock:
            if len(self._sessions) >= self._max_sessions:
                await self._cleanup_old_sessions()
            
            session_id = str(uuid.uuid4())[:8]
            session = ProcessSession(
                id=session_id,
                command=command,
                scope_key=scope_key
            )
            
            self._sessions[session_id] = session
            logger.info(f"[Process] 创建会话: {session_id}, 命令: {command}")
            
            return session
    
    async def get_session(self, session_id: str, scope_key: Optional[str] = None) -> Optional[ProcessSession]:
        """
        获取进程会话
        
        Args:
            session_id: 会话 ID
            scope_key: 作用域键（用于权限检查）
            
        Returns:
            进程会话
        """
        session = self._sessions.get(session_id)
        if session:
            if scope_key and session.scope_key and session.scope_key != scope_key:
                return None
        return session
    
    async def list_sessions(
        self,
        scope_key: Optional[str] = None,
        status: Optional[ProcessStatus] = None
    ) -> List[ProcessSession]:
        """
        列出进程会话
        
        Args:
            scope_key: 作用域键（用于过滤）
            status: 状态过滤
            
        Returns:
            会话列表
        """
        sessions = []
        for session in self._sessions.values():
            if scope_key and session.scope_key and session.scope_key != scope_key:
                continue
            if status and session.status != status:
                continue
            sessions.append(session)
        
        return sorted(sessions, key=lambda s: s.started_at, reverse=True)
    
    async def remove_session(self, session_id: str) -> bool:
        """
        移除会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否成功移除
        """
        async with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                if session.status == ProcessStatus.RUNNING:
                    await self.kill_session(session_id)
                del self._sessions[session_id]
                logger.info(f"[Process] 移除会话: {session_id}")
                return True
            return False
    
    async def kill_session(self, session_id: str) -> bool:
        """
        终止会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否成功终止
        """
        session = self._sessions.get(session_id)
        if not session or session.status != ProcessStatus.RUNNING:
            return False
        
        if session._process:
            try:
                session._process.kill()
                await session._process.wait()
            except ProcessLookupError:
                pass
        
        session.status = ProcessStatus.KILLED
        session.completed_at = datetime.now()
        session.exit_code = -9
        
        logger.info(f"[Process] 终止会话: {session_id}")
        return True
    
    async def _cleanup_old_sessions(self) -> None:
        """清理旧会话"""
        completed_sessions = [
            s for s in self._sessions.values()
            if s.status != ProcessStatus.RUNNING
        ]
        
        completed_sessions.sort(key=lambda s: s.completed_at or s.started_at)
        
        to_remove = len(self._sessions) - self._max_sessions + 10
        for session in completed_sessions[:to_remove]:
            del self._sessions[session.id]
            logger.info(f"[Process] 清理会话: {session.id}")


process_manager = ProcessManager()


class ProcessTool(BaseTool):
    """进程管理工具"""
    
    @property
    def name(self) -> str:
        return "process"
    
    @property
    def description(self) -> str:
        return "管理后台进程。支持列表、轮询、日志、终止等操作。"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "要执行的操作",
                    "enum": ["list", "poll", "log", "kill", "remove", "clear"],
                    "default": "list"
                },
                "session_id": {
                    "type": "string",
                    "description": "会话 ID（poll/log/kill/remove 操作需要）"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制（list/log 操作）",
                    "default": 50
                },
                "offset": {
                    "type": "integer",
                    "description": "偏移量（log 操作）",
                    "default": 0
                },
                "status": {
                    "type": "string",
                    "description": "状态过滤（list 操作）",
                    "enum": ["running", "completed", "failed", "timeout", "killed"]
                }
            },
            "required": ["action"]
        }
    
    async def execute(
        self,
        action: str,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        scope_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行进程管理操作
        
        Args:
            action: 操作类型
            session_id: 会话 ID
            limit: 数量限制
            offset: 偏移量
            status: 状态过滤
            scope_key: 作用域键
            **kwargs: 其他参数
            
        Returns:
            操作结果
        """
        if action == "list":
            return await self._action_list(scope_key, status, limit)
        elif action == "poll":
            return await self._action_poll(session_id, scope_key)
        elif action == "log":
            return await self._action_log(session_id, scope_key, limit, offset)
        elif action == "kill":
            return await self._action_kill(session_id, scope_key)
        elif action == "remove":
            return await self._action_remove(session_id, scope_key)
        elif action == "clear":
            return await self._action_clear(scope_key, status)
        else:
            return {
                "success": False,
                "error": f"未知操作: {action}"
            }
    
    async def _action_list(
        self,
        scope_key: Optional[str],
        status: Optional[str],
        limit: int
    ) -> Dict[str, Any]:
        """列出会话"""
        status_enum = ProcessStatus(status) if status else None
        sessions = await process_manager.list_sessions(scope_key, status_enum)
        
        return {
            "success": True,
            "action": "list",
            "sessions": [s.to_dict() for s in sessions[:limit]],
            "total": len(sessions),
            "running": sum(1 for s in sessions if s.status == ProcessStatus.RUNNING)
        }
    
    async def _action_poll(
        self,
        session_id: Optional[str],
        scope_key: Optional[str]
    ) -> Dict[str, Any]:
        """轮询会话状态"""
        if not session_id:
            return {
                "success": False,
                "error": "缺少 session_id 参数"
            }
        
        session = await process_manager.get_session(session_id, scope_key)
        if not session:
            return {
                "success": False,
                "error": f"会话不存在: {session_id}"
            }
        
        result = session.to_dict()
        result["new_stdout"] = session.stdout_buffer[-10:]
        result["new_stderr"] = session.stderr_buffer[-10:]
        
        return {
            "success": True,
            "action": "poll",
            **result
        }
    
    async def _action_log(
        self,
        session_id: Optional[str],
        scope_key: Optional[str],
        limit: int,
        offset: int
    ) -> Dict[str, Any]:
        """获取会话日志"""
        if not session_id:
            return {
                "success": False,
                "error": "缺少 session_id 参数"
            }
        
        session = await process_manager.get_session(session_id, scope_key)
        if not session:
            return {
                "success": False,
                "error": f"会话不存在: {session_id}"
            }
        
        stdout_lines = session.stdout_buffer[offset:offset + limit]
        stderr_lines = session.stderr_buffer[offset:offset + limit]
        
        return {
            "success": True,
            "action": "log",
            "session_id": session_id,
            "stdout": "\n".join(stdout_lines),
            "stderr": "\n".join(stderr_lines),
            "stdout_lines": len(stdout_lines),
            "stderr_lines": len(stderr_lines),
            "total_stdout_lines": len(session.stdout_buffer),
            "total_stderr_lines": len(session.stderr_buffer)
        }
    
    async def _action_kill(
        self,
        session_id: Optional[str],
        scope_key: Optional[str]
    ) -> Dict[str, Any]:
        """终止会话"""
        if not session_id:
            return {
                "success": False,
                "error": "缺少 session_id 参数"
            }
        
        session = await process_manager.get_session(session_id, scope_key)
        if not session:
            return {
                "success": False,
                "error": f"会话不存在: {session_id}"
            }
        
        if session.status != ProcessStatus.RUNNING:
            return {
                "success": False,
                "error": f"会话已结束: {session.status.value}"
            }
        
        success = await process_manager.kill_session(session_id)
        
        return {
            "success": success,
            "action": "kill",
            "session_id": session_id,
            "message": "进程已终止" if success else "终止失败"
        }
    
    async def _action_remove(
        self,
        session_id: Optional[str],
        scope_key: Optional[str]
    ) -> Dict[str, Any]:
        """移除会话"""
        if not session_id:
            return {
                "success": False,
                "error": "缺少 session_id 参数"
            }
        
        session = await process_manager.get_session(session_id, scope_key)
        if not session:
            return {
                "success": False,
                "error": f"会话不存在: {session_id}"
            }
        
        success = await process_manager.remove_session(session_id)
        
        return {
            "success": success,
            "action": "remove",
            "session_id": session_id,
            "message": "会话已移除" if success else "移除失败"
        }
    
    async def _action_clear(
        self,
        scope_key: Optional[str],
        status: Optional[str]
    ) -> Dict[str, Any]:
        """清理已完成的会话"""
        status_enum = ProcessStatus(status) if status else None
        
        sessions = await process_manager.list_sessions(scope_key, status_enum)
        
        removed_count = 0
        for session in sessions:
            if session.status != ProcessStatus.RUNNING:
                if await process_manager.remove_session(session.id):
                    removed_count += 1
        
        return {
            "success": True,
            "action": "clear",
            "removed_count": removed_count,
            "message": f"已清理 {removed_count} 个会话"
        }


def get_process_tool() -> ToolDefinition:
    """
    获取进程管理工具定义
    
    Returns:
        工具定义实例
    """
    tool_instance = ProcessTool()
    
    return create_tool(
        name="process",
        description="管理后台进程。支持列表、轮询、日志、终止等操作。",
        parameters=tool_instance.parameters,
        execute=tool_instance.execute
    )
