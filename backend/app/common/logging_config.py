"""
日志配置模块
提供统一的日志配置
"""
import logging


def setup_logging():
    """
    配置应用日志
    
    设置日志级别、格式等基础配置
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，通常使用 __name__
        
    Returns:
        配置好的日志记录器
    """
    return logging.getLogger(name)
