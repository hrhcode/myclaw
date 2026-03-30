"""
工具调用循环检测机制

检测和防止 AI 陷入重复工具调用的循环
"""
import hashlib
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class LoopSeverity(str, Enum):
    """
    循环严重程度
    
    Attributes:
        NONE: 无循环
        WARNING: 警告级别
        CRITICAL: 严重级别
        CIRCUIT_BREAKER: 触发熔断
    """
    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class ToolCallRecord:
    """
    工具调用记录
    
    Attributes:
        tool_name: 工具名称
        params_hash: 参数哈希
        timestamp: 时间戳
        result_hash: 结果哈希
    """
    tool_name: str
    params_hash: str
    timestamp: float
    result_hash: Optional[str] = None


@dataclass
class LoopDetectionConfig:
    """
    循环检测配置
    
    Attributes:
        enabled: 是否启用
        warning_threshold: 警告阈值
        critical_threshold: 严重阈值
        circuit_breaker_threshold: 熔断阈值
        history_size: 历史记录大小
        detectors: 启用的检测器
    """
    enabled: bool = True
    warning_threshold: int = 10
    critical_threshold: int = 20
    circuit_breaker_threshold: int = 30
    history_size: int = 30
    detectors: Dict[str, bool] = field(default_factory=lambda: {
        "generic_repeat": True,
        "known_poll_no_progress": True,
        "ping_pong": True
    })


@dataclass
class LoopDetectionResult:
    """
    循环检测结果
    
    Attributes:
        severity: 严重程度
        message: 检测消息
        pattern: 检测到的模式
        count: 重复次数
        should_block: 是否应该阻止
    """
    severity: LoopSeverity = LoopSeverity.NONE
    message: str = ""
    pattern: str = ""
    count: int = 0
    should_block: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "severity": self.severity.value,
            "message": self.message,
            "pattern": self.pattern,
            "count": self.count,
            "should_block": self.should_block
        }


