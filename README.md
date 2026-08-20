# Robot Walk Recognizer

**Did the robot make it back home?**

TECH 315 Models of Computation · Westcliff University · group project
Pramish Sihali, Rista Shrestha, Raksha Shrestha, Manish Yadav

A robot's walk is written as compass moves over the alphabet `{N, S, E, W}` —
one symbol is one unit step, so `NNESSW` means north, north, east, south,
south, west. That one string is handed to **three independent machines**, each
answering a harder question, and each needing a strictly more powerful model of
computation to answer it.

| Tier | Machine | Question | Language | Class |
|------|---------|----------|----------|-------|
| 1 | DFA `M1` | Did the robot ever immediately undo its last move? | no substring in `{NS, SN, EW, WE}` | regular |
| 2 | PDA `P2` + CFG `G2` | Did the robot end on its starting row? | `#N = #S` | context-free, not regular |
| 3 | TM `M3` | Did the robot end exactly back home? | `#N = #S` and `#E = #W` | decidable, not context-free |

The three questions are **independent, not nested**: `NS` fails Tier 1 but
passes Tiers 2 and 3. No tier short-circuits another — all three always answer.

Each tier is a *real formal machine*, not a Python counter wearing a machine's
name: an explicit transition table for the DFA, a genuine stack for the PDA,
and a tape with a moving head for the Turing machine.

## Quick start

Python 3.9 or newer. No third-party packages, nothing to install.

```bash
python3 main.py NNESSW          # one walk through all three machines
python3 main.py NNESSW --pause  # one machine at a time (projector setting)
python3 main.py --demo          # the 8 design-validation walks
python3 main.py --tables        # print δ1, δ2 and δ3
python3 main.py                 # interactive prompt, used for the live demo

python3 run_tests.py            # the full test suite: 161 tests, ~10s
python3 analysis/analyze.py     # the performance measurements
```

## Hosted demo (Vercel)

The same system is also reachable from a browser: `api/index.py` is a thin
FastAPI wrapper around `robot_walk.pipeline` (imported unchanged, same rule
the tests and analysis harness follow), and `index.html` is one plain
HTML/CSS/JS page — no build step, no framework — that calls it. It reproduces
the CLI's four modes (one walk, `--demo`, `--tables`, the test suite) as
buttons, and shows the exact same text report in a `<pre>` block. This is a
convenience for sharing the system outside class; the graded live demo is
still `main.py`, text-only, per the syllabus.

```bash
pip install fastapi uvicorn        # not needed by main.py itself
uvicorn api.index:app --reload     # http://127.0.0.1:8000, frontend served separately

npm i -g vercel
vercel dev                         # serves index.html + api/* together, like production
vercel --prod                      # deploy
```

| Route | Mirrors |
|-------|---------|
| `POST /api/run {walk, full_trace}` | `main.py WALK [--full-tape]` |
| `GET /api/demo` | `main.py --demo` |
| `GET /api/tables` | `main.py --tables` |
| `GET /api/tests` | `run_tests.py` |

`/api/tests` runs all 161 tests on request (~10s); `vercel.json` sets
`maxDuration: 60` for that function — lower it, or the plan's limit, if the
hosting plan doesn't allow 60s.

## Layout

| Path | What it holds |
|------|---------------|
| `main.py` | command-line driver: single walk, demo, tables, interactive mode |
| `robot_walk/` | the system — one module per machine, plus the pipeline that runs all three |
| `tests/` | 161 tests, graded against an independent oracle |
| `run_tests.py` | test runner with a grouped summary |
| `analysis/` | the performance measurement harness and what it found |
| `demo/` | the live-demo run sheet and the presentation deck |
| `api/index.py`, `index.html`, `vercel.json`, `requirements.txt` | the hosted browser demo (Vercel) |

Each folder has its own README with the detail.

## What the measurements found

- Tier 1: one step per symbol, six states, always.
- Tier 2: one step per symbol plus two ε-moves; stack as tall as the running tally.
- Tier 3: **exactly `(n+1)(n+10)` steps on any accepted walk of length `n`** —
  independent of how the walk is arranged. Verified against all 1,398,101
  accepted walks of length ≤ 10 and measured to `n = 1024`.
- The worst case is an *accepted* input: rejections stop early.

## Theory behind the tiers

- **Tier 2 is not regular.** Intersect `L2` with `N*S*` and you get `NⁿSⁿ`, the
  textbook pumping-lemma example.
- **Tier 3 is not context-free.** Intersect `L3` with `N*E*S*W*` and you get
  `NⁿEᵐSⁿWᵐ`. Since the context-free languages are closed under intersection
  with a regular language, a context-free `L3` would make that language
  context-free too — and the pumping lemma for context-free languages says it
  is not. The same argument doubles as a live demonstration that the
  context-free languages are **not** closed under intersection.
- The Turing machine is a **decider**: it halts on every input. The halting
  problem shows that not every Turing machine does; this problem sits safely
  below that ceiling.

Reference: Sipser, M. (2013). *Introduction to the theory of computation*
(3rd ed.). Cengage Learning.
