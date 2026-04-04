from __future__ import annotations

import asyncio
import json
import os
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import MCP_SERVERS_CONFIG_KEY
from app.core.database import AsyncSessionLocal
from app.dao.config_dao import ConfigDAO
from app.tools import ToolResult, create_tool, tool_registry

DEFAULT_PROTOCOL_VERSION = "2024-11-05"
DEFAULT_CLIENT_INFO = {"name": "myclaw", "version": "1.0.0"}
MCP_TOOL_PREFIX = "mcp__"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workspace_root() -> str:
    root = os.getenv("MYCLAW_DEFAULT_WORKSPACE")
    if root:
        return root

    cwd = Path.cwd()
    if cwd.name.lower() == "backend":
        return str(cwd.parent)
    return str(cwd)


def _default_servers() -> list[dict[str, Any]]:
    workspace_root = _workspace_root()
    docs_root = str(Path(workspace_root).parent / "docs")
    now = _utc_now_iso()
    return [
        {
            "id": "filesystem",
            "name": "Filesystem Gateway",
            "description": "面向本地工作区的文件、目录和批量扫描能力，适合知识沉淀与项目巡检。",
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", workspace_root],
            "endpoint": None,
            "enabled": True,
            "tags": ["本地文件", "知识库联动", "推荐"],
            "workspaces": [workspace_root, docs_root],
            "env": {},
            "headers": {},
            "timeout_seconds": 8,
            "status": "disabled",
            "resources": 0,
            "tools": 0,
            "prompts": 0,
            "alerts": 0,
            "capabilities": [],
            "tool_names": [],
            "resource_names": [],
            "prompt_names": [],
            "status_reason": "尚未探测",
            "last_probe_at": None,
            "updated_at": now,
            "events": [],
            "tool_definitions": [],
        },
        {
            "id": "postgres",
            "name": "Postgres Ops",
            "description": "把数据库查询、表结构浏览和只读巡检纳入 MCP 能力面板，适合运营与排障。",
            "transport": "http",
            "command": None,
            "args": [],
            "endpoint": "http://localhost:8811/mcp",
            "enabled": False,
            "tags": ["数据库", "只读巡检"],
            "workspaces": ["backend", "ops"],
            "env": {},
            "headers": {},
            "timeout_seconds": 8,
            "status": "disabled",
            "resources": 0,
            "tools": 0,
            "prompts": 0,
            "alerts": 0,
            "capabilities": [],
            "tool_names": [],
            "resource_names": [],
            "prompt_names": [],
            "status_reason": "尚未探测",
            "last_probe_at": None,
            "updated_at": now,
            "events": [],
            "tool_definitions": [],
        },
        {
            "id": "browser",
            "name": "Browser Runner",
            "description": "用于网页采集、流程回放和自动化截图的浏览器能力，后续可与自动化任务联动。",
            "transport": "sse",
            "command": None,
            "args": [],
            "endpoint": "http://localhost:8933/events",
            "enabled": False,
            "tags": ["浏览器", "自动化"],
            "workspaces": ["frontend"],
            "env": {},
            "headers": {},
            "timeout_seconds": 8,
            "status": "disabled",
            "resources": 0,
            "tools": 0,
            "prompts": 0,
            "alerts": 0,
            "capabilities": [],
            "tool_names": [],
            "resource_names": [],
            "prompt_names": [],
            "status_reason": "尚未探测",
            "last_probe_at": None,
            "updated_at": now,
            "events": [],
            "tool_definitions": [],
        },
    ]


