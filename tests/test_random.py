"""Randomized differential testing against the oracle.

The exhaustive tests cover every walk up to length six or eight, which is a
complete proof for short inputs but says nothing about longer ones. These tests
sample longer walks instead: 5,000 random walks of length 0 to 20, plus walks
drawn from skewed distributions that make near-misses likely -- a walk that is
one step short of balanced is a far better test than a walk drawn uniformly,
because uniform walks are almost never in L2 or L3 at all.

The seed is fixed, so a failure here is reproducible rather than a rumour.
"""

import random
import unittest

from robot_walk import pipeline

from . import oracle

SAMPLE = 5000


class UniformRandomTests(unittest.TestCase):

    def test_all_three_tiers_against_the_oracle(self):
        for word in oracle.random_walks(SAMPLE, max_length=20, seed=315):
            self.assertEqual(pipeline.verdicts(word), oracle.expected(word), repr(word))

    def test_long_random_walks(self):
        for word in oracle.random_walks(200, max_length=120, seed=6):
            self.assertEqual(pipeline.verdicts(word), oracle.expected(word), repr(word))


class NearMissTests(unittest.TestCase):
    """Walks built to sit just inside or just outside the language."""

    def setUp(self):
        self.generator = random.Random(2026)

    def shuffled(self, word):
        letters = list(word)
        self.generator.shuffle(letters)
        return "".join(letters)

    def test_balanced_walks_are_accepted_however_they_are_shuffled(self):
        for size in range(1, 25):
            word = self.shuffled("NS" * size + "EW" * size)
            self.assertEqual(
                pipeline.verdicts(word)[1:], (True, True), repr(word)
            )

    def test_one_step_short_is_rejected(self):
        for size in range(1, 20):
            word = self.shuffled("NS" * size + "EW" * size)
            for position in range(0, len(word), 11):
                short = word[:position] + word[position + 1:]
                self.assertEqual(
                    pipeline.verdicts(short), oracle.expected(short), repr(short)
                )

    def test_one_step_too_many_is_rejected(self):
        for size in range(1, 25):
            word = self.shuffled("NS" * size + "EW" * size) + "N"
            self.assertFalse(pipeline.verdicts(word)[1], repr(word))
            self.assertFalse(pipeline.verdicts(word)[2], repr(word))

    def test_north_south_balanced_but_east_west_not(self):
        # The walks that separate Tier 2 from Tier 3: exactly the strings the
        # pushdown automaton cannot tell apart from the accepted ones.
        for size in range(1, 25):
            word = self.shuffled("NS" * size + "E" * size + "W" * (size - 1))
            self.assertTrue(pipeline.verdicts(word)[1], repr(word))
            self.assertFalse(pipeline.verdicts(word)[2], repr(word))

    def test_one_direction_only(self):
        for size in range(1, 40):
            self.assertEqual(
                pipeline.verdicts("N" * size), (True, False, False)
            )
            self.assertEqual(
                pipeline.verdicts("E" * size), (True, True, False)
            )

    def test_a_reversal_hidden_in_a_long_clean_walk(self):
        for position in range(0, 60, 3):
            word = "NE" * 30
            word = word[:position] + "SN" + word[position:]
            self.assertFalse(pipeline.verdicts(word)[0], repr(word))

    def test_random_junk_never_crashes_the_system(self):
        alphabet = "NSEW nsew0123!#\t"
        for _ in range(400):
            length = self.generator.randint(0, 15)
            word = "".join(self.generator.choice(alphabet) for _ in range(length))
            verdicts = pipeline.verdicts(word)
            self.assertEqual(verdicts, oracle.expected(word), repr(word))


if __name__ == "__main__":
    unittest.main()
