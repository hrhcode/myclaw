"""
Shell 命令执行工具

提供安全的命令执行能力，支持超时控制、后台执行和安全策略
"""
import asyncio
import logging
import os
import platform
import re
import shlex
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from app.tools.base import BaseTool, ToolDefinition, create_tool

logger = logging.getLogger(__name__)


DEFAULT_DENYLIST = {
    "rm", "rmdir", "del", "format", "fdisk", "mkfs",
    "dd", "shred", "wipe", "sudo", "su", "passwd",
    "chmod", "chown", "chgrp", "shutdown", "reboot",
    "init", "systemctl", "service", "crontab"
}

DEFAULT_SAFE_BINS = {
    "cat", "head", "tail", "less", "more",
    "grep", "egrep", "fgrep", "sed", "awk",
    "sort", "uniq", "wc", "cut", "tr",
    "echo", "printf", "date", "whoami", "pwd",
    "ls", "dir", "find", "which", "whereis",
    "curl", "wget"
}

DEFAULT_ALLOWED_ENV_VARS = {
    "PATH", "HOME", "USER", "LANG", "LC_ALL",
    "PYTHONIOENCODING", "NODE_OPTIONS"
}


class SecurityMode(str, Enum):
    """安全模式"""
    DENY = "deny"
    ALLOWLIST = "allowlist"
    FULL = "full"


@dataclass
class CommandResult:
    """
    命令执行结果
    
    Attributes:
        success: 是否成功
        exit_code: 退出码
        stdout: 标准输出
        stderr: 标准错误
        execution_time_ms: 执行时间（毫秒）
        timed_out: 是否超时
    """
    success: bool
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int = 0
    timed_out: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": self.execution_time_ms,
            "timed_out": self.timed_out
        }


@dataclass
class SecurityPolicy:
    """
    命令执行安全策略
    
    Attributes:
        mode: 安全模式
        allowlist: 允许的命令列表
        denylist: 禁止的命令列表
        safe_bins: 安全二进制文件（仅标准输入）
        allowed_env_vars: 允许的环境变量
        max_timeout_seconds: 最大超时时间
        max_output_bytes: 最大输出字节数
    """
    mode: SecurityMode = SecurityMode.DENY
    allowlist: Set[str] = field(default_factory=set)
    denylist: Set[str] = field(default_factory=lambda: DEFAULT_DENYLIST.copy())
    safe_bins: Set[str] = field(default_factory=lambda: DEFAULT_SAFE_BINS.copy())
    allowed_env_vars: Set[str] = field(default_factory=lambda: DEFAULT_ALLOWED_ENV_VARS.copy())
    max_timeout_seconds: int = 1800
    max_output_bytes: int = 1000000


