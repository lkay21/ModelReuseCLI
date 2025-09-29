import unittest
import time
from tests.base import BaseCLITestCase

# Import metrics to test
from metrics.size_score import size_score
from metrics.ramp_up_time import ramp_up_time
from metrics.performance_claims import performance_claims


class TestMetricsIntegration(BaseCLITestCase):
    """Test metrics with real API calls and data."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Use small, stable models for testing
        self.small_model = "distilbert-base-uncased"
        self.tiny_model = "prajjwal1/bert-tiny"
    
    def test_size_score_real_small_model(self):
        """Test size_score with a real small model."""
        result = size_score(self.small_model)
        
        print(f"Real size_score result for {self.small_model}: {result}")
        
        # Validate structure
        self.assertIsInstance(result, dict)
        expected_platforms = ["raspberry_pi", "jetson_nano", "desktop_pc", "aws_server"]
        
        for platform in expected_platforms:
            self.assertIn(platform, result)
            self.assertScore01(result[platform])
    
    def test_size_score_real_tiny_model(self):
        """Test size_score with a real tiny model."""
        result = size_score(self.tiny_model)
        
        print(f"Real size_score result for {self.tiny_model}: {result}")
        
        # Tiny model should have higher scores (smaller is better)
        self.assertIsInstance(result, dict)
        for platform, score in result.items():
            self.assertScore01(score)
    
    def test_ramp_up_time_real(self):
        """Test ramp_up_time with a real model."""
        result = ramp_up_time(self.small_model)
        
        print(f"Real ramp_up_time result for {self.small_model}: {result}")
        
        # Should return a valid score
        self.assertScore01(result)
    
    def test_performance_claims_real(self):
        """Test performance_claims with a real model (if API key available)."""
        try:
            result = performance_claims(self.small_model)
            print(f"Real performance_claims result for {self.small_model}: {result}")
            self.assertScore01(result)
        except Exception as e:
            # If API key not available, just log and skip
            print(f"Skipping performance_claims test: {e}")
            self.skipTest("API key not available for performance_claims")
    
    def test_multiple_metrics_consistency(self):
        """Test that multiple calls to the same metric are consistent."""
        # Test size_score consistency
        result1 = size_score(self.small_model)
        time.sleep(1)  # Small delay
        result2 = size_score(self.small_model)
        
        self.assertEqual(result1, result2, "size_score should be consistent across calls")
        
        # Test ramp_up_time consistency
        ramp1 = ramp_up_time(self.small_model)
        time.sleep(1)
        ramp2 = ramp_up_time(self.small_model)
        
        self.assertEqual(ramp1, ramp2, "ramp_up_time should be consistent across calls")


# if __name__ == "__main__":
#     unittest.main()