"""Tier 3: the Turing machine M3 (decidable).

Question: did the robot end exactly back home?

    L3 = { w in SIGMA* : #N(w) = #S(w) and #E(w) = #W(w) }

In plain terms this machine is a notebook: the walk is written on a paper
strip, and symbols are crossed off in matched pairs -- north against south,
then east against west. The strip can be re-read and rewritten, so the pairing
runs twice, which is exactly what a single stack cannot do.

    M3 = (Q3, SIGMA, GAMMA, delta3, q0, q_accept, q_reject)
    GAMMA = {N, S, E, W, x, _}      x marks a crossed-off symbol, _ is blank

The machine is built from one reusable subroutine, PAIR-CHECK(X, Y), following
the decider for {a^n b^n c^n} in Sipser (2013, Section 3.1). PAIR-CHECK is
instantiated twice -- once as (N, S) and once as (E, W) -- and the two copies
are unioned into one flat transition table delta3, so what runs is a single
ordinary Turing machine with a fixed finite state set.

Tape convention: the tape holds one blank, then the input, then blanks, and the
head starts on the first input symbol. That single blank to the left of the
input is the left-end marker, which is what makes "return to the left-hand end
of the tape" a real sequence of transitions rather than an instruction the
machine could not carry out.

L3 is not context-free: intersect it with the regular language N*E*S*W* and it
becomes {N^n E^m S^n W^m}, which the pumping lemma for context-free languages
rules out (Sipser, 2013, Section 2.3).
"""

from .spec import SIGMA, Run

BLANK = "_"
CROSS = "x"
GAMMA = ("N", "S", "E", "W", CROSS, BLANK)

ACCEPT = "q_accept"
REJECT = "q_reject"
VALIDATE = "q_validate"

LEFT, RIGHT = "L", "R"

#: Safety net against a transition table with a loop in it -- not against long
#: input. M3 costs exactly (n + 1)(n + 10) steps on an accepted walk of length
#: n (Week 7 analysis), so the limit has to grow with n or it stops legitimate
#: runs: a fixed ceiling of two million halted every accepted walk longer than
#: 1,408 symbols, which is a crash rather than a decision.
STEP_LIMIT_BASE = 10_000


def step_limit(length: int) -> int:
    """A ceiling an order of magnitude above any run this machine can make."""
    return STEP_LIMIT_BASE + 10 * (length + 11) ** 2


def _rewind(target: str) -> str:
    """Name of the state that walks back to the left end and then enters ``target``."""
    return f"q_rewind>{target}"


def _pair_check(tag: str, x: str, y: str, on_pass: str, delta: dict) -> str:
    """Add one instantiation of PAIR-CHECK(X, Y) to ``delta``; return its entry state.

    The subroutine crosses off one X, then one Y, and repeats; it rejects as
    soon as either symbol runs out while the other has not.
    """
    seek_x = f"q_{tag}_seek_{x}"
    seek_y = f"q_{tag}_seek_{y}"
    verify = f"q_{tag}_verify_no_{y}"

    # Scan right for an unmarked X.
    for symbol in GAMMA:
        if symbol == x:
            # Cross it off, then go back and look for its partner Y.
            delta[(seek_x, symbol)] = (_rewind(seek_y), CROSS, LEFT)
        elif symbol == BLANK:
            # No X left; make sure no unmarked Y is left either.
            delta[(seek_x, symbol)] = (_rewind(verify), BLANK, LEFT)
        else:
            delta[(seek_x, symbol)] = (seek_x, symbol, RIGHT)

    # Scan right for the partner Y.
    for symbol in GAMMA:
        if symbol == y:
            delta[(seek_y, symbol)] = (_rewind(seek_x), CROSS, LEFT)
        elif symbol == BLANK:
            delta[(seek_y, symbol)] = (REJECT, BLANK, LEFT)      # X had no partner
        else:
            delta[(seek_y, symbol)] = (seek_y, symbol, RIGHT)

    # Every X is crossed off; an unmarked Y now means the counts differ.
    for symbol in GAMMA:
        if symbol == y:
            delta[(verify, symbol)] = (REJECT, symbol, RIGHT)
        elif symbol == BLANK:
            delta[(verify, symbol)] = (_rewind(on_pass), BLANK, LEFT)
        else:
            delta[(verify, symbol)] = (verify, symbol, RIGHT)

    # The three places above that need the head back at the left end.
    for target in (seek_x, seek_y, verify, on_pass):
        _add_rewind(target, delta)

    return seek_x


def _add_rewind(target: str, delta: dict) -> None:
    """Move left until the left-end blank, then step right into ``target``."""
    state = _rewind(target)
    for symbol in GAMMA:
        if symbol == BLANK:
            delta[(state, symbol)] = (target, BLANK, RIGHT)
        else:
            delta[(state, symbol)] = (state, symbol, LEFT)


def _build_delta() -> dict:
    """delta3 : Q3 x GAMMA -> Q3 x GAMMA x {L, R}."""
    delta = {}

    # Phase 2 first, so phase 1 can name it as its continuation.
    phase2 = _pair_check("p2", "E", "W", ACCEPT, delta)
    phase1 = _pair_check("p1", "N", "S", phase2, delta)

    # Step 1: scan the input; anything outside SIGMA has no transition and the
    # machine halts in q_reject.
    for symbol in SIGMA:
        delta[(VALIDATE, symbol)] = (VALIDATE, symbol, RIGHT)
    delta[(VALIDATE, CROSS)] = (VALIDATE, CROSS, RIGHT)
    delta[(VALIDATE, BLANK)] = (_rewind(phase1), BLANK, LEFT)
    _add_rewind(phase1, delta)

    return delta


