from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParsedMessage:
    text: str = ""
    is_at: bool = False
    images: List[str] = field(default_factory=list)
    at_user_ids: List[str] = field(default_factory=list)


# QQ 官方消息中 @用户 的格式：<@!user_id>
_MENTION_RE = re.compile(r"<@!(\d+)>")


def parse_official_message(
    event_data: Dict[str, Any],
    bot_id: Optional[str] = None,
) -> ParsedMessage:
    """解析 QQ 官方机器人消息事件，提取文本、@信息和图片。

    QQ 官方 API 消息格式：
    - content: 纯文本，@某人 表示为 <@!user_id>
    - attachments: 附件列表，每个包含 url（图片等）
    - mention_everyone: 是否 @了所有人
    """
    result = ParsedMessage()

    # 解析 content 中的文本和 @信息
    content = event_data.get("content", "").strip()

    # 提取所有 @用户 ID
    mentions = _MENTION_RE.findall(content)
    result.at_user_ids = mentions

    # 判断是否 @了机器人
    if bot_id and bot_id in mentions:
        result.is_at = True

    # 去掉 content 中的 <@!xxx> 标记，保留纯文本
    clean_text = _MENTION_RE.sub("", content).strip()
    result.text = clean_text

    # 解析附件（图片等）
    attachments = event_data.get("attachments", [])
    for att in attachments:
        url = att.get("url", "")
        if url and _is_image_url(url):
            result.images.append(url)

    return result


def should_respond(
    parsed: ParsedMessage,
    event_type: str,
    trigger_mode: str,
    private_enabled: bool,
) -> bool:
    """判断是否应该响应该消息。

    event_type:
    - AT_MESSAGE_CREATE: 频道内 @机器人 的消息
    - DIRECT_MESSAGE_CREATE: 频道私信消息
    - C2C_MESSAGE_CREATE: QQ 单聊消息
    - GROUP_AT_MESSAGE_CREATE: QQ 群聊 @机器人 消息
    """
    # 频道私信
    if event_type == "DIRECT_MESSAGE_CREATE":
        return private_enabled

    # QQ 单聊
    if event_type == "C2C_MESSAGE_CREATE":
        return private_enabled

    # 频道 @ 消息
    if event_type == "AT_MESSAGE_CREATE":
        if trigger_mode == "all_messages":
            return True
        # 频道消息本身就是 @触发 的，所以 at_only 和 at_or_mention 都响应
        return True

    # QQ 群聊 @ 消息
    if event_type == "GROUP_AT_MESSAGE_CREATE":
        if trigger_mode == "all_messages":
            return True
        return True

    return False


def _is_image_url(url: str) -> bool:
    """简单判断 URL 是否为图片。"""
    lower = url.lower().split("?")[0]
    return any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"))
