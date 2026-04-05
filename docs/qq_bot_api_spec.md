# QQ 机器人官方 API 规范整理

> 基于 QQ 开放平台官方文档整理：https://bot.q.qq.com/wiki/develop/api-v2/

## 一、接入票据

注册创建机器人后获得的接入票据：

| 名称 | 描述 | 备注 |
|------|------|------|
| AppID | 机器人 ID | 必须使用 |
| AppSecret | 机器人密钥 | 用于 OAuth 场景进行请求签名 |
| Token | 机器人 Token | **已废弃**，请使用 Access Token 鉴权方式 |

## 二、API 调用与鉴权

### 2.1 获取 Access Token

```http
POST https://bots.qq.com/app/getAppAccessToken
Content-Type: application/json

{
  "appId": "YOUR_APP_ID",
  "clientSecret": "YOUR_APP_SECRET"
}
```

**返回：**
```json
{
  "access_token": "ACCESS_TOKEN",
  "expires_in": "7200"
}
```

**注意事项：**
- access_token 有效期 7200 秒
- 在过期前 60 秒内请求会获得新 token，旧 token 在这 60 秒内仍有效
- 需要开发者自行管理 token 刷新

### 2.2 API 鉴权方式

**统一 API 地址：** `https://api.sgroup.qq.com`

**请求头：**
```
Authorization: QQBot {ACCESS_TOKEN}
Content-Type: application/json
```

## 三、WebSocket 事件订阅

### 3.1 连接流程

1. **获取网关地址**：调用 `/gateway/bot` 接口获取 WebSocket 地址
2. **建立连接**：连接 WebSocket，收到 `OP 10 Hello` 消息
3. **发送鉴权**：发送 `OP 2 Identify` 进行登录鉴权
4. **心跳保活**：按周期发送 `OP 1 Heartbeat` 心跳

### 3.2 Payload 数据结构

```json
{
  "id": "event_id",
  "op": 0,
  "d": {},
  "s": 42,
  "t": "GATEWAY_EVENT_NAME"
}
```

| 字段 | 描述 |
|------|------|
| id | 事件 ID |
| op | OpCode 操作码 |
| s | 消息序列号（下行消息唯一标识） |
| t | 事件类型（op=0 时有效） |
| d | 事件内容 |

### 3.3 OpCode 操作码

| Code | 名称 | 客户端行为 | 描述 |
|------|------|-----------|------|
| 0 | Dispatch | Receive | 服务端消息推送 |
| 1 | Heartbeat | Send/Receive | 心跳 |
| 2 | Identify | Send | 客户端鉴权 |
| 6 | Resume | Send | 恢复连接 |
| 7 | Reconnect | Receive | 服务端通知重连 |
| 9 | Invalid Session | Receive | 参数错误 |
| 10 | Hello | Receive | 连接建立后第一条消息 |
| 11 | Heartbeat ACK | Receive | 心跳响应 |
| 12 | HTTP Callback ACK | Reply | HTTP 回调确认 |
| 13 | 回调地址验证 | Receive | 平台验证回调地址 |

### 3.4 Identify 鉴权帧

```json
{
  "op": 2,
  "d": {
    "token": "QQBot {ACCESS_TOKEN}",
    "intents": 513,
    "shard": [0, 4],
    "properties": {
      "$os": "linux",
      "$browser": "my_library",
      "$device": "my_library"
    }
  }
}
```

### 3.5 Intents 事件订阅

**位运算计算方式：** `intents = 0 | (1 << N) | (1 << M) | ...`

| Intent | 位移 | 事件类型 |
|--------|------|----------|
| GUILDS | 0 | 频道事件（加入/退出频道、子频道创建/更新/删除） |
| GUILD_MEMBERS | 1 | 成员事件（加入/更新/移除） |
| GUILD_MESSAGES | 9 | 频道全量消息（私域机器人） |
| GUILD_MESSAGE_REACTIONS | 10 | 表情表态事件 |
| DIRECT_MESSAGE | 12 | 频道私信消息 |
| **GROUP_AND_C2C_EVENT** | **25** | **QQ群聊/单聊事件** ⭐ |
| INTERACTION | 26 | 互动事件 |
| MESSAGE_AUDIT | 27 | 消息审核事件 |
| FORUMS_EVENT | 28 | 论坛事件（私域机器人） |
| AUDIO_ACTION | 29 | 音频事件 |
| PUBLIC_GUILD_MESSAGES | 30 | 频道@机器人消息 |

### 3.6 GROUP_AND_C2C_EVENT (1 << 25) 事件详情

**这是 QQ 群聊和单聊场景的核心事件！**

| 事件类型 | 触发场景 |
|----------|----------|
| `C2C_MESSAGE_CREATE` | 用户单聊发消息给机器人 |
| `GROUP_AT_MESSAGE_CREATE` | 用户在群里@机器人 |
| `FRIEND_ADD` | 用户添加机器人好友 |
| `FRIEND_DEL` | 用户删除机器人 |
| `GROUP_ADD_ROBOT` | 机器人被添加到群聊 |
| `GROUP_DEL_ROBOT` | 机器人被移出群聊 |

### 3.7 心跳机制

**发送心跳：**
```json
{
  "op": 1,
  "d": 251  // 最新收到的消息序列号 s，首次连接传 null
}
```

