"""Tier 3 tests: the Turing machine M3.

Two claims need testing here that the lower tiers do not raise. First, M3 is a
decider: it must halt on every input, not merely on the inputs we happen to
try. Second, it is one flat machine built from a subroutine instantiated twice,
so the transition table must be total and the two phases must run in order.
"""

import unittest

from robot_walk import tm

from . import oracle

EXHAUSTIVE_LENGTH = 6       # 5,461 walks, each run to a halt

HALTING = (tm.ACCEPT, tm.REJECT)


def crossings(word):
    """The rows of the default trace that record a symbol being crossed off."""
    return [row for row in tm.run(word).trace if str(row[2]).startswith("cross off")]


class TransitionTableTests(unittest.TestCase):

    def test_the_table_is_total_over_working_states_and_tape_symbols(self):
        working = [state for state in tm.STATES if state not in HALTING]
        for state in working:
            for symbol in tm.GAMMA:
                self.assertIn((state, symbol), tm.DELTA, f"delta3({state}, {symbol})")

    def test_the_machine_has_the_size_the_design_predicts(self):
        self.assertEqual(len(tm.STATES), 16)
        self.assertEqual(len(tm.DELTA), 84)

    def test_the_table_is_the_subroutine_instantiated_twice(self):
        phase1 = [state for state in tm.STATES if "p1" in state]
        phase2 = [state for state in tm.STATES if "p2" in state]
        self.assertEqual(len(phase1), len(phase2))

    def test_transitions_stay_inside_the_tape_alphabet(self):
        for (_, _), (next_state, write, direction) in tm.DELTA.items():
            self.assertIn(write, tm.GAMMA)
            self.assertIn(direction, (tm.LEFT, tm.RIGHT))
            self.assertIn(next_state, tm.STATES)

    def test_the_machine_only_ever_writes_a_cross_or_what_it_read(self):
        for (state, symbol), (_, write, _) in tm.DELTA.items():
            self.assertIn(write, (symbol, tm.CROSS), (state, symbol))

    def test_the_halting_states_have_no_transitions(self):
        for state in HALTING:
            for symbol in tm.GAMMA:
                self.assertNotIn((state, symbol), tm.DELTA)


class TapeTests(unittest.TestCase):

    def test_the_input_is_written_with_a_blank_to_its_left(self):
        tape = tm.Tape("NS")
        self.assertEqual(tape.cells[0], tm.BLANK)
        self.assertEqual(tape.read(), "N")

    def test_the_head_moves_one_cell_at_a_time(self):
        tape = tm.Tape("NS")
        tape.move(tm.RIGHT)
        self.assertEqual(tape.read(), "S")
        tape.move(tm.LEFT)
        self.assertEqual(tape.read(), "N")

    def test_the_head_cannot_fall_off_the_left_end(self):
        tape = tm.Tape("N")
        for _ in range(5):
            tape.move(tm.LEFT)
        self.assertEqual(tape.head, 0)

    def test_the_tape_is_unbounded_to_the_right(self):
        tape = tm.Tape("N")
        for _ in range(50):
            tape.move(tm.RIGHT)
        self.assertEqual(tape.read(), tm.BLANK)

    def test_writing_replaces_one_cell(self):
        tape = tm.Tape("NS")
        tape.write(tm.CROSS)
        self.assertEqual(tape.contents(), "xS")

    def test_the_configuration_marks_exactly_one_cell(self):
        configuration = tm.Tape("NESW").configuration()
        self.assertEqual(configuration.count("["), 1)
        self.assertEqual(configuration.count("]"), 1)


class DeciderTests(unittest.TestCase):
    """It must halt on every input, and say so."""

    def test_it_halts_on_every_short_walk(self):
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            run = tm.run(word)                      # returning at all is the test
            self.assertIn(run.verdict, ("ACCEPT", "REJECT"), repr(word))

    def test_it_halts_on_malformed_input(self):
        for word in oracle.MALFORMED:
            self.assertFalse(tm.run(word).accepted, repr(word))

    def test_it_halts_on_a_long_walk(self):
        self.assertTrue(tm.run("NE" * 100 + "SW" * 100).accepted)

    def test_it_reports_its_own_step_count(self):
        self.assertIn("machine steps", tm.run("NS").summary)

    def test_the_step_count_grows_quadratically_not_worse(self):
        for k in (4, 8, 16, 32):
            word = "NE" * k + "SW" * k
            steps = int(tm.run(word).summary.split("(")[1].split()[0])
            self.assertLess(steps, 3 * len(word) ** 2, word)

    def test_an_illegal_symbol_stops_the_machine_at_once(self):
        run = tm.run("NEB")
        self.assertFalse(run.accepted)
        self.assertIn("not in the tape alphabet", run.summary)
        self.assertLess(int(run.summary.split("(")[1].split()[0]), 10)


