from __future__ import annotations

import json
import re
from typing import Any


def _slugify(name: str) -> str:
    """将名称转为适合做 id 的 slug。"""
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "mcp-server"


def _normalize_server(name: str, raw: dict[str, Any]) -> dict[str, Any]:
    """将 Claude Desktop 单项配置转为内部格式。"""
    server: dict[str, Any] = {"name": name}

    if "command" in raw:
        server["transport"] = "stdio"
        server["command"] = raw["command"]
        args = raw.get("args", [])
        server["args"] = args if isinstance(args, list) else [str(args)]
    elif "url" in raw:
        server["transport"] = "http"
        server["endpoint"] = raw["url"]
    elif "endpoint" in raw:
        transport = raw.get("type", raw.get("transport", "http"))
        server["transport"] = transport if transport in ("http", "sse") else "http"
        server["endpoint"] = raw["endpoint"]
    else:
        raise ValueError(f"服务 '{name}' 缺少 command 或 url 字段")

    if "env" in raw and isinstance(raw["env"], dict):
        server["env"] = {str(k): str(v) for k, v in raw["env"].items()}
    if "headers" in raw and isinstance(raw["headers"], dict):
        server["headers"] = {str(k): str(v) for k, v in raw["headers"].items()}

    server["description"] = raw.get("description", "")
    server["enabled"] = raw.get("enabled", True)
    server["timeout_seconds"] = raw.get("timeout", raw.get("timeout_seconds", 8))
    if not isinstance(server["timeout_seconds"], int):
        server["timeout_seconds"] = 8

    return server


def _parse_claude_desktop(data: dict[str, Any]) -> tuple[list[dict], list[str]]:
    """解析 Claude Desktop 格式: { "mcpServers": { ... } }"""
    servers: list[dict] = []
    errors: list[str] = []
    mcp_servers = data.get("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        return servers, ["mcpServers 字段不是对象类型"]
    for name, cfg in mcp_servers.items():
        if not isinstance(cfg, dict):
            errors.append(f"服务 '{name}' 配置不是对象类型")
            continue
        try:
            servers.append(_normalize_server(name, cfg))
        except ValueError as exc:
            errors.append(str(exc))
    return servers, errors


def _parse_native_list(data: list[Any]) -> tuple[list[dict], list[str]]:
    """解析原生格式: [ { "name": "...", ... } ]"""
    servers: list[dict] = []
    errors: list[str] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"第 {idx + 1} 项不是对象类型")
            continue
        name = item.get("name", f"mcp-server-{idx + 1}")
        try:
            server: dict[str, Any] = {
                "name": name,
                "description": item.get("description", ""),
                "transport": item.get("transport", "stdio"),
                "enabled": item.get("enabled", True),
                "timeout_seconds": item.get("timeout_seconds", 8),
            }
            if server["transport"] == "stdio":
                server["command"] = item.get("command")
                if not server["command"]:
                    raise ValueError(f"服务 '{name}' 使用 stdio 传输但缺少 command")
                server["args"] = item.get("args", [])
            else:
                server["endpoint"] = item.get("endpoint")
                if not server["endpoint"]:
                    raise ValueError(f"服务 '{name}' 使用 {server['transport']} 传输但缺少 endpoint")
            if "env" in item:
                server["env"] = item["env"]
            if "headers" in item:
                server["headers"] = item["headers"]
            servers.append(server)
        except ValueError as exc:
            errors.append(str(exc))
    return servers, errors


def _parse_single_object(data: dict[str, Any]) -> tuple[list[dict], list[str]]:
    """解析单对象格式: { "name": "...", "command": "..." } 或 { "command": "..." }"""
    name = data.get("name", "imported-server")
    try:
        return [_normalize_server(name, data)], []
    except ValueError as exc:
        return [], [str(exc)]


def parse_mcp_config(json_text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """解析多种格式的 MCP 配置 JSON，返回 (服务器配置列表, 错误信息列表)。

    支持的格式:
    1. Claude Desktop: { "mcpServers": { "name": { "command": ..., "args": [...] } } }
    2. 原生格式: [ { "name": "...", "transport": "...", ... } ]
    3. 单对象: { "name": "...", "command": "..." }
    4. 嵌套: { "mcp": { "servers": { ... } } }
    """
    text = json_text.strip()
    if not text:
        return [], ["输入为空"]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return [], [f"JSON 语法错误: {exc.msg} (第 {exc.lineno} 行, 第 {exc.colno} 列)"]

    # 原生数组格式
    if isinstance(data, list):
        return _parse_native_list(data)

    if not isinstance(data, dict):
        return [], ["配置必须是 JSON 对象或数组"]

    # Claude Desktop 格式
    if "mcpServers" in data:
        return _parse_claude_desktop(data)

    # 嵌套格式: { "mcp": { "servers": { ... } } }
    if "mcp" in data and isinstance(data["mcp"], dict):
        inner = data["mcp"]
        if "servers" in inner and isinstance(inner["servers"], dict):
            return _parse_claude_desktop({"mcpServers": inner["servers"]})

    # VS Code / 通用 { "servers": { ... } } 格式
    if "servers" in data and isinstance(data["servers"], dict):
        return _parse_claude_desktop({"mcpServers": data["servers"]})

    # 单对象格式
    if "command" in data or "url" in data or "endpoint" in data:
        return _parse_single_object(data)

    return [], ["无法识别的 MCP 配置格式，请检查 JSON 结构"]
