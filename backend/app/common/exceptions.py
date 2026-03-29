"""
自定义异常类模块
定义应用中使用的各种异常类型
"""
from fastapi import HTTPException


class BusinessException(Exception):
    """
    业务异常基类

    所有业务异常都应继承此类
    提供统一的错误码和消息格式
    """

    def __init__(self, code: int, message: str, error: str = None):
        """
        初始化业务异常

        Args:
            code: HTTP状态码
            message: 用户友好的错误消息
            error: 详细错误信息（用于日志）
        """
        self.code = code
        self.message = message
        self.error = error
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        转换为FastAPI HTTPException

        Returns:
            HTTPException对象
        """
        return HTTPException(
            status_code=self.code,
            detail=self.message
        )


class ConfigException(BusinessException):
    """
    配置相关异常

    当配置读取、写入或验证失败时抛出
    """

    def __init__(self, message: str, error: str = None):
        super().__init__(code=400, message=message, error=error)


class EmbeddingException(BusinessException):
    """
    嵌入服务异常

    当向量嵌入生成失败时抛出
    """

    def __init__(self, message: str, error: str = None):
        super().__init__(code=500, message=message, error=error)


class MemoryException(BusinessException):
    """
    记忆管理异常

    当长期记忆操作失败时抛出
    """

    def __init__(self, message: str, error: str = None):
        super().__init__(code=400, message=message, error=error)


class ToolException(BusinessException):
    """
    工具执行异常

    当工具调用或执行失败时抛出
    """

    def __init__(self, message: str, error: str = None):
        super().__init__(code=400, message=message, error=error)


class SearchException(BusinessException):
    """
    搜索服务异常

    当搜索操作失败时抛出
    """

    def __init__(self, message: str, error: str = None):
        super().__init__(code=500, message=message, error=error)


class NotFoundException(BusinessException):
    """
    资源不存在异常

    当请求的资源不存在时抛出
    """

    def __init__(self, resource: str, resource_id: any):
        message = f"{resource}不存在，ID: {resource_id}"
        super().__init__(code=404, message=message, error=message)


class ValidationException(BusinessException):
    """
    数据验证异常

    当输入数据验证失败时抛出
    """

    def __init__(self, message: str, error: str = None):
        super().__init__(code=400, message=message, error=error)
