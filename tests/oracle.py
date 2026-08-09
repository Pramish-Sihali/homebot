"""The oracle: an independent answer to each of the three questions.

Every test that checks a verdict compares the machine against this module
rather than against a hand-written expected value, so the machines are never
graded by the same logic that produces them. The oracle deliberately uses the
most ordinary Python available -- a regular-expression search and three calls
to str.count -- because its job is to be obviously right, not to be a model of
computation. It is a measuring instrument only; nothing in robot_walk imports it.
"""

import itertools
import random
import re

SIGMA = ("N", "S", "E", "W")

#: The four immediate reversals Tier 1 forbids.
REVERSALS = re.compile("NS|SN|EW|WE")


def tier1(word: str) -> bool:
    """True when the walk never immediately undoes a step."""
    return all(symbol in SIGMA for symbol in word) and not REVERSALS.search(word)


def tier2(word: str) -> bool:
    """True when the walk ends on its starting row."""
    return (
        all(symbol in SIGMA for symbol in word)
        and word.count("N") == word.count("S")
    )


def tier3(word: str) -> bool:
    """True when the walk ends exactly back home."""
    return tier2(word) and word.count("E") == word.count("W")


def expected(word: str):
    """The three verdicts the system should produce for ``word``."""
    return (tier1(word), tier2(word), tier3(word))


def all_walks(max_length: int, alphabet=SIGMA):
    """Every walk of length 0 through ``max_length``, shortest first."""
    for length in range(max_length + 1):
        for letters in itertools.product(alphabet, repeat=length):
            yield "".join(letters)


def count_walks(max_length: int, alphabet=SIGMA) -> int:
    """How many walks ``all_walks`` will yield."""
    size = len(alphabet)
    return sum(size ** length for length in range(max_length + 1))


def random_walks(count: int, max_length: int = 20, seed: int = 315):
    """Reproducible random walks; the seed is fixed so failures can be rerun."""
    generator = random.Random(seed)
    for _ in range(count):
        length = generator.randint(0, max_length)
        yield "".join(generator.choice(SIGMA) for _ in range(length))


def displacement(word: str):
    """Net (east, north) offset, computed by simple arithmetic."""
    east = word.count("E") - word.count("W")
    north = word.count("N") - word.count("S")
    return east, north


#: Table 8 of the Week 4 design document: the walks the design predicts
#: verdicts for, with the verdicts it predicts.
DESIGN_VECTORS = (
    ("", (True, True, True), "the robot never moves"),
    ("NESW", (True, True, True), "a unit square, ending at home"),
    ("NNESSW", (True, True, True), "up 2, right 1, down 2, left 1"),
    ("NES", (True, True, False), "same row, one column east"),
    ("NNE", (True, False, False), "ends up and to the right"),
    ("NEB", (False, False, False), "illegal symbol B"),
    ("NS", (False, True, True), "steps north, then immediately back"),
    ("NNSSEEWW", (False, True, True), "out and back twice, with reversals"),
)

#: Inputs that are not walks at all. Each must be rejected by all three tiers
#: rather than crashing the system.
MALFORMED = (
    "NEB",          # a letter outside the alphabet
    "nesw",         # the right letters in the wrong case
    "N S",          # an embedded space
    "N3E2",         # decimal distances, the encoding Tier 2 could not handle
    "NE!",          # punctuation
    "NORTH",        # a word rather than a walk
    "\t",           # whitespace only
    "N\nS",         # an embedded newline
)
