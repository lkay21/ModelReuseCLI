import os
# from model import Model, Code, Dataset

from utils import url_parser
# from utils.url_parser import parse_url_file
from tests.base import BaseCLITestCase
from unittest.mock import patch

import logging
logger = logging.getLogger('cli_logger')



class URLFileIntegrationTests(BaseCLITestCase):
    def setUp(self):
        # Create a sample input file for testing
        self.sample_input_path = "tests/sample_input.txt"
        with open(self.sample_input_path, "w") as f:
            f.write(
                """https://github.com/google-research/bert, https://huggingface.co/datasets/bookcorpus/bookcorpus, https://huggingface.co/google-bert/bert-base-uncased
                ,,https://huggingface.co/parvk11/audience_classifier_model
                https://gitlab.com/google-research/bert,,https://huggingface.co/openai/whisper-tiny
                ,,https://huggingface.co/google-bert/bert-base-uncased
                ,https://www.image-net.org/,https://huggingface.co/google-bert/bert-base-uncased"""            )
            
    def tearDown(self):
        # Clean up the sample input file after the test
        if os.path.exists(self.sample_input_path):
            os.remove(self.sample_input_path)

    @patch("utils.url_parser.get_prompt_key")
    def test_parse_url_file_integration(self, MockGetPromptKey):
        """
        Test the parse_url_file function with a sample input file.
        """
        # Mock get_prompt_key to return purdue_genai key
        MockGetPromptKey.return_value = {'purdue_genai': 'fake-key'}
        
        # Parse the input file
        models, dataset_registry = url_parser.parse_URL_file(self.sample_input_path, is_zipped=False)
        url_parser.print_model_summary(models, dataset_registry)

        # Validate the parsed models
        self.assertEqual(len(models), 5)  # Ensure five models are parsed
        
        # Validate that models have the expected attributes
        for model in models:
            self.assertIsNotNone(model.id)
            # Some models may not have code or dataset, just check they exist as attributes
            self.assertTrue(hasattr(model, 'code'))
            self.assertTrue(hasattr(model, 'dataset'))
