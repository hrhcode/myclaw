import asyncio
import os
import unittest

from fastapi import HTTPException

from app.common.security import _extract_token, require_api_auth


class SecurityTestCase(unittest.TestCase):
    def test_extract_token(self):
        self.assertEqual(_extract_token("Bearer abc123", None), "abc123")
        self.assertEqual(_extract_token(None, "key123"), "key123")
        self.assertIsNone(_extract_token("Token x", None))

    def test_require_api_auth_without_config(self):
        os.environ.pop("MYCLAW_API_TOKEN", None)
        asyncio.run(require_api_auth(None, None))

    def test_require_api_auth_with_config(self):
        os.environ["MYCLAW_API_TOKEN"] = "demo-token"
        asyncio.run(require_api_auth("Bearer demo-token", None))
        with self.assertRaises(HTTPException):
            asyncio.run(require_api_auth("Bearer wrong-token", None))


if __name__ == "__main__":
    unittest.main()
