"""The ASCII picture of a walk, so an audience can check any verdict by eye.

This is presentation only -- no recognition happens here. Every yes/no printed
by the system comes from the three machines; the grid is what lets a person in
the room confirm the answer without trusting the code.
"""

from .spec import STEP, SIGMA

HOME = "H"
ROBOT = "R"
VISITED = "*"
EMPTY = "."


def path(word: str):
    """The cells the robot occupies, starting at home (0, 0)."""
    east, north = 0, 0
    cells = [(0, 0)]
    for symbol in word:
        if symbol not in SIGMA:                     # illegal symbols move nothing
            continue
        de, dn = STEP[symbol]
        east, north = east + de, north + dn
        cells.append((east, north))
    return cells


def render(word: str, indent: str = "    ") -> str:
    """Draw the walk on a grid, with H at the start and R where it ended."""
    cells = path(word)
    start, end = cells[0], cells[-1]
    visited = set(cells)

    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    lines = []
    for y in range(max(ys), min(ys) - 1, -1):
        row = []
        for x in range(min(xs), max(xs) + 1):
            if (x, y) == end and end != start:
                row.append(ROBOT)
            elif (x, y) == start:
                row.append(HOME)
            elif (x, y) in visited:
                row.append(VISITED)
            else:
                row.append(EMPTY)
        lines.append(indent + " ".join(row))

    east, north = end
    if end == start:
        where = "the robot is standing on home"
    else:
        parts = []
        if north:
            parts.append(f"{abs(north)} {'north' if north > 0 else 'south'}")
        if east:
            parts.append(f"{abs(east)} {'east' if east > 0 else 'west'}")
        where = "the robot ends " + " and ".join(parts) + " of home"

    legend = f"{indent}H = home   R = where the robot stopped   * = a cell it passed through"
    return "\n".join(lines + ["", legend, f"{indent}{where}"])


def displacement(word: str):
    """Net (east, north) offset of the walk, used in the summary lines."""
    return path(word)[-1]
