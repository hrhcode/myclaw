import asyncio
import unittest

from app.tools.builtin.time_tool import TimeTool


class TimeToolTestCase(unittest.TestCase):
    def test_execute_friendly_format(self):
        result = asyncio.run(
            TimeTool().execute(format="friendly", timezone="local", include_date=True)
        )

        self.assertIn("time", result)
        self.assertIn("timestamp", result)
        self.assertIn("iso", result)
        self.assertTrue(result["time"])

    def test_execute_timestamp_format(self):
        result = asyncio.run(TimeTool().execute(format="timestamp"))

        self.assertTrue(str(result["time"]).isdigit())


if __name__ == "__main__":
    unittest.main()
