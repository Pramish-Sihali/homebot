"""Tier 2: the pushdown automaton P2 (context-free).

Question: did the robot end on its starting row?

    L2 = { w in SIGMA* : #N(w) = #S(w) }

In plain terms this machine is a stack of sticky notes: one note goes on the
pile for every north step and one is torn off for every south step, while east
and west are ignored. An empty pile at the end means the robot finished on the
row it started on.

    P2 = (Q2, SIGMA, GAMMA, delta2, q_start, F2)

The stack is a real stack object -- push and pop only, and only the top symbol
is ever read. The invariant is that the stack above the bottom marker $ always
holds |#N - #S| copies of whichever direction is currently ahead, so a step
opposite the top cancels it (pop) and a step in the same direction, or any step
on an empty tally, extends it (push).

L2 is not regular: intersect with N*S* and it becomes {N^n S^n}, the canonical
pumping-lemma language of Sipser (2013, Section 1.4).
"""

from .spec import SIGMA, Run

BOTTOM = "$"
START = "q_start"
LOOP = "q_loop"
ACCEPT = "q_accept"

STATES = (START, LOOP, ACCEPT)
GAMMA = ("N", "S", BOTTOM)
ACCEPTING = frozenset({ACCEPT})

EPSILON = ""

#: delta2 : (state, read, pop) -> (state, push)
#: "" is epsilon. In the push string the leftmost symbol ends up on top, which
#: is Sipser's convention; ("q_loop", "N", "$") -> ("q_loop", "N$") therefore
#: pops $ and puts back N above $.
DELTA = {
    (START, EPSILON, EPSILON): (LOOP, BOTTOM),      # mark the bottom of the stack
    (LOOP, "N", "S"): (LOOP, EPSILON),              # a pending south cancels; pop
    (LOOP, "N", "N"): (LOOP, "NN"),                 # tally already north; extend it
    (LOOP, "N", BOTTOM): (LOOP, "N" + BOTTOM),      # tally empty; start a north tally
    (LOOP, "S", "N"): (LOOP, EPSILON),              # a pending north cancels; pop
    (LOOP, "S", "S"): (LOOP, "SS"),                 # tally already south; extend it
    (LOOP, "S", BOTTOM): (LOOP, "S" + BOTTOM),      # tally empty; start a south tally
    (LOOP, "E", EPSILON): (LOOP, EPSILON),          # east never touches the stack
    (LOOP, "W", EPSILON): (LOOP, EPSILON),          # west never touches the stack
    (LOOP, EPSILON, BOTTOM): (ACCEPT, EPSILON),     # input gone, tally empty; accept
}

MEANING = {
    (START, EPSILON, EPSILON): "mark the bottom of the stack",
    (LOOP, "N", "S"): "a pending south cancels; pop",
    (LOOP, "N", "N"): "tally already north; extend it",
    (LOOP, "N", BOTTOM): "tally empty; start a north tally",
    (LOOP, "S", "N"): "a pending north cancels; pop",
    (LOOP, "S", "S"): "tally already south; extend it",
    (LOOP, "S", BOTTOM): "tally empty; start a south tally",
    (LOOP, "E", EPSILON): "stack untouched",
    (LOOP, "W", EPSILON): "stack untouched",
    (LOOP, EPSILON, BOTTOM): "input exhausted, tally empty; accept",
}


class Stack:
    """A real stack: the machine may push, pop, and look at the top only."""

    def __init__(self):
        self._cells = []

    def push(self, symbol: str) -> None:
        self._cells.append(symbol)

    def pop(self) -> str:
        return self._cells.pop()

    def top(self):
        return self._cells[-1] if self._cells else None

    def is_empty(self) -> bool:
        return not self._cells

    def __len__(self) -> int:
        return len(self._cells)

    def __str__(self) -> str:
        """Written bottom-to-top, so the rightmost symbol is the top."""
        return "".join(self._cells) if self._cells else "(empty)"