class LoopDetector:
    """
    循环检测器
    
    检测重复的工具调用模式
    """
    
    POLL_TOOLS = {"poll", "status", "list", "get", "fetch"}
    
    def __init__(self, config: LoopDetectionConfig):
        """
        初始化检测器
        
        Args:
            config: 检测配置
        """
        self._config = config
        self._history: deque = deque(maxlen=config.history_size)
    
    def record_call(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Optional[Any] = None
    ) -> None:
        """
        记录工具调用
        
        Args:
            tool_name: 工具名称
            params: 调用参数
            result: 调用结果
        """
        params_hash = self._hash_params(params)
        result_hash = self._hash_result(result) if result else None
        
        record = ToolCallRecord(
            tool_name=tool_name,
            params_hash=params_hash,
            timestamp=time.time(),
            result_hash=result_hash
        )
        
        self._history.append(record)
    
    def detect(self) -> LoopDetectionResult:
        """
        检测循环
        
        Returns:
            检测结果
        """
        if not self._config.enabled:
            return LoopDetectionResult()
        
        if len(self._history) < 3:
            return LoopDetectionResult()
        
        results = []
        
        if self._config.detectors.get("generic_repeat", True):
            results.append(self._detect_generic_repeat())
        
        if self._config.detectors.get("known_poll_no_progress", True):
            results.append(self._detect_poll_no_progress())
        
        if self._config.detectors.get("ping_pong", True):
            results.append(self._detect_ping_pong())
        
        most_severe = LoopDetectionResult()
        for result in results:
            if self._severity_level(result.severity) > self._severity_level(most_severe.severity):
                most_severe = result
        
        return most_severe
    
    def _detect_generic_repeat(self) -> LoopDetectionResult:
        """
        检测通用重复模式
        
        Returns:
            检测结果
        """
        if len(self._history) < 3:
            return LoopDetectionResult()
        
        call_counts: Dict[str, int] = {}
        
        for record in self._history:
            key = f"{record.tool_name}:{record.params_hash}"
            call_counts[key] = call_counts.get(key, 0) + 1
        
        max_count = max(call_counts.values())
        max_key = max(call_counts, key=call_counts.get)
        
        if max_count >= self._config.circuit_breaker_threshold:
            return LoopDetectionResult(
                severity=LoopSeverity.CIRCUIT_BREAKER,
                message=f"检测到严重循环: 工具 '{max_key}' 已重复调用 {max_count} 次",
                pattern="generic_repeat",
                count=max_count,
                should_block=True
            )
        
        if max_count >= self._config.critical_threshold:
            return LoopDetectionResult(
                severity=LoopSeverity.CRITICAL,
                message=f"检测到重复调用: 工具 '{max_key}' 已调用 {max_count} 次",
                pattern="generic_repeat",
                count=max_count,
                should_block=True
            )
        
        if max_count >= self._config.warning_threshold:
            return LoopDetectionResult(
                severity=LoopSeverity.WARNING,
                message=f"警告: 工具 '{max_key}' 已调用 {max_count} 次",
                pattern="generic_repeat",
                count=max_count,
                should_block=False
            )
        
        return LoopDetectionResult()
    
    def _detect_poll_no_progress(self) -> LoopDetectionResult:
        """
        检测轮询无进展模式
        
        Returns:
            检测结果
        """
        poll_records = [
            r for r in self._history
            if r.tool_name.lower() in self.POLL_TOOLS
        ]
        
        if len(poll_records) < 3:
            return LoopDetectionResult()
        
        result_hashes = [r.result_hash for r in poll_records if r.result_hash]
        
        if len(result_hashes) < 3:
            return LoopDetectionResult()
        
        if len(set(result_hashes[-5:])) == 1:
            return LoopDetectionResult(
                severity=LoopSeverity.WARNING,
                message="检测到轮询无进展: 连续多次返回相同结果",
                pattern="poll_no_progress",
                count=len(result_hashes),
                should_block=False
            )
        
        return LoopDetectionResult()
    
    def _detect_ping_pong(self) -> LoopDetectionResult:
        """
        检测乒乓模式（A-B-A-B 交替）
        
        Returns:
            检测结果
        """
        if len(self._history) < 4:
            return LoopDetectionResult()
        
        recent = list(self._history)[-8:]
        
        tools = [r.tool_name for r in recent]
        
        for i in range(len(tools) - 3):
            if (
                tools[i] == tools[i + 2] and
                tools[i + 1] == tools[i + 3] and
                tools[i] != tools[i + 1]
            ):
                return LoopDetectionResult(
                    severity=LoopSeverity.WARNING,
                    message=f"检测到乒乓模式: {tools[i]} <-> {tools[i+1]}",
                    pattern="ping_pong",
                    count=4,
                    should_block=False
                )
        
        return LoopDetectionResult()
    
    def _severity_level(self, severity: LoopSeverity) -> int:
        """
        获取严重程度级别
        
        Args:
            severity: 严重程度
            
        Returns:
            级别数值
        """
        levels = {
            LoopSeverity.NONE: 0,
            LoopSeverity.WARNING: 1,
            LoopSeverity.CRITICAL: 2,
            LoopSeverity.CIRCUIT_BREAKER: 3
        }
        return levels.get(severity, 0)
    
    def _hash_params(self, params: Dict[str, Any]) -> str:
        """
        计算参数哈希
        
        Args:
            params: 参数字典
            
        Returns:
            哈希字符串
        """
        try:
            import json
            normalized = json.dumps(params, sort_keys=True, default=str)
            return hashlib.md5(normalized.encode()).hexdigest()[:8]
        except Exception:
            return "unknown"
    
    def _hash_result(self, result: Any) -> str:
        """
        计算结果哈希
        
        Args:
            result: 结果
            
        Returns:
            哈希字符串
        """
        try:
            import json
            if isinstance(result, dict):
                normalized = json.dumps(result, sort_keys=True, default=str)
            else:
                normalized = str(result)
            return hashlib.md5(normalized.encode()).hexdigest()[:8]
        except Exception:
            return "unknown"
    
    def clear(self) -> None:
        """清空历史记录"""
        self._history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计字典
        """
        tool_counts: Dict[str, int] = {}
        for record in self._history:
            tool_counts[record.tool_name] = tool_counts.get(record.tool_name, 0) + 1
        
        return {
            "history_size": len(self._history),
            "max_history_size": self._config.history_size,
            "unique_tools": len(tool_counts),
            "tool_counts": tool_counts
        }


class LoopDetectionManager:
    """
    循环检测管理器
    
    管理多个会话的循环检测器
    """
    
    def __init__(self, default_config: Optional[LoopDetectionConfig] = None):
        """
        初始化管理器
        
        Args:
            default_config: 默认配置
        """
        self._default_config = default_config or LoopDetectionConfig()
        self._detectors: Dict[str, LoopDetector] = {}
    
    def get_detector(self, session_id: str) -> LoopDetector:
        """
        获取会话的检测器
        
        Args:
            session_id: 会话 ID
            
        Returns:
            循环检测器
        """
        if session_id not in self._detectors:
            self._detectors[session_id] = LoopDetector(self._default_config)
        return self._detectors[session_id]
    
    def record_call(
        self,
        session_id: str,
        tool_name: str,
        params: Dict[str, Any],
        result: Optional[Any] = None
    ) -> None:
        """
        记录工具调用
        
        Args:
            session_id: 会话 ID
            tool_name: 工具名称
            params: 调用参数
            result: 调用结果
        """
        detector = self.get_detector(session_id)
        detector.record_call(tool_name, params, result)
    
    def detect(self, session_id: str) -> LoopDetectionResult:
        """
        检测循环
        
        Args:
            session_id: 会话 ID
            
        Returns:
            检测结果
        """
        detector = self.get_detector(session_id)
        return detector.detect()
    
    def clear_session(self, session_id: str) -> None:
        """
        清除会话检测器
        
        Args:
            session_id: 会话 ID
        """
        if session_id in self._detectors:
            self._detectors[session_id].clear()
            del self._detectors[session_id]
    
    def clear_all(self) -> None:
        """清除所有检测器"""
        self._detectors.clear()


loop_detection_manager = LoopDetectionManager()


def create_loop_detector(config: Optional[LoopDetectionConfig] = None) -> LoopDetector:
    """
    创建循环检测器
    
    Args:
        config: 检测配置
        
    Returns:
        循环检测器实例
    """
    return LoopDetector(config or LoopDetectionConfig())
