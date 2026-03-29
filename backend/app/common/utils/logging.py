"""
日志工具函数模块
"""
import logging

logger = logging.getLogger(__name__)


def log_search_start(query: str, search_type: str, top_k: int):
    """
    记录搜索开始的日志
    
    Args:
        query: 搜索查询
        search_type: 搜索类型
        top_k: 返回结果数量
    """
    logger.info(f"[{search_type}] 开始搜索")
    logger.info(f"  ├─ 查询内容: {query[:50]}{'...' if len(query) > 50 else ''}")
    logger.info(f"  └─ 返回数量: {top_k}")


def log_search_result(count: int, search_type: str, source: str):
    """
    记录搜索结果的日志
    
    Args:
        count: 结果数量
        search_type: 搜索类型
        source: 结果来源
    """
    logger.info(f"[{search_type}] 搜索完成，找到 {count} 条结果 (来源: {source})")