def _lookup(state, symbol, top):
    """Find the one applicable transition, preferring a stack-reading one.

    delta2 is single-valued for every (state, symbol, top), so P2 is
    deterministic and L2 is a deterministic context-free language.
    """
    for key in ((state, symbol, top), (state, symbol, EPSILON)):
        if key in DELTA:
            return key, DELTA[key]
    return None, None


def run(word: str) -> Run:
    """Run P2 on ``word``, recording the stack after every move."""
    stack = Stack()
    state = START
    trace = []
    step_number = 0
    position = 0
    rejected_because = ""

    # The epsilon move out of q_start that plants the bottom marker.
    key, action = _lookup(state, EPSILON, stack.top())
    state, push = action
    for symbol in reversed(push):
        stack.push(symbol)
    trace.append((step_number, "--", "-", push, str(stack), MEANING[key]))

    while position < len(word):
        symbol = word[position]
        step_number += 1
        if symbol not in SIGMA:
            rejected_because = f"the symbol '{symbol}' is not in the alphabet"
            trace.append((step_number, symbol, "-", "-", str(stack), "no transition; reject"))
            state = None
            break

        key, action = _lookup(state, symbol, stack.top())
        if action is None:
            rejected_because = f"no transition on {symbol} with {stack.top()} on top"
            trace.append((step_number, symbol, "-", "-", str(stack), "no transition; reject"))
            state = None
            break

        _, read, pop = key
        next_state, push = action
        popped = "-"
        if pop != EPSILON:
            popped = stack.pop()
        for symbol_to_push in reversed(push):
            stack.push(symbol_to_push)
        state = next_state
        position += 1
        trace.append(
            (step_number, read, popped, push or "-", str(stack), MEANING[key])
        )

    accepted = False
    if state is not None:
        # Input exhausted: the accepting epsilon move needs $ alone on the stack.
        step_number += 1
        if stack.top() == BOTTOM and len(stack) == 1:
            key = (LOOP, EPSILON, BOTTOM)
            state, _ = DELTA[key]
            stack.pop()
            accepted = True
            trace.append((step_number, "--", BOTTOM, "-", str(stack), MEANING[key]))
        else:
            leftover = str(stack).replace(BOTTOM, "")
            direction = "north" if leftover.startswith("N") else "south"
            rejected_because = (
                f"the tally is not empty: {len(leftover)} unmatched "
                f"{direction} step{'s' if len(leftover) != 1 else ''} remain"
            )
            trace.append(
                (step_number, "--", "-", "-", str(stack), "input exhausted, tally not empty; reject")
            )

    summary = (
        "the north and south steps cancel exactly, so the robot ends on its starting row"
        if accepted
        else rejected_because
    )

    return Run(
        tier=2,
        machine="PDA P2",
        question="Did the robot end on its starting row?",
        accepted=accepted,
        trace=trace,
        headers=("#", "read", "pop", "push", "stack (bottom..top)", "meaning"),
        summary=summary,
    )


def transition_table() -> str:
    """Render delta2 as a table, for the --tables option of the driver."""
    lines = [
        "delta2 : (state, read, pop) -> (state, push)   (Tier 2, pushdown automaton)",
        "",
        f"    {'state':<9}{'read':<6}{'pop':<6}{'-> state':<10}{'push':<6}meaning",
        "    " + "-" * 78,
    ]
    for key, (next_state, push) in DELTA.items():
        state, read, pop = key
        lines.append(
            f"    {state:<9}{read or 'eps':<6}{pop or 'eps':<6}"
            f"{next_state:<10}{push or 'eps':<6}{MEANING[key]}"
        )
    lines.append("")
    lines.append(f"    GAMMA = {{{', '.join(GAMMA)}}};  start state {START};  F2 = {{{ACCEPT}}}")
    lines.append("    delta2 is single-valued, so P2 is deterministic")
    return "\n".join(lines)
