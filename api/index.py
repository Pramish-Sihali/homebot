"""FastAPI wrapper around the robot_walk pipeline -- hosted demo for Vercel.

Serves the same computations `main.py` prints to a terminal, as JSON, so the
system can also be tried from a browser. The recognizers are imported
unchanged from `robot_walk/`; nothing here re-implements or patches them --
same rule the Week 6 test suite and Week 7 analysis harness already follow.
"""

import sys
import time
import unittest
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robot_walk import dfa, grid, pda, pipeline, tm  # noqa: E402
from robot_walk.spec import SIGMA  # noqa: E402
from main import DEMO_WALKS  # noqa: E402
import run_tests as suite_runner  # noqa: E402

MAX_WALK_LENGTH = 2000  # keeps a hosted request fast; main.py has no such limit

#: A few longer, more elaborate walks for the hosted demo tab to try, in
#: addition to (never replacing) the Week 4 design document's Table 8 above --
#: those 8 are a locked, already-graded validation set, so this list lives
#: here rather than in `main.py`'s DEMO_WALKS. No "expected" verdict: these
#: illustrate the system rather than validate it against a submitted table.
EXTRA_WALKS = (
    ("NNNEEESSSWWW", "a bigger square, three steps a side — still gets all the way home"),
    ("NENENENE", "a steady diagonal that never turns back — and never returns"),
    ("NEESWWNS", "a longer path where Tier 1 catches a reversal right near the end"),
    ("NESWNESWNESW", "the home loop, walked three times in a row"),
    ("NNEESSWWNNEESSWWNNEESSWW", "the home loop, extended — long enough to watch the tape do real work"),
)

app = FastAPI(title="Robot Walk Recognizer")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/", response_class=HTMLResponse)
def index():
    """The front end. Vercel's FastAPI preset routes the whole app -- including
    '/' -- through this one function, so the page has to be served from a real
    route rather than relying on `index.html` being picked up as a static file."""
    return (ROOT / "index.html").read_text(encoding="utf-8")


class WalkRequest(BaseModel):
    walk: str = ""
    full_trace: bool = False


def _clean(word: str) -> str:
    word = word.strip().upper()
    if len(word) > MAX_WALK_LENGTH:
        raise HTTPException(
            400, f"walk too long for the hosted demo (limit {MAX_WALK_LENGTH} symbols)"
        )
    return word


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _serialize_run(run) -> dict:
    """A Run dataclass as plain JSON -- the data the front end draws visuals from."""
    return {
        "tier": run.tier,
        "machine": run.machine,
        "question": run.question,
        "accepted": run.accepted,
        "verdict": run.verdict,
        "summary": run.summary,
        "headers": list(run.headers),
        "trace": [list(row) for row in run.trace],
        "extra": list(run.extra),
    }


@app.post("/api/run")
def run_walk(payload: WalkRequest):
    word = _clean(payload.walk)
    # Always analysed with the compact (non-full-tape) trace: that shape is
    # what the tier visuals expect. `full_trace` only affects the optional
    # raw CLI-style text report, exactly as it does for `main.py --full-tape`.
    runs = pipeline.analyse(word, full_trace=False)
    tier1, tier2, tier3 = (run.accepted for run in runs)
    return {
        "walk": word,
        "path": [list(cell) for cell in grid.path(word)],
        "report": pipeline.report(word, full_trace=payload.full_trace),
        "verdicts": {"tier1": tier1, "tier2": tier2, "tier3": tier3},
        "runs": [_serialize_run(run) for run in runs],
    }


@app.get("/api/demo")
def demo():
    """The Table 8 design-validation walks -- what `main.py --demo` runs."""
    rows = []
    failures = 0
    for word, expected, description in DEMO_WALKS:
        actual = pipeline.verdicts(word)
        ok = actual == expected
        failures += not ok
        rows.append(
            {
                "walk": word or "(empty)",
                "description": description,
                "tier1": actual[0],
                "tier2": actual[1],
                "tier3": actual[2],
                "matches_design": ok,
            }
        )
    extra = []
    for word, description in EXTRA_WALKS:
        actual = pipeline.verdicts(word)
        extra.append(
            {
                "walk": word,
                "description": description,
                "tier1": actual[0],
                "tier2": actual[1],
                "tier3": actual[2],
            }
        )

    return {"rows": rows, "failures": failures, "extra": extra}