class CrossingOffTests(unittest.TestCase):

    def test_the_trace_matches_the_design_document(self):
        tapes = [row[3] for row in tm.run("NNESSW").trace]
        self.assertEqual(
            tapes,
            ["NNESSW", "xNESSW", "xNExSW", "xxExSW", "xxExxW",
             "xxExxW", "xxxxxW", "xxxxxx", "xxxxxx"],
        )

    def test_an_accepted_walk_ends_with_everything_crossed_off(self):
        for word in ("NS", "NESW", "NNESSW", "EW", "SNWE"):
            final = tm.run(word).trace[-1][3]
            self.assertEqual(set(final), {tm.CROSS}, word)

    def test_every_accepted_walk_is_crossed_off_in_pairs(self):
        word = "NNESSW"
        self.assertEqual(len(crossings(word)), len(word))

    def test_north_and_south_are_paired_before_east_and_west(self):
        # The two phases are sequential, which is what a single stack could not
        # do and what the rewritable tape buys.
        crossed = [row[2].split()[-1] for row in crossings("NESWNS")]
        first_east_west = next(
            i for i, symbol in enumerate(crossed) if symbol in ("E", "W")
        )
        self.assertTrue(all(symbol in ("N", "S") for symbol in crossed[:first_east_west]))
        self.assertTrue(all(symbol in ("E", "W") for symbol in crossed[first_east_west:]))

    def test_a_surplus_symbol_is_left_uncrossed(self):
        # NSS has one south too many; the extra S is still on the tape when the
        # machine rejects.
        self.assertEqual(tm.run("NSS").trace[-1][3], "xxS")

    def test_the_last_symbol_may_be_crossed_off_before_the_rejection(self):
        # PAIR-CHECK crosses off an X and only then looks for its partner, so
        # NNS ends with a blank-looking tape and still rejects. A full tape is
        # therefore not what acceptance means -- reaching q_accept is.
        run = tm.run("NNS")
        self.assertEqual(run.trace[-1][3], "xxx")
        self.assertFalse(run.accepted)

    def test_the_rejection_names_the_unmatched_direction(self):
        self.assertIn("no S to cancel", tm.run("NNS").summary)
        self.assertIn("no N to cancel", tm.run("NSS").summary)
        self.assertIn("no W to cancel", tm.run("NSE").summary)

    def test_the_full_trace_prints_every_configuration(self):
        run = tm.run("NS", full_trace=True)
        steps = int(run.summary.split("(")[1].split()[0])
        self.assertEqual(len(run.trace), steps + 2)   # start row and accept row
        for row in run.trace[1:-1]:
            self.assertEqual(str(row[2]).count("["), 1, row)


class LanguageTests(unittest.TestCase):

    def test_empty_walk_is_accepted(self):
        self.assertTrue(tm.run("").accepted)

    def test_balanced_in_one_direction_only_is_rejected(self):
        self.assertFalse(tm.run("NSE").accepted)
        self.assertFalse(tm.run("EWN").accepted)

    def test_order_does_not_matter(self):
        for word in ("NSEW", "NESW", "WSEN", "SWNE"):
            self.assertTrue(tm.run(word).accepted, word)

    def test_design_vectors(self):
        for word, expected, _ in oracle.DESIGN_VECTORS:
            self.assertEqual(tm.run(word).accepted, expected[2], repr(word))

    def test_exhaustive_agreement_with_the_oracle(self):
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            self.assertEqual(tm.run(word).accepted, oracle.tier3(word), repr(word))

    def test_acceptance_means_the_robot_is_home(self):
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            if tm.run(word).accepted:
                self.assertEqual(oracle.displacement(word), (0, 0), repr(word))


if __name__ == "__main__":
    unittest.main()
