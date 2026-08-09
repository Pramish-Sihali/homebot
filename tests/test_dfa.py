"""Tier 1 tests: the deterministic finite automaton M1.

Three things are checked: that the machine on disk is the machine in the design
document, that it behaves like a deterministic finite automaton is required to
behave, and that it accepts exactly the language L1.
"""

import unittest

from robot_walk import dfa

from . import oracle

EXHAUSTIVE_LENGTH = 8       # 87,381 walks


class TransitionTableTests(unittest.TestCase):
    """The table is the machine, so the table is what the design fixes."""

    def test_state_set_matches_the_design(self):
        self.assertEqual(
            set(dfa.STATES),
            {"q0", "q_N", "q_S", "q_E", "q_W", "q_dead"},
        )

    def test_delta_is_total_over_states_and_alphabet(self):
        for state in dfa.STATES:
            for symbol in oracle.SIGMA:
                self.assertIn(symbol, dfa.DELTA[state], f"delta1({state}, {symbol})")

    def test_delta_is_a_function_into_the_state_set(self):
        for state in dfa.STATES:
            for symbol, target in dfa.DELTA[state].items():
                self.assertIn(target, dfa.STATES)

    def test_every_state_but_the_trap_accepts(self):
        self.assertEqual(set(dfa.ACCEPTING), set(dfa.STATES) - {dfa.DEAD})

    def test_the_four_reversals_are_the_only_edges_into_the_trap(self):
        into_trap = {
            (state, symbol)
            for state in dfa.STATES
            if state != dfa.DEAD
            for symbol, target in dfa.DELTA[state].items()
            if target == dfa.DEAD
        }
        self.assertEqual(
            into_trap,
            {("q_N", "S"), ("q_S", "N"), ("q_E", "W"), ("q_W", "E")},
        )

    def test_the_trap_is_absorbing(self):
        for symbol in oracle.SIGMA:
            self.assertEqual(dfa.step(dfa.DEAD, symbol), dfa.DEAD)

    def test_a_direction_state_is_entered_only_on_its_own_symbol(self):
        for state in dfa.STATES:
            for symbol, target in dfa.DELTA[state].items():
                if target != dfa.DEAD:
                    self.assertEqual(target, f"q_{symbol}")


class MachineBehaviourTests(unittest.TestCase):
    """Properties every deterministic finite automaton must have."""

    def test_the_machine_reads_every_symbol(self):
        run = dfa.run("NNESSW")
        self.assertEqual(len(run.trace), len("NNESSW") + 1)

    def test_the_machine_keeps_reading_after_it_dies(self):
        # A DFA has no early exit: it must consume the whole input.
        run = dfa.run("NSNSNS")
        self.assertEqual(len(run.trace), 7)
        self.assertFalse(run.accepted)

    def test_the_state_path_is_deterministic(self):
        self.assertEqual(dfa.state_path("NNESSW"), dfa.state_path("NNESSW"))

    def test_the_state_path_matches_the_design_document(self):
        self.assertEqual(
            dfa.state_path("NNESSW"),
            "q0 --N-> q_N --N-> q_N --E-> q_E --S-> q_S --S-> q_S --W-> q_W",
        )

    def test_a_rejected_walk_ends_in_the_trap(self):
        self.assertEqual(dfa.state_path("NNSW").split()[-1], dfa.DEAD)

    def test_the_run_reports_why_it_rejected(self):
        run = dfa.run("NNSW")
        self.assertIn("undoes", run.summary)

    def test_only_the_last_move_is_remembered(self):
        # Two walks ending in the same direction leave the machine in the same
        # state, which is the whole content of "a finite automaton has no
        # memory beyond its state".
        self.assertEqual(dfa.state_path("NEN").split()[-1],
                         dfa.state_path("WSEN").split()[-1])


class LanguageTests(unittest.TestCase):
    """Acceptance must coincide with membership in L1."""

    def assert_verdict(self, word):
        self.assertEqual(
            dfa.run(word).accepted, oracle.tier1(word), f"input {word!r}"
        )

    def test_empty_walk_is_accepted(self):
        self.assertTrue(dfa.run("").accepted)

    def test_single_steps_are_accepted(self):
        for symbol in oracle.SIGMA:
            self.assertTrue(dfa.run(symbol).accepted)

    def test_each_reversal_is_rejected(self):
        for pair in ("NS", "SN", "EW", "WE"):
            self.assertFalse(dfa.run(pair).accepted, pair)

    def test_a_reversal_is_caught_wherever_it_sits(self):
        for word in ("NSEEEE", "EEENSE", "EEEENS"):
            self.assertFalse(dfa.run(word).accepted, word)

    def test_repeated_steps_are_not_reversals(self):
        self.assertTrue(dfa.run("NNNNNN").accepted)

    def test_turning_is_not_a_reversal(self):
        self.assertTrue(dfa.run("NENENE").accepted)

    def test_a_walk_that_returns_home_can_still_pass_tier_1(self):
        # NESW ends exactly where it started, yet no single step undoes the one
        # before it, so L1 says yes. This is the known limit of a regular
        # language, not a defect in the machine.
        self.assertTrue(dfa.run("NESW").accepted)
        self.assertEqual(oracle.displacement("NESW"), (0, 0))

    def test_a_walk_that_revisits_a_cell_can_still_pass_tier_1(self):
        # NENWSW crosses its own path at (0, 1). A finite automaton sees only
        # the pair of steps in front of it and cannot notice.
        self.assertTrue(dfa.run("NENWSW").accepted)
        self.assertEqual(oracle.displacement("NENWSW"), (-1, 1))

    def test_the_reverse_of_a_reversal_is_still_a_reversal(self):
        # NEWS looks like a tour but contains EW, so Tier 1 rejects it.
        self.assertFalse(dfa.run("NEWS").accepted)

    def test_malformed_input_is_rejected(self):
        for word in oracle.MALFORMED:
            self.assertFalse(dfa.run(word).accepted, repr(word))

    def test_design_vectors(self):
        for word, expected, _ in oracle.DESIGN_VECTORS:
            self.assertEqual(dfa.run(word).accepted, expected[0], repr(word))

    def test_exhaustive_agreement_with_the_oracle(self):
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            self.assert_verdict(word)

    def test_long_walk(self):
        self.assertTrue(dfa.run("NE" * 5000).accepted)
        self.assertFalse(dfa.run("NE" * 5000 + "W").accepted)


if __name__ == "__main__":
    unittest.main()
