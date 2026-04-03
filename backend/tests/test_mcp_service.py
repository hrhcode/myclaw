import json
import unittest
from unittest.mock import AsyncMock, patch

from app.common.constants import MCP_SERVERS_CONFIG_KEY
from app.services.mcp_service import McpService


class McpServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_load_servers_bootstraps_defaults_when_missing(self):
        service = McpService()

        with (
            patch("app.services.mcp_service.ConfigDAO.get_value", new=AsyncMock(return_value=None)),
            patch("app.services.mcp_service.ConfigDAO.upsert", new=AsyncMock()) as upsert,
        ):
            servers = await service.list_servers(db=object())

        self.assertGreaterEqual(len(servers), 1)
        upsert.assert_awaited_once()
        self.assertEqual(upsert.await_args.args[1], MCP_SERVERS_CONFIG_KEY)

    async def test_create_server_persists_json_payload(self):
        service = McpService()
        existing = []

        with (
            patch("app.services.mcp_service.ConfigDAO.get_value", new=AsyncMock(return_value=json.dumps(existing))),
            patch("app.services.mcp_service.ConfigDAO.upsert", new=AsyncMock()) as upsert,
        ):
            server = await service.create_server(
                db=object(),
                payload={
                    "name": "Demo",
                    "transport": "http",
                    "endpoint": "http://localhost:9000/mcp",
                    "enabled": True,
                },
            )

        self.assertEqual(server["name"], "Demo")
        persisted = json.loads(upsert.await_args.args[2])
        self.assertEqual(persisted[0]["name"], "Demo")
        self.assertEqual(persisted[0]["endpoint"], "http://localhost:9000/mcp")

    async def test_probe_server_updates_runtime_fields(self):
        service = McpService()
        stored = [
            {
                "id": "demo",
                "name": "Demo",
                "description": "",
                "transport": "http",
                "command": None,
                "args": [],
                "endpoint": "http://localhost:9000/mcp",
                "enabled": True,
                "tags": [],
                "workspaces": [],
                "env": {},
                "headers": {},
                "timeout_seconds": 8,
                "status": "degraded",
                "resources": 0,
                "tools": 0,
                "prompts": 0,
                "alerts": 0,
                "capabilities": [],
                "tool_names": [],
                "resource_names": [],
                "prompt_names": [],
                "tool_definitions": [],
                "status_reason": None,
                "last_probe_at": None,
                "updated_at": None,
                "events": [],
            }
        ]

        with (
            patch("app.services.mcp_service.ConfigDAO.get_value", new=AsyncMock(return_value=json.dumps(stored))),
            patch("app.services.mcp_service.ConfigDAO.upsert", new=AsyncMock()),
            patch(
                "app.services.mcp_service.McpService._probe_http",
                new=AsyncMock(return_value={
                    "resources": 3,
                    "tools": 2,
                    "prompts": 1,
                    "capabilities": ["tools", "resources", "prompts"],
                    "tool_names": ["query", "inspect"],
                    "resource_names": ["schema://users"],
                    "prompt_names": ["help"],
                }),
            ),
        ):
            result = await service.probe_server(db=object(), server_id="demo")

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "connected")
        self.assertEqual(result["tools"], 2)
        self.assertEqual(result["resources"], 3)
        self.assertEqual(result["prompts"], 1)

    async def test_sync_runtime_tools_registers_dynamic_tools(self):
        service = McpService()
        servers = [
            {
                "id": "demo",
                "name": "Demo",
                "enabled": True,
                "tool_definitions": [
                    {
                        "name": "query_users",
                        "description": "Query users",
                        "inputSchema": {"type": "object", "properties": {}},
                    }
                ],
            }
        ]

        fake_registry = type("Registry", (), {"register": unittest.mock.Mock(), "list_tools": unittest.mock.Mock(return_value=[]), "unregister": unittest.mock.Mock()})()
        with patch("app.services.mcp_service.tool_registry", fake_registry):
            await service.sync_runtime_tools(db=object(), servers=servers)

        fake_registry.register.assert_called_once()
        registered_tool = fake_registry.register.call_args.args[0]
        self.assertTrue(registered_tool.name.startswith("mcp__demo__"))


if __name__ == "__main__":
    unittest.main()
