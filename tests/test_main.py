import unittest
from unittest.mock import patch, MagicMock
import sys

# Import the actual main.py module
import main

class TestMainCLI(unittest.TestCase):

    @patch("main.check_environment", return_value=True)
    @patch("main.setup_logger")
    @patch("main.get_prompt_key")
    @patch("main.parse_URL_file")
    @patch("main.print_model_summary")
    @patch("os.path.exists", return_value=True)
    @patch("main.json.dumps", side_effect=lambda x: str(x))
    def test_main_success(
        self, mock_json, mock_exists, mock_print_summary,
        mock_parse, mock_get_key, mock_logger, mock_env
    ):
        """
        Test the normal successful execution of main():
        - Environment check passes
        - URL file exists
        - parse_URL_file returns one mock model and a dataset registry
        - model.evaluate() is called and output is printed
        """
        # Mock a model returned by parse_URL_file
        mock_model = MagicMock()
        mock_model.evaluate.return_value = {"metric": 0.9}
        mock_parse.return_value = ([mock_model], {"dataset1": "info"})

        # Simulate command-line arguments
        test_args = ["main.py", "fake_file.txt"]
        with patch.object(sys, "argv", test_args):
            with patch("builtins.print") as mock_print:
                main.main()
                # Ensure evaluate() was called on the model
                mock_model.evaluate.assert_called_once()
                # Ensure print() was called with the evaluated metrics
                mock_print.assert_called_with(str({"metric": 0.9}))

    @patch("main.check_environment", return_value=False)
    def test_main_environment_failure(self, mock_env):
        """
        Test behavior when environment check fails:
        - check_environment() returns False
        - main() should exit with code 1
        """
        test_args = ["main.py", "fake_file.txt"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main.main()
            self.assertEqual(cm.exception.code, 1)

    @patch("main.check_environment", return_value=True)
    @patch("os.path.exists", return_value=False)
    def test_main_file_not_found(self, mock_exists, mock_env):
        """
        Test behavior when the specified URL file does not exist:
        - Environment check passes
        - os.path.exists() returns False
        - main() should exit with code 1
        """
        test_args = ["main.py", "missing_file.txt"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit) as cm:
                main.main()
            self.assertEqual(cm.exception.code, 1)


# if __name__ == "__main__":
#     unittest.main()
