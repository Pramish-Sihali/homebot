# Robot Walk Recognizer — Week 7 performance analysis

TECH 315 Models of Computation · Group project
Pramish Sihali, Rista Shrestha, Raksha Shrestha, Manish Yadav

`analyze.py` measures the `robot_walk` package in the repository root,
imported unchanged.
Every figure in `TECH315_Week7_Project_Paper` comes from a run of it.

## Running it

From the repository root:

```bash
python3 analysis/analyze.py            # every section, about 11 seconds
python3 analysis/analyze.py growth     # how cost grows with input length
python3 analysis/analyze.py shapes     # why the arrangement of the input does not matter
python3 analysis/analyze.py space      # memory each machine needs
python3 analysis/analyze.py clock      # wall-clock time and what is practical
python3 analysis/analyze.py extremes   # best case, worst case, exhaustive search
```

## Two units, kept apart

- **Machine steps** — symbols read, stack operations, head moves. What the
  model actually does; machine-independent; the honest measure.
- **Seconds** — what Python takes to simulate those steps. Measures the laptop
  as much as the machine; useful only for knowing what can be demonstrated
  live.

## What it found

| Result | |
|--------|--|
| Tier 1 | one step per symbol, six states, always |
| Tier 2 | one step per symbol plus two ε-moves; stack as tall as the tally |
| Tier 3 | **exactly `(n+1)(n+10)` steps on any accepted walk of length n** — independent of how the walk is arranged |
| Cheapest rejection | `3n + 5` steps, for a walk with no partners at all |
| Worst case | an *accepted* walk: rejections stop early |
| Slowest component | the CFG parser (~n^2.8 measured, O(n⁴) worst case) — and it decides nothing |

The closed form was verified against every accepted walk of length ≤ 10
(1,398,101 strings) and against measured runs up to n = 1,024.

**One defect found and fixed:** the Turing machine's safety limit was a fixed
2,000,000 steps, so every accepted walk longer than 1,408 symbols raised an
error instead of deciding. The limit now grows with the input. A regression
test was added to the Week 6 suite, which is now 161 tests.

## Next

Week 8 is the presentation and live demo. These numbers set the practical
sizes: Tiers 1 and 2 handle hundreds of thousands of symbols, Tier 3 a few
thousand, the parser a few dozen — and a demo walk of a dozen symbols keeps
every trace readable on a projector anyway.