class CommandValidator:
    """
    命令验证器
    
    根据安全策略验证命令是否允许执行
    """
    
    DANGEROUS_PATTERNS = [
        r';\s*rm\b',
        r'&&\s*rm\b',
        r'\|\|\s*rm\b',
        r'>\s*/dev/',
        r'\$\([^)]+\)',
        r'`[^`]+`',
        r'\$\{[^}]+\}',
        r'\|\s*bash\b',
        r'\|\s*sh\b',
        r'\|\s*python\b',
        r'\|\s*perl\b',
        r'\|\s*ruby\b',
        r'nc\s+-',
        r'netcat',
        r'/etc/passwd',
        r'/etc/shadow',
        r'id_rsa',
        r'\.ssh/',
    ]
    
    def __init__(self, policy: SecurityPolicy):
        """
        初始化命令验证器
        
        Args:
            policy: 安全策略
        """
        self._policy = policy
    
    def validate(self, command: str, workdir: Optional[str] = None) -> tuple[bool, str]:
        """
        验证命令是否允许执行
        
        Args:
            command: 要验证的命令
            workdir: 工作目录
            
        Returns:
            (是否允许, 原因)
        """
        if not command or not command.strip():
            return False, "命令为空"
        
        command = command.strip()
        
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"命令包含危险模式: {pattern}"
        
        if self._policy.mode == SecurityMode.FULL:
            return True, "完全访问模式"
        
        if self._policy.mode == SecurityMode.DENY:
            return False, "命令执行已被禁用"
        
        if self._policy.mode == SecurityMode.ALLOWLIST:
            base_cmd = self._extract_base_command(command)
            
            if base_cmd in self._policy.denylist:
                return False, f"命令 '{base_cmd}' 在禁止列表中"
            
            if base_cmd in self._policy.safe_bins:
                return True, f"命令 '{base_cmd}' 在安全命令列表中"
            
            if base_cmd in self._policy.allowlist:
                return True, f"命令 '{base_cmd}' 在允许列表中"
            
            return False, f"命令 '{base_cmd}' 不在允许列表中"
        
        return True, "验证通过"
    
    def _extract_base_command(self, command: str) -> str:
        """
        提取基础命令名
        
        Args:
            command: 完整命令
            
        Returns:
            基础命令名
        """
        import re
        
        command = command.strip()
        
        if command.startswith('"') or command.startswith("'"):
            match = re.match(r'^["\']([^"\'\s]+)', command)
            if match:
                return os.path.basename(match.group(1))
        
        parts = command.split()
        if parts:
            base = parts[0]
            if base in ('sudo', 'doas', 'run0'):
                return parts[1] if len(parts) > 1 else base
            return os.path.basename(base)
        
        return command
    
    def filter_env(self, env: Dict[str, str]) -> Dict[str, str]:
        """
        过滤环境变量
        
        Args:
            env: 原始环境变量
            
        Returns:
            过滤后的环境变量
        """
        if self._policy.mode == SecurityMode.FULL:
            return env
        
        filtered = {}
        for key, value in env.items():
            if key in self._policy.allowed_env_vars:
                filtered[key] = value
            elif key.startswith("MYCLAW_"):
                filtered[key] = value
        
        return filtered


