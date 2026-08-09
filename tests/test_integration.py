"""Integration tests: the three machines wired together as one system.

These tests treat the pipeline as a black box and check the properties the
project claims about the system as a whole -- that all three tiers always
answer, that their answers are related the way the theory says, and that the
printed report is usable in front of an audience.
"""

import unittest

from robot_walk import dfa, grid, pda, pipeline, spec, tm

from . import oracle

EXHAUSTIVE_LENGTH = 6


class VerdictTests(unittest.TestCase):

    def test_three_verdicts_are_returned(self):
        verdicts = pipeline.verdicts("NNESSW")
        self.assertEqual(len(verdicts), 3)
        for verdict in verdicts:
            self.assertIsInstance(verdict, bool)

    def test_the_design_validation_vectors(self):
        # Table 8 of the Week 4 design document, the contract the system was
        # written against.
        for word, expected, description in oracle.DESIGN_VECTORS:
            self.assertEqual(pipeline.verdicts(word), expected, f"{word!r} ({description})")

    def test_the_pipeline_agrees_with_the_three_machines(self):
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            self.assertEqual(
                pipeline.verdicts(word),
                (dfa.run(word).accepted, pda.run(word).accepted, tm.run(word).accepted),
                repr(word),
            )

    def test_the_pipeline_agrees_with_the_oracle(self):
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            self.assertEqual(pipeline.verdicts(word), oracle.expected(word), repr(word))

    def test_malformed_input_is_rejected_by_every_tier(self):
        for word in oracle.MALFORMED:
            self.assertEqual(pipeline.verdicts(word), (False, False, False), repr(word))

    def test_the_system_is_deterministic(self):
        for word in ("NNESSW", "NNE", "NEB", ""):
            self.assertEqual(pipeline.verdicts(word), pipeline.verdicts(word), word)


class LanguageRelationshipTests(unittest.TestCase):
    """The relationships between L1, L2 and L3 that the design document claims."""

    def test_home_implies_the_starting_row(self):
        # L3 is a subset of L2.
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            tier1, tier2, tier3 = pipeline.verdicts(word)
            if tier3:
                self.assertTrue(tier2, repr(word))

    def test_the_starting_row_does_not_imply_home(self):
        self.assertEqual(pipeline.verdicts("NES"), (True, True, False))

    def test_tier_1_is_independent_of_the_other_two(self):
        # A walk can fail Tier 1 and pass Tiers 2 and 3 ...
        self.assertEqual(pipeline.verdicts("NS"), (False, True, True))
        # ... and pass Tier 1 while failing the other two.
        self.assertEqual(pipeline.verdicts("NNE"), (True, False, False))

    def test_every_combination_the_design_predicts_actually_occurs(self):
        seen = {pipeline.verdicts(word) for word in oracle.all_walks(5)}
        for combination in (
            (True, True, True),
            (True, True, False),
            (True, False, False),
            (False, True, True),
            (False, True, False),
            (False, False, False),
        ):
            self.assertIn(combination, seen, combination)

    def test_no_tier_short_circuits_another(self):
        # Tier 1 rejects NS, and Tiers 2 and 3 still run and still answer.
        report = pipeline.report("NS")
        for tier in ("TIER 1", "TIER 2", "TIER 3"):
            self.assertIn(tier, report)
        self.assertEqual(report.count("VERDICT:"), 3)


