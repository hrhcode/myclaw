"""
QQ 通道模块
基于 NapCat/go-cqhttp 实现的 QQ 机器人通道
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import aiohttp

from app.channels.base import BaseChannel
from app.gateway.types import Message

logger = logging.getLogger(__name__)


class QQChannel(BaseChannel):
    """
    QQ 通道
    基于 NapCat/go-cqhttp 实现的 QQ 机器人通道
    
    支持功能:
    - 私聊消息收发
    - 群聊消息收发
    - WebSocket 事件监听
    """
    
    def __init__(
        self,
        api_url: str = "http://localhost:6099",
        access_token: Optional[str] = None,
    ):
        """
        初始化 QQ 通道
        
        Args:
            api_url: NapCat API 地址
            access_token: 访问令牌
        """
        super().__init__(channel_name="qq")
        self._api_url = api_url.rstrip("/")
        self._access_token = access_token
        self._ws_url = self._api_url.replace("http://", "ws://").replace("https://", "wss://")
        self._ws = None
        self._ws_task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def start(self) -> None:
        """
        启动 QQ 通道
        
        连接 WebSocket 并开始监听消息
        """
        try:
            self._running = True
            self._session = aiohttp.ClientSession()
            
            self._ws_task = asyncio.create_task(self._connect_and_listen())
            
            await asyncio.sleep(0.5)
            
            logger.info(f"QQ 通道已启动: {self._api_url}")
        except Exception as e:
            self._error = str(e)
            self._running = False
            logger.error(f"QQ 通道启动失败: {e}")
    
    async def stop(self) -> None:
        """
        停止 QQ 通道
        
        断开 WebSocket 连接
        """
        self._running = False
        self._connected = False
        
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            self._ws_task = None
        
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info("QQ 通道已停止")
    
    async def _connect_and_listen(self) -> None:
        """
        连接 WebSocket 并监听消息
        """
        retry_count = 0
        max_retries = 5
        retry_delay = 5
        
        while self._running and retry_count < max_retries:
            try:
                ws_url = f"{self._ws_url}/ws"
                headers = {}
                if self._access_token:
                    headers["Authorization"] = f"Bearer {self._access_token}"
                
                async with self._session.ws_connect(ws_url, headers=headers) as ws:
                    self._ws = ws
                    self._connected = True
                    self._error = None
                    retry_count = 0
                    
                    logger.info("QQ WebSocket 已连接")
                    
                    async for msg in ws:
                        if not self._running:
                            break
                        
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await self._handle_ws_message(msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WebSocket 错误: {ws.exception()}")
                            break
                
                self._connected = False
                self._ws = None
                
            except Exception as e:
                self._connected = False
                self._error = str(e)
                retry_count += 1
                logger.error(f"QQ WebSocket 连接失败 ({retry_count}/{max_retries}): {e}")
                
                if self._running and retry_count < max_retries:
                    await asyncio.sleep(retry_delay)
        
        if retry_count >= max_retries:
            logger.error("QQ 通道连接重试次数已达上限")
    
    async def _handle_ws_message(self, data: str) -> None:
        """
        处理 WebSocket 消息
        
        Args:
            data: JSON 格式的消息数据
        """
        try:
            event = json.loads(data)
            
            if event.get("post_type") == "message":
                message = self._parse_message(event)
                if message:
                    await self._on_message(message)
                    
        except json.JSONDecodeError as e:
            logger.error(f"解析 WebSocket 消息失败: {e}")
        except Exception as e:
            logger.error(f"处理 WebSocket 消息失败: {e}")
    
    def _parse_message(self, data: Dict[str, Any]) -> Optional[Message]:
        """
        解析 QQ 消息格式
        
        Args:
            data: QQ 消息数据
            
        Returns:
            Message 对象，解析失败返回 None
        """
        try:
            message_type = data.get("message_type", "")
            is_group = message_type == "group"
            
            content = self._extract_text(data.get("message", []))
            if not content:
                return None
            
            user_id = str(data.get("user_id", ""))
            sender = data.get("sender", {})
            user_name = sender.get("nickname", "") or sender.get("card", "") or user_id
            
            message = Message(
                id=str(data.get("message_id", "")),
                content=content,
                user_id=user_id,
                user_name=user_name,
                group_id=str(data.get("group_id", "")) if is_group else None,
                group_name="",
                is_group=is_group,
                channel="qq",
                raw=data,
            )
            
            return message
            
        except Exception as e:
            logger.error(f"解析 QQ 消息失败: {e}")
            return None
    
    def _extract_text(self, message: Any) -> str:
        """
        从消息中提取文本内容
        
        Args:
            message: 消息内容（可以是字符串或消息段列表）
            
        Returns:
            文本内容
        """
        if isinstance(message, str):
            return message
        
        if isinstance(message, list):
            texts = []
            for segment in message:
                if isinstance(segment, dict) and segment.get("type") == "text":
                    texts.append(segment.get("data", {}).get("text", ""))
            return "".join(texts)
        
        return ""
    
    async def send(self, target: str, message: str) -> bool:
        """
        发送 QQ 消息
        
        Args:
            target: 目标标识，格式为 "user:xxx" 或 "group:xxx"
            message: 消息内容
            
        Returns:
            是否发送成功
        """
        if not self._session:
            logger.error("QQ 通道未初始化")
            return False
        
        try:
            if ":" in target:
                kind, target_id = target.split(":", 1)
            else:
                kind = "user"
                target_id = target
            
            if kind == "group":
                endpoint = f"{self._api_url}/send_group_msg"
                params = {"group_id": int(target_id), "message": message}
            else:
                endpoint = f"{self._api_url}/send_private_msg"
                params = {"user_id": int(target_id), "message": message}
            
            async with self._session.post(endpoint, json=params) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("status") == "ok":
                        logger.debug(f"QQ 消息发送成功: {kind}:{target_id}")
                        return True
                    else:
                        logger.error(f"QQ 消息发送失败: {result}")
                        return False
                else:
                    logger.error(f"QQ 消息发送失败: HTTP {resp.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"QQ 消息发送失败: {e}")
            return False
    
    async def get_group_info(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        获取群信息
        
        Args:
            group_id: 群号
            
        Returns:
            群信息字典
        """
        if not self._session:
            return None
        
        try:
            async with self._session.get(
                f"{self._api_url}/get_group_info",
                params={"group_id": group_id},
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("status") == "ok":
                        return result.get("data")
        except Exception as e:
            logger.error(f"获取群信息失败: {e}")
        
        return None
    
    async def get_login_info(self) -> Optional[Dict[str, Any]]:
        """
        获取登录信息
        
        Returns:
            登录信息字典
        """
        if not self._session:
            return None
        
        try:
            async with self._session.get(f"{self._api_url}/get_login_info") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("status") == "ok":
                        return result.get("data")
        except Exception as e:
            logger.error(f"获取登录信息失败: {e}")
        
        return None
