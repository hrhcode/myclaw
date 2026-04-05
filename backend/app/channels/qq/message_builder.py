from __future__ import annotations

from typing import List

# QQ 官方 API 消息长度限制
MAX_QQ_MSG_LENGTH = 2000


def split_long_text(text: str, max_length: int = MAX_QQ_MSG_LENGTH) -> List[str]:
    """将长文本拆分为不超过 max_length 的片段。"""
    if len(text) <= max_length:
        return [text]

    chunks: List[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # 尝试在换行符处截断
        cut_pos = remaining.rfind("\n", 0, max_length)
        if cut_pos == -1 or cut_pos < max_length // 2:
            # 尝试在句号、空格处截断
            for sep in ["。", "！", "？", "；", "，", " "]:
                cut_pos = remaining.rfind(sep, 0, max_length)
                if cut_pos != -1 and cut_pos >= max_length // 2:
                    cut_pos += len(sep)
                    break
            else:
                cut_pos = max_length

        chunks.append(remaining[:cut_pos])
        remaining = remaining[cut_pos:]

    return chunks
