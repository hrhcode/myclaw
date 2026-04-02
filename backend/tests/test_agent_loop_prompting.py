import unittest
from types import SimpleNamespace

from app.agent_loop.controller import AgentLoopController
from app.agent_loop.prompting import (
    build_assistant_history_content,
    build_model_history,
    build_system_prompt,
)
from app.agent_loop.types import LoopRuntimeConfig


class AgentLoopPromptingTestCase(unittest.TestCase):
    def test_build_system_prompt_includes_loop_contract(self):
        prompt = build_system_prompt(
            tool_enabled=True,
            max_iterations=4,
            profile="coding",
            workspace_dir="D:/Project/Me/myclaw-new/myclaw",
            available_tool_names=["web_search", "web_fetch", "exec"],
        )

        self.assertIn("Operate with an explicit loop", prompt)
        self.assertIn("4 iterations", prompt)
        self.assertIn("Never fabricate tool results", prompt)
        self.assertIn("Tool availability (filtered by policy)", prompt)
        self.assertIn("When a first-class tool exists for an action", prompt)
        self.assertIn("Working directory: D:/Project/Me/myclaw-new/myclaw", prompt)
        self.assertIn("- web_search:", prompt)
        self.assertIn("Tool profile for this run: coding", prompt)

    def test_assistant_history_content_appends_tool_trace_summary(self):
        tool_calls = [
            SimpleNamespace(
                tool_name="web_search",
                status="success",
                execution_time_ms=320,
                result='{"content":{"summary":"Found release note","url":"https://example.com"}}',
                error=None,
            )
        ]

        content = build_assistant_history_content("Here is the answer.", tool_calls)

        self.assertIn("Here is the answer.", content)
        self.assertIn("[Tool Trace Summary]", content)
        self.assertIn("web_search", content)
        self.assertIn("Found release note", content)

    def test_build_model_history_keeps_roles_and_rehydrates_tool_trace(self):
        messages = [
            SimpleNamespace(id=1, role="user", content="Find the latest release"),
            SimpleNamespace(id=2, role="assistant", content="I checked the web."),
        ]
        tool_map = {
            2: [
                SimpleNamespace(
                    tool_name="web_search",
                    status="success",
                    execution_time_ms=210,
                    result='{"content":{"summary":"Release 1.2 shipped"}}',
                    error=None,
                )
            ]
        }

        history = build_model_history(messages, tool_map)

        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertIn("Release 1.2 shipped", history[1]["content"])

    def test_controller_build_initial_messages_layers_system_memory_and_history(self):
        controller = AgentLoopController()
        runtime_config = LoopRuntimeConfig(use_tools=True, max_iterations=5)

        messages = controller._build_initial_messages(
            message_history=[{"role": "user", "content": "Hello"}],
            memory_context="## Relevant Memory\n- prefers concise answers",
            runtime_config=runtime_config,
            workspace_dir="D:/Project/Me/myclaw-new/myclaw",
            context_summary="Use terse updates.",
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Operate with an explicit loop", messages[0]["content"])
        self.assertIn("## Tool Call Style", messages[0]["content"])
        self.assertIn("## Answer Quality", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "system")
        self.assertIn("Session Context Summary", messages[1]["content"])
        self.assertEqual(messages[2]["role"], "system")
        self.assertIn("Retrieved memory relevant", messages[2]["content"])
        self.assertEqual(messages[3]["role"], "user")


if __name__ == "__main__":
    unittest.main()
