import os
import unittest
import logging
import tempfile
from unittest.mock import patch
import sys

# Import your setup_logger function
from utils.logger import setup_logger

class TestSetupLogger(unittest.TestCase):

    def setUp(self):
        # Backup original environment variables
        self._old_environ = os.environ.copy()
        # Create temporary file for logging
        self.tmp_log_file = tempfile.NamedTemporaryFile(delete=False)
        self.tmp_log_file.close()  # close so logger can open it

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_environ)
        try:
            os.unlink(self.tmp_log_file.name)
        except FileNotFoundError:
            pass

    def test_log_file_missing(self):
        """If LOG_FILE env variable is missing, sys.exit should be called"""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as cm:
                setup_logger()
            self.assertEqual(cm.exception.code, 1)

    def test_log_level_0_silence(self):
        """LOG_LEVEL=0 should silence all logging"""
        with patch.dict(os.environ, {"LOG_FILE": self.tmp_log_file.name, "LOG_LEVEL": "0"}):
            logger = setup_logger()
            self.assertEqual(logger.level, logging.NOTSET)
            self.assertTrue(logging.root.manager.disable >= logging.CRITICAL)

    def test_log_level_1_info(self):
        """LOG_LEVEL=1 should set logger to INFO"""
        with patch.dict(os.environ, {"LOG_FILE": self.tmp_log_file.name, "LOG_LEVEL": "1"}):
            logger = setup_logger()
            self.assertEqual(logger.level, logging.INFO)
            self.assertFalse(logging.root.manager.disable)

    def test_log_level_2_debug(self):
        """LOG_LEVEL=2 should set logger to DEBUG"""
        with patch.dict(os.environ, {"LOG_FILE": self.tmp_log_file.name, "LOG_LEVEL": "2"}):
            logger = setup_logger()
            self.assertEqual(logger.level, logging.DEBUG)
            self.assertFalse(logging.root.manager.disable)

    def test_invalid_log_level_defaults_to_0(self):
        """Non-integer LOG_LEVEL should default to 0 (silent)"""
        with patch.dict(os.environ, {"LOG_FILE": self.tmp_log_file.name, "LOG_LEVEL": "invalid"}):
            logger = setup_logger()
            self.assertEqual(logger.level, logging.NOTSET)
            self.assertTrue(logging.root.manager.disable >= logging.CRITICAL)

    # def test_logger_has_file_and_console_handlers(self):
    #     """Logger should have both a file handler and console handler"""
    #     with patch.dict(os.environ, {"LOG_FILE": self.tmp_log_file.name, "LOG_LEVEL": "2"}):
    #         logger = setup_logger()
    #         file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    #         console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    #         self.assertTrue(file_handlers)
    #         self.assertTrue(console_handlers)

# if __name__ == "__main__":
#     unittest.main()
