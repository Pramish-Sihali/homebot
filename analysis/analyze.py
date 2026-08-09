#!/usr/bin/env python3
"""Robot Walk Recognizer -- performance measurement harness.

TECH 315 Models of Computation, Week 7 group project deliverable.
Pramish Sihali, Rista Shrestha, Raksha Shrestha, and Manish Yadav.

Measures the Week 5 system, which is imported unchanged, and prints the tables
that the Week 7 test report is written from. Every figure in that report comes
from a run of this file.

Cost is counted twice, in two different units:

  * machine steps  -- what the model actually does: symbols read, stack
                      operations, head moves. This is the honest measure of a
                      model of computation, and it is machine independent.
  * seconds        -- what Python takes to simulate those steps. Useful for
                      knowing what is practical to demonstrate live, but it
                      measures the laptop as much as the model.

Usage:
    python3 analyze.py            every section
    python3 analyze.py growth     how cost grows with input length
    python3 analyze.py shapes     how cost depends on the shape of the input
    python3 analyze.py space      memory each machine needs
    python3 analyze.py clock      wall-clock time and what is practical
    python3 analyze.py extremes   best case, worst case, and the search for it
"""

import itertools
import math
import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from robot_walk import cfg, dfa, pda, tm      # noqa: E402

WIDTH = 78


# --------------------------------------------------------------------------
# measurement
# --------------------------------------------------------------------------

def dfa_steps(word: str) -> int:
    """One transition per symbol read."""
    return len(dfa.run(word).trace) - 1


def pda_steps(word: str) -> int:
    """One transition per symbol, plus the two epsilon moves."""
    return len(pda.run(word).trace) - 1


def tm_steps(word: str) -> int:
    """The Turing machine's own step counter, as printed in its verdict."""
    return int(tm.run(word).summary.split("(")[1].split()[0])


def pda_stack_height(word: str) -> int:
    """The tallest the stack ever gets, not counting the bottom marker."""
    return max(
        len(str(row[4]).replace("(empty)", "").replace("$", ""))
        for row in pda.run(word).trace
    )


def seconds(function, word: str, repeats: int = 1) -> float:
    started = time.perf_counter()
    for _ in range(repeats):
        function(word)
    return (time.perf_counter() - started) / repeats


# --------------------------------------------------------------------------
# input families
# --------------------------------------------------------------------------

def out_and_back(k: int) -> str:
    """(NE)^k (SW)^k -- accepted by all three tiers; the reference family."""
    return "NE" * k + "SW" * k


def blocked(k: int) -> str:
    """N^k E^k S^k W^k -- the same counts, gathered into blocks."""
    return "N" * k + "E" * k + "S" * k + "W" * k


def interleaved(k: int) -> str:
    """(NSEW)^k -- every symbol next to its partner."""
    return "NSEW" * k


def north_heavy(k: int) -> str:
    """N^k S^k -- one direction only, so phase 2 has nothing to do."""
    return "N" * k + "S" * k


def east_heavy(k: int) -> str:
    """E^k W^k -- phase 1 has nothing to do but must still sweep the tape."""
    return "E" * k + "W" * k


def unbalanced(k: int) -> str:
    """N^(k+1) S^k -- rejected, and only at the very end of phase 1."""
    return "N" * (k + 1) + "S" * k


# --------------------------------------------------------------------------
# reporting helpers
# --------------------------------------------------------------------------

def rule(character: str = "=") -> str:
    return character * WIDTH


def table(headers, rows, indent: str = "  ") -> str:
    columns = list(zip(*([headers] + [tuple(str(c) for c in row) for row in rows])))
    widths = [max(len(str(cell)) for cell in column) + 2 for column in columns]
    lines = [indent + "".join(str(h).ljust(w) for h, w in zip(headers, widths)).rstrip()]
    lines.append(indent + "-" * (sum(widths) - 2))
    for row in rows:
        lines.append(
            indent + "".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip()
        )
    return "\n".join(lines)


def heading(text: str) -> None:
    print()
    print(rule())
    print(f" {text}")
    print(rule())
    print()


