import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import requests
from apis import purdue_genai  # Correct module

class TestPurdueGenAI(unittest.TestCase):

    # -----------------------------
    # get_purdue_genai_key tests
    # -----------------------------
    def test_get_key_from_env(self):
        with patch.dict(os.environ, {"GEN_AI_STUDIO_API_KEY": "env_key"}):
            self.assertEqual(purdue_genai.get_purdue_genai_key(), "env_key")

    def test_get_key_from_file(self):
        with patch.dict(os.environ, {}, clear=True):
            m = mock_open(read_data="file_key\n")
            with patch("builtins.open", m):
                self.assertEqual(purdue_genai.get_purdue_genai_key(), "file_key")

    def test_get_key_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.open", side_effect=FileNotFoundError):
                self.assertIsNone(purdue_genai.get_purdue_genai_key())

    # -----------------------------
    # prompt_purdue_genai tests
    # -----------------------------
    @patch("apis.purdue_genai.requests.post")
    def test_prompt_success(self, mock_post):
        """Return content when status_code is 200 (lines 63–65)"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Hello response"}}]
        }
        mock_post.return_value = mock_resp

        result = purdue_genai.prompt_purdue_genai("Hello", "api_key")
        self.assertEqual(result, "Hello response")
        mock_post.assert_called_once()


# if __name__ == "__main__":
#     unittest.main()
