import unittest
from unittest.mock import patch, MagicMock
import os
import tenacity
from apis import git_api  # <-- updated import

class TestGitAPI(unittest.TestCase):

    def test_check_git_token_env(self):
        """Return token from environment variable"""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "envtoken"}):
            token = git_api.check_git_token()
            self.assertEqual(token, "envtoken")

    def test_check_git_token_file(self):
        """Return token from git_token.txt if env missing (lines 21–26)"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data="filetoken")):
                token = git_api.check_git_token()
                self.assertEqual(token, "filetoken")

    def test_check_git_token_missing(self):
        """Return None if no token in env or file"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.open", side_effect=FileNotFoundError):
                token = git_api.check_git_token()
                self.assertIsNone(token)

    @patch("apis.git_api.time.sleep", return_value=None)
    @patch("apis.git_api.requests.get")
    def test_make_request_success(self, mock_get, mock_sleep):
        """Return response immediately on 200"""
        mock_resp = MagicMock(status_code=200, json=lambda: {"key": "value"})
        mock_get.return_value = mock_resp

        resp = git_api.make_request("https://example.com", {})
        self.assertEqual(resp.json(), {"key": "value"})
        mock_get.assert_called_once()

    @patch("apis.git_api.time.sleep", return_value=None)
    @patch("apis.git_api.requests.get")
    def test_make_request_rate_limit(self, mock_get, mock_sleep):
        """Simulate rate-limit and then success"""
        # First response is 403 rate-limit, then 200 success
        resp_403 = MagicMock(status_code=403, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1"})
        resp_200 = MagicMock(status_code=200, json=lambda: {"ok": True})
        mock_get.side_effect = [resp_403, resp_200]

        resp = git_api.make_request("https://example.com", {})
        self.assertEqual(resp.json(), {"ok": True})
        self.assertEqual(mock_get.call_count, 2)

    def test_set_git_headers_no_token(self):
        """Empty headers if no token (lines 61–64)"""
        with patch("apis.git_api.check_git_token", return_value=None):
            headers = git_api.set_git_headers()
            self.assertEqual(headers, {})

    def test_set_git_headers_with_token(self):
        """Headers include Authorization if token exists (lines 61–64)"""
        with patch("apis.git_api.check_git_token", return_value="abc123"):
            headers = git_api.set_git_headers()
            self.assertEqual(headers, {"Authorization": "Bearer abc123"})

    @patch("apis.git_api.set_git_headers", return_value={})
    @patch("apis.git_api.make_request")
    def test_get_contributors(self, mock_request, mock_headers):
        """Return JSON from make_request"""
        mock_request.return_value.json.return_value = [{"login": "alice", "contributions": 10}]
        contributors = git_api.get_contributors("owner/repo")
        self.assertEqual(contributors[0]["login"], "alice")
        self.assertEqual(contributors[0]["contributions"], 10)
        mock_request.assert_called_once()

if __name__ == "__main__":
    unittest.main()