class ReportTests(unittest.TestCase):
    """The printed report is the deliverable; it has to hold together."""

    def setUp(self):
        self.report = pipeline.report("NNESSW")

    def test_the_report_shows_the_input_and_its_counts(self):
        self.assertIn("INPUT: NNESSW", self.report)
        self.assertIn("#N = 2", self.report)

    def test_the_report_draws_the_walk(self):
        self.assertIn("H = home", self.report)

    def test_the_report_carries_one_trace_per_machine(self):
        self.assertIn("stack (bottom..top)", self.report)
        self.assertIn("-> state", self.report)
        self.assertIn("tape", self.report)

    def test_the_report_names_the_model_of_each_tier(self):
        for label in ("regular", "context-free (not regular)",
                      "decidable (not context-free)"):
            self.assertIn(label, self.report)

    def test_the_report_explains_each_machine_in_plain_terms(self):
        for metaphor in ("goldfish", "sticky notes", "notebook"):
            self.assertIn(metaphor, self.report)

    def test_an_accepted_walk_gets_a_derivation(self):
        self.assertIn("Leftmost derivation", self.report)

    def test_a_rejected_walk_gets_no_derivation(self):
        self.assertNotIn("Leftmost derivation", pipeline.report("NNE"))

    def test_the_report_ends_with_a_summary_of_the_three_answers(self):
        summary = self.report[self.report.index("SUMMARY"):]
        self.assertEqual(summary.count("ACCEPT"), 3)

    def test_the_report_survives_the_empty_walk(self):
        report = pipeline.report("")
        self.assertIn("(empty string)", report)
        self.assertEqual(report.count("VERDICT:"), 3)

    def test_the_report_survives_malformed_input(self):
        for word in oracle.MALFORMED:
            self.assertEqual(pipeline.report(word).count("VERDICT:"), 3, repr(word))

    def test_the_full_tape_option_lengthens_only_the_tier_3_trace(self):
        short = pipeline.report("NS")
        full = pipeline.report("NS", full_trace=True)
        self.assertGreater(len(full), len(short))
        self.assertIn("[", full)


class GridTests(unittest.TestCase):
    """The picture is how an audience checks the machines; it must be right."""

    def test_the_path_starts_at_home(self):
        self.assertEqual(grid.path("NNESSW")[0], (0, 0))

    def test_the_path_has_one_cell_per_step(self):
        self.assertEqual(len(grid.path("NNESSW")), 7)

    def test_the_displacement_matches_arithmetic(self):
        for word in oracle.all_walks(5):
            self.assertEqual(grid.displacement(word), oracle.displacement(word), word)

    def test_a_walk_that_ends_home_says_so(self):
        self.assertIn("standing on home", grid.render("NESW"))

    def test_a_walk_that_ends_elsewhere_says_where(self):
        self.assertIn("1 north and 1 east", grid.render("NE"))

    def test_the_robot_marker_appears_only_when_it_is_away_from_home(self):
        away = grid.render("NE").split("\n\n")[0]        # the map, not the legend
        home = grid.render("NESW").split("\n\n")[0]
        self.assertIn(grid.ROBOT, away)
        self.assertNotIn(grid.ROBOT, home)
        self.assertIn(grid.HOME, home)

    def test_illegal_symbols_do_not_move_the_robot(self):
        self.assertEqual(grid.displacement("NEB"), grid.displacement("NE"))

    def test_the_grid_does_not_decide_anything(self):
        # The picture is presentation only: recognition happens in the machines.
        self.assertNotIn("accept", grid.render("NESW").lower())


class SpecTests(unittest.TestCase):

    def test_the_alphabet_is_the_four_compass_moves(self):
        self.assertEqual(spec.SIGMA, ("N", "S", "E", "W"))

    def test_every_symbol_has_a_unit_step(self):
        for symbol in spec.SIGMA:
            east, north = spec.STEP[symbol]
            self.assertEqual(abs(east) + abs(north), 1, symbol)

    def test_opposites_are_mutual(self):
        for symbol, opposite in spec.OPPOSITE.items():
            self.assertEqual(spec.OPPOSITE[opposite], symbol)

    def test_counts_are_descriptive_only(self):
        self.assertEqual(spec.counts("NNESSW"), {"N": 2, "S": 2, "E": 1, "W": 1})

    def test_well_formedness_matches_the_alphabet(self):
        self.assertTrue(spec.is_well_formed("NESW"))
        self.assertFalse(spec.is_well_formed("NEB"))


if __name__ == "__main__":
    unittest.main()
