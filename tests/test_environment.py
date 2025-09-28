import logging
import os
import main
import subprocess
import sys
import tempfile
import unittest


from tests.base import BaseCLITestCase
from utils.prompt_key import get_prompt_key
from utils.env_check import check_environment
from unittest.mock import patch
from utils.logger import setup_logger



class TestEnvironment(BaseCLITestCase):
    '''Testing exception handling and environment checks'''
    def setUp(self):
        # Make a copy of the original environment
        self._old_environ = os.environ.copy()

        # Create sample input.txt
        self.tmpdir = tempfile.TemporaryDirectory()
        self.input_file = "input.txt"

        content = """https://github.com/google-research/bert, https://huggingface.co/datasets/bookcorpus/bookcorpus, https://huggingface.co/google-bert/bert-base-uncased
,,https://huggingface.co/parvk11/audience_classifier_model
,,https://huggingface.co/openai/whisper-tiny/tree/main
"""
        with open(self.input_file, "w") as f:
            f.write(content)
                
    def tearDown(self):
        # Restore the original environment
        os.environ.clear()
        os.environ.update(self._old_environ)
        self.tmpdir.cleanup()
    
    def test_git_token_fail(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(check_environment())  # returns False when GIT_TOKEN missing

    def test_logfile_fail(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(check_environment())  # returns False when LOG_FILE missing
    
    def test_no_prompt_token(self):
        '''Pop env variable GEMINI_API_KEY and ensure gemini_key.txt is empty. Pop env variable 
        GEN_AI_STUDIO_API_KEY. 
        Ensure system exits with code 1.
        '''
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GEN_AI_STUDIO_API_KEY": ""}, clear=True):
            with self.assertRaises(SystemExit) as cm:
                get_prompt_key()
            self.assertEqual(cm.exception.code, 1)
    
    def test_with_log_level_0(self):
        '''Test code with log level 0. Ensure logger level is set to CRITICAL'''
        with patch.dict(os.environ, {"LOG_LEVEL": "0"}):
            setup_logger()
            logger = logging.getLogger('cli_logger')
           
           # Verify that no logs are captured for any standard level
            for level_name, level_value in [
                ("DEBUG", logging.DEBUG),
                ("INFO", logging.INFO),
                ("WARNING", logging.WARNING),
                ("ERROR", logging.ERROR),
                ("CRITICAL", logging.CRITICAL)
            ]:
                with self.assertRaises(AssertionError):
                    with self.assertLogs(logger, level=level_name):
                        logger.log(level_value, f"This should not appear at {level_name}")

    def test_with_log_level_1(self):
        '''Test code with log level 1. Ensure logger level is set to INFO'''
        with patch.dict(os.environ, {"LOG_LEVEL": "1"}):
            setup_logger()
            logger = logging.getLogger('cli_logger')
            self.assertFalse(logger.disabled)
            self.assertEqual(logger.level, logging.INFO)

    def test_with_log_level_2(self):
        '''Test code with log level 2. Ensure logger level is set to DEBUG'''
        with patch.dict(os.environ, {"LOG_LEVEL": "2"}):
            setup_logger()
            logger = logging.getLogger('cli_logger')
            self.assertFalse(logger.disabled)
            self.assertEqual(logger.level, logging.DEBUG)


if __name__ == "__main__":
    unittest.main()
