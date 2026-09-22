"""
Shared pieces for every course file.

Map legend (read by static/js/game.js):

    #  ground         S  stone          W  wall (solid)
    G  lab panel      V  vines (solid until cut with the dagger)
    ~  water (solid, decorative)
    T  tree trunk     L  leaves         U  pipe (decoration)
    A  specimen tank (decoration)      .  air

    %  live data stream (deadly: the player is sent back to the last ledge)

    P  player spawn   N  guide (BYTE / VEX / PING / LINT)   B  sign
    C  terminal       D  door tiles     k  locked door (DOOR CODE)
    X  exit           v  vent exit (VENT KEY)   !  wire mouth / HDMI port
    I  hint chip      Q  dagger         K  candy
    [  bug cage       m  walkable mentor bot (Secure Coding)
    s  snake          h  hostile doctor n  idle doctor
    c  crawler bug    b  bug            z  packet sniffer (Internet)
    M  big snake      Y  VEX            R  the brain (bosses)
    O  obelisk        @  obelisk button (finale levels only)
"""

DEFAULT_MAP = [
    "........................................",
    "........................................",
    "........................................",
    "..LLL..........LLL...........LLL........",
    ".LLLLL........LLLLL.........LLLLL.......",
    "..LTL..........LTL...........LTL........",
    "...T............T.....I.......T.........",
    "...T............T....###......T....D....",
    "..PT.......N....T.............T..C.D..X.",
    "########################################",
    "########################################",
    "########################################",
]


def level(number, title, **fields):
    """
    Every level has the same shape. Fields not given fall back to
    sensible defaults, and `lesson` is built from `learn`/`example`
    when a level does not define its own.
    """
    data = {
        "number": number,
        "title": title,
        "kind": "level",      # "level" (playable map) or "quiz" (checkpoint questions)
        "section": "",
        "objective": "",
        "prerequisites": [],
        "concepts": [],
        "story": "",
        "goal": "",
        "gameplay": "",
        "learn": [],
        "example": "",
        "lesson": None,
        "dialogue": [],
        "sign": "",
        "npcs": [],
        "challenge": {},
        "reasoning": "",
        "success": "",
        "failure": "",
        "explanation": "",
        "reward": "",
        "mentor": "",
        "hints": [],
        "map": None,
        "theme": None,
        "start_items": [],
        "intro": False,
        "boss": False,
        "no_lesson": False,      # story-only level: no notes before play
        "guide": "BYTE",         # name of the voice that talks in-game
        "bugs": [],              # malware labels for bug enemies [{name, fact}]
        "dark": False,           # lights fade out along the map until bugs are dead
        "door_by_bugs": False,   # the door opens when every bug is dead
        "gate": False,           # draw the door as a firewall gate
        "finale": False,         # ends with the lights-out reveal
        "obelisk": False,        # the shared course finale: press the button, light the beam
        "music": "ossuary",      # key into curriculum.MUSIC; plays once when the level starts, loops on obelisk levels
        "mimic": False,          # desk levels: the monitor mirrors the player
        "code_lines": [],        # lines that appear on the monitor as the player runs
        "challenge_by_language": None,   # {"python": {...}, "javascript": {...}}
    }
    data.update(fields)

    if data["challenge_by_language"] and not data["challenge"]:
        # The default (used by the validator and when no language is chosen).
        data["challenge"] = data["challenge_by_language"]["python"]

    if data["no_lesson"] and data["lesson"] is None:
        data["lesson"] = {"title": data["title"], "points": [], "example": ""}

    if data["lesson"] is None:
        data["lesson"] = {
            "title": data["title"],
            "points": list(data["learn"]),
            "example": data["example"],
        }
    else:
        if not data["learn"]:
            data["learn"] = list(data["lesson"].get("points", []))
        if not data["example"]:
            data["example"] = data["lesson"].get("example", "")

    if not data["section"]:
        data["section"] = data["title"]

    return data


# ---------------------------------------------------------
# MAP BUILDER (coordinates instead of hand-counted strings)
# ---------------------------------------------------------

def grid(*rows):
    """A map: 12 rows, all the same width (40 or wider)."""
    width = len(rows[0])
    assert len(rows) == 12, "map needs 12 rows, got %d" % len(rows)
    for index, row in enumerate(rows):
        assert len(row) == width, "row %d is %d wide, expected %d" % (index, len(row), width)
    return list(rows)


def room(width, wall="W", floor_rows=3):
    """An empty room: walls left/right/top, a solid floor at the bottom."""
    rows = [["." for _ in range(width)] for _ in range(12)]
    for x in range(width):
        rows[0][x] = wall
        for y in range(12 - floor_rows, 12):
            rows[y][x] = wall
    for y in range(12):
        rows[y][0] = wall
        rows[y][width - 1] = wall
    return rows


def open_ground(width, ground="#"):
    """Outdoors: no walls, sky above, ground for the bottom three rows."""
    rows = [["." for _ in range(width)] for _ in range(12)]
    for x in range(width):
        for y in (9, 10, 11):
            rows[y][x] = ground
    return rows


def put(rows, row, col, text):
    """Write a string into a row starting at a column."""
    for offset, ch in enumerate(text):
        rows[row][col + offset] = ch


def finish(rows):
    return grid(*("".join(r) for r in rows))


# The obelisk plain every course ends on. 'O' is the obelisk, '@' its button.
def obelisk_map():
    rows = open_ground(48)
    put(rows, 8, 2, "P")
    put(rows, 8, 8, "N")
    put(rows, 8, 30, "O")
    put(rows, 8, 34, "@")
    return finish(rows)


def obelisk_level(number, course_title, zone, reward, guide, story, lesson_points):
    return level(
        number, "The Obelisk",
        section="The Obelisk",
        objective="Light your beam.",
        concepts=["completion"],
        obelisk=True,
        boss=False,
        lesson={
            "title": "What you carry out of %s" % zone,
            "points": lesson_points,
            "example": "",
        },
        story=story,
        goal="Walk to the obelisk and press E at the button.",
        gameplay="Walk right. Press E at the button. Watch the sky.",
        guide=guide,
        dialogue=[
            "Every recruit who finishes a course lights a beam here. It stays lit.",
            "Finish the others and you'll see them side by side. Go on - press it.",
        ],
        challenge={"type": "walk", "prompt": "Press the button on the obelisk."},
        reasoning="A shared ritual that marks course completion and makes progress across courses visible.",
        success="A beam of light climbs into the sky and stays there.",
        failure="-",
        explanation="%s complete. Your beam is lit for good." % course_title,
        reward=reward,
        mentor="Congratulate the learner and point them to the next course.",
        hints=["The button is at the base of the obelisk."],
        map=obelisk_map(),
        theme="obelisk",
    )
