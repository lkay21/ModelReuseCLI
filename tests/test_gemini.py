import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
from apis import gemini
import requests

class TestGeminiAPI(unittest.TestCase):

    def test_get_gemini_key_env(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "abc123"}):
            self.assertEqual(gemini.get_gemini_key(), "abc123")

    def test_get_gemini_key_file(self):
        with patch.dict(os.environ, {}, clear=True):
            m = mock_open(read_data="file_key\n")
            with patch("builtins.open", m):
                self.assertEqual(gemini.get_gemini_key(), "file_key")

    def test_get_gemini_key_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.open", side_effect=FileNotFoundError):
                self.assertIsNone(gemini.get_gemini_key())

    # Disable retry by patching requests.post directly
    @patch("apis.gemini.requests.post")
    def test_prompt_gemini_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Hello"}]}}]
        }
        mock_post.return_value = mock_resp

        result = gemini.prompt_gemini("Hello", "api_key")
        self.assertEqual(result, "Hello")


# if __name__ == "__main__":
#     unittest.main()
