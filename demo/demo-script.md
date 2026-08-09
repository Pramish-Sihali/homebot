# Week 8 — Live Demo Run Sheet

TECH 315 Models of Computation · Robot Walk Recognizer
Pramish Sihali, Rista Shrestha, Raksha Shrestha, Manish Yadav

Roughly 7 minutes. Every walk below has been run against the real program and
the verdicts here are what it actually prints.

## Before you start

Open a terminal, then:

```bash
cd ~/Desktop/tech-315/week_5
```

Everything runs from `week_5/`. Python 3.9+, no installs needed.

Set the terminal up before the room fills:

- **Full screen** (F11), **120 columns minimum** — the VERDICT lines are 116
  characters wide and look broken if they wrap.
- **Light background, dark text.** Projectors wash out dark themes.
- Font around 24-26px on a 1920-wide projector.

Use `--pause` everywhere. A full report is about ninety lines and a projector
shows roughly thirty-five, so without it you are scrolling while you talk.
With it the report arrives one machine at a time and you press Enter when the
room is ready.

---

## Beat 0 — "these are real machines" (30 sec)

```bash
python3 main.py --tables
```

Scroll through delta1, delta2, delta3. Do not read them aloud.

> "24 DFA transitions, 84 Turing machine transitions. We never wrote
> `if count == 0`. Each machine looks up its next move in a table, the way the
> definition says it should."

This answers "you just wrote Python counters and called them machines" before
anyone thinks to ask it.

---

## Beats 1-5 — interactive mode

```bash
python3 main.py --pause
```

You get a `walk>` prompt. Type a walk, press Enter — the picture appears. Press
Enter again and Tier 1 runs. From there each press of Enter brings the next
machine: Tier 2, Tier 3, then the summary. Type `quit` to leave.

Five screens per walk, each one narratable. Do not rush the Enter key — the
pause is there so the room can look at the trace while you explain it.

### Beat 1 — `NESW` — the baseline

Picture: a unit square, robot standing back on `H`.
**Tier 1 yes · Tier 2 yes · Tier 3 yes.**

This is the only beat where the audience sees the full output shape, so let it
breathe: DFA state path, PDA stack table, the leftmost derivation in G2, the TM
cross-off trace, the summary. After this they know the layout and every later
beat can go straight to the verdicts.

### Beat 2 — `NNE` — the DFA runs out of memory

Picture: `R` two north and one east of home.
**Tier 1 yes · Tier 2 NO · Tier 3 no.**

> "The DFA is perfectly happy — nothing doubled back. But it physically cannot
> know where the robot ended. It's a goldfish. Meanwhile the stack still has two
> sticky notes on it, so tier 2 catches it."

### Beat 3 — `NES` — the beat that justifies the Turing machine

Picture: `R` sitting one cell **east** of `H`.
**Tier 1 yes · Tier 2 yes · Tier 3 NO.**

> "Tier 2 says yes, you are back on your starting row — and it is right. Look at
> the picture, he is on the row. It just is not enough. One stack counted one
> axis. To check both axes at once you provably need the tape."

The most important 40 seconds of the talk. It is Theorem 2 made visual: the
audience sees why one counter cannot do the job before anyone says the words
"CFLs are not closed under intersection."

### Beat 4 — `NS` — the punchline

Picture: north, then straight back. Robot standing on `H`.
**Tier 1 NO · Tier 2 yes · Tier 3 yes.**

> "It failed the easiest question and passed the hardest one. The tiers are not
> nested. They are three independent questions that happen to need three
> different classes of machine."

Audiences assume a ladder where failing tier 1 fails everything. Breaking that
on purpose is what makes the design read as deliberate.

### Beat 5 — `NEB` — rejection and the alphabet (5 sec)

**All three reject.** `B` is not in the alphabet. Move on quickly.

Then type `quit`.

---

## Beat 6 — the tape, for real

```bash
python3 main.py NNEESSWW --full-tape --pause
```

Scroll the configurations in `u q v` notation.

> "Every one of those lines is one move of the head. 162 steps to answer one
> yes/no question about eight letters."

Then the Week 7 finding — the exact cost, not a bound:

**Tier 3 takes exactly `(n+1)(n+10)` steps on every accepted walk of length n.**

| walk       | n | steps printed | (n+1)(n+10) |
|------------|---|---------------|-------------|
| `NS`       | 2 | 36            | 36          |
| `NESW`     | 4 | 70            | 70          |
| `NNESSW`   | 6 | 112           | 112         |
| `NNEESSWW` | 8 | 162           | 162         |

> "Not an upper bound. The exact count. And it never varies with the
> arrangement of the letters, only with how many there are."

Then the counterintuitive bit: `NES` was **rejected** in 40 steps, not the 52
the formula would predict — rejections quit early, so **the worst case is an
accepted input.**

---

## Beat 7 — close

```bash
python3 main.py --demo
```

One screen, the 8 design-validation walks from the Week 4 design document,
all passing.

> "Everything you just watched is checked automatically every time we run it.
> Week 6 grew that into 161 tests."

---

## Coverage

| CLI feature      | shown in  |
|------------------|-----------|
| `--tables`       | Beat 0    |
| interactive mode | Beats 1-5 |
| `--pause`        | throughout|
| single walk      | Beat 6    |
| `--full-tape`    | Beat 6    |
| `--demo`         | Beat 7    |

Core ideas hit: the machines are real · finite memory is not enough · one stack
is not enough · the tiers are independent, not nested · the TM always halts ·
exact measured cost · the whole thing is tested.

---

## Things to sort out before the day

- Who drives the keyboard, who narrates. Two people, not one.
- Run the "audience predicts before you press Enter" bit on **Beats 3 and 4
  only**. On every walk it drags, and Beat 3 is the one where guessing wrong
  actually teaches something.
- Keep demo walks short. Week 7 numbers say the CFG parser gets slow past a few
  dozen symbols, and long traces stop being readable on a projector well before
  that. Nothing here is longer than 8 symbols.
- Known cosmetic wrinkle: in interactive mode the picture prints once before the
  first Enter and again at the top of the report, so it shows twice. Reads as
  "predict, then confirm" if you say so out loud; otherwise ignore it.
- Rehearse once end to end with the projector actually plugged in. The only
  thing that reliably goes wrong is the font being too small to read.

## Fallback if the laptop dies

`week_5/TECH315_Week5_Project_Paper.pdf` has the traces, and
`week_7/TECH315_Week7_Source_Code.pdf` has a full verbatim run. Have both open
in tabs.
