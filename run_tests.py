#!/usr/bin/env python3
"""Robot Walk Recognizer -- test runner.

TECH 315 Models of Computation, Week 6 group project deliverable.
Pramish Sihali, Rista Shrestha, Raksha Shrestha, and Manish Yadav.

Runs the whole suite and prints a summary grouped by what is being tested, so
the result is readable in a report and on a projector rather than a wall of
dots. The suite itself is ordinary unittest; `python3 -m unittest discover` or
any IDE runner will run exactly the same tests.

Usage:
    python3 run_tests.py             run everything and print the summary
    python3 run_tests.py --verbose   also print every test name as it runs
    python3 run_tests.py tests.test_tm   run one module
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests import oracle        # noqa: E402  (needs the path set above)

WIDTH = 78

MODULES = (
    ("tests.test_dfa", "Tier 1 -- deterministic finite automaton"),
    ("tests.test_pda", "Tier 2 -- pushdown automaton"),
    ("tests.test_cfg", "Tier 2 -- context-free grammar"),
    ("tests.test_tm", "Tier 3 -- Turing machine"),
    ("tests.test_integration", "Integration -- the three tiers as one system"),
    ("tests.test_random", "Randomized differential testing"),
    ("tests.test_efficiency", "Efficiency -- cost in each machine's own units"),
)


def table(headers, rows, indent="  "):
    columns = list(zip(*([headers] + [tuple(str(c) for c in row) for row in rows])))
    widths = [max(len(str(cell)) for cell in column) + 2 for column in columns]
    lines = [indent + "".join(str(h).ljust(w) for h, w in zip(headers, widths)).rstrip()]
    lines.append(indent + "-" * (sum(widths) - 2))
    for row in rows:
        lines.append(
            indent + "".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip()
        )
    return "\n".join(lines)


def run_module(name, verbose=False):
    """Run one test module and return (tests, failures, errors, seconds)."""
    suite = unittest.defaultTestLoader.loadTestsFromName(name)
    stream = sys.stdout if verbose else open("/dev/null", "w")
    runner = unittest.TextTestRunner(stream=stream, verbosity=2 if verbose else 0)
    started = time.perf_counter()
    result = runner.run(suite)
    elapsed = time.perf_counter() - started
    if not verbose:
        stream.close()
    return result, elapsed


def main(argv):
    verbose = "--verbose" in argv
    chosen = [a for a in argv if not a.startswith("--")]
    modules = [(name, label) for name, label in MODULES if not chosen or name in chosen]

    print("=" * WIDTH)
    print(" ROBOT WALK RECOGNIZER -- TEST SUITE")
    print(" TECH 315 Models of Computation, Week 6")
    print("=" * WIDTH)
    print()
    print("  System under test: the Week 5 implementation, imported unchanged")
    print(f"  Oracle:            {oracle.__name__}, an independent answer to "
          "each question")
    print(f"  Exhaustive cover:  every walk up to length 8 for the three "
          f"machines ({oracle.count_walks(8):,} strings),")
    print(f"                     up to length 7 for the grammar parser "
          f"({oracle.count_walks(7):,} strings)")
    print()

    rows = []
    total_tests = total_bad = 0
    total_time = 0.0
    failures = []

    for name, label in modules:
        result, elapsed = run_module(name, verbose)
        bad = len(result.failures) + len(result.errors)
        rows.append(
            (
                label,
                result.testsRun,
                "-" if not bad else bad,
                "pass" if not bad else "FAIL",
                f"{elapsed:.2f}s",
            )
        )
        total_tests += result.testsRun
        total_bad += bad
        total_time += elapsed
        failures.extend(result.failures + result.errors)

    print(table(("What is tested", "Tests", "Failed", "Result", "Time"), rows))
    print()
    print(
        f"  {total_tests} tests, {total_tests - total_bad} passed, "
        f"{total_bad} failed, {total_time:.2f}s"
    )
    print()

    if failures:
        print("=" * WIDTH)
        for test, traceback in failures:
            print(f" FAILED: {test}")
            print(traceback)
        print("=" * WIDTH)
        return 1

    print("  All tests pass: the system agrees with the oracle on every walk")
    print("  tested, and every machine behaves the way its model requires.")
    print("=" * WIDTH)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
