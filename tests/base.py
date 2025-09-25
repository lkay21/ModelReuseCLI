import unittest
from abc import ABC, abstractmethod

class BaseCLITestCase(unittest.TestCase, ABC):
    """
    Shared helpers/fixtures for CLI tests.
    Marked abstract so it isn't meant to be run directly.
    """

    #abstract contract: each concrete test must prepare fixtures 
    @abstractmethod
    def setUp(self) -> None:  
        return super().setUp()

    def assertScore01(self, val):
        self.assertIsInstance(val, (int, float))
        self.assertGreaterEqual(val, 0.0)
        self.assertLessEqual(val, 1.0)

    def assertNonNegative(self, val):
        self.assertIsInstance(val, (int, float))
        self.assertGreaterEqual(val, 0.0)

