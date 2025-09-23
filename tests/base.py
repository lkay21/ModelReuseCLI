import unittest

class BaseCLITestCase(unittest.TestCase):
    """Shared helpers for CLI tests."""

    def assertScore01(self, val: float) -> None:
        self.assertIsInstance(val, (int, float))
        self.assertGreaterEqual(val, 0.0)
        self.assertLessEqual(val, 1.0)

    def assertNonNegative(self, val: float) -> None:
        self.assertIsInstance(val, (int, float))
        self.assertGreaterEqual(val, 0.0)
