"""Robot Walk Recognizer -- TECH 315 group project, Week 5 implementation.

One walk over {N, S, E, W} is checked by three machines of increasing power:

    Tier 1  DFA M1   no immediate reversal          regular
    Tier 2  PDA P2   #N = #S                        context-free
    Tier 3  TM  M3   #N = #S and #E = #W            decidable

Each tier is a genuine formal machine -- an explicit transition table, a real
stack, a real tape and head -- not a counter wearing a machine's name.
"""

from . import cfg, dfa, grid, pda, pipeline, spec, tm

__all__ = ["cfg", "dfa", "grid", "pda", "pipeline", "spec", "tm"]
