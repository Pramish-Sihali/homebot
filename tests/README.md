# Robot Walk Recognizer — Week 6 test suite

TECH 315 Models of Computation · Group project
Pramish Sihali, Rista Shrestha, Raksha Shrestha, Manish Yadav

The system under test is the `robot_walk` package in the repository root,
imported unchanged: nothing here edits, patches, or re-implements any part of it.

## Running it

Python 3.9 or newer, no third-party packages. From the repository root:

```bash
python3 run_tests.py                 # everything, with a grouped summary
python3 run_tests.py --verbose       # also print every test name
python3 run_tests.py tests.test_tm   # one module
python3 -m unittest discover         # plain unittest, same tests
```

161 tests, about 10 seconds.

## What is tested

| Module | Tests | What it covers |
|--------|-------|----------------|
| `tests/test_dfa.py` | 27 | δ₁ is the table the design fixes; trap behaviour; L1 exhaustively to length 8 |
| `tests/test_pda.py` | 27 | the stack holds \|#N − #S\| after every step; determinism; L2 exhaustively to length 8 |
| `tests/test_cfg.py` | 15 | G2's rules; L(G2) = L2; printed derivations really are leftmost |
| `tests/test_tm.py` | 32 | δ₃ is total; the tape and head behave; it halts on everything; L3 exhaustively to length 6 |
| `tests/test_integration.py` | 35 | all three tiers always answer; L3 ⊆ L2; Tier 1 independent; the printed report |
| `tests/test_random.py` | 9 | 5,000 random walks plus near-misses, against the oracle |
| `tests/test_efficiency.py` | 16 | O(n) for Tiers 1–2, O(n²) for Tier 3, measured in machine steps |

## The oracle

`tests/oracle.py` answers the three questions independently — a regular
expression for the reversals, `str.count` for the two balance conditions — so
no machine is ever graded by the logic that produced it. It is a measuring
instrument: nothing in `robot_walk` imports it.

## Exhaustive vs. random

Every walk up to length 8 is tested against all three machines: 87,381 strings,
which is a complete proof of correctness *for inputs that short*. The grammar
parser is exhausted to length 7 instead, because it costs O(n⁴). Longer inputs
are covered by 5,000 seeded random walks plus walks built to sit one step
inside or outside the language, where a bug is most likely to hide.

## Next

Week 7 analyses the performance numbers these tests produce and writes the test
report.
