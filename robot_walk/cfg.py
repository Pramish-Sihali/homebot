"""Tier 2, grammar side: the context-free grammar G2.

    G2 = (V, SIGMA, R, B),  V = {B},  B for "balanced"

        B -> N B S B | S B N B | E B | W B | eps

Every rule introduces N and S in equal numbers or not at all, so #N = #S is an
invariant of any derivation: L(G2) = L2, the language the Tier 2 pushdown
automaton recognizes. The parser here is not the recognizer -- P2 is -- but it
turns an accepted walk into a leftmost derivation, which is the visible
evidence that the grammar and the machine describe the same language.

Every rule except the epsilon rule consumes at least one terminal, and the
epsilon rule applies only to an empty span, so the recursion always shrinks the
span and the parse terminates.
"""

START = "B"
VARIABLES = ("B",)

#: The right-hand sides of R, in the order they are tried.
RULES = (
    ("N", "B", "S", "B"),
    ("S", "B", "N", "B"),
    ("E", "B"),
    ("W", "B"),
    (),
)


def rule_text(rule) -> str:
    return "".join(rule) if rule else "eps"


GRAMMAR_TEXT = "B -> " + " | ".join(rule_text(rule) for rule in RULES)


def parse(word: str):
    """Return a parse tree for ``word``, or None if G2 cannot derive it.

    A tree is (rule, [subtree, ...]), with one subtree per variable in the rule.
    """
    memo = {}

    def parse_span(start: int, end: int):
        if (start, end) in memo:
            return memo[(start, end)]
        memo[(start, end)] = None                   # guard against re-entry
        for rule in RULES:
            children = match(rule, 0, start, end)
            if children is not None:
                memo[(start, end)] = (rule, children)
                return memo[(start, end)]
        return None

    def match(rule, index: int, start: int, end: int):
        """Match rule[index:] against word[start:end], collecting subtrees."""
        if index == len(rule):
            return [] if start == end else None

        item = rule[index]
        if item not in VARIABLES:                   # a terminal
            if start < end and word[start] == item:
                return match(rule, index + 1, start + 1, end)
            return None

        for split in range(start, end + 1):        # a variable: try every split
            subtree = parse_span(start, split)
            if subtree is None:
                continue
            rest = match(rule, index + 1, split, end)
            if rest is not None:
                return [subtree] + rest
        return None

    return parse_span(0, len(word))


def leftmost_derivation(word: str):
    """Return the leftmost derivation of ``word`` as a list of sentential forms."""
    tree = parse(word)
    if tree is None:
        return None

    forms = [START]
    frontier = [(START, tree)]                      # items: terminal, or (variable, subtree)
    while True:
        position = next(
            (i for i, item in enumerate(frontier) if not isinstance(item, str)), None
        )
        if position is None:
            return forms
        _, subtree = frontier[position]
        rule, children = subtree
        expansion = []
        child_index = 0
        for symbol in rule:
            if symbol in VARIABLES:
                expansion.append((symbol, children[child_index]))
                child_index += 1
            else:
                expansion.append(symbol)
        frontier[position:position + 1] = expansion
        forms.append(_render(frontier))


def _render(frontier) -> str:
    text = "".join(item if isinstance(item, str) else item[0] for item in frontier)
    return text or "eps"


def derivation_lines(word: str, limit: int = 12):
    """Format the leftmost derivation for printing, eliding a long middle."""
    forms = leftmost_derivation(word)
    if forms is None:
        return None
    if len(forms) <= limit:
        shown = forms
    else:
        shown = forms[: limit - 4] + ["...", *forms[-3:]]
    lines = []
    for index, form in enumerate(shown):
        lines.append(("    " if index == 0 else " => ") + form)
    return lines
