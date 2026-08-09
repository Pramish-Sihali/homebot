#!/usr/bin/env python3
"""Robot Walk Recognizer -- command-line driver.

TECH 315 Models of Computation, Week 5 group project deliverable.
Pramish Sihali, Rista Shrestha, Raksha Shrestha, and Manish Yadav.

Usage:
    python3 main.py NNESSW              run one walk through all three machines
    python3 main.py NNESSW --full-tape  print every Turing machine configuration
    python3 main.py NNESSW --pause      stop between machines, one screen at a time
    python3 main.py --demo              run the design-validation walks in order
    python3 main.py --tables            print the three transition tables
    python3 main.py                     interactive prompt (used for the live demo)

--pause combines with the interactive prompt and is the Week 8 demo setting: a
full report is around ninety lines, more than a projector shows at a readable
font size, so the report is handed over one machine at a time.
"""

import sys

from robot_walk import dfa, grid, pda, pipeline, tm

BANNER = r"""
================================================================================
  ROBOT WALK RECOGNIZER          TECH 315 Models of Computation, Week 5
  One walk over {N, S, E, W}, three machines, three yes/no questions.

    Tier 1   DFA   Did the robot ever immediately undo its last move?
    Tier 2   PDA   Did the robot end on its starting row?
    Tier 3   TM    Did the robot end exactly back home?
================================================================================
"""

#: The design-validation walks from Table 8 of the Week 4 design document, with
#: the verdicts the design predicts. Week 6 turns these into a full test suite.
DEMO_WALKS = (
    ("", (True, True, True), "the robot never moves"),
    ("NESW", (True, True, True), "a unit square, ending at home"),
    ("NNESSW", (True, True, True), "up 2, right 1, down 2, left 1"),
    ("NES", (True, True, False), "same row, one column east"),
    ("NNE", (True, False, False), "ends up and to the right"),
    ("NEB", (False, False, False), "illegal symbol B"),
    ("NS", (False, True, True), "steps north, then immediately back"),
    ("NNSSEEWW", (False, True, True), "out and back twice, with reversals"),
)


def run_one(word: str, full_trace: bool = False, pause: bool = False) -> None:
    """Print the report, optionally handing it over one section at a time."""
    if not pause:
        print(pipeline.report(word, full_trace=full_trace))
        return

    sections = pipeline.report_sections(word, full_trace=full_trace)
    for position, (_, text) in enumerate(sections):
        print(text)
        following = sections[position + 1 :]
        if not following:
            break
        try:
            input(f"  press Enter for {following[0][0]}... ")
        except EOFError:
            # Not a terminal (piped input): print the rest without stopping.
            print("\n".join(text for _, text in following))
            return
        except KeyboardInterrupt:
            print()
            return
        print()


def run_demo() -> None:
    """Every walk in Table 8, with a pass/fail against the predicted verdicts."""
    print(BANNER)
    rows = []
    failures = 0
    for word, expected, description in DEMO_WALKS:
        actual = pipeline.verdicts(word)
        ok = actual == expected
        failures += not ok
        rows.append(
            (
                word or "(empty)",
                description,
                *["yes" if value else "no" for value in actual],
                "pass" if ok else "FAIL",
            )
        )
    print("  Design-validation walks (Week 4 design document, Table 8)\n")
    print(
        pipeline.table(
            ("walk", "what it is", "tier 1", "tier 2", "tier 3", "vs design"), rows
        )
    )
    print()
    if failures:
        print(f"  {failures} walk(s) disagree with the design.")
        sys.exit(1)
    print("  All 8 walks agree with the verdicts predicted by the design.")
    print("  Note how the last two rows fail tier 1 but pass tiers 2 and 3:")
    print("  the three questions are independent, not nested.\n")


def show_tables() -> None:
    print(BANNER)
    for module in (dfa, pda, tm):
        print(module.transition_table())
        print()


def interactive(pause: bool = False) -> None:
    """The live-demo loop: type a walk, see the grid, then see the three answers."""
    print(BANNER)
    print("  Type a walk (letters N, S, E, W), or 'quit' to stop.")
    print("  Tip: look at the picture and predict the three answers first.\n")
    while True:
        try:
            word = input("  walk> ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if word in ("QUIT", "EXIT", "Q"):
            return
        print()
        print(grid.render(word))
        print()
        try:
            input("  press Enter to run the three machines... ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        print()
        run_one(word, pause=pause)
        print()


def main(argv) -> None:
    arguments = [a for a in argv if not a.startswith("--")]
    options = {a for a in argv if a.startswith("--")}

    if "--help" in options or "-h" in arguments:
        print(__doc__)
        return
    if "--tables" in options:
        show_tables()
        return
    if "--demo" in options:
        run_demo()
        return
    pause = "--pause" in options
    if not arguments:
        interactive(pause=pause)
        return

    print(BANNER)
    for word in arguments:
        run_one(word.upper(), full_trace="--full-tape" in options, pause=pause)


if __name__ == "__main__":
    main(sys.argv[1:])
