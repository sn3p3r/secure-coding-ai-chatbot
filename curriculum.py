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
from courses.banter import doctor_lines, guide_lines

# Music catalogue. Files live in static/audio; credits are shown in the
# site footer (CREDITS tab) and in static/audio/CREDITS.md.
MUSIC = {
    "ossuary": {
        "file": "audio/music/ossuary-1-a-beginning.mp3",
        "title": "Ossuary 1 - A Beginning",
        "artist": "Kevin MacLeod (incompetech.com)",
        "license": "Creative Commons: By Attribution 4.0 License",
        "license_url": "http://creativecommons.org/licenses/by/4.0/",
        "source_url": "https://incompetech.com/music/royalty-free/",
        "changes": "Unchanged. Played once when a level starts and looped on the obelisk levels.",
    },
}


def music_credits():
    return list(MUSIC.values())


def level_music(lvl):
    """{"file", "loop"} for the browser, or None (quizzes, unknown keys)."""
    track = MUSIC.get(lvl.get("music") or "")
    if lvl["kind"] == "quiz" or track is None:
        return None
    return {"file": "/static/" + track["file"], "loop": bool(lvl["obelisk"]), "title": track["title"]}
from courses.python_course import PYTHON_LEVELS
from courses.cybersecurity import CYBER_LEVELS
from courses.internet import INTERNET_LEVELS
from courses.secure_coding import SECURE_LEVELS


COURSES = {
    "cybersecurity": {
        "slug": "cybersecurity",
        "number": "01",
        "title": "Cybersecurity",
        "zone": "The Wire",
        "theme": "jungle",
        "description": "Break into a lab, step by step - and learn what every one of those steps looks like to a defender.",
        "intro": "You come out of a wire into a jungle. Somewhere ahead is a white lab. Nobody has told you why.",
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


LANGUAGES = ("python", "javascript")


def resolve_challenge(lvl, language=None):
    """The challenge for one player: language-specific when the level has variants."""
    variants = lvl.get("challenge_by_language")
    if variants:
        return variants.get(language) or variants["python"]
    return lvl["challenge"]


def level_map(course, lvl):
    return lvl["map"] or DEFAULT_MAP


def level_theme(course, lvl):
    return lvl["theme"] or course["theme"]


def mentor_briefing(course, lvl, language=None):
    """
    What SecureMentor is told about the level the player is on.
    Everything the player can already see is included; answer keys,
    regexes and correct orders are not.
    """
    challenge = resolve_challenge(lvl, language)
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

    if lvl.get("no_lesson"):
        lines.append("This is a story-only level with no lesson: keep replies atmospheric and short, "
                     "explain controls if asked, and say the teaching starts at the lab.")

    if kind == "quiz":
        lines.append("This is a checkpoint quiz. Questions (the correct options are deliberately NOT listed here):")
        for i, q in enumerate(challenge["questions"], 1):
            lines.append("%d. %s  Options: %s" % (i, q["prompt"], " | ".join(q["options"])))
    elif kind == "swipe":
        labels = challenge.get("labels") or ["SCAM", "LEGIT"]
        lines.append("Sorting deck, %s vs %s (verdicts deliberately NOT listed). Coach on the pattern, never on a specific card:" % (labels[0], labels[1]))
        for i, card in enumerate(challenge["cards"], 1):
            lines.append("%d. [%s] %s - %s %s" % (i, card["kind"], card["from"], card.get("subject", ""), card["body"][:160]))
    elif kind == "walk":
        lines.append("Story level: no terminal. The goal is to reach the exit; explain mechanics if asked."
                     + (" This is the obelisk finale: pressing the button lights the course's beam." if lvl.get("obelisk") else ""))
    elif kind == "wires":
        lines.append("Wiring puzzle: devices %s must be connected to ports %s according to the sign in the level (mapping NOT listed here)."
                     % (", ".join(challenge["devices"]), ", ".join(challenge["ports"])))
    elif kind == "route_packets":
        lines.append("Packet delivery: machines %s. Packets: %s. (Correct deliveries NOT listed.)"
                     % ("; ".join("%s = %s" % (m["name"], m["ip"]) for m in challenge["machines"]),
                        "; ".join("%s to %s" % (p["label"], p["to"]) for p in challenge["packets"])))
        if challenge.get("dns"):
            lines.append("DNS table shown to the learner: " + "; ".join("%s = %s" % kv for kv in challenge["dns"].items()))
    elif kind == "ip_assign":
        lines.append("IP assignment on network %sx; addresses in use: %s. Explain the rules (four numbers 0-255, same prefix, last number 1-254, unique) but never propose a specific address."
                     % (challenge["network"], ", ".join(challenge["taken"])))
    elif kind == "idea":
        lines.append("The learner is writing down a website idea (name, one-sentence pitch, three pages). Help them sharpen it with questions; do not write it for them.")
    elif kind == "language":
        lines.append("The learner is choosing the course language (%s)." % " or ".join(challenge["options"]))
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


def public_level(course, lvl, language=None, beams=None):
    """
    The version of a level that is safe to send to the browser:
    answers, regexes, target lines and correct orders are stripped.
    `language` picks the code variant; `beams` lists finished courses
    for the obelisk sky.
    """
    challenge = resolve_challenge(lvl, language)
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

    elif kind == "swipe":
        # Verdicts and explanations arrive one card at a time from the server.
        public_challenge["cards"] = [
            {"kind": c["kind"], "from": c["from"], "subject": c.get("subject", ""), "body": c["body"]}
            for c in challenge["cards"]
        ]
        public_challenge["labels"] = challenge.get("labels") or ["SCAM", "LEGIT"]

    elif kind == "wires":
        public_challenge["devices"] = challenge["devices"]
        public_challenge["ports"] = challenge["ports"]

    elif kind == "route_packets":
        public_challenge["machines"] = challenge["machines"]
        public_challenge["packets"] = challenge["packets"]
        public_challenge["dns"] = challenge.get("dns", {})

    elif kind == "ip_assign":
        public_challenge["network"] = challenge["network"]
        public_challenge["taken"] = challenge["taken"]

    elif kind == "language":
        public_challenge["options"] = challenge["options"]

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
        "banter": {
            "doctor": doctor_lines(level_theme(course, lvl)),
            "guide": guide_lines(lvl["guide"]),
        },
        "music": level_music(lvl),
        "challenge": public_challenge,
        "hints": lvl["hints"],
        "reward": lvl["reward"],
        "map": level_map(course, lvl),
        "intro": lvl["intro"],
        "boss": lvl["boss"],
        "start_items": lvl["start_items"],
        "no_lesson": lvl["no_lesson"],
        "guide": lvl["guide"],
        "bugs": lvl["bugs"],
        "dark": lvl["dark"],
        "door_by_bugs": lvl["door_by_bugs"],
        "gate": lvl["gate"],
        "finale": lvl["finale"],
        "obelisk": lvl["obelisk"],
        "mimic": lvl["mimic"],
        "code_lines": lvl["code_lines"],
        "beams": list(beams or []),
        "language": language or "python",
        "level_count": len(course["levels"]),
    }
