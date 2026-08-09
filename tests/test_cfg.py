"""Tier 2 tests, grammar side: the context-free grammar G2.

The design document claims L(G2) = L2 -- that the grammar generates exactly the
language the pushdown automaton recognizes. These tests check that claim
directly, and check that the derivations the system prints are real leftmost
derivations of the walk they claim to derive.
"""

import unittest

from robot_walk import cfg, pda

from . import oracle

EXHAUSTIVE_LENGTH = 7       # 21,845 walks; the parser costs O(n^4), so it
                            # is exhausted one length short of the machines


def replay(forms, word):
    """Check a printed derivation really is a leftmost derivation of ``word``."""
    if forms[0] != cfg.START:
        return False
    if (forms[-1] if forms[-1] != "eps" else "") != word:
        return False
    for before, after in zip(forms, forms[1:]):
        before = "" if before == "eps" else before
        after = "" if after == "eps" else after
        position = next(
            (i for i, symbol in enumerate(before) if symbol in cfg.VARIABLES), None
        )
        if position is None:
            return False
        prefix, suffix = before[:position], before[position + 1:]
        # Only the leftmost variable may be replaced, and by one rule's body.
        if not after.startswith(prefix) or not after.endswith(suffix):
            return False
        body = after[len(prefix):len(after) - len(suffix)] if suffix else after[len(prefix):]
        if tuple(body) not in cfg.RULES and not (body == "" and () in cfg.RULES):
            return False
    return True


class GrammarTests(unittest.TestCase):

    def test_the_rules_match_the_design_document(self):
        self.assertEqual(
            set(cfg.RULES),
            {
                ("N", "B", "S", "B"),
                ("S", "B", "N", "B"),
                ("E", "B"),
                ("W", "B"),
                (),
            },
        )

    def test_there_is_one_variable(self):
        self.assertEqual(cfg.VARIABLES, ("B",))
        self.assertEqual(cfg.START, "B")

    def test_the_start_variable_does_not_collide_with_a_terminal(self):
        self.assertNotIn(cfg.START, oracle.SIGMA)

    def test_every_rule_keeps_north_and_south_balanced(self):
        for rule in cfg.RULES:
            terminals = [symbol for symbol in rule if symbol not in cfg.VARIABLES]
            self.assertEqual(terminals.count("N"), terminals.count("S"), rule)

    def test_every_rule_but_epsilon_consumes_a_terminal(self):
        # This is what makes the parser terminate.
        for rule in cfg.RULES:
            if rule:
                self.assertTrue(
                    any(symbol not in cfg.VARIABLES for symbol in rule), rule
                )


class ParserTests(unittest.TestCase):

    def test_the_empty_walk_is_derivable(self):
        self.assertIsNotNone(cfg.parse(""))

    def test_an_unbalanced_walk_is_not_derivable(self):
        self.assertIsNone(cfg.parse("N"))
        self.assertIsNone(cfg.parse("NNS"))

    def test_malformed_input_is_not_derivable(self):
        for word in oracle.MALFORMED:
            self.assertIsNone(cfg.parse(word), repr(word))

    def test_the_parser_agrees_with_the_oracle_exhaustively(self):
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            self.assertEqual(
                cfg.parse(word) is not None, oracle.tier2(word), repr(word)
            )

    def test_the_grammar_and_the_machine_describe_the_same_language(self):
        # L(G2) = L2, the claim the design document makes.
        for word in oracle.all_walks(EXHAUSTIVE_LENGTH):
            self.assertEqual(
                cfg.parse(word) is not None, pda.run(word).accepted, repr(word)
            )


class DerivationTests(unittest.TestCase):

    def test_the_derivation_of_the_design_walk(self):
        self.assertEqual(
            cfg.leftmost_derivation("NNESSW"),
            ["B", "NBSB", "NNBSBSB", "NNEBSBSB", "NNESBSB", "NNESSB",
             "NNESSWB", "NNESSW"],
        )

    def test_a_derivation_is_leftmost_and_ends_at_the_walk(self):
        for word in oracle.all_walks(6):
            if not oracle.tier2(word):
                continue
            forms = cfg.leftmost_derivation(word)
            self.assertIsNotNone(forms, repr(word))
            self.assertTrue(replay(forms, word), f"{word!r}: {forms}")

    def test_no_derivation_for_a_walk_outside_the_language(self):
        self.assertIsNone(cfg.leftmost_derivation("NNE"))
        self.assertIsNone(cfg.derivation_lines("NNE"))

    def test_the_printed_derivation_is_elided_when_long(self):
        lines = cfg.derivation_lines("NESW" * 6)
        self.assertLessEqual(len(lines), 12)
        self.assertIn("...", "".join(lines))

    def test_a_short_derivation_is_printed_whole(self):
        lines = cfg.derivation_lines("NS")
        self.assertNotIn("...", "".join(lines))


if __name__ == "__main__":
    unittest.main()
