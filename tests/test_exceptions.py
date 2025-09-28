import logging
import os
import main
import subprocess
import sys
import tempfile


from tests.base import BaseCLITestCase


logger = logging.getLogger('cli_logger')


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
        # Do not set a GIT_TOKEN variable in env
        os.environ.pop("GIT_TOKEN", None)
        with self.assertRaises(SystemExit) as cm:
            main.main()
        self.assertEqual(cm.exception.code, 1)

    def test_logfile_fail(self):
        # Do not set a LOG_FILE name in env
        os.environ.pop("LOG_FILE", None)
        with self.assertRaises(SystemExit) as cm:
            main.main()
        self.assertEqual(cm.exception.code, 1)
    
    def test_urlfile_fail(self):
        # Fake URL_FILE name for ./run URL_FILE command
        result = subprocess.run(["./run", "fake_file.txt"], capture_output=True, text=True,)
        self.assertEqual(result.returncode, 1)
    
    def test_no_prompt_token(self):
        '''Pop env variable GEMINI_API_KEY and ensure gemini_key.txt is empty. Pop env variable 
        GEN_AI_STUDIO_API_KEY. 
        Ensure system exits with code 1.
        '''
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GEN_AI_STUDIO_API_KEY", None)
        result = subprocess.run(["./run", self.input_file], capture_output=True, text=True,)
        self.assertEqual(result.returncode, 1)

        



        

    
    

    

