"""
文本处理工具函数模块
"""
import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """
    估算文本的token数量
    
    Args:
        text: 文本内容
        
    Returns:
        估算的token数量
    """
    if not text:
        return 0
    
    return int(len(text.split()) * 1.3)


def calculate_importance_score(text: str, importance_keywords: List[str] = None) -> float:
    """
    计算文本的重要性分数
    
    Args:
        text: 文本内容
        importance_keywords: 重要性关键词列表
        
    Returns:
        重要性分数 (0.0-1.0)
    """
    if not text:
        return 0.0
    
    if importance_keywords is None:
        importance_keywords = [
            "重要", "关键", "必须", "记住", "不要忘记",
            "重要信息", "关键信息", "核心", "主要",
            "prefer", "like", "want", "need", "require",
            "设置", "配置", "选项", "参数", "偏好"
        ]
    
    score = 0.0
    text_lower = text.lower()
    
    for keyword in importance_keywords:
        if keyword.lower() in text_lower:
            score += 0.1
    
    if "？" in text or "?" in text:
        score += 0.05
    
    if "！" in text or "!" in text:
        score += 0.05
    
    if len(text.split()) > 20:
        score += 0.1
    
    final_score = min(score, 1.0)
    logger.debug(f"[重要性计算] 文本: {text[:30]}... -> 分数: {final_score:.2f}")
    return final_score


def format_memory_for_storage(summary_item: Dict) -> str:
    """
    格式化记忆用于存储
    
    Args:
        summary_item: 摘要项
        
    Returns:
        格式化的记忆文本
    """
    role = summary_item.get("role", "user")
    content = summary_item.get("summary", "")
    
    if role == "user":
        return f"用户提到: {content}"
    else:
        return f"系统/助手: {content}"


def jaccard_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的Jaccard相似度
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        Jaccard相似度 (0-1)
    """
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    
    if not set1 and not set2:
        return 1.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def chunk_markdown_text(text: str, max_chars: int = 1200, overlap_chars: int = 150) -> List[str]:
    """Split markdown text into retrieval-friendly chunks."""
    normalized = (text or "").replace("\r\n", "\n").strip()
    if not normalized:
        return []

    sections = re.split(r"(?m)(?=^#{1,6}\s+)", normalized)
    sections = [section.strip() for section in sections if section.strip()]
    if not sections:
        sections = [normalized]

    chunks: List[str] = []
    current = ""

    def flush_current() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    for section in sections:
        if len(section) <= max_chars:
            candidate = f"{current}\n\n{section}".strip() if current else section
            if len(candidate) <= max_chars:
                current = candidate
            else:
                flush_current()
                current = section
            continue

        flush_current()
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n{2,}", section) if paragraph.strip()]
        buffer = ""
        for paragraph in paragraphs:
            candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
            if len(candidate) <= max_chars:
                buffer = candidate
                continue
            if buffer:
                chunks.append(buffer.strip())
            if len(paragraph) <= max_chars:
                buffer = paragraph
                continue

            start = 0
            step = max(max_chars - overlap_chars, 1)
            while start < len(paragraph):
                piece = paragraph[start:start + max_chars].strip()
                if piece:
                    chunks.append(piece)
                start += step
            buffer = ""

        if buffer:
            chunks.append(buffer.strip())

    flush_current()
    return chunks
