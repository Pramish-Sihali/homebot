"""Shared vocabulary for the three-tier robot walk recognizer.

One walk is one string over SIGMA = {N, S, E, W}; one symbol is one unit step.
The same string is handed to three independent machines, each answering a
harder question and each needing a strictly more powerful model:

    Tier 1  DFA  regular          no immediate reversal
    Tier 2  PDA  context-free     #N = #S   (ends on the starting row)
    Tier 3  TM   decidable        #N = #S and #E = #W   (ends exactly home)

Design reference: Week 4 design document, following Sipser (2013).
"""

from dataclasses import dataclass, field

SIGMA = ("N", "S", "E", "W")

#: One unit step per symbol, as (east, north) offsets.
STEP = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}

#: Each direction's opposite; a symbol immediately followed by its opposite is
#: the "immediate reversal" that Tier 1 rejects.
OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


@dataclass
class Run:
    """The outcome of running one machine on one input string.

    Attributes:
        tier: 1, 2 or 3.
        machine: short name of the model, e.g. "DFA M1".
        question: the plain-language question this tier answers.
        accepted: True if the machine halted in an accepting configuration.
        trace: table rows recording the computation, one row per step.
        headers: column headers for ``trace``.
        summary: one line explaining the verdict.
        extra: optional extra text blocks printed under the trace.
    """

    tier: int
    machine: str
    question: str
    accepted: bool
    trace: list = field(default_factory=list)
    headers: tuple = ()
    summary: str = ""
    extra: list = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return "ACCEPT" if self.accepted else "REJECT"


def is_well_formed(word: str) -> bool:
    """True when every character of ``word`` is a legal compass move."""
    return all(symbol in SIGMA for symbol in word)


def counts(word: str) -> dict:
    """Symbol counts, written #a(w) in the design document."""
    return {symbol: word.count(symbol) for symbol in SIGMA}
