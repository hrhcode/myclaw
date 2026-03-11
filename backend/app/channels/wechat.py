"""
企业微信通道模块
实现企业微信机器人的消息收发
"""

import hashlib
import logging
import time
import xml.etree.ElementTree as ET
from typing import Any, Optional

import httpx
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.channels.base import BaseChannel
from app.config import get_config

logger = logging.getLogger(__name__)


class WechatChannel(BaseChannel):
    """
    企业微信通道
    处理企业微信机器人的消息收发
    """

    def __init__(self):
        """初始化企业微信通道"""
        super().__init__("wechat")
        config = get_config()
        self.corp_id = config.wechat.corp_id
        self.agent_id = config.wechat.agent_id
        self.secret = config.wechat.secret
        self.token = config.wechat.token
        self.encoding_aes_key = config.wechat.encoding_aes_key
        
        self._access_token: Optional[str] = None
        self._token_expire_time: int = 0

    def verify_signature(self, signature: str, timestamp: str, nonce: str, echostr: str = "") -> bool:
        """
        验证微信签名
        
        Args:
            signature: 签名
            timestamp: 时间戳
            nonce: 随机数
            echostr: 随机字符串（URL 验证时使用）
            
        Returns:
            签名是否有效
        """
        if not self.token:
            return False
            
        items = [self.token, timestamp, nonce]
        items.sort()
        sha1 = hashlib.sha1("".join(items).encode()).hexdigest()
        return sha1 == signature

    async def get_access_token(self) -> str:
        """
        获取企业微信 access_token
        
        Returns:
            access_token
        """
        if self._access_token and time.time() < self._token_expire_time:
            return self._access_token
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.secret,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
        
        if data.get("errcode", 0) != 0:
            raise Exception(f"获取 access_token 失败: {data.get('errmsg')}")
        
        self._access_token = data["access_token"]
        self._token_expire_time = time.time() + data["expires_in"] - 300
        
        return self._access_token

    async def send_message(
        self,
        to: str,
        content: str,
        msg_type: str = "text",
        **kwargs,
    ) -> bool:
        """
        发送消息到企业微信
        
        Args:
            to: 接收者（用户 ID）
            content: 消息内容
            msg_type: 消息类型
            **kwargs: 其他参数
            
        Returns:
            是否发送成功
        """
        try:
            access_token = await self.get_access_token()
            
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send"
            params = {"access_token": access_token}
            
            data = {
                "touser": to,
                "msgtype": msg_type,
                "agentid": self.agent_id,
                msg_type: {"content": content},
                "safe": 0,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, params=params, json=data)
                result = response.json()
            
            if result.get("errcode", 0) != 0:
                logger.error(f"发送消息失败: {result.get('errmsg')}")
                return False
            
            logger.info(f"消息发送成功: to={to}")
            return True
            
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False

    async def handle_message(self, message: dict[str, Any]) -> Optional[str]:
        """
        处理接收到的微信消息
        
        Args:
            message: 消息内容（已解析的 XML）
            
        Returns:
            回复消息内容
        """
        msg_type = message.get("MsgType", "")
        
        if msg_type == "text":
            content = message.get("Content", "")
            from_user = message.get("FromUserName", "")
            
            logger.info(f"收到文本消息: from={from_user}, content={content[:50]}...")
            
            return None
        
        return None

    def parse_message(self, xml_content: str) -> dict[str, Any]:
        """
        解析微信消息 XML
        
        Args:
            xml_content: XML 内容
            
        Returns:
            解析后的消息字典
        """
        root = ET.fromstring(xml_content)
        message = {}
        
        for child in root:
            message[child.tag] = child.text
        
        return message

    def decrypt_message(self, encrypted_msg: str) -> str:
        """
        解密企业微信消息
        
        Args:
            encrypted_msg: 加密的消息
            
        Returns:
            解密后的消息
        """
        if not self.encoding_aes_key:
            return encrypted_msg
        
        key = bytes.fromhex(self.encoding_aes_key + self.encoding_aes_key[:8])
        
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        decryptor = cipher.decryptor()
        
        encrypted_data = bytes.fromhex(encrypted_msg)
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()
        
        msg_len = int.from_bytes(unpadded_data[16:20], "big")
        message = unpadded_data[20 : 20 + msg_len].decode("utf-8")
        
        return message

    def encrypt_message(self, message: str) -> str:
        """
        加密企业微信消息
        
        Args:
            message: 原始消息
            
        Returns:
            加密后的消息
        """
        if not self.encoding_aes_key:
            return message
        
        key = bytes.fromhex(self.encoding_aes_key + self.encoding_aes_key[:8])
        
        msg_bytes = message.encode("utf-8")
        msg_len = len(msg_bytes)
        
        import os
        random_bytes = os.urandom(16)
        
        data = random_bytes + msg_len.to_bytes(4, "big") + msg_bytes
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(key), modes.ECB())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return encrypted_data.hex()
