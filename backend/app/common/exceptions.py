"""
自定义异常类模块
定义应用中使用的各种异常类型
"""


class ConfigException(Exception):
    """
    配置相关异常
    
    当配置读取、写入或验证失败时抛出
    """
    pass


class EmbeddingException(Exception):
    """
    嵌入服务异常
    
    当向量嵌入生成失败时抛出
    """
    pass


class MemoryException(Exception):
    """
    记忆管理异常
    
    当长期记忆操作失败时抛出
    """
    pass


class ToolException(Exception):
    """
    工具执行异常
    
    当工具调用或执行失败时抛出
    """
    pass


class SearchException(Exception):
    """
    搜索服务异常
    
    当搜索操作失败时抛出
    """
    pass
