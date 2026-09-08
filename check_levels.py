"""
Validate every course and level before shipping.

Run it whenever you edit a map or a challenge:

    python3 check_levels.py

It checks map sizes, required markers, challenge data, that no
answers leak to the browser, and - most importantly - that every
item, sign, terminal, NPC and exit can actually be reached with the
player's jump (about 2 tiles up, 3 tiles across).
"""

import re
import sys

from curriculum import COURSES, COURSE_ORDER, public_level

SOLID = set("#SWG~")          # V (vines) and D (doors) open up, so they are passable
JUMP_ROWS = 2                 # tiles the player can rise in one jump
JUMP_COLS = 3                 # tiles the player can cross in one jump
TARGETS = "IQKCBXnN"          # things the player must be able to reach


def is_solid(rows, x, y):
    if x < 0 or x >= len(rows[0]):
        return True
    if y < 0:
        return False
    if y >= len(rows):
        return True
    return rows[y][x] in SOLID


def is_standing(rows, x, y):
    return not is_solid(rows, x, y) and is_solid(rows, x, y + 1)


def fall(rows, x, y):
    """Where the player ends up after dropping from (x, y)."""
    while y < len(rows) and not is_solid(rows, x, y) and not is_solid(rows, x, y + 1):
        y += 1
    if y >= len(rows) or is_solid(rows, x, y):
        return None
    return (x, y)


def reachable_standing_cells(rows):
    height = len(rows)
    width = len(rows[0])

    start = None
    for y in range(height):
        for x in range(width):
            if rows[y][x] == "P":
                start = fall(rows, x, y)
    if start is None:
        return set()

    seen = {start}
    queue = [start]

    while queue:
        x, y = queue.pop()

        def visit(cell):
            if cell and cell not in seen:
                seen.add(cell)
                queue.append(cell)

        # Walk (and drop off edges)
        for dx in (-1, 1):
            if not is_solid(rows, x + dx, y):
                visit(fall(rows, x + dx, y))

        # Jump: rise up to JUMP_ROWS with headroom, then move sideways
        for dy in range(0, JUMP_ROWS + 1):
            if any(is_solid(rows, x, y - k) for k in range(1, dy + 1)):
                break
            top = y - dy
            if dy > 0:
                visit(fall(rows, x, top))
            for direction in (-1, 1):
                reach = JUMP_COLS if dy < JUMP_ROWS else JUMP_COLS - 1
                for dx in range(1, reach + 1):
                    nx = x + direction * dx
                    if is_solid(rows, nx, top):
                        break
                    visit(fall(rows, nx, top))

    return seen


def target_reachable(rows, reached, x, y, marker):
    """
    Items float in their cell (grab by jumping); NPCs, signs and
    terminals settle on the floor; BYTE hovers where placed.
    """
    if marker in "nBC":
        settled = fall(rows, x, y)
        return settled in reached

    if marker == "X":
        return (x, y) in reached or fall(rows, x, y) in reached

    # Items / BYTE: within a short jump of a reached standing cell
    for (rx, ry) in reached:
        if abs(rx - x) <= 2 and 0 <= ry - y <= JUMP_ROWS:
            if not any(is_solid(rows, rx, ry - k) for k in range(1, ry - y + 1)):
                return True
        if abs(rx - x) <= 1 and -1 <= ry - y <= 0:
            return True
    return False


