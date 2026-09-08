"""
Cyber Academy curriculum.

Each course lives in its own file under courses/ (plain Python data).
This module assembles them and provides the lookups the routes use.

Challenge types (checked server-side in challenges.py):

    mcq          - options + index of the correct one
    text_answer  - short typed answer, compared to an accepted list
    python_lines - one regex per required line of Python (never executed)
    code_review  - pick the dangerous/broken line, then pick why
    fill_blank   - code with ___ blanks + accepted answers per blank
    order_code   - drag shuffled lines into the correct order
"""

from courses.common import DEFAULT_MAP
from courses.python_course import PYTHON_LEVELS
from courses.cybersecurity import CYBER_LEVELS
from courses.internet import INTERNET_LEVELS
from courses.secure_coding import SECURE_LEVELS


COURSES = {
    "cybersecurity": {
        "slug": "cybersecurity",
        "number": "01",
        "title": "Cybersecurity",
        "zone": "The Watchtower",
        "theme": "tower",
        "description": "Learn how threats work, how systems are defended, and how security incidents are handled.",
        "intro": "The Watchtower guards the Academy's walls. Here you learn to see threats before they see you.",
        "levels": CYBER_LEVELS,
    },
    "python": {
        "slug": "python",
        "number": "02",
        "title": "Python",
        "zone": "The Grove",
        "theme": "forest",
        "description": "Learn programming fundamentals through interactive challenges and coding puzzles.",
        "intro": "The Grove is where recruits first learn to speak to machines. Every door here listens to Python.",
        "levels": PYTHON_LEVELS,
    },
    "internet": {
        "slug": "internet",
        "number": "03",
        "title": "Internet Basics",
        "zone": "The Relay",
        "theme": "relay",
        "description": "Discover how computers communicate using networks, IP addresses, DNS, and packets.",
        "intro": "The Relay is a field of signal towers. Follow a message from your hand to the far side of the world.",
        "levels": INTERNET_LEVELS,
    },
    "secure-coding": {
        "slug": "secure-coding",
        "number": "04",
        "title": "Secure Coding",
        "zone": "The Foundry",
        "theme": "foundry",
        "description": "Learn to identify vulnerabilities and use AI as a secure coding mentor.",
        "intro": "The Foundry forges the Academy's own code. Nothing ships until a reviewer has read it.",
        "levels": SECURE_LEVELS,
    },
}

# The quiz stores "secure" for the secure-coding course.
QUIZ_TO_COURSE = {
    "python": "python",
    "cybersecurity": "cybersecurity",
    "internet": "internet",
    "secure": "secure-coding",
}

COURSE_ORDER = ["cybersecurity", "python", "internet", "secure-coding"]


def get_course(slug):
    return COURSES.get(slug)


def get_level(slug, number):
    course = get_course(slug)
    if course is None:
        return None
    if not isinstance(number, int) or number < 1 or number > len(course["levels"]):
        return None
    return course["levels"][number - 1]


def course_sections(course):
    """Levels grouped by section, in order, for the course sidebar."""
    sections = []
    for lvl in course["levels"]:
        if not sections or sections[-1]["name"] != lvl["section"]:
            sections.append({"name": lvl["section"], "levels": []})
        sections[-1]["levels"].append(lvl)
    return sections


def level_map(course, lvl):
    return lvl["map"] or DEFAULT_MAP


def level_theme(course, lvl):
    return lvl["theme"] or course["theme"]