**心跳响应：**
```json
{
  "op": 11
}
```

### 3.8 断线重连 Resume

```json
{
  "op": 6,
  "d": {
    "token": "QQBot {ACCESS_TOKEN}",
    "session_id": "session_id",
    "seq": 1337
  }
}
```

## 四、消息发送 API

### 4.1 场景区分

| 场景 | API 路径 | 说明 |
|------|----------|------|
| **QQ 单聊** | `POST /v2/users/{openid}/messages` | openid 来自事件 |
| **QQ 群聊** | `POST /v2/groups/{group_openid}/messages` | group_openid 来自事件 |
| 频道子频道 | `POST /channels/{channel_id}/messages` | 频道场景 |
| 频道私信 | `POST /dms/{guild_id}/messages` | 频道私信场景 |

### 4.2 单聊消息

**请求：**
```http
POST /v2/users/{openid}/messages
Authorization: QQBot {ACCESS_TOKEN}
Content-Type: application/json

{
  "content": "消息内容",
  "msg_type": 0,
  "msg_id": "回复的消息ID（被动消息）"
}
```

**返回：**
```json
{
  "id": "消息唯一ID",
  "timestamp": 1234567890
}
```

### 4.3 群聊消息

**请求：**
```http
POST /v2/groups/{group_openid}/messages
Authorization: QQBot {ACCESS_TOKEN}
Content-Type: application/json

{
  "content": "消息内容",
  "msg_type": 0,
  "msg_id": "回复的消息ID（被动消息）"
}
```

### 4.4 消息类型

| msg_type | 说明 |
|----------|------|
| 0 | 文本消息 |
| 2 | Markdown |
| 3 | Ark 消息 |
| 4 | Embed |
| 7 | 富媒体 |

### 4.5 消息频次限制

| 场景 | 主动消息 | 被动消息 |
|------|----------|----------|
| 单聊 | 每月 4 条/用户 | 60 分钟内最多 5 次/消息 |
| 群聊 | 每月 4 条/群 | 5 分钟内最多 5 次/消息 |
| 频道子频道 | 每天 20 条/子频道 | 5 分钟有效期 |

## 五、事件数据结构

### 5.1 单聊消息事件 (C2C_MESSAGE_CREATE)

```json
{
  "author": {
    "user_openid": "E4F4AEA33253A2797FB897C50B81D7ED"
  },
  "content": "消息内容",
  "id": "ROBOT1.0_xxx",
  "timestamp": "2023-11-06T13:37:18+08:00"
}
```

### 5.2 群聊@机器人事件 (GROUP_AT_MESSAGE_CREATE)

```json
{
  "author": {
    "member_openid": "E4F4AEA33253A2797FB897C50B81D7ED"
  },
  "content": " 消息内容",
  "group_openid": "C9F778FE6ADF9D1D1DBE395BF744A33A",
  "id": "ROBOT1.0_xxx",
  "timestamp": "2023-11-06T13:37:18+08:00"
}
```

### 5.3 频道@机器人事件 (AT_MESSAGE_CREATE)

```json
{
  "author": {
    "id": "1234",
    "username": "abc",
    "bot": false
  },
  "channel_id": "100010",
  "content": "<@!机器人ID> 消息内容",
  "guild_id": "18700000000001",
  "id": "0812345677890abcdef",
  "timestamp": "2021-05-20T15:14:58+08:00"
}
```

## 六、唯一身份机制

不同 bot 获取的用户/群标识不同：

| 场景 | 标识名称 | 说明 |
|------|----------|------|
| 单聊 | `user_openid` | 用户在当前 bot 下的唯一标识 |
| 群聊 | `group_openid` | 群在当前 bot 下的唯一标识 |
| 群成员 | `member_openid` | 用户在当前群+bot 下的唯一标识 |
| 频道 | `user.id` | 频道用户 ID |

## 七、错误码

| Code | 含义 | 处理方式 |
|------|------|----------|
| 4001 | 无效的 opcode | 重新 Identify |
| 4002 | 无效的 payload | 重新 Identify |
| 4007 | seq 错误 | Resume |
| 4006 | 无效的 session id | Identify |
| 4008 | 发送过快 | 重连后 Resume |
| 4009 | 连接过期 | Resume |
| 4010 | 无效的 shard | 重新 Identify |
| 4013 | 无效的 intent | 重新 Identify |
| 4014 | intent 无权限 | 重新 Identify |
| 4914 | 机器人已下架 | 联系官方 |
| 4915 | 机器人已封禁 | 申请解封 |

## 八、关键注意事项

1. **场景区分**：QQ 群聊/单聊 与 频道 是两套不同的体系
   - 频道使用 `AT_MESSAGE_CREATE`、`DIRECT_MESSAGE_CREATE`
   - 群聊/单聊使用 `GROUP_AT_MESSAGE_CREATE`、`C2C_MESSAGE_CREATE`

2. **Intents 配置**：需要根据场景正确配置 intents
   - 频道场景：`1 << 30` (PUBLIC_GUILD_MESSAGES)
   - 群聊/单聊：`1 << 25` (GROUP_AND_C2C_EVENT)

3. **用户标识**：不同场景使用不同的用户标识字段
   - 频道：`author.id`
   - 单聊：`author.user_openid`
   - 群聊：`author.member_openid`

4. **消息发送 API**：不同场景使用不同的 API 端点
