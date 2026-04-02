import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.tools.base import ToolDefinition
from app.tools.executor import ToolExecutor


class ToolExecutorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_plain_dict_result_is_treated_as_success(self):
        async def execute(**kwargs):
            return {"time": "10:00:00", "timezone": "UTC"}

        tool = ToolDefinition(
            name="plain_dict_tool",
            description="test",
            parameters={"type": "object", "properties": {}, "required": []},
            execute=execute,
            enabled=True,
        )

        with patch("app.tools.executor.tool_registry.get_tool", return_value=tool):
            result = await ToolExecutor(timeout_seconds=5).execute_tool("plain_dict_tool", {})

        self.assertTrue(result.success)
        self.assertEqual(result.content["time"], "10:00:00")


if __name__ == "__main__":
    unittest.main()