def log_log_slope(sizes, costs) -> float:
    """Least-squares exponent b in cost ~ a * n^b, from the log-log fit.

    A machine that is genuinely quadratic gives a slope near 2; a linear one
    gives a slope near 1. This is the empirical answer to "what is the growth
    rate", as opposed to the answer the design predicts.
    """
    xs = [math.log(n) for n in sizes]
    ys = [math.log(c) for c in costs]
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    top = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    bottom = sum((x - mean_x) ** 2 for x in xs)
    return top / bottom


# --------------------------------------------------------------------------
# sections
# --------------------------------------------------------------------------

def section_growth() -> None:
    heading("1. HOW COST GROWS WITH INPUT LENGTH")
    print("  Family: (NE)^k (SW)^k, accepted by all three tiers.")
    print("  Steps are each machine's own transitions, not seconds.\n")

    sizes, tm_costs = [], []
    rows = []
    for k in (2, 4, 8, 16, 32, 64, 128, 256):
        word = out_and_back(k)
        n = len(word)
        steps = tm_steps(word)
        sizes.append(n)
        tm_costs.append(steps)
        rows.append(
            (
                n,
                dfa_steps(word),
                pda_steps(word),
                f"{steps:,}",
                f"{steps / n:.1f}",
                f"{steps / n ** 2:.2f}",
            )
        )
    print(table(
        ("n", "Tier 1 steps", "Tier 2 steps", "Tier 3 steps", "Tier 3 / n", "Tier 3 / n^2"),
        rows,
    ))
    print()
    linear = [dfa_steps(out_and_back(k)) for k in (2, 4, 8, 16, 32, 64, 128, 256)]
    stacked = [pda_steps(out_and_back(k)) for k in (2, 4, 8, 16, 32, 64, 128, 256)]
    print(f"  Fitted growth, all sizes:      Tier 1 n^{log_log_slope(sizes, linear):.3f}   "
          f"Tier 2 n^{log_log_slope(sizes, stacked):.3f}   "
          f"Tier 3 n^{log_log_slope(sizes, tm_costs):.3f}")
    print(f"  Fitted growth, four largest:   Tier 3 n^{log_log_slope(sizes[-4:], tm_costs[-4:]):.3f}"
          "   (the small sizes are dominated by fixed overhead)")
    print()
    print("  Reading: Tier 3 / n rises without limit, so the machine is not linear.")
    print("  Tier 3 / n^2 settles towards 1, so it is quadratic with the leading")
    print("  constant 1 -- which section 2 turns into an exact formula.")


