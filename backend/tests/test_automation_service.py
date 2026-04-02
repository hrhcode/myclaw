import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services.automation_service import AutomationService, compute_next_run, validate_schedule


class AutomationServiceTestCase(unittest.IsolatedAsyncioTestCase):
    def test_compute_next_run_interval(self):
        base = datetime(2026, 4, 2, 10, 0, 0)
        result = compute_next_run("interval", "15", timezone="UTC", from_time=base)
        self.assertEqual(result, datetime(2026, 4, 2, 10, 15, 0))

    def test_compute_next_run_daily_with_timezone(self):
        base = datetime(2026, 4, 2, 10, 0, 0)
        result = compute_next_run("daily", "09:30", timezone="Asia/Shanghai", from_time=base)
        self.assertEqual(result, datetime(2026, 4, 3, 1, 30, 0))

    def test_compute_next_run_weekly(self):
        base = datetime(2026, 4, 2, 10, 0, 0)  # Thursday UTC
        result = compute_next_run("weekly", "0|09:00", timezone="UTC", from_time=base)
        self.assertEqual(result, datetime(2026, 4, 6, 9, 0, 0))

    def test_compute_next_run_once_future(self):
        base = datetime(2026, 4, 2, 10, 0, 0)
        result = compute_next_run("once", "2026-04-02T20:30:00+08:00", timezone="Asia/Shanghai", from_time=base)
        self.assertEqual(result, datetime(2026, 4, 2, 12, 30, 0))

    def test_compute_next_run_cron(self):
        base = datetime(2026, 4, 2, 10, 0, 0)
        result = compute_next_run("cron", "0 9 * * 1-5", timezone="UTC", from_time=base)
        self.assertEqual(result, datetime(2026, 4, 3, 9, 0, 0))

    def test_validate_schedule_rejects_bad_values(self):
        with self.assertRaises(ValueError):
            validate_schedule("interval", "abc", "UTC")
        with self.assertRaises(ValueError):
            validate_schedule("weekly", "8|09:00", "UTC")
        with self.assertRaises(ValueError):
            validate_schedule("cron", "not-a-cron", "UTC")

    async def test_run_due_once_uses_runner_signature_without_db(self):
        service = AutomationService()
        db = object()
        automation = SimpleNamespace(
            id=9,
            session_id=3,
            prompt="/status",
            schedule_type="interval",
            schedule_value="1",
            timezone="UTC",
        )
        run_record = SimpleNamespace(id=11)
        runner = AsyncMock(return_value="run-123")

        with (
            patch("app.services.automation_service.AutomationDAO.list_due", new=AsyncMock(return_value=[automation])),
            patch("app.services.automation_service.AutomationRunDAO.create", new=AsyncMock(return_value=run_record)),
            patch("app.services.automation_service.AutomationRunDAO.update", new=AsyncMock()) as update_run,
            patch("app.services.automation_service.AutomationDAO.update", new=AsyncMock()) as update_automation,
        ):
            await service.run_due_once(db, runner)

        runner.assert_awaited_once_with(3, "/status", 9)
        self.assertEqual(update_run.await_args_list[-1].kwargs["status"], "success")
        self.assertGreaterEqual(update_automation.await_count, 1)

    async def test_run_due_once_records_failure(self):
        service = AutomationService()
        db = object()
        automation = SimpleNamespace(
            id=12,
            session_id=4,
            prompt="/status",
            schedule_type="interval",
            schedule_value="1",
            timezone="UTC",
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
        self.assertGreaterEqual(update_automation.await_count, 1)

    async def test_manual_run_disables_once_job(self):
        service = AutomationService()
        db = object()
        automation = SimpleNamespace(
            id=22,
            session_id=5,
            prompt="hello",
            schedule_type="once",
            schedule_value="2026-04-03T09:00:00+08:00",
            timezone="Asia/Shanghai",
        )
        run_record = SimpleNamespace(id=14)
        runner = AsyncMock(return_value="run-manual")

        with (
            patch("app.services.automation_service.AutomationDAO.get_by_id", new=AsyncMock(return_value=automation)),
            patch("app.services.automation_service.AutomationRunDAO.create", new=AsyncMock(return_value=run_record)),
            patch("app.services.automation_service.AutomationRunDAO.update", new=AsyncMock()),
            patch("app.services.automation_service.AutomationDAO.update", new=AsyncMock()) as update_automation,
        ):
            run_id = await service.trigger_manual_run(db, 22, runner)

        self.assertEqual(run_id, "run-manual")
        update_call = update_automation.await_args_list[-1]
        self.assertFalse(update_call.kwargs["enabled"])
        self.assertIsNone(update_call.kwargs["next_run_at"])


if __name__ == "__main__":
    unittest.main()
