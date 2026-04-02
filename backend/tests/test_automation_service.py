import asyncio
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services.automation_service import AutomationService, compute_next_run


class AutomationServiceTestCase(unittest.IsolatedAsyncioTestCase):
    def test_compute_next_run_interval(self):
        base = datetime(2026, 4, 2, 10, 0, 0)
        result = compute_next_run("interval", "15", from_time=base)
        self.assertEqual(result, datetime(2026, 4, 2, 10, 15, 0))

    def test_compute_next_run_daily(self):
        base = datetime(2026, 4, 2, 10, 0, 0)
        result = compute_next_run("daily", "09:30", from_time=base)
        self.assertEqual(result, datetime(2026, 4, 3, 9, 30, 0))

    def test_compute_next_run_weekly(self):
        base = datetime(2026, 4, 2, 10, 0, 0)  # Thursday
        result = compute_next_run("weekly", "0|09:00", from_time=base)  # Monday
        self.assertEqual(result, datetime(2026, 4, 6, 9, 0, 0))

    async def test_run_due_once_uses_runner_signature_without_db(self):
        service = AutomationService()
        db = object()
        automation = SimpleNamespace(
            id=9,
            session_id=3,
            prompt="/status",
            schedule_type="interval",
            schedule_value="1",
        )
        run_record = SimpleNamespace(id=11)
        runner = AsyncMock(return_value="run-123")

        with (
            patch("app.services.automation_service.AutomationDAO.list_due", new=AsyncMock(return_value=[automation])),
            patch("app.services.automation_service.AutomationRunDAO.create", new=AsyncMock(return_value=run_record)) as create_run,
            patch("app.services.automation_service.AutomationRunDAO.update", new=AsyncMock()) as update_run,
            patch("app.services.automation_service.AutomationDAO.update", new=AsyncMock()) as update_automation,
        ):
            await service.run_due_once(db, runner)

        runner.assert_awaited_once_with(3, "/status", 9)
        create_run.assert_awaited_once()
        update_run.assert_awaited()
        update_automation.assert_awaited()

    async def test_run_due_once_records_failure(self):
        service = AutomationService()
        db = object()
        automation = SimpleNamespace(
            id=12,
            session_id=4,
            prompt="/status",
            schedule_type="interval",
            schedule_value="1",
        )
        run_record = SimpleNamespace(id=13)
        runner = AsyncMock(side_effect=RuntimeError("boom"))

        with (
            patch("app.services.automation_service.AutomationDAO.list_due", new=AsyncMock(return_value=[automation])),
            patch("app.services.automation_service.AutomationRunDAO.create", new=AsyncMock(return_value=run_record)),
            patch("app.services.automation_service.AutomationRunDAO.update", new=AsyncMock()) as update_run,
            patch("app.services.automation_service.AutomationDAO.update", new=AsyncMock()) as update_automation,
        ):
            await service.run_due_once(db, runner)

        runner.assert_awaited_once_with(4, "/status", 12)
        failure_call = update_run.await_args_list[-1]
        self.assertEqual(failure_call.kwargs["status"], "failed")
        self.assertIn("boom", failure_call.kwargs["error"])
        self.assertTrue(update_automation.await_count >= 1)


if __name__ == "__main__":
    unittest.main()