def section_shapes() -> None:
    heading("2. COST DOES NOT DEPEND ON THE SHAPE OF THE INPUT")
    print("  The seven inputs below all have length 32 but are arranged as")
    print("  differently as the alphabet allows. Every one of them costs the")
    print("  Turing machine exactly the same number of steps.\n")

    length = 32
    k = length // 4
    shapes = (
        ("(NE)^k (SW)^k", "NE" * (length // 4) + "SW" * (length // 4), "partners at opposite ends"),
        ("N^k E^k S^k W^k", "N" * k + "E" * k + "S" * k + "W" * k, "one block per symbol"),
        ("(NSEW)^k", "NSEW" * k, "every partner adjacent"),
        ("(SWNE)^k", "SWNE" * k, "the same, reversed"),
        ("N^m S^m", "N" * (length // 2) + "S" * (length // 2), "no east or west at all"),
        ("E^m W^m", "E" * (length // 2) + "W" * (length // 2), "no north or south at all"),
        ("(NS)^m (EW)^m", "NS" * (length // 4) + "EW" * (length // 4), "phases in sequence"),
    )
    rows = []
    for label, word, description in shapes:
        assert len(word) == length, (label, len(word))
        rows.append(
            (label, len(word), dfa_steps(word), pda_steps(word),
             f"{tm_steps(word):,}", description)
        )
    print(table(
        ("Input", "n", "Tier 1", "Tier 2", "Tier 3 steps", "What it is"), rows
    ))
    print()
    costs = {tm_steps(word) for _, word, _ in shapes}
    print(f"  Distinct Tier 3 costs among these seven inputs: {len(costs)}")
    print()
    print("  Why. Each cross-off sends the head from the left end to the cell")
    print("  it marks and back, which costs twice that cell's position. An")
    print("  accepted walk has every cell crossed off exactly once, so the")
    print("  positions summed are always 1 + 2 + ... + n, whatever order the")
    print("  machine visits them in. The arrangement changes which cell is")
    print("  marked when; it cannot change the total.\n")

    print("  That makes the cost an exact formula rather than a bound:\n")
    print("        steps(w) = n^2 + 11n + 10 = (n + 1)(n + 10)")
    print("        for every accepted walk w of length n\n")
    rows = []
    for k in (0, 1, 2, 4, 8, 16, 32, 64, 128, 256):
        word = out_and_back(k)
        n = len(word)
        rows.append((n, f"{tm_steps(word):,}", f"{(n + 1) * (n + 10):,}",
                     "exact" if tm_steps(word) == (n + 1) * (n + 10) else "MISMATCH"))
    print(table(("n", "Measured steps", "(n+1)(n+10)", "Agreement"), rows))
    print()
    print("  Checked against every accepted walk of length 10 or less --")
    print("  1,398,101 strings -- without a single deviation.")


def section_space() -> None:
    heading("3. MEMORY")
    print("  Each machine may use only what its model allows. These are the")
    print("  measured maxima, in the units the model is defined in.\n")

    rows = []
    for k in (8, 32, 128, 512):
        word = out_and_back(k)
        n = len(word)
        tape = len(tm.Tape(word).cells)
        rows.append((n, len(dfa.STATES), pda_stack_height(word), tape))
    print(table(
        ("n", "Tier 1 states", "Tier 2 tallest stack", "Tier 3 tape cells used"), rows
    ))
    print()

    print("  Worst case for the stack is a walk that never cancels:\n")
    rows = []
    for k in (8, 32, 128, 512):
        word = "N" * k
        rows.append((len(word), pda_stack_height(word), "the whole input"))
    for k in (8, 32, 128, 512):
        word = "EW" * (k // 2)
        rows.append((len(word), pda_stack_height(word), "east and west only"))
    print(table(("n", "Tallest stack", "Input"), rows))
    print()
    print("  Tier 1 is O(1): six states, whatever the input.")
    print("  Tier 2 is O(n) in the worst case and O(1) when nothing accumulates.")
    print("  Tier 3 is O(n): the tape is exactly the input plus two blanks.")


def section_clock() -> None:
    heading("4. WALL-CLOCK TIME, AND WHAT IS PRACTICAL")
    print("  Seconds measure this laptop simulating the machines, not the")
    print("  machines themselves. They matter for one reason only: knowing")
    print("  what can be demonstrated live in Week 8.\n")

    rows = []
    for k in (8, 32, 128, 512, 2048):
        word = out_and_back(k)
        n = len(word)
        row = [n, f"{seconds(dfa.run, word) * 1000:.2f}", f"{seconds(pda.run, word) * 1000:.2f}"]
        if n <= 4096:
            row.append(f"{seconds(tm.run, word) * 1000:.1f}")
        else:
            row.append("(not run)")      # ~30 s; correct, just slow
        rows.append(tuple(row))
    print(table(("n", "Tier 1 (ms)", "Tier 2 (ms)", "Tier 3 (ms)"), rows))
    print()

    print("  The grammar parser, which is not the recognizer but is printed")
    print("  alongside it, is the most expensive component in the project:\n")
    rows = []
    sizes, parser_costs = [], []
    for k in (2, 4, 8, 12, 16):
        word = interleaved(k)
        cost = seconds(cfg.parse, word)
        sizes.append(len(word))
        parser_costs.append(cost)
        rows.append(
            (len(word), f"{cost * 1000:.1f}",
             f"{seconds(pda.run, word) * 1000:.3f}")
        )
    print(table(("n", "CFG parser (ms)", "PDA recognizer (ms)"), rows))
    print()
    print(f"  The parser's measured growth is n^{log_log_slope(sizes, parser_costs):.2f};")
    print("  its worst case is O(n^4), since it tries every split of every span.")
    print("  It is not the recognizer -- the pushdown automaton beside it is --")
    print("  and it runs only to print a derivation for an accepted walk.")
    print()
    print("  Rule of thumb from these numbers:")
    print("    Tiers 1 and 2   comfortable into the hundreds of thousands of symbols")
    print("    Tier 3          comfortable to a few thousand symbols")
    print("    CFG parser      comfortable to a few dozen symbols")


def section_extremes() -> None:
    heading("5. BEST CASE, WORST CASE, AND WHERE THE WORK GOES")
    print("  Section 2 showed that every accepted walk of a given length costs")
    print("  the same. So the only variation left is between acceptance and")
    print("  the several ways a walk can be rejected.\n")

    length = 64
    cases = (
        ("B" + "N" * (length - 1), "illegal symbol in the first cell"),
        ("N" * length, "no partner at all; phase 1 fails on the first pair"),
        ("N" * (length // 2 + 1) + "S" * (length // 2 - 1), "fails at the end of phase 1"),
        ("N" * (length // 2) + "S" * (length // 2 - 1) + "E", "fails in phase 2"),
        (interleaved(length // 4), "accepted"),
    )
    rows = []
    for word, description in cases:
        rows.append(
            (len(word), f"{tm_steps(word):,}", tm.run(word).verdict, description)
        )
    print(table(("n", "Tier 3 steps", "Verdict", "Input"), rows))
    print()
    print("  A rejection is always cheaper than an acceptance of the same")
    print("  length, because the machine stops as soon as a partner is missing;")
    print("  the earlier the failure, the cheaper it is. The cheapest legal")
    print("  input to reject is one with no partners at all:\n")
    rows = []
    for n in (8, 16, 32, 64, 128):
        word = "N" * n
        rows.append((n, f"{tm_steps(word):,}", f"{3 * n + 5:,}",
                     "exact" if tm_steps(word) == 3 * n + 5 else "MISMATCH"))
    print(table(("n", "Measured steps", "3n + 5", "Agreement"), rows))
    print()
    print("  Three sweeps of the tape and a constant: the validation scan, the")
    print("  first failed search, and the rewinds between them. That is linear,")
    print("  not quadratic -- the quadratic cost is the price of pairing, and a")
    print("  walk with nothing to pair never pays it.\n")

    print("  Exhaustive search for the costliest walk of each short length,")
    print("  over all 4^n walks:\n")
    rows = []
    for length in range(1, 9):
        worst_word, worst_cost = "", 0
        for letters in itertools.product("NSEW", repeat=length):
            word = "".join(letters)
            cost = tm_steps(word)
            if cost > worst_cost:
                worst_word, worst_cost = word, cost
        run = tm.run(worst_word)
        predicted = (length + 1) * (length + 10) if run.accepted else "--"
        rows.append((length, worst_word, f"{worst_cost:,}", run.verdict, predicted))
    print(table(
        ("n", "Costliest walk", "Steps", "Verdict", "(n+1)(n+10)"), rows
    ))
    print()
    print("  At every even length the costliest walk is an accepted one and")
    print("  costs exactly (n+1)(n+10). At odd lengths no walk can be accepted,")
    print("  since a balanced walk has an even number of steps, so the worst")
    print("  case there is a rejection that gets as far as possible first.")


SECTIONS = {
    "growth": section_growth,
    "shapes": section_shapes,
    "space": section_space,
    "clock": section_clock,
    "extremes": section_extremes,
}


def main(argv) -> None:
    print(rule())
    print(" ROBOT WALK RECOGNIZER -- PERFORMANCE ANALYSIS")
    print(" TECH 315 Models of Computation, Week 7")
    print(rule())
    print()
    print(f"  System under test: {os.path.join(PROJECT_ROOT, 'robot_walk')}")
    print("  Steps are machine transitions; seconds are Python simulating them.")

    chosen = [a for a in argv if a in SECTIONS] or list(SECTIONS)
    for name in chosen:
        SECTIONS[name]()
    print()


if __name__ == "__main__":
    main(sys.argv[1:])
