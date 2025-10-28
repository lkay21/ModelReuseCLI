import unittest
import logging
from unittest.mock import patch, MagicMock
from tests.base import BaseCLITestCase

# Import all metric functions
from metrics.size_score import size_score
from metrics.ramp_up_time import ramp_up_time
from metrics.bus_factor import bus_factor
from metrics.license import license_score
from metrics.code_quality import code_quality
from metrics.dataset_quality import compute_dataset_quality
from metrics.performance_claims import performance_claims
from metrics.dataset_and_code_score import dataset_and_code_score


class TestMetricsSeparate(BaseCLITestCase):
    """Test each metric function individually with mocked dependencies."""
    
    def setUp(self):
        """Set up test fixtures - required by BaseCLITestCase."""
        super().setUp()
        # Set up logger for tests
        self.logger = logging.getLogger('cli_logger')
    
    def test_basic_discovery(self):
        """Basic test to ensure the test is discovered."""
        self.assertTrue(True)
        print("Test discovery working!")

    @patch("metrics.size_score.HFClient")
    def test_size_score_valid_model(self, MockHFClient):
        """Test size_score with a valid model that has safetensors."""
        # Mock the HFClient and its model_info method
        mock_client = MockHFClient.return_value
        mock_client.model_info.return_value = {
            "safetensors": MagicMock(total=5e9)  # 5 GB model size
        }

        # Call the size_score function
        model_id = "test-model"
        result = size_score(model_id)
        
        print(f"Size score result: {result}")

        # Validate the result structure
        self.assertIsInstance(result, dict)
        expected_platforms = ["raspberry_pi", "jetson_nano", "desktop_pc", "aws_server"]
        for platform in expected_platforms:
            self.assertIn(platform, result)
            self.assertIsInstance(result[platform], (int, float))
            self.assertGreaterEqual(result[platform], 0)
            self.assertLessEqual(result[platform], 1)

    @patch("metrics.size_score.HFClient")
    def test_size_score_no_safetensors(self, MockHFClient):
        """Test size_score when model has no safetensors."""
        mock_client = MockHFClient.return_value
        mock_client.model_info.return_value = {}

        model_id = "test-model"
        result = size_score(model_id)
        
        print(f"Size score (no safetensors) result: {result}")

        # All platforms should return 0
        self.assertIsInstance(result, dict)
        for platform, score in result.items():
            self.assertEqual(score, 0)

    @patch("metrics.ramp_up_time.get_prompt_key")
    @patch("metrics.ramp_up_time.HFClient")
    def test_ramp_up_time_with_readme(self, MockHFClient, MockGetPromptKey):
        """Test ramp_up_time with a model that has a README."""
        mock_client = MockHFClient.return_value
        mock_client.model_info.return_value = {
            "cardData": {"library_name": "transformers"},
            "readme": "This is a test README with model information."
        }
        mock_client.model_card_text.return_value = "This is a test README with model information."
        
        # Mock get_prompt_key to return None (so LLM blend is skipped)
        MockGetPromptKey.return_value = {}

        model_id = "test-model"
        result = ramp_up_time(model_id)
        
        print(f"Ramp up time result: {result}")

        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 1)

    @patch("metrics.bus_factor.git_api.get_contributors")
    def test_bus_factor(self, mock_get_contributors):
        """Test bus_factor function."""
        # Mock the GitHub API response
        mock_get_contributors.return_value = [
            {"login": "user1", "contributions": 100},
            {"login": "user2", "contributions": 50},
            {"login": "user3", "contributions": 25},
            {"login": "user4", "contributions": 10},
            {"login": "user5", "contributions": 5},
        ]
        
        id = "freeCodeCamp/freeCodeCamp"
        
        # Call the function and capture the result
        result = bus_factor(id, "github")
        self.logger.debug(f"Bus Factor for {id}: {result}")

        # Validate the result
        self.logger.debug(f"Bus factor result: {result}")
        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 1)

    @patch("metrics.license.HFClient")
    @patch("metrics.license.get_prompt_key")
    @patch("metrics.license.prompt_purdue_genai")
    def test_license_metric(self, mock_prompt_purdue, mock_get_prompt_key, mock_hf_client):
        """Test license_score function with mocked dependencies."""
        # Mock the HFClient
        mock_client = mock_hf_client.return_value
        mock_client.model_info.return_value = {"license": "MIT"}
        mock_client.model_card_text.return_value = "This model is licensed under MIT license."
        
        # Mock the API key
        mock_get_prompt_key.return_value = {'purdue_genai': 'fake-api-key'}
        
        # Mock the prompt response with the expected format
        mock_prompt_purdue.return_value = "0.8: This model has a clear MIT license (0.4/0.5) and is compatible with LGPLv2.1 (0.4/0.5)"
        
        model_id = "test-model"
        result = license_score(model_id)

        print(f"License score result: {result}")

        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 1)

    def test_code_quality(self):
        """Test code_quality function."""
        code_url = "https://github.com/google-research/bert"
        result = code_quality(code_url, "github")

        self.logger.debug(f"Code quality result: {result}")

        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 1)

    @patch("metrics.dataset_quality.get_prompt_key")
    def test_dataset_quality(self, MockGetPromptKey):
        """Test dataset_quality function."""
        # Mock get_prompt_key to return None (function will return 0.0)
        MockGetPromptKey.return_value = None
        
        model_id = "test-model"
        result = compute_dataset_quality(model_id)
        
        print(f"Dataset quality result: {result}")

        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 1)

    @patch("metrics.performance_claims.get_prompt_key")
    @patch("metrics.performance_claims.prompt_purdue_genai")
    @patch("metrics.performance_claims.HFClient")
    def test_performance_claims_mocked(self, MockHFClient, MockPrompt, MockGetPromptKey):
        """Test performance_claims with mocked dependencies."""
        # Mock HFClient
        mock_client = MockHFClient.return_value
        mock_client.model_info.return_value = {
            "readme": "This model achieves state-of-the-art performance."
        }
        mock_client.model_card_text.return_value = "This model achieves state-of-the-art performance."
        
        # Mock get_prompt_key to return purdue_genai
        MockGetPromptKey.return_value = {'purdue_genai': 'fake-key'}
        
        # Mock the prompt function
        MockPrompt.return_value = "0.8"  # Mock response indicating good performance claims

        model_id = "test-model"
        result = performance_claims(model_id)
        
        print(f"Performance claims result: {result}")

        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 1)

    @patch("metrics.dataset_and_code_score.make_request")
    @patch("metrics.dataset_and_code_score.HfFileSystem")
    @patch("metrics.dataset_and_code_score.HFClient")
    def test_dataset_and_code_score_mocked(self, MockHFClient, MockHfFS, MockMakeRequest):
        """Test dataset_and_code_score with mocked dependencies."""
        # Mock filesystem
        mock_fs = MockHfFS.return_value
        mock_fs.ls.return_value = [
            {"name": "datasets/test-dataset/README.md"},
            {"name": "datasets/test-dataset/data.csv"}
        ]
        
        # Mock GitHub API request
        MockMakeRequest.return_value.json.return_value = {
            "tree": [
                {"path": "README.md"},
                {"path": "requirements.txt"},
                {"path": "tests/test_model.py"}
            ]
        }

        dataset_id = "test-dataset"
        code_id = "test-repo"
        code_type = "github"
        result = dataset_and_code_score(dataset_id, code_id, code_type)
        
        print(f"Dataset and code score result: {result}")

        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 1)


# if __name__ == "__main__":
#     unittest.main()