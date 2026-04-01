import unittest

from app.api.config import _is_sensitive_key, _mask_value


class ConfigMaskingTestCase(unittest.TestCase):
    def test_sensitive_key_detection(self):
        self.assertTrue(_is_sensitive_key("zhipu_api_key"))
        self.assertTrue(_is_sensitive_key("service_token"))
        self.assertTrue(_is_sensitive_key("my_secret_value"))
        self.assertFalse(_is_sensitive_key("llm_model"))

    def test_mask_value(self):
        self.assertEqual(_mask_value(None), None)
        self.assertEqual(_mask_value("abcd"), "****")
        self.assertEqual(_mask_value("abcdefghijkl"), "abcd****ijkl")


if __name__ == "__main__":
    unittest.main()
