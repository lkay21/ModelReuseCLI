import os
# from model import Model, Code, Dataset

from utils import url_parser
# from utils.url_parser import parse_url_file
from tests.base import BaseCLITestCase

import logging
logger = logging.getLogger('cli_logger')



class URLFileIntegrationTests(BaseCLITestCase):
    def setUp(self):
        # Create a sample input file for testing
        self.sample_input_path = "tests/sample_input.txt"
        with open(self.sample_input_path, "w") as f:
            # Use only 1 model for faster testing while still validating integration
            f.write(
                """,,https://huggingface.co/openai/whisper-tiny"""            )
            
    def tearDown(self):
        # Clean up the sample input file after the test
        if os.path.exists(self.sample_input_path):
            os.remove(self.sample_input_path)

    def test_parse_url_file_integration(self):
        """
        Test the parse_url_file function with a sample input file.
        """
        # Parse the input file
        models, dataset_registry = url_parser.parse_URL_file(self.sample_input_path)
        url_parser.print_model_summary(models, dataset_registry)

        # Validate the parsed models
        self.assertEqual(len(models), 1)  # Test with 1 model for speed

        # Run the pipeline for each model
        for model in models:
            model.calcMetricsParallel()

            # Debug: Print metrics and latencies
            logger.debug(f"\nMetrics for model {model.id}:")
            for metric, value in model.metrics.items():
                logger.debug(f"  {metric}: {value}")

            logger.debug(f"\nLatencies for model {model.id}:")
            for latency, value in model.latencies.items():
                logger.debug(f"  {latency}: {value}")

            # Validate metrics
            for metric, value in model.metrics.items():
                if isinstance(value, (int, float)):
                    self.assertScore01(value)  # Ensure value is between 0 and 1
                elif isinstance(value, dict):  # For size_score
                    for platform, score in value.items():
                        self.assertScore01(score)

            # Validate latencies
            for latency, value in model.latencies.items():
                self.assertNonNegative(value)  # Ensure latency is non-negative