def check_map(rows, tag, problems):
    if len(rows) != 12 or any(len(r) != 40 for r in rows):
        problems.append((tag, "map must be 40x12, got %dx%d" % (len(rows[0]), len(rows))))
        return

    flat = "".join(rows)
    for marker, want in (("P", 1), ("C", 1), ("X", 1)):
        if flat.count(marker) != want:
            problems.append((tag, "expected exactly %d '%s', found %d" % (want, marker, flat.count(marker))))
    if "D" not in flat:
        problems.append((tag, "no door tiles"))
    if flat.count("B") > 1:
        problems.append((tag, "more than one sign"))

    reached = reachable_standing_cells(rows)
    if not reached:
        problems.append((tag, "player spawn missing or falls out of the map"))
        return

    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell in TARGETS and not target_reachable(rows, reached, x, y, cell):
                problems.append((tag, "'%s' at column %d row %d cannot be reached (jump is %d rows / %d cols)"
                                 % (cell, x, y, JUMP_ROWS, JUMP_COLS)))

    # Signs, terminals and idle doctors drop to the floor in-game; two of
    # them in the same column would fight over the E key.
    settled = []
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell in "BCn":
                landing = fall(rows, x, y)
                if landing:
                    settled.append((cell, landing[0]))
    # The E key reaches 22px; two things closer than 3 columns (48px)
    # could both be in range at once.
    for i, (cell_a, col_a) in enumerate(settled):
        for cell_b, col_b in settled[i + 1:]:
            if abs(col_a - col_b) < 3:
                problems.append((tag, "'%s' (column %d) and '%s' (column %d) are too close - keep interactables 3+ columns apart"
                                 % (cell_a, col_a, cell_b, col_b)))


def check_challenge(lvl, tag, problems):
    ch = lvl["challenge"]
    kind = ch.get("type")

    try:
        if kind == "mcq":
            assert 0 <= ch["answer"] < len(ch["options"])
        elif kind == "text_answer":
            assert ch["accepted"]
        elif kind == "python_lines":
            for p in ch["patterns"]:
                re.compile(p["regex"])
        elif kind == "code_review":
            assert 1 <= ch["target_line"] <= len(ch["code"])
            assert 0 <= ch["why_answer"] < len(ch["why_options"])
        elif kind == "fill_blank":
            blanks = sum(line.count("___") for line in ch["code"])
            assert blanks == len(ch["answers"]), "blanks %d != answers %d" % (blanks, len(ch["answers"]))
        elif kind == "order_code":
            n = len(ch["pieces"])
            assert sorted(ch["shuffle"]) == list(range(n)), "shuffle is not a permutation"
            assert ch["shuffle"] != list(range(n)), "pieces are not shuffled"
        elif kind == "quiz":
            assert ch["questions"], "quiz has no questions"
            for q in ch["questions"]:
                assert 0 <= q["answer"] < len(q["options"])
        else:
            raise AssertionError("unknown challenge type %r" % kind)
    except AssertionError as error:
        problems.append((tag, "challenge: %s" % (error or kind)))

    for key in ("objective", "story", "goal", "explanation", "reward"):
        if not lvl[key]:
            problems.append((tag, "empty field %s" % key))
    if not lvl["lesson"]["points"]:
        problems.append((tag, "no lesson points"))


def check_leaks(course, lvl, tag, problems):
    pub = public_level(course, lvl)["challenge"]
    for secret in ("regex", "patterns", "target_line", "why_answer", "accepted", "shuffle", "answers", "answer"):
        if secret in pub:
            problems.append((tag, "answer key '%s' leaks to the browser" % secret))
    if pub.get("type") == "quiz":
        for q in pub.get("questions", []):
            if "answer" in q:
                problems.append((tag, "quiz answers leak to the browser"))


def main():
    problems = []
    for slug in COURSE_ORDER:
        course = COURSES[slug]
        for lvl in course["levels"]:
            tag = "%s L%02d %s" % (slug, lvl["number"], lvl["title"])
            check_challenge(lvl, tag, problems)
            check_leaks(course, lvl, tag, problems)
            if lvl["map"]:
                check_map(lvl["map"], tag, problems)
            elif lvl.get("kind") != "quiz":
                # Levels without a map share the course default; check it once per course.
                pass
        print("%-15s %2d levels" % (slug, len(course["levels"])))

    if problems:
        print("\n%d problem(s):" % len(problems))
        for tag, text in problems:
            print("  [%s] %s" % (tag, text))
        sys.exit(1)

    print("\nAll levels OK.")


if __name__ == "__main__":
    main()
