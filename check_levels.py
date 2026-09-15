"""
Validate every course and level before shipping.

Run it whenever you edit a map or a challenge:

    python3 check_levels.py

It checks map sizes, required markers, challenge data, that no
answers leak to the browser, and - most importantly - that every
item, sign, terminal, NPC, enemy and exit can actually be reached
with the player's jump (about 2 tiles up, 3 tiles across).
"""

import re
import sys

from curriculum import COURSES, COURSE_ORDER, public_level

SOLID = set("#SWG~[")         # V (vines), D and k (doors) open up, so they are passable
DEADLY = "%"                  # the live data stream: landing in it is not a place to stand
JUMP_ROWS = 2                 # tiles the player can rise in one jump
JUMP_COLS = 3                 # tiles the player can cross in one jump
TARGETS = "IQKCBXnNcbYRv[!zm@O"   # things the player must be able to reach
FLOOR_BOUND = "BCnm@O"        # things that drop to the floor in-game
LANGUAGES = ("python", "javascript")


def with_door_frames(rows):
    """
    Mirrors the engine: every upright door (two stacked D or k tiles)
    gets a solid frame from its top to the ceiling, so the validator
    cannot 'reach' things by jumping over a closed door either.
    """
    grid = [list(r) for r in rows]
    width = len(rows[0])
    for x in range(width):
        stack = [y for y in range(len(rows)) if rows[y][x] in "Dk"]
        if len(stack) < 2:
            continue
        y = min(stack) - 1
        while y >= 0 and grid[y][x] == ".":
            grid[y][x] = "F"
            y -= 1
    return ["".join(r) for r in grid]


def is_solid(rows, x, y):
    if x < 0 or x >= len(rows[0]):
        return True
    if y < 0:
        return False
    if y >= len(rows):
        return True
    return rows[y][x] in SOLID or rows[y][x] == "F"


def fall(rows, x, y):
    """Where the player ends up after dropping from (x, y); None if that is nowhere safe."""
    while y < len(rows) and not is_solid(rows, x, y) and not is_solid(rows, x, y + 1):
        y += 1
    if y >= len(rows) or is_solid(rows, x, y):
        return None
    if rows[y][x] in DEADLY:
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

        for dx in (-1, 1):
            if not is_solid(rows, x + dx, y):
                visit(fall(rows, x + dx, y))

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
    if marker in FLOOR_BOUND:
        return fall(rows, x, y) in reached

    if marker in "Xv!":
        return (x, y) in reached or fall(rows, x, y) in reached

    if marker == "[":
        # A cage is solid; the player needs to stand next to it.
        return any(abs(rx - x) <= 1 and abs(ry - y) <= 1 for (rx, ry) in reached)

    for (rx, ry) in reached:
        if abs(rx - x) <= 2 and 0 <= ry - y <= JUMP_ROWS:
            if not any(is_solid(rows, rx, ry - k) for k in range(1, ry - y + 1)):
                return True
        if abs(rx - x) <= 1 and -1 <= ry - y <= 0:
            return True
    return False


def check_map(rows, lvl, tag, problems):
    if len(rows) != 12 or any(len(r) != len(rows[0]) for r in rows) or len(rows[0]) < 40:
        problems.append((tag, "map must be 12 rows of equal width (40+), got %s" % [len(r) for r in rows]))
        return

    flat = "".join(rows)
    kind = lvl["challenge"].get("type")
    ends_itself = lvl["finale"] or lvl["obelisk"]

    if flat.count("P") != 1:
        problems.append((tag, "expected exactly one 'P', found %d" % flat.count("P")))

    if kind != "walk" and flat.count("C") != 1:
        problems.append((tag, "expected exactly one 'C' (terminal), found %d" % flat.count("C")))

    exits = flat.count("X") + flat.count("v")
    if not ends_itself and exits != 1:
        problems.append((tag, "expected exactly one exit ('X' or 'v'), found %d" % exits))
    if lvl["finale"] and "R" not in flat:
        problems.append((tag, "finale level needs the brain 'R'"))
    if lvl["obelisk"] and ("O" not in flat or "@" not in flat):
        problems.append((tag, "obelisk level needs 'O' and its button '@'"))

    if kind not in ("walk",) and "D" not in flat and "k" not in flat:
        problems.append((tag, "no door tiles"))
    if flat.count("B") > 1:
        problems.append((tag, "more than one sign"))
    if "v" in flat and "Y" not in flat:
        problems.append((tag, "a vent exit needs the doctor boss 'Y' to drop the key"))
    if lvl["door_by_bugs"] and "[" not in flat and "b" not in flat:
        problems.append((tag, "door_by_bugs but no bugs or cages"))
    if ("b" in flat or "[" in flat) and not lvl["bugs"]:
        problems.append((tag, "bugs on the map but no 'bugs' labels on the level"))

    rows = with_door_frames(rows)
    reached = reachable_standing_cells(rows)
    if not reached:
        problems.append((tag, "player spawn missing or falls out of the map"))
        return

    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell in TARGETS and not target_reachable(rows, reached, x, y, cell):
                problems.append((tag, "'%s' at column %d row %d cannot be reached (jump is %d rows / %d cols)"
                                 % (cell, x, y, JUMP_ROWS, JUMP_COLS)))

    settled = []
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell in FLOOR_BOUND:
                landing = fall(rows, x, y)
                if landing:
                    settled.append((cell, landing[0]))
    for i, (cell_a, col_a) in enumerate(settled):
        for cell_b, col_b in settled[i + 1:]:
            if abs(col_a - col_b) < 3:
                problems.append((tag, "'%s' (column %d) and '%s' (column %d) are too close - keep interactables 3+ columns apart"
                                 % (cell_a, col_a, cell_b, col_b)))