class McpService:
    async def list_servers(self, db: AsyncSession) -> list[dict[str, Any]]:
        return await self._load_servers(db)

    async def get_stats(self, db: AsyncSession) -> dict[str, int]:
        servers = await self._load_servers(db)
        return {
            "total": len(servers),
            "enabled": sum(1 for item in servers if item.get("enabled")),
            "resources": sum(int(item.get("resources", 0)) for item in servers),
            "alerts": sum(int(item.get("alerts", 0)) for item in servers),
        }

    async def create_server(self, db: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
        servers = await self._load_servers(db)
        now = _utc_now_iso()
        server = {
            "id": payload.get("id") or uuid4().hex[:12],
            "name": payload["name"],
            "description": payload.get("description", ""),
            "transport": payload.get("transport", "stdio"),
            "command": payload.get("command"),
            "args": payload.get("args", []),
            "endpoint": payload.get("endpoint"),
            "enabled": payload.get("enabled", True),
            "tags": payload.get("tags", []),
            "workspaces": payload.get("workspaces", []),
            "env": payload.get("env", {}),
            "headers": payload.get("headers", {}),
            "timeout_seconds": payload.get("timeout_seconds", 8),
            "status": "disabled" if not payload.get("enabled", True) else "degraded",
            "resources": 0,
            "tools": 0,
            "prompts": 0,
            "alerts": 0,
            "capabilities": [],
            "tool_names": [],
            "resource_names": [],
            "prompt_names": [],
            "status_reason": "创建后尚未探测",
            "last_probe_at": None,
            "updated_at": now,
            "events": [
                {
                    "id": f"created-{uuid4().hex[:8]}",
                    "level": "info",
                    "message": "服务配置已创建，等待首次探测。",
                    "time": "刚刚",
                }
            ],
        }
        self._validate_server(server)
        servers.append(server)
        await self._save_servers(db, servers)
        await self.sync_runtime_tools(db, servers)
        return server

    async def update_server(self, db: AsyncSession, server_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        servers = await self._load_servers(db)
        server = next((item for item in servers if item["id"] == server_id), None)
        if not server:
            return None

        for key, value in payload.items():
            server[key] = value
        server["updated_at"] = _utc_now_iso()
        self._validate_server(server)
        if not server.get("enabled"):
            server["status"] = "disabled"
            server["status_reason"] = "已停用"
            server["alerts"] = 0
        await self._save_servers(db, servers)
        await self.sync_runtime_tools(db, servers)
        return server

    async def delete_server(self, db: AsyncSession, server_id: str) -> bool:
        servers = await self._load_servers(db)
        next_servers = [item for item in servers if item["id"] != server_id]
        if len(next_servers) == len(servers):
            return False
        await self._save_servers(db, next_servers)
        await self.sync_runtime_tools(db, next_servers)
        return True

    async def probe_server(self, db: AsyncSession, server_id: str) -> dict[str, Any] | None:
        servers = await self._load_servers(db)
        server = next((item for item in servers if item["id"] == server_id), None)
        if not server:
            return None
        updated = await self._probe(server)
        server.clear()
        server.update(updated)
        await self._save_servers(db, servers)
        await self.sync_runtime_tools(db, servers)
        return server

    async def probe_all(self, db: AsyncSession) -> list[dict[str, Any]]:
        servers = await self._load_servers(db)
        results = list(
            await asyncio.gather(
                *(self._probe(server) for server in servers),
                return_exceptions=True,
            )
        )
        probed: list[dict[str, Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                server = dict(servers[i])
                server["status"] = "degraded"
                server["status_reason"] = str(result)
                probed.append(server)
            else:
                probed.append(result)
        await self._save_servers(db, probed)
        await self.sync_runtime_tools(db, probed)
        return probed

    async def toggle_server(self, db: AsyncSession, server_id: str, enabled: bool) -> dict[str, Any] | None:
        """直接切换服务器的启用/停用状态。"""
        return await self.update_server(db, server_id, {"enabled": enabled})

    async def import_from_json(
        self, db: AsyncSession, json_text: str, auto_probe: bool = True
    ) -> dict[str, Any]:
        """从 JSON 文本导入 MCP 服务器配置。

        返回 { "servers": [...], "errors": [...], "created_count": N, "skipped_count": M }
        """
        from app.services.mcp_config_parser import parse_mcp_config

        parsed_servers, parse_errors = parse_mcp_config(json_text)
        if not parsed_servers and parse_errors:
            return {"servers": [], "errors": parse_errors, "created_count": 0, "skipped_count": 0}

        existing = await self._load_servers(db)
        existing_names = {s.get("name", "").lower() for s in existing}

        created: list[dict[str, Any]] = []
        skipped: int = 0
        errors: list[str] = list(parse_errors)

        for cfg in parsed_servers:
            name = cfg.get("name", "")
            if name.lower() in existing_names:
                skipped += 1
                continue
            try:
                server = await self.create_server(db, cfg)
                created.append(server)
                existing_names.add(name.lower())
            except ValueError as exc:
                errors.append(f"服务 '{name}': {exc}")

        if auto_probe and created:
            for idx, server in enumerate(created):
                try:
                    probed = await self.probe_server(db, server["id"])
                    if probed:
                        created[idx] = probed
                except Exception as exc:
                    errors.append(f"探测 '{server['name']}' 失败: {exc}")

        return {
            "servers": created,
            "errors": errors,
            "created_count": len(created),
            "skipped_count": skipped,
        }

    async def sync_runtime_tools(
        self,
        db: AsyncSession,
        servers: list[dict[str, Any]] | None = None,
    ) -> None:
        servers = servers or await self._load_servers(db)
        managed_server_ids = {str(server["id"]) for server in servers}
        for tool in list(tool_registry.list_tools()):
            if tool.name.startswith(MCP_TOOL_PREFIX):
                parts = tool.name.split("__", 2)
                if len(parts) >= 3:
                    server_id = parts[1]
                    if server_id not in managed_server_ids:
                        tool_registry.unregister(tool.name)

        for server in servers:
            self._unregister_server_tools(server["id"])
            if not server.get("enabled"):
                continue
            for tool_definition in server.get("tool_definitions", []):
                if not isinstance(tool_definition, dict):
                    continue
                raw_name = str(tool_definition.get("name") or "").strip()
                if not raw_name:
                    continue
                runtime_name = self._tool_registry_name(server["id"], raw_name)
                description = tool_definition.get("description") or f"MCP tool from {server['name']}"
                parameters = tool_definition.get("inputSchema")
                if not isinstance(parameters, dict):
                    parameters = {"type": "object", "properties": {}}

                async def _execute(_server_id=server["id"], _tool_name=raw_name, **kwargs: Any):
                    async with AsyncSessionLocal() as runtime_db:
                        return await self.invoke_tool(runtime_db, _server_id, _tool_name, kwargs)

                tool_registry.register(
                    create_tool(
                        name=runtime_name,
                        description=f"[MCP:{server['name']}] {description}",
                        parameters=parameters,
                        execute=_execute,
                        enabled=True,
                    )
                )

    async def invoke_tool(
        self,
        db: AsyncSession,
        server_id: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        servers = await self._load_servers(db)
        server = next((item for item in servers if item["id"] == server_id), None)
        if not server:
            return ToolResult(success=False, content=None, error=f"MCP server '{server_id}' not found.")
        if not server.get("enabled"):
            return ToolResult(success=False, content=None, error=f"MCP server '{server.get('name', server_id)}' is disabled.")

        try:
            if server["transport"] == "stdio":
                result = await self._call_stdio_tool(server, tool_name, arguments)
            elif server["transport"] == "http":
                result = await self._call_http_tool(server, tool_name, arguments)
            else:
                return ToolResult(
                    success=False,
                    content=None,
                    error="SSE MCP transport is not yet available for runtime tool invocation.",
                )
            return ToolResult(success=True, content=result)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, content=None, error=str(exc))

    async def _load_servers(self, db: AsyncSession) -> list[dict[str, Any]]:
        raw = await ConfigDAO.get_value(db, MCP_SERVERS_CONFIG_KEY)
        if not raw:
            servers = _default_servers()
            await self._save_servers(db, servers)
            return servers

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            servers = _default_servers()
            await self._save_servers(db, servers)
            return servers

        if not isinstance(data, list):
            servers = _default_servers()
            await self._save_servers(db, servers)
            return servers

        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            server = {
                "id": item.get("id") or f"mcp-{index}",
                "name": item.get("name") or f"MCP {index + 1}",
                "description": item.get("description", ""),
                "transport": item.get("transport", "stdio"),
                "command": item.get("command"),
                "args": item.get("args", []),
                "endpoint": item.get("endpoint"),
                "enabled": bool(item.get("enabled", True)),
                "tags": item.get("tags", []),
                "workspaces": item.get("workspaces", []),
                "env": item.get("env", {}),
                "headers": item.get("headers", {}),
                "timeout_seconds": int(item.get("timeout_seconds", 8)),
                "status": item.get("status", "disabled"),
                "resources": int(item.get("resources", 0)),
                "tools": int(item.get("tools", 0)),
                "prompts": int(item.get("prompts", 0)),
                "alerts": int(item.get("alerts", 0)),
                "capabilities": item.get("capabilities", []),
                "tool_names": item.get("tool_names", []),
                "resource_names": item.get("resource_names", []),
                "prompt_names": item.get("prompt_names", []),
                "tool_definitions": item.get("tool_definitions", []),
                "status_reason": item.get("status_reason"),
                "last_probe_at": item.get("last_probe_at"),
                "updated_at": item.get("updated_at"),
                "events": item.get("events", []),
            }
            normalized.append(server)

        return normalized

    async def _save_servers(self, db: AsyncSession, servers: list[dict[str, Any]]) -> None:
        await ConfigDAO.upsert(
            db,
            MCP_SERVERS_CONFIG_KEY,
            json.dumps(servers, ensure_ascii=False),
            "MCP server definitions",
        )

    def _validate_server(self, server: dict[str, Any]) -> None:
        transport = server.get("transport")
        if transport not in {"stdio", "http", "sse"}:
            raise ValueError("unsupported transport")
        if transport == "stdio" and not server.get("command"):
            raise ValueError("stdio transport requires command")
        if transport in {"http", "sse"} and not server.get("endpoint"):
            raise ValueError(f"{transport} transport requires endpoint")
        if not isinstance(server.get("args", []), list):
            raise ValueError("args must be a list")
        if not isinstance(server.get("tags", []), list):
            raise ValueError("tags must be a list")
        if not isinstance(server.get("workspaces", []), list):
            raise ValueError("workspaces must be a list")
        if not isinstance(server.get("env", {}), dict):
            raise ValueError("env must be an object")
        if not isinstance(server.get("headers", {}), dict):
            raise ValueError("headers must be an object")

    async def _probe(self, server: dict[str, Any]) -> dict[str, Any]:
        server = dict(server)
        server["updated_at"] = _utc_now_iso()
        if not server.get("enabled"):
            server["status"] = "disabled"
            server["resources"] = 0
            server["tools"] = 0
            server["prompts"] = 0
            server["alerts"] = 0
            server["capabilities"] = []
            server["tool_names"] = []
            server["resource_names"] = []
            server["prompt_names"] = []
            server["tool_definitions"] = []
            server["status_reason"] = "已停用"
            server["events"] = self._build_events(server, "info", "服务已停用，未执行探测。")
            return server

        try:
            if server["transport"] == "stdio":
                result = await self._probe_stdio(server)
            elif server["transport"] == "http":
                result = await self._probe_http(server)
            else:
                result = await self._probe_sse(server)
            server.update(result)
            server["status"] = "connected"
            server["alerts"] = 0
            server["status_reason"] = "探测成功"
            server["last_probe_at"] = _utc_now_iso()
            server["events"] = self._build_events(server, "success", "最近一次探测成功。")
            return server
        except Exception as exc:  # noqa: BLE001
            server["status"] = "degraded"
            server["resources"] = 0
            server["tools"] = 0
            server["prompts"] = 0
            server["alerts"] = 1
            server["capabilities"] = []
            server["tool_names"] = []
            server["resource_names"] = []
            server["prompt_names"] = []
            server["tool_definitions"] = []
            server["status_reason"] = str(exc)
            server["last_probe_at"] = _utc_now_iso()
            server["events"] = self._build_events(server, "warning", f"探测失败：{exc}")
            return server

    def _build_events(self, server: dict[str, Any], level: str, message: str) -> list[dict[str, str]]:
        previous_events = [event for event in server.get("events", []) if isinstance(event, dict)][:2]
        current = {
            "id": uuid4().hex[:8],
            "level": level,
            "message": message,
            "time": "刚刚",
        }
        return [current, *previous_events]

    async def _probe_stdio(self, server: dict[str, Any]) -> dict[str, Any]:
        command, args = self._split_command(server["command"], server.get("args", []))
        timeout = max(int(server.get("timeout_seconds", 30)), 1)
        env = os.environ.copy()
        env.update({str(key): str(value) for key, value in server.get("env", {}).items()})
        cwd = server.get("workspaces", [None])[0] or None
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
        stderr_chunks: list[bytes] = []
        stderr_task = asyncio.create_task(self._drain_stderr(process.stderr, stderr_chunks))
        try:
            await asyncio.wait_for(
                self._stdio_request(process, "initialize", {
                    "protocolVersion": DEFAULT_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": DEFAULT_CLIENT_INFO,
                }),
                timeout=timeout,
            )
            await self._stdio_notify(process, "notifications/initialized", {})
            tools = await self._safe_stdio_list(process, "tools/list", timeout)
            resources = await self._safe_stdio_list(process, "resources/list", timeout)
            prompts = await self._safe_stdio_list(process, "prompts/list", timeout)
        finally:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=1)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            stderr_task.cancel()
            try:
                await stderr_task
            except asyncio.CancelledError:
                pass

        return self._build_probe_result(tools, resources, prompts)

    @staticmethod
    async def _drain_stderr(
        stream: asyncio.StreamReader | None,
        chunks: list[bytes],
    ) -> None:
        if stream is None:
            return
        while True:
            try:
                chunk = await stream.read(4096)
                if not chunk:
                    return
                chunks.append(chunk)
            except asyncio.CancelledError:
                try:
                    remaining = await stream.read()
                    if remaining:
                        chunks.append(remaining)
                except Exception:
                    pass
                raise

    async def _probe_http(self, server: dict[str, Any]) -> dict[str, Any]:
        timeout = max(int(server.get("timeout_seconds", 30)), 1)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **server.get("headers", {}),
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            await self._http_request(
                client,
                server["endpoint"],
                headers,
                "initialize",
                {
                    "protocolVersion": DEFAULT_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": DEFAULT_CLIENT_INFO,
                },
            )
            tools = await self._safe_http_list(client, server["endpoint"], headers, "tools/list")
            resources = await self._safe_http_list(client, server["endpoint"], headers, "resources/list")
            prompts = await self._safe_http_list(client, server["endpoint"], headers, "prompts/list")
        return self._build_probe_result(tools, resources, prompts)

    async def _probe_sse(self, server: dict[str, Any]) -> dict[str, Any]:
        timeout = max(int(server.get("timeout_seconds", 30)), 1)
        headers = {"Accept": "text/event-stream", **server.get("headers", {})}
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(server["endpoint"], headers=headers)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "text/event-stream" not in content_type and "stream" not in content_type:
                raise RuntimeError(f"unexpected SSE content-type: {content_type or 'unknown'}")
        return self._build_probe_result([], [], [])

    def _split_command(self, command: str, args: list[str]) -> tuple[str, list[str]]:
        if args:
            return command, [str(item) for item in args]
        parts = shlex.split(command, posix=os.name != "nt")
        if not parts:
            raise ValueError("invalid command")
        return parts[0], parts[1:]

    async def _safe_stdio_list(self, process: asyncio.subprocess.Process, method: str, timeout: int) -> list[dict[str, Any]]:
        try:
            response = await asyncio.wait_for(self._stdio_request(process, method, {}), timeout=timeout)
        except Exception:
            return []
        return self._extract_items(response)

    async def _safe_http_list(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        headers: dict[str, str],
        method: str,
    ) -> list[dict[str, Any]]:
        try:
            response = await self._http_request(client, endpoint, headers, method, {})
        except Exception:
            return []
        return self._extract_items(response)

    def _extract_items(self, payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        for key in ("tools", "resources", "prompts"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    def _build_probe_result(
        self,
        tools: list[dict[str, Any]],
        resources: list[dict[str, Any]],
        prompts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        capabilities: list[str] = []
        if tools:
            capabilities.append("tools")
        if resources:
            capabilities.append("resources")
        if prompts:
            capabilities.append("prompts")
        return {
            "resources": len(resources),
            "tools": len(tools),
            "prompts": len(prompts),
            "capabilities": capabilities,
            "tool_names": [str(item.get("name", "")) for item in tools if item.get("name")],
            "resource_names": [
                str(item.get("name") or item.get("uri", ""))
                for item in resources
                if item.get("name") or item.get("uri")
            ],
            "prompt_names": [str(item.get("name", "")) for item in prompts if item.get("name")],
            "tool_definitions": tools,
        }

    def _tool_registry_name(self, server_id: str, tool_name: str) -> str:
        normalized_tool = "".join(char if char.isalnum() or char == "_" else "_" for char in tool_name)
        return f"{MCP_TOOL_PREFIX}{server_id}__{normalized_tool or 'tool'}"

    def _unregister_server_tools(self, server_id: str) -> None:
        prefix = f"{MCP_TOOL_PREFIX}{server_id}__"
        for tool in list(tool_registry.list_tools()):
            if tool.name.startswith(prefix):
                tool_registry.unregister(tool.name)

    async def _call_stdio_tool(self, server: dict[str, Any], tool_name: str, arguments: dict[str, Any]) -> Any:
        command, args = self._split_command(server["command"], server.get("args", []))
        timeout = max(int(server.get("timeout_seconds", 8)), 1)
        env = os.environ.copy()
        env.update({str(key): str(value) for key, value in server.get("env", {}).items()})
        cwd = server.get("workspaces", [None])[0] or None
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
        try:
            await asyncio.wait_for(
                self._stdio_request(process, "initialize", {
                    "protocolVersion": DEFAULT_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": DEFAULT_CLIENT_INFO,
                }),
                timeout=timeout,
            )
            await self._stdio_notify(process, "notifications/initialized", {})
            result = await asyncio.wait_for(
                self._stdio_request(process, "tools/call", {"name": tool_name, "arguments": arguments}),
                timeout=timeout,
            )
            return result
        finally:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=1)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

    async def _call_http_tool(self, server: dict[str, Any], tool_name: str, arguments: dict[str, Any]) -> Any:
        timeout = max(int(server.get("timeout_seconds", 8)), 1)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **server.get("headers", {}),
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            await self._http_request(
                client,
                server["endpoint"],
                headers,
                "initialize",
                {
                    "protocolVersion": DEFAULT_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": DEFAULT_CLIENT_INFO,
                },
            )
            return await self._http_request(
                client,
                server["endpoint"],
                headers,
                "tools/call",
                {"name": tool_name, "arguments": arguments},
            )

    async def _stdio_notify(self, process: asyncio.subprocess.Process, method: str, params: dict[str, Any]) -> None:
        body = {"jsonrpc": "2.0", "method": method, "params": params}
        await self._write_stdio_message(process, body)

    async def _stdio_request(
        self,
        process: asyncio.subprocess.Process,
        method: str,
        params: dict[str, Any],
    ) -> Any:
        request_id = uuid4().hex
        body = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        await self._write_stdio_message(process, body)

        while True:
            message = await self._read_stdio_message(process)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = message["error"]
                if isinstance(error, dict):
                    raise RuntimeError(error.get("message", "MCP request failed"))
                raise RuntimeError("MCP request failed")
            return message.get("result", {})

    async def _write_stdio_message(self, process: asyncio.subprocess.Process, body: dict[str, Any]) -> None:
        if process.stdin is None:
            raise RuntimeError("stdin unavailable")
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        header = f"Content-Length: {len(payload)}\r\n\r\n".encode("utf-8")
        process.stdin.write(header + payload)
        await process.stdin.drain()

    async def _read_stdio_message(self, process: asyncio.subprocess.Process) -> dict[str, Any]:
        if process.stdout is None:
            raise RuntimeError("stdout unavailable")
        raw_headers = await process.stdout.readuntil(b"\r\n\r\n")
        headers = raw_headers.decode("utf-8", errors="ignore").split("\r\n")
        content_length = 0
        for line in headers:
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":", 1)[1].strip())
                break
        if content_length <= 0:
            raise RuntimeError("invalid MCP frame")
        payload = await process.stdout.readexactly(content_length)
        return json.loads(payload.decode("utf-8"))

    async def _http_request(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        headers: dict[str, str],
        method: str,
        params: dict[str, Any],
    ) -> Any:
        request_id = uuid4().hex
        response = await client.post(
            endpoint,
            json={"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
            headers=headers,
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            data = self._parse_sse_response(response.text, request_id)
        else:
            data = response.json()
        if isinstance(data, dict) and "error" in data:
            error = data["error"]
            if isinstance(error, dict):
                raise RuntimeError(error.get("message", "MCP request failed"))
            raise RuntimeError("MCP request failed")
        if not isinstance(data, dict):
            raise RuntimeError("invalid MCP response")
        return data.get("result", {})

    @staticmethod
    def _parse_sse_response(text: str, request_id: str) -> dict[str, Any]:
        """解析 SSE 格式的 MCP 响应，提取消息事件对应的 JSON-RPC result。"""
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            payload = line[len("data:") :].strip()
            if not payload:
                continue
            try:
                obj = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and obj.get("id") == request_id:
                return obj
        raise RuntimeError("no matching JSON-RPC response found in SSE stream")
