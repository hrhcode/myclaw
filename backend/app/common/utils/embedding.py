"""
嵌入向量工具函数模块
"""
import struct
import hashlib
from typing import List


def embedding_to_bytes(embedding: List[float]) -> bytes:
    """
    将向量嵌入列表转换为字节存储
    
    Args:
        embedding: 向量嵌入列表
        
    Returns:
        字节表示
    """
    return struct.pack(f'{len(embedding)}f', *embedding)


def bytes_to_embedding(data: bytes) -> List[float]:
    """
    将字节转换回向量嵌入列表
    
    Args:
        data: 字节数据
        
    Returns:
        向量嵌入列表
    """
    if not data:
        return []
    count = len(data) // 4
    return list(struct.unpack(f'{count}f', data))


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的余弦相似度
    
    Args:
        vec1: 向量1
        vec2: 向量2
        
    Returns:
        余弦相似度 (0-1)
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def compute_content_hash(content: str) -> str:
    """
    计算内容的SHA256哈希值
    
    Args:
        content: 要哈希的内容
        
    Returns:
        SHA256哈希字符串
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
