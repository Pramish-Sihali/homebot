"""Tier 2 tests: the pushdown automaton P2.

The stack is the whole point of this tier, so most of these tests watch the
stack rather than the verdict: that it holds the running tally, that east and
west never touch it, that the bottom marker survives until the end, and that
the machine is deterministic.
"""

import unittest

from robot_walk import pda

from . import oracle

EXHAUSTIVE_LENGTH = 8       # 87,381 walks


def stack_after_each_step(word):
    """The stack column of the trace, one entry per step."""
    return [row[4] for row in pda.run(word).trace]


class TransitionTableTests(unittest.TestCase):

    def test_states_and_stack_alphabet_match_the_design(self):
        self.assertEqual(set(pda.STATES), {"q_start", "q_loop", "q_accept"})
        self.assertEqual(set(pda.GAMMA), {"N", "S", "$"})

    def test_the_table_has_the_ten_transitions_of_the_design(self):
        self.assertEqual(len(pda.DELTA), 10)

    def test_every_transition_is_explained(self):
        for key in pda.DELTA:
            self.assertIn(key, pda.MEANING)

    def test_the_machine_is_deterministic(self):
        # For every reachable (state, symbol, top) at most one transition may
        # apply, counting the epsilon-top entries that match any top.
        for state in pda.STATES:
            for symbol in oracle.SIGMA + ("",):
                for top in pda.GAMMA:
                    applicable = [
                        key
                        for key in pda.DELTA
                        if key[0] == state
                        and key[1] == symbol
                        and key[2] in (top, "")
                    ]
                    self.assertLessEqual(len(applicable), 1, (state, symbol, top))

    def test_east_and_west_never_touch_the_stack(self):
        for symbol in ("E", "W"):
            _, push = pda.DELTA[("q_loop", symbol, "")]
            self.assertEqual(push, "")

    def test_acceptance_requires_an_empty_tally(self):
        key = ("q_loop", "", "$")
        self.assertEqual(pda.DELTA[key][0], "q_accept")


class StackTests(unittest.TestCase):
    """The Stack class must behave like a stack and nothing more."""

    def test_push_and_pop_are_last_in_first_out(self):
        stack = pda.Stack()
        for symbol in "NSE":
            stack.push(symbol)
        self.assertEqual(stack.pop(), "E")
        self.assertEqual(stack.pop(), "S")
        self.assertEqual(stack.top(), "N")

    def test_a_new_stack_is_empty(self):
        self.assertTrue(pda.Stack().is_empty())
        self.assertIsNone(pda.Stack().top())

    def test_the_string_form_is_written_bottom_to_top(self):
        stack = pda.Stack()
        stack.push("$")
        stack.push("N")
        self.assertEqual(str(stack), "$N")


class StackInvariantTests(unittest.TestCase):
    """The stack above $ always holds |#N - #S| for the prefix read so far."""

    def check_invariant(self, word):
        stacks = stack_after_each_step(word)
        for count in range(len(word) + 1):
            prefix = word[:count]
            stack = stacks[count]
            expected = abs(prefix.count("N") - prefix.count("S"))
            self.assertEqual(
                len(stack) - 1, expected, f"{word!r} after {prefix!r}: {stack}"
            )

    def test_invariant_on_the_design_walk(self):
        self.check_invariant("NNESSW")

    def test_invariant_when_south_comes_first(self):
        self.check_invariant("SSNN")

    def test_invariant_when_directions_interleave(self):
        self.check_invariant("NSNSNS")

    def test_invariant_on_a_long_walk(self):
        self.check_invariant("NNNEEWWSSS")

    def test_the_bottom_marker_is_never_lost(self):
        for stack in stack_after_each_step("NNESSW")[:-1]:
            self.assertTrue(stack.startswith("$"), stack)

    def test_the_tally_never_mixes_directions(self):
        # Above $ the stack is all N or all S, never both: it is one signed
        # counter, not a record of the walk.
        for word in ("NSNSNN", "SSNNSS", "NNSSNN"):
            for stack in stack_after_each_step(word):
                tally = stack.replace("$", "").replace("(empty)", "")
                self.assertIn(set(tally), [set(), {"N"}, {"S"}], f"{word}: {stack}")

    def test_the_stack_trace_matches_the_design_document(self):
        self.assertEqual(
            stack_after_each_step("NNESSW"),
            ["$", "$N", "$NN", "$NN", "$N", "$", "$", "(empty)"],
        )


class LanguageTests(unittest.TestCase):

    def assert_verdict(self, word):
        self.assertEqual(
            pda.run(word).accepted, oracle.tier2(word), f"input {word!r}"
        )

    def test_empty_walk_is_accepted(self):
        self.assertTrue(pda.run("").accepted)

    def test_east_and_west_alone_are_accepted(self):
        self.assertTrue(pda.run("EEEWWW").accepted)
        self.assertTrue(pda.run("EEEE").accepted)

    def test_order_does_not_matter(self):
        for word in ("NNSS", "NSNS", "SSNN", "SNSN", "NSSN"):
            self.assertTrue(pda.run(word).accepted, word)

    def test_a_closing_step_may_come_first(self):
        # Unlike brackets, S may precede its N: the tally is signed.
        self.assertTrue(pda.run("SN").accepted)

    def test_unbalanced_walks_are_rejected(self):
        for word in ("N", "NNS", "SSN", "NNEESW"):
            self.assertFalse(pda.run(word).accepted, word)

    def test_the_rejection_message_counts_the_leftover(self):
        run = pda.run("NNE")
        self.assertIn("2 unmatched north", run.summary)

    def test_a_single_leftover_is_reported_in_the_singular(self):
        self.assertIn("1 unmatched", pda.run("N").summary)

    def test_malformed_input_is_rejected(self):
        for word in oracle.MALFORMED:
            self.assertFalse(pda.run(word).accepted, repr(word))

    def test_design_vectors(self):
        for word, expected, _ in oracle.DESIGN_VECTORS:
            self.assertEqual(pda.run(word).accepted, expected[1], repr(word))

    def test_exhaustive_agreement_with_the_oracle(self):
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            self.assert_verdict(word)

    def test_deep_stack(self):
        # 2,000 north steps, then 2,000 south: the stack grows to 2,000, which
        # is the unbounded memory a finite automaton does not have.
        word = "N" * 2000 + "S" * 2000
        self.assertTrue(pda.run(word).accepted)
        self.assertFalse(pda.run(word + "N").accepted)


if __name__ == "__main__":
    unittest.main()