class ExecTool(BaseTool):
    """Shell 命令执行工具"""
    
    def __init__(
        self,
        security_mode: SecurityMode = SecurityMode.ALLOWLIST,
        allowlist: Optional[Set[str]] = None,
        denylist: Optional[Set[str]] = None,
        default_timeout_seconds: int = 300,
        max_timeout_seconds: int = 1800,
        max_output_bytes: int = 1000000,
        default_workdir: Optional[str] = None
    ):
        """
        初始化 Exec 工具
        
        Args:
            security_mode: 安全模式
            allowlist: 允许的命令列表
            denylist: 禁止的命令列表
            default_timeout_seconds: 默认超时时间
            max_timeout_seconds: 最大超时时间
            max_output_bytes: 最大输出字节数
            default_workdir: 默认工作目录
        """
        self._policy = SecurityPolicy(
            mode=security_mode,
            allowlist=allowlist or set(),
            denylist=denylist if denylist is not None else DEFAULT_DENYLIST.copy(),
            max_timeout_seconds=max_timeout_seconds,
            max_output_bytes=max_output_bytes
        )
        self._validator = CommandValidator(self._policy)
        self._default_timeout = default_timeout_seconds
        self._default_workdir = default_workdir
    
    @property
    def name(self) -> str:
        return "exec"
    
    @property
    def description(self) -> str:
        return "在安全沙箱中执行 Shell 命令。支持超时控制和输出限制。"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 Shell 命令"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒），默认 300 秒",
                    "default": 300,
                    "minimum": 1,
                    "maximum": 1800
                },
                "workdir": {
                    "type": "string",
                    "description": "工作目录，默认为当前目录"
                },
                "env": {
                    "type": "object",
                    "description": "环境变量（键值对）",
                    "additionalProperties": {"type": "string"}
                },
                "shell": {
                    "type": "boolean",
                    "description": "是否使用 Shell 执行",
                    "default": True
                },
                "capture_stderr": {
                    "type": "boolean",
                    "description": "是否捕获标准错误",
                    "default": True
                }
            },
            "required": ["command"]
        }
    
    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        workdir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        shell: bool = True,
        capture_stderr: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行 Shell 命令
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
            workdir: 工作目录
            env: 环境变量
            shell: 是否使用 Shell 执行
            capture_stderr: 是否捕获标准错误
            **kwargs: 其他参数
            
        Returns:
            执行结果字典
        """
        workdir = workdir or self._default_workdir
        timeout = min(timeout or self._default_timeout, self._policy.max_timeout_seconds)
        
        is_valid, reason = self._validator.validate(command, workdir)
        if not is_valid:
            return {
                "success": False,
                "error": f"命令验证失败: {reason}",
                "command": command
            }
        
        if workdir:
            try:
                workdir_path = Path(workdir).resolve()
                if not workdir_path.exists():
                    return {
                        "success": False,
                        "error": f"工作目录不存在: {workdir}",
                        "command": command
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"工作目录无效: {e}",
                    "command": command
                }
        
        merged_env = dict(os.environ)
        if env:
            filtered_env = self._validator.filter_env(env)
            merged_env.update(filtered_env)
        
        try:
            result = await self._run_command(
                command=command,
                timeout=timeout,
                workdir=workdir,
                env=merged_env,
                shell=shell,
                capture_stderr=capture_stderr
            )
            
            return {
                "success": result.success,
                "command": command,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time_ms": result.execution_time_ms,
                "timed_out": result.timed_out
            }
            
        except Exception as e:
            logger.error(f"[Exec] 命令执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def _run_command(
        self,
        command: str,
        timeout: int,
        workdir: Optional[str],
        env: Dict[str, str],
        shell: bool,
        capture_stderr: bool
    ) -> CommandResult:
        """
        运行命令
        
        Args:
            command: 命令
            timeout: 超时时间
            workdir: 工作目录
            env: 环境变量
            shell: 是否使用 Shell
            capture_stderr: 是否捕获标准错误
            
        Returns:
            命令结果
        """
        start_time = time.time()
        
        is_windows = platform.system() == "Windows"
        
        if shell:
            if is_windows:
                executable = None
                args = ["powershell", "-Command", command]
            else:
                executable = "/bin/bash"
                args = ["-c", command]
        else:
            executable = None
            if is_windows:
                args = ["powershell", "-Command", command]
            else:
                args = shlex.split(command)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                executable=executable,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE if capture_stderr else asyncio.subprocess.DEVNULL,
                cwd=workdir,
                env=env
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                stdout = self._decode_output(stdout_bytes, self._policy.max_output_bytes)
                stderr = self._decode_output(stderr_bytes, self._policy.max_output_bytes) if capture_stderr else ""
                
                return CommandResult(
                    success=process.returncode == 0,
                    exit_code=process.returncode or 0,
                    stdout=stdout,
                    stderr=stderr,
                    execution_time_ms=execution_time_ms,
                    timed_out=False
                )
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                return CommandResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"命令执行超时（{timeout}秒）",
                    execution_time_ms=execution_time_ms,
                    timed_out=True
                )
                
        except FileNotFoundError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                exit_code=127,
                stdout="",
                stderr=f"命令未找到: {e}",
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time_ms=execution_time_ms
            )
    
    def _decode_output(self, data: bytes, max_bytes: int) -> str:
        """
        解码输出
        
        Args:
            data: 原始字节数据
            max_bytes: 最大字节数
            
        Returns:
            解码后的字符串
        """
        if not data:
            return ""
        
        if len(data) > max_bytes:
            data = data[:max_bytes]
            truncated = True
        else:
            truncated = False
        
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = data.decode("gbk" if platform.system() == "Windows" else "latin-1")
            except UnicodeDecodeError:
                text = data.decode("utf-8", errors="replace")
        
        if truncated:
            text += "\n... (输出已截断)"
        
        return text


def get_exec_tool(
    security_mode: str = "allowlist",
    allowlist: Optional[List[str]] = None,
    denylist: Optional[List[str]] = None,
    default_workdir: Optional[str] = None
) -> ToolDefinition:
    """
    获取 Exec 工具定义
    
    Args:
        security_mode: 安全模式（deny/allowlist/full）
        allowlist: 允许的命令列表
        denylist: 禁止的命令列表
        default_workdir: 默认工作目录
        
    Returns:
        工具定义实例
    """
    mode = SecurityMode(security_mode.lower())
    
    tool_instance = ExecTool(
        security_mode=mode,
        allowlist=set(allowlist) if allowlist else None,
        denylist=set(denylist) if denylist else None,
        default_workdir=default_workdir
    )
    
    return create_tool(
        name="exec",
        description="在安全沙箱中执行 Shell 命令。支持超时控制和输出限制。",
        parameters=tool_instance.parameters,
        execute=tool_instance.execute
    )
