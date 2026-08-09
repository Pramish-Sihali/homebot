"""The integrated system: one input string, three machines, one report.

    input string --> [Tier 1 DFA] --> [Tier 2 PDA] --> [Tier 3 TM]

The three recognizers share nothing but the input string. Each is run in turn
and prints its own trace -- state path, stack trace, tape trace -- followed by
its own verdict. The tiers are deliberately not short-circuited: a rejection at
Tier 1 does not stop Tier 2, because the three questions are independent and
the demonstration depends on seeing all three answers.
"""

from . import cfg, dfa, grid, pda, tm
from .spec import Run, counts

WIDTH = 78

METAPHOR = {
    1: "a goldfish: it remembers only which way it moved last",
    2: "a stack of sticky notes: one note per north step, torn off by a south step",
    3: "a notebook: symbols crossed off in pairs on a strip of paper",
}

CLASS = {
    1: "regular",
    2: "context-free (not regular)",
    3: "decidable (not context-free)",
}


def rule(character: str = "=") -> str:
    return character * WIDTH


def table(headers, rows, indent: str = "  ") -> str:
    """Format rows as a fixed-width table sized to its contents."""
    columns = list(zip(*([headers] + [tuple(str(cell) for cell in row) for row in rows])))
    widths = [max(len(str(cell)) for cell in column) + 2 for column in columns]
    lines = [indent + "".join(str(h).ljust(w) for h, w in zip(headers, widths)).rstrip()]
    lines.append(indent + "-" * (sum(widths) - 2))
    for row in rows:
        lines.append(
            indent + "".join(str(cell).ljust(w) for cell, w in zip(row, widths)).rstrip()
        )
    return "\n".join(lines)


def format_run(run: Run) -> str:
    """One tier's section of the report: question, trace, verdict."""
    lines = [
        rule("-"),
        f"TIER {run.tier} -- {run.machine} -- {CLASS[run.tier]}",
        rule("-"),
        f"  Question: {run.question}",
        f"  In plain terms: {METAPHOR[run.tier]}",
        "",
        table(run.headers, run.trace),
        "",
    ]
    for block in run.extra:
        lines.append(block)
        lines.append("")
    lines.append(f"  VERDICT: {run.verdict} -- {run.summary}")
    lines.append("")
    return "\n".join(lines)


def analyse(word: str, full_trace: bool = False):
    """Run all three recognizers on ``word`` and return their results in order."""
    tier1 = dfa.run(word)
    tier2 = pda.run(word)
    tier3 = tm.run(word, full_trace=full_trace)

    # The grammar side of Tier 2: an accepted walk gets a leftmost derivation
    # in G2, which is the visible link between the machine and the grammar.
    if tier2.accepted:
        derivation = cfg.derivation_lines(word)
        if derivation:
            tier2.extra.append(
                "\n".join(
                    [
                        f"  Leftmost derivation in G2   ({cfg.GRAMMAR_TEXT})",
                        "",
                        *[f"  {line}" for line in derivation],
                    ]
                )
            )
    return [tier1, tier2, tier3]


def report_sections(word: str, full_trace: bool = False):
    """The report split into the pieces a live demo pauses between.

    Returns ``(label, text)`` pairs in printing order, where the label names
    that piece. Joining the texts with a newline reproduces :func:`report`
    exactly, so the paused and unpaused demos show identical output.
    """
    tally = counts(word)
    shown = word if word else "(empty string)"
    heading = "\n".join(
        [
            rule(),
            f" INPUT: {shown}",
            f" length {len(word)}   "
            + "   ".join(f"#{symbol} = {count}" for symbol, count in tally.items()),
            rule(),
            "",
            " The walk",
            "",
            grid.render(word),
            "",
        ]
    )

    runs = analyse(word, full_trace=full_trace)
    summary = "\n".join(
        [
            rule(),
            " SUMMARY",
            table(
                ("tier", "machine", "question", "verdict"),
                [(run.tier, run.machine, run.question, run.verdict) for run in runs],
                indent=" ",
            ),
            rule(),
        ]
    )

    return [
        ("the walk", heading),
        *[(f"Tier {run.tier} ({run.machine})", format_run(run)) for run in runs],
        ("the summary", summary),
    ]


def report(word: str, full_trace: bool = False) -> str:
    """The full text report for one input string."""
    return "\n".join(text for _, text in report_sections(word, full_trace=full_trace))


def verdicts(word: str):
    """Just the three yes/no answers, for batch runs and test suites."""
    return tuple(run.accepted for run in analyse(word))
