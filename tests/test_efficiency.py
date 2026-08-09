"""Efficiency tests: does each machine cost what its model says it should?

The syllabus asks Week 6 to validate accuracy *and* efficiency, so these tests
assert the cost of each tier in the machine's own units -- symbols read, stack
operations, machine steps -- rather than in seconds, which would measure the
laptop rather than the model. Week 7 takes these numbers and analyses them.
"""

import time
import unittest

from robot_walk import dfa, pda, tm

from . import oracle


def tm_steps(word):
    """The Turing machine's own step counter, taken from its verdict line."""
    return int(tm.run(word).summary.split("(")[1].split()[0])


class FiniteAutomatonCostTests(unittest.TestCase):
    """One step per symbol, constant memory: O(n) time, O(1) space."""

    def test_one_step_per_symbol(self):
        for size in (0, 1, 10, 100, 1000):
            word = "NE" * size
            self.assertEqual(len(dfa.run(word).trace), len(word) + 1)

    def test_the_state_set_never_grows(self):
        # The machine has six states whatever it is fed; that is what "finite
        # memory" means.
        before = set(dfa.STATES)
        dfa.run("NE" * 5000)
        self.assertEqual(set(dfa.STATES), before)
        self.assertEqual(len(dfa.STATES), 6)

    def test_a_very_long_walk_is_still_fast(self):
        started = time.perf_counter()
        dfa.run("NE" * 50000)
        self.assertLess(time.perf_counter() - started, 2.0)


class PushdownAutomatonCostTests(unittest.TestCase):
    """One step per symbol, stack as tall as the tally: O(n) time and space."""

    def test_one_step_per_symbol_plus_two_epsilon_moves(self):
        for size in (1, 10, 100):
            word = "NS" * size
            # One row to plant $, one per symbol, one to accept.
            self.assertEqual(len(pda.run(word).trace), len(word) + 2)

    def test_the_stack_is_never_taller_than_the_tally(self):
        for word in oracle.random_walks(300, max_length=40, seed=7):
            for row in pda.run(word).trace:
                stack = str(row[4]).replace("(empty)", "")
                self.assertLessEqual(len(stack), len(word) + 1, word)

    def test_the_worst_case_stack_is_the_whole_input(self):
        word = "N" * 500
        tallest = max(
            len(str(row[4]).replace("(empty)", "")) for row in pda.run(word).trace
        )
        self.assertEqual(tallest, len(word) + 1)     # the tally plus the marker

    def test_east_and_west_cost_no_stack_space(self):
        word = "EW" * 500
        tallest = max(
            len(str(row[4]).replace("(empty)", "")) for row in pda.run(word).trace
        )
        self.assertEqual(tallest, 1)                 # the bottom marker alone


class TuringMachineCostTests(unittest.TestCase):
    """Two phases, each crossing off pairs with a sweep per pair: O(n^2)."""

    def test_the_step_count_stays_under_a_quadratic_bound(self):
        for k in (2, 4, 8, 16, 32, 64):
            word = "NE" * k + "SW" * k
            self.assertLess(tm_steps(word), 3 * len(word) ** 2, word)

    def test_the_ratio_to_n_squared_settles_rather_than_grows(self):
        ratios = []
        for k in (4, 8, 16, 32, 64):
            word = "NE" * k + "SW" * k
            ratios.append(tm_steps(word) / len(word) ** 2)
        for earlier, later in zip(ratios, ratios[1:]):
            self.assertLess(later, earlier)          # falling towards a constant
        self.assertLess(ratios[-1], 1.5)

    def test_the_cost_is_not_linear(self):
        # Doubling the input must more than double the work, or the machine
        # would not be doing the sweeps the design calls for.
        short = tm_steps("NE" * 16 + "SW" * 16)
        long = tm_steps("NE" * 32 + "SW" * 32)
        self.assertGreater(long, 2 * short)

    def test_rejection_can_be_cheaper_than_acceptance(self):
        # An illegal symbol is caught in the first scan, without any crossing
        # off at all.
        self.assertLess(tm_steps("B" + "NE" * 50), tm_steps("NE" * 50 + "SW" * 50))

    def test_every_run_halts_within_the_safety_limit(self):
        self.assertLess(tm_steps("NESW" * 60), tm.step_limit(240))

    def test_the_safety_limit_never_stops_a_legitimate_run(self):
        # Found in Week 7: a fixed ceiling of two million steps halted every
        # accepted walk longer than 1,408 symbols, turning a decision into a
        # crash. The limit now grows with the input, so it stays an order of
        # magnitude above the machine's exact cost of (n + 1)(n + 10).
        for n in (1408, 1410, 2000, 4000):
            self.assertGreater(tm.step_limit(n), (n + 1) * (n + 10), n)
        word = "NESW" * 355                          # 1,420 symbols
        self.assertTrue(tm.run(word).accepted)


class ComparativeCostTests(unittest.TestCase):
    """The escalation the project is about, measured."""

    def test_the_higher_tier_costs_more_on_the_same_input(self):
        word = "NE" * 40 + "SW" * 40
        self.assertLess(len(dfa.run(word).trace), tm_steps(word))
        self.assertLess(len(pda.run(word).trace), tm_steps(word))

    def test_the_two_cheap_tiers_cost_the_same_order(self):
        word = "NE" * 100 + "SW" * 100
        self.assertLess(
            abs(len(dfa.run(word).trace) - len(pda.run(word).trace)), 5
        )

    def test_the_whole_suite_of_design_walks_runs_instantly(self):
        started = time.perf_counter()
        for word, _, _ in oracle.DESIGN_VECTORS:
            tm.run(word)
        self.assertLess(time.perf_counter() - started, 0.5)


if __name__ == "__main__":
    unittest.main()
