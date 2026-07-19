"""Deliberate failing contract used by recovery and repair tests."""

import unittest

from fixture_math import classify_number


class NegativeNumberContract(unittest.TestCase):
    def test_negative_number_has_distinct_classification(self) -> None:
        self.assertEqual(classify_number(-1), "negative")


if __name__ == "__main__":
    unittest.main()
