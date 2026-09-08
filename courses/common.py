"""
Shared pieces for every course file.

Map legend (read by static/js/game.js):

    #  ground         S  stone          W  wall (solid)
    G  lab panel      V  vines (solid until cut with the dagger)
    ~  water (solid, decorative)
    T  tree trunk     L  leaves         U  pipe (decoration)
    A  specimen tank (decoration)      .  air

    P  player spawn   N  BYTE           B  sign
    C  terminal       D  door tiles     X  exit
    I  hint chip      Q  dagger         K  candy
    s  snake          h  hostile doctor n  idle doctor
    M  big snake (boss)
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
    }
    data.update(fields)

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
