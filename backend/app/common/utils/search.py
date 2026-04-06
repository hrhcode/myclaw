"""
搜索相关工具函数模块
"""
import logging
from typing import List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def normalize_bm25_score(bm25_rank: int) -> float:
    """
    将BM25排名转换为0-1分数
    
    Args:
        bm25_rank: BM25排名（越小越好）
        
    Returns:
        归一化分数 (0-1)
    """
    return 1.0 / (1.0 + max(0, bm25_rank))


def mmr_rerank(
    results: List[Tuple[object, float, str]],
    lambda_param: float = 0.7,
    top_k: int = 5
) -> List[Tuple[object, float, str]]:
    """
    使用MMR算法对搜索结果进行重排序
    
    Args:
        results: 原始搜索结果 (对象, 分数, 来源)
        lambda_param: MMR参数，平衡相关性和多样性 (0-1)
        top_k: 返回结果数量
        
    Returns:
        重排序后的结果列表
    """
    from app.common.utils.text import jaccard_similarity
    
    if not results:
        return []
    
    selected = []
    remaining = results.copy()
    
    for _ in range(min(top_k, len(results))):
        if not remaining:
            break
        
        best_idx = 0
        best_score = -float('inf')
        
        for i, (obj, score, source) in enumerate(remaining):
            mmr_score = lambda_param * score
            
            for selected_obj, _, _ in selected:
                selected_text = getattr(selected_obj, 'content', '')
                current_text = getattr(obj, 'content', '')
                similarity = jaccard_similarity(selected_text, current_text)
                mmr_score -= (1 - lambda_param) * similarity
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i
        
        selected.append(remaining[best_idx])
        del remaining[best_idx]
    
    return selected


def apply_temporal_decay(
    results: List[Tuple[object, float, str]],
    half_life_days: int = 30,
    enable_decay: bool = True
) -> List[Tuple[object, float, str]]:
    """
    对搜索结果应用时间衰减
    
    Args:
        results: 原始搜索结果 (对象, 分数, 来源)
        half_life_days: 半衰期天数
        enable_decay: 是否启用时间衰减
        
    Returns:
        应用衰减后的结果列表
    """
    if not enable_decay:
        return results
    
    decayed_results = []
    current_time = datetime.now()
    
    for obj, score, source in results:
        # Evergreen 记忆不衰减
        if getattr(obj, 'is_evergreen', False):
            decayed_results.append((obj, score, source))
            continue

        if not obj or not hasattr(obj, 'created_at'):
            decayed_results.append((obj, score, source))
            continue
        
        created_at = getattr(obj, 'created_at', None)
        if not created_at:
            decayed_results.append((obj, score, source))
            continue
        
        age_days = (current_time - created_at).days
        
        if age_days < 0:
            decayed_results.append((obj, score, source))
            continue
        
        lambda_param = 0.693 / half_life_days
        
        decay_factor = 2.718 ** (-lambda_param * age_days)
        
        decayed_score = score * decay_factor
        
        decayed_results.append((obj, decayed_score, source))
    
    return decayed_results
