"""Passing baseline tests for the deterministic fixture."""

import unittest

from fixture_math import classify_number


class FixtureMathTests(unittest.TestCase):
    def test_positive_number(self) -> None:
        self.assertEqual(classify_number(2), "positive")

    def test_zero_is_non_positive(self) -> None:
        self.assertEqual(classify_number(0), "non-positive")


if __name__ == "__main__":
    unittest.main()
