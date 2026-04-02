import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services.session_service import SessionService


class SessionServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_resolve_session_prefers_requested_session(self):
        service = SessionService()
        session = SimpleNamespace(id=7)

        with patch("app.services.session_service.SessionDAO.get_by_id", new=AsyncMock(return_value=session)):
            result = await service.resolve_session(object(), 7)

        self.assertIs(result, session)

    async def test_resolve_session_falls_back_to_default(self):
        service = SessionService()
        default_session = SimpleNamespace(id=1)

        with (
            patch("app.services.session_service.SessionDAO.get_by_id", new=AsyncMock(return_value=None)),
            patch("app.services.session_service.SessionDAO.get_default", new=AsyncMock(return_value=default_session)),
        ):
            result = await service.resolve_session(object(), 99)

        self.assertIs(result, default_session)

    async def test_get_status_expands_tool_lists_and_recent_runs(self):
        service = SessionService()
        session = SimpleNamespace(
            id=5,
            name="ops",
            mode="personal",
            workspace_path="D:/workspace",
            model="glm-test",
            provider="zhipu",
            tool_profile="full",
            tool_allow="get_current_time,sessions_list",
            tool_deny="web_search",
            max_iterations=6,
            context_summary="summary",
            memory_auto_extract=True,
            memory_threshold=3,
            is_default=False,
        )
        run = SimpleNamespace(
            run_id="run-1",
            conversation_id=42,
            user_message="/status",
            stop_reason="command",
            compacted_summary="compact",
            started_at=datetime(2026, 4, 2, 10, 0, 0),
            completed_at=datetime(2026, 4, 2, 10, 0, 1),
        )

        with (
            patch("app.services.session_service.SessionDAO.get_by_id", new=AsyncMock(return_value=session)),
            patch("app.services.session_service.AgentRunDAO.list_by_session", new=AsyncMock(return_value=[run])),
        ):
            status = await service.get_status(object(), 5)

        self.assertEqual(status["tool_allow"], ["get_current_time", "sessions_list"])
        self.assertEqual(status["tool_deny"], ["web_search"])
        self.assertEqual(status["recent_runs"][0]["run_id"], "run-1")


if __name__ == "__main__":
    unittest.main()