def _dfa_structured() -> dict:
    return {
        "symbols": list(SIGMA),
        "start": dfa.START,
        "dead": dfa.DEAD,
        "rows": [
            {
                "state": state,
                "cells": [dfa.DELTA[state][s] for s in SIGMA],
                "accepting": state in dfa.ACCEPTING,
            }
            for state in dfa.STATES
        ],
    }


def _pda_structured() -> dict:
    rows = []
    for (state, read, pop), (next_state, push) in pda.DELTA.items():
        rows.append(
            {
                "state": state,
                "read": read or "ε",
                "pop": pop or "ε",
                "next_state": next_state,
                "push": push or "ε",
                "meaning": pda.MEANING[(state, read, pop)],
            }
        )
    return {"start": pda.START, "accept": pda.ACCEPT, "rows": rows}


def _tm_phase(state: str) -> str:
    if state in (tm.ACCEPT, tm.REJECT):
        return "halt"
    if "p1" in state:
        return "phase 1: pair N against S"
    if "p2" in state:
        return "phase 2: pair E against W"
    return "check the alphabet"


def _tm_structured() -> dict:
    rows = []
    for (state, symbol), (next_state, write, direction) in tm.DELTA.items():
        rows.append(
            {
                "state": state,
                "symbol": symbol,
                "next_state": next_state,
                "write": write,
                "direction": direction,
                "phase": _tm_phase(state),
            }
        )
    return {"accept": tm.ACCEPT, "reject": tm.REJECT, "count": len(rows), "rows": rows}


@app.get("/api/tables")
def tables():
    """The three transition tables -- what `main.py --tables` prints, plus a
    structured form the front end renders as real tables instead of text."""
    return {
        "dfa": dfa.transition_table(),
        "pda": pda.transition_table(),
        "tm": tm.transition_table(),
        "dfa_structured": _dfa_structured(),
        "pda_structured": _pda_structured(),
        "tm_structured": _tm_structured(),
    }


class _CollectingResult(unittest.TestResult):
    """A TestResult that also records every test that ran, not just failures.

    run_tests.py only needs pass/fail counts for its terminal summary; the
    hosted demo additionally wants to list which of the 161 tests ran, so
    this is kept here rather than changing the Week 6 runner.
    """

    def __init__(self):
        super().__init__()
        self.details = []

    @staticmethod
    def _describe(test) -> dict:
        """A test's Python name, turned into a plain-language phrase.

        ``test_a_reversal_is_caught_wherever_it_sits`` becomes "A reversal is
        caught wherever it sits". The original id is kept as ``raw`` for
        anyone who wants the literal, technical name.
        """
        full_id = test.id()
        method = full_id.split(".")[-1]
        words = method[len("test_"):] if method.startswith("test_") else method
        words = words.replace("_", " ").strip()
        phrase = (words[:1].upper() + words[1:]) if words else method
        return {"name": phrase, "raw": full_id}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.details.append({**self._describe(test), "outcome": "pass"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.details.append({**self._describe(test), "outcome": "fail"})

    def addError(self, test, err):
        super().addError(test, err)
        self.details.append({**self._describe(test), "outcome": "fail"})


def _run_module_detailed(name: str):
    suite = unittest.defaultTestLoader.loadTestsFromName(name)
    result = _CollectingResult()
    started = time.perf_counter()
    suite.run(result)
    elapsed = time.perf_counter() - started
    return result, elapsed


@app.get("/api/tests")
def run_test_suite():
    """Runs the Week 6 suite (161 tests), each one named, grouped by module."""
    rows = []
    total_tests = total_bad = 0
    total_time = 0.0
    for name, label in suite_runner.MODULES:
        result, elapsed = _run_module_detailed(name)
        bad = len(result.failures) + len(result.errors)
        rows.append(
            {
                "label": label,
                "tests": result.testsRun,
                "failed": bad,
                "seconds": round(elapsed, 2),
                "cases": result.details,
            }
        )
        total_tests += result.testsRun
        total_bad += bad
        total_time += elapsed
    return {
        "rows": rows,
        "total": total_tests,
        "passed": total_tests - total_bad,
        "failed": total_bad,
        "seconds": round(total_time, 2),
        "success": total_bad == 0,
    }
