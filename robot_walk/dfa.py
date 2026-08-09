"""Tier 1: the deterministic finite automaton M1 (regular).

Question: did the robot ever immediately undo its last move?

    L1 = { w in SIGMA* : w contains no substring in {NS, SN, EW, WE} }

In plain terms this machine is a goldfish. It remembers exactly one thing --
which direction it moved last -- because that is all a finite automaton can
hold. The recognizer below is driven by the explicit transition table DELTA
(Table 2 of the Week 4 design document); it never counts anything.

    M1 = (Q1, SIGMA, delta1, q0, F1)
"""

from .spec import SIGMA, Run

START = "q0"
DEAD = "q_dead"

#: delta1 : Q1 x SIGMA -> Q1, exactly as tabulated in the design document.
#: State q_d means "the last symbol read was d and no reversal has occurred".
DELTA = {
    "q0": {"N": "q_N", "S": "q_S", "E": "q_E", "W": "q_W"},
    "q_N": {"N": "q_N", "S": DEAD, "E": "q_E", "W": "q_W"},
    "q_S": {"N": DEAD, "S": "q_S", "E": "q_E", "W": "q_W"},
    "q_E": {"N": "q_N", "S": "q_S", "E": "q_E", "W": DEAD},
    "q_W": {"N": "q_N", "S": "q_S", "E": DEAD, "W": "q_W"},
    DEAD: {"N": DEAD, "S": DEAD, "E": DEAD, "W": DEAD},
}

STATES = tuple(DELTA)

#: Every state except the trap accepts, so M1 accepts whenever it survives the
#: input -- including the empty string.
ACCEPTING = frozenset(state for state in STATES if state != DEAD)


def step(state: str, symbol: str) -> str:
    """One application of delta1. Symbols outside SIGMA lead to the trap."""
    if symbol not in SIGMA:
        return DEAD
    return DELTA[state][symbol]


def run(word: str) -> Run:
    """Read ``word`` one symbol at a time and report the state path."""
    state = START
    trace = [(0, "--", "(start)", state, "yes" if state in ACCEPTING else "no")]
    reason = ""

    for index, symbol in enumerate(word, start=1):
        previous = state
        state = step(state, symbol)
        note = ""
        if state == DEAD and previous != DEAD:
            if symbol not in SIGMA:
                note = f"'{symbol}' is not a compass move"
                reason = f"the symbol '{symbol}' is not in the alphabet"
            else:
                undone = word[index - 2] if index >= 2 else "?"
                note = f"{symbol} immediately undoes {undone}"
                reason = (
                    f"step {index} ({symbol}) immediately undoes step "
                    f"{index - 1} ({undone})"
                )
        trace.append(
            (index, symbol, previous, state, "yes" if state in ACCEPTING else "no", note)
        )

    accepted = state in ACCEPTING
    if accepted:
        summary = "the walk never doubles back on itself in a single step"
    else:
        summary = reason

    # Pad the first row so every row has the same width.
    trace[0] = trace[0] + ("",)

    return Run(
        tier=1,
        machine="DFA M1",
        question="Did the robot ever immediately undo its last move?",
        accepted=accepted,
        trace=trace,
        headers=("#", "read", "state", "-> state", "accepting?", "note"),
        summary=summary,
    )


def state_path(word: str) -> str:
    """The state path in the arrow notation used in the design document."""
    state = START
    parts = [state]
    for symbol in word:
        state = step(state, symbol)
        parts.append(f"--{symbol}-> {state}")
    return " ".join(parts)


def transition_table() -> str:
    """Render delta1 as a table, for the --tables option of the driver."""
    lines = [
        "delta1 : Q1 x SIGMA -> Q1        (Tier 1, deterministic finite automaton)",
        "",
        f"    {'state':<10}" + "".join(f"{s:<10}" for s in SIGMA) + "accepting?",
        "    " + "-" * 56,
    ]
    for state in STATES:
        row = f"    {state:<10}" + "".join(f"{DELTA[state][s]:<10}" for s in SIGMA)
        lines.append(row + ("yes" if state in ACCEPTING else "no"))
    lines.append("")
    lines.append(f"    start state {START};  F1 = Q1 \\ {{{DEAD}}}")
    lines.append("    the four transitions into q_dead from a direction state are the reversals")
    return "\n".join(lines)