DELTA = _build_delta()
START = VALIDATE
STATES = tuple(dict.fromkeys([state for state, _ in DELTA] + [ACCEPT, REJECT]))

PHASE_LABEL = {
    "q_validate": "check the alphabet",
    "p1": "phase 1: pair N against S",
    "p2": "phase 2: pair E against W",
}


def _phase_of(state: str) -> str:
    if ACCEPT in state or REJECT in state:
        return "halt"
    if "p1" in state:
        return PHASE_LABEL["p1"]
    if "p2" in state:
        return PHASE_LABEL["p2"]
    return PHASE_LABEL["q_validate"]


class Tape:
    """A real tape: an unbounded strip of cells plus a head that moves L or R."""

    def __init__(self, word: str):
        self.cells = [BLANK] + list(word) + [BLANK]
        self.head = 1                                # on the first input symbol

    def read(self) -> str:
        return self.cells[self.head]

    def write(self, symbol: str) -> None:
        self.cells[self.head] = symbol

    def move(self, direction: str) -> None:
        self.head += 1 if direction == RIGHT else -1
        if self.head < 0:                            # cannot fall off the left end
            self.head = 0
        while self.head >= len(self.cells):          # the strip is unbounded to the right
            self.cells.append(BLANK)

    def contents(self) -> str:
        return "".join(self.cells).strip(BLANK) or "(empty)"

    def configuration(self) -> str:
        """The tape with the head position marked, e.g. xN[E]SSW."""
        parts = []
        for index, symbol in enumerate(self.cells):
            parts.append(f"[{symbol}]" if index == self.head else symbol)
        return "".join(parts)


def run(word: str, full_trace: bool = False) -> Run:
    """Run M3 on ``word``. Returns the crossing-off history, or every step."""
    tape = Tape(word)
    state = START
    steps = 0
    trace = []
    rejected_because = ""

    def record(action: str, phase_state: str = None) -> None:
        if full_trace:                               # the state name names the phase
            trace.append((steps, action, tape.contents()))
        else:
            trace.append((steps, _phase_of(phase_state or state), action, tape.contents()))

    record("input written on the tape")

    while state not in (ACCEPT, REJECT):
        symbol = tape.read()
        action = DELTA.get((state, symbol))
        if action is None:
            rejected_because = f"the symbol '{symbol}' is not in the tape alphabet"
            record(f"no transition on '{symbol}'; reject")
            state = REJECT
            break

        next_state, write, direction = action
        crossed_off = write == CROSS and symbol != CROSS
        tape.write(write)
        tape.move(direction)
        previous_state, state = state, next_state
        steps += 1

        if full_trace:
            # The configuration after the move, and the state the machine is
            # now in: exactly Sipser's u q v notation, written u[v0]v1...
            trace.append((steps, state, tape.configuration()))
        elif crossed_off:
            record(f"cross off {symbol}")
        elif next_state == REJECT:
            if "seek" in previous_state:
                missing = previous_state.rsplit("_", 1)[-1]
                partner = {"S": "N", "W": "E"}.get(missing, missing)
                rejected_because = f"an unmatched {partner} step has no {missing} to cancel it"
            else:
                missing = previous_state.rsplit("_", 1)[-1]
                partner = {"S": "N", "W": "E"}.get(missing, missing)
                rejected_because = f"an unmatched {missing} step has no {partner} to cancel it"
            record("no partner left; reject", previous_state)
        elif previous_state.startswith("q_p1_verify") and "p2" in next_state:
            record("no unmarked N or S remains; phase 1 passes", previous_state)

        if steps > step_limit(len(word)):            # never reached; M3 is a decider
            raise RuntimeError("step limit exceeded")

    accepted = state == ACCEPT
    if accepted:
        record("no unmarked E or W remains; phase 2 passes", "q_p2_done")

    if not rejected_because and not accepted:
        rejected_because = "the walk does not return to the starting cell"

    summary = (
        f"every step was cancelled by an opposite step, so the robot ends exactly home "
        f"({steps} machine steps)"
        if accepted
        else f"{rejected_because} ({steps} machine steps)"
    )

    return Run(
        tier=3,
        machine="TM M3",
        question="Did the robot end exactly back home?",
        accepted=accepted,
        trace=trace,
        headers=(
            ("#", "state", "configuration") if full_trace else ("#", "phase", "action", "tape")
        ),
        summary=summary,
    )


def transition_table() -> str:
    """Render delta3 as a table, for the --tables option of the driver."""
    lines = [
        "delta3 : Q3 x GAMMA -> Q3 x GAMMA x {L, R}     (Tier 3, Turing machine)",
        "",
        f"    {'state':<26}{'read':<6}{'-> state':<26}{'write':<7}move",
        "    " + "-" * 72,
    ]
    for (state, symbol), (next_state, write, direction) in DELTA.items():
        lines.append(
            f"    {state:<26}{symbol:<6}{next_state:<26}{write:<7}{direction}"
        )
    lines.append("")
    lines.append(
        f"    {len(STATES)} states, {len(DELTA)} transitions, all generated from one "
        "PAIR-CHECK(X, Y) subroutine"
    )
    lines.append("    an undefined transition halts the machine in q_reject")
    return "\n".join(lines)