def check_challenge(lvl, tag, problems):
    variants = lvl.get("challenge_by_language")
    if variants:
        for language in LANGUAGES:
            if language not in variants:
                problems.append((tag, "missing a %s variant of the challenge" % language))
        for language, ch in variants.items():
            check_one_challenge(ch, tag + " [" + language + "]", problems)
    else:
        check_one_challenge(lvl["challenge"], tag, problems)

    for key in ("objective", "story", "goal", "explanation", "reward"):
        if not lvl[key]:
            problems.append((tag, "empty field %s" % key))
    if not lvl["no_lesson"] and not lvl["lesson"]["points"]:
        problems.append((tag, "no lesson points"))


def check_one_challenge(ch, tag, problems):
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
        elif kind == "swipe":
            assert len(ch["cards"]) >= 4, "a deck needs at least 4 cards"
            for c in ch["cards"]:
                assert isinstance(c["scam"], bool) and c["why"] and c["body"] and c["from"]
            scams = sum(1 for c in ch["cards"] if c["scam"])
            assert 0 < scams < len(ch["cards"]), "a deck needs both scams and legit messages"
        elif kind == "walk":
            pass
        elif kind == "wires":
            n = len(ch["devices"])
            assert len(ch["ports"]) == n and len(ch["answer"]) == n, "devices, ports and answer must match in length"
            assert sorted(ch["answer"]) == list(range(n)), "answer must be a permutation of the ports"
        elif kind == "route_packets":
            assert len(ch["answer"]) == len(ch["packets"]), "one answer per packet"
            dns = ch.get("dns", {})
            for packet, target in zip(ch["packets"], ch["answer"]):
                assert 0 <= target < len(ch["machines"]), "answer out of range"
                resolved = dns.get(packet["to"], packet["to"])
                assert resolved == ch["machines"][target]["ip"], "packet %s does not resolve to its answer" % packet["label"]
        elif kind == "ip_assign":
            assert ch["network"].endswith(".") and ch["network"].count(".") == 3, "network must be a three-octet prefix ending in a dot"
            assert all(t.startswith(ch["network"]) for t in ch["taken"]), "taken addresses must be on the network"
        elif kind == "idea":
            pass
        elif kind == "language":
            assert set(ch["options"]) <= set(LANGUAGES), "unknown language option"
        else:
            raise AssertionError("unknown challenge type %r" % kind)
    except AssertionError as error:
        problems.append((tag, "challenge: %s" % (error or kind)))


def check_leaks(course, lvl, tag, problems):
    for language in LANGUAGES:
        check_leaks_for(course, lvl, tag, problems, language)


def check_leaks_for(course, lvl, tag, problems, language):
    pub = public_level(course, lvl, language)["challenge"]
    for secret in ("regex", "patterns", "target_line", "why_answer", "accepted", "shuffle", "answers", "answer"):
        if secret in pub:
            problems.append((tag, "answer key '%s' leaks to the browser" % secret))
    for q in pub.get("questions", []):
        if "answer" in q:
            problems.append((tag, "quiz answers leak to the browser"))
    for c in pub.get("cards", []):
        if "scam" in c or "why" in c:
            problems.append((tag, "swipe verdicts leak to the browser"))


def main():
    problems = []
    for slug in COURSE_ORDER:
        course = COURSES[slug]
        for lvl in course["levels"]:
            tag = "%s L%02d %s" % (slug, lvl["number"], lvl["title"])
            check_challenge(lvl, tag, problems)
            check_leaks(course, lvl, tag, problems)
            if lvl["map"]:
                check_map(lvl["map"], lvl, tag, problems)
        print("%-15s %2d levels" % (slug, len(course["levels"])))

    if problems:
        print("\n%d problem(s):" % len(problems))
        for tag, text in problems:
            print("  [%s] %s" % (tag, text))
        sys.exit(1)

    print("\nAll levels OK.")


if __name__ == "__main__":
    main()