def mentor_briefing(course, lvl):
    """
    What SecureMentor is told about the level the player is on.
    Everything the player can already see is included; answer keys,
    regexes and correct orders are not.
    """
    challenge = lvl["challenge"]
    kind = challenge.get("type")
    lesson = lvl["lesson"]

    lines = [
        "Zone: %s (%s course). Section: %s. Level %d of %d: %s."
        % (course["zone"], course["title"], lvl["section"], lvl["number"], len(course["levels"]), lvl["title"]),
        "Objective: " + lvl["objective"],
        "Story: " + lvl["story"],
        "Lesson notes the learner has just read:",
    ]
    lines += ["- " + point for point in lesson.get("points", [])]
    if lesson.get("example"):
        lines.append("Example shown in the lesson:\n" + lesson["example"])

    if kind == "quiz":
        lines.append("This is a checkpoint quiz. Questions (the correct options are deliberately NOT listed here):")
        for i, q in enumerate(challenge["questions"], 1):
            lines.append("%d. %s  Options: %s" % (i, q["prompt"], " | ".join(q["options"])))
    else:
        lines.append("Terminal challenge (%s): %s" % (kind, challenge.get("prompt", "")))
        if kind == "python_lines":
            lines.append("The terminal expects exactly %d line(s) of Python." % len(challenge["patterns"]))
        elif kind == "fill_blank":
            lines.append("Code with blanks:\n" + "\n".join(challenge["code"]))
            if challenge.get("bank"):
                lines.append("Word bank offered to the learner: " + " | ".join(challenge["bank"]))
        elif kind == "order_code":
            lines.append("Lines the learner must arrange (shown here in the shuffled order they see):\n"
                         + "\n".join(challenge["pieces"][i] for i in challenge["shuffle"]))
        elif kind == "code_review":
            lines.append("Code under review:\n" + "\n".join("%d: %s" % (i + 1, l) for i, l in enumerate(challenge["code"])))
            lines.append("Reasons offered: " + " | ".join(challenge["why_options"]))
        elif kind == "mcq":
            lines.append("Options: " + " | ".join(challenge["options"]))

    if lvl.get("mentor"):
        lines.append("Mentor guidance for this level: " + lvl["mentor"])
    if lvl.get("hints"):
        lines.append("Built-in nudges (never be more direct than these): " + " / ".join(lvl["hints"]))

    lines.append(
        "Rules for this reply: do not state the exact line, blank value, order, option letter or answer. "
        "Ask one guiding question or point to the lesson note that applies. "
        "Stay under 120 words unless the learner asks for more."
    )
    return "\n".join(lines)


def public_level(course, lvl):
    """
    The version of a level that is safe to send to the browser:
    answers, regexes, target lines and correct orders are stripped.
    """
    challenge = lvl["challenge"]
    kind = challenge.get("type")

    public_challenge = {
        "type": kind,
        "prompt": challenge.get("prompt", ""),
        "placeholder": challenge.get("placeholder", ""),
        "label": challenge.get("label", "TERMINAL"),
    }

    if kind == "mcq":
        public_challenge["options"] = challenge["options"]

    elif kind == "code_review":
        public_challenge["code"] = challenge["code"]
        public_challenge["why_options"] = challenge["why_options"]

    elif kind == "python_lines":
        public_challenge["line_count"] = len(challenge["patterns"])

    elif kind == "fill_blank":
        public_challenge["code"] = challenge["code"]
        public_challenge["bank"] = challenge.get("bank", [])
        public_challenge["blank_count"] = len(challenge["answers"])

    elif kind == "order_code":
        # Only the shuffled view is sent; the correct order stays here.
        public_challenge["pieces"] = [challenge["pieces"][i] for i in challenge["shuffle"]]

    elif kind == "quiz":
        public_challenge["questions"] = [
            {"prompt": q["prompt"], "options": q["options"]} for q in challenge["questions"]
        ]

    return {
        "course": course["slug"],
        "course_title": course["title"],
        "zone": course["zone"],
        "theme": level_theme(course, lvl),
        "number": lvl["number"],
        "kind": lvl["kind"],
        "title": lvl["title"],
        "section": lvl["section"],
        "objective": lvl["objective"],
        "story": lvl["story"],
        "goal": lvl["goal"],
        "dialogue": lvl["dialogue"],
        "sign": lvl["sign"],
        "npcs": lvl["npcs"],
        "challenge": public_challenge,
        "hints": lvl["hints"],
        "reward": lvl["reward"],
        "map": level_map(course, lvl),
        "intro": lvl["intro"],
        "boss": lvl["boss"],
        "start_items": lvl["start_items"],
        "level_count": len(course["levels"]),
    }
