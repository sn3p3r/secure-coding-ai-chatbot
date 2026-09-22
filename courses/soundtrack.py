"""
Which track plays on which level.

Keys are the names in curriculum.MUSIC:
    ossuary     "Ossuary 1 - A Beginning"  - beginnings, quiet fights, every obelisk (looped)
    venus       "Vibing Over Venus"        - calm levels with nothing to fight
    samba       "Blobby Samba"             - levels where you fight bugs / viruses
    cretaceous  "Cretaceous Dawn"          - the moment a boss shows up (looped)
    rhino       "Rhinoceros"               - the first time you enter a course's lab (one level per course)

Edit the tables below to move a track; a level not listed here falls
back to the rule in `track_for()`. Nothing else needs to change.
"""

LEVEL_MUSIC = {
    "python": {
        1: "ossuary", 2: "venus", 3: "venus", 4: "ossuary",
        6: "samba", 7: "ossuary", 8: "samba", 9: "ossuary",
        11: "samba", 12: "samba", 13: "ossuary", 15: "samba", 16: "samba",
        17: "ossuary",                      # the big snake: Cretaceous Dawn takes over when it appears
        19: "samba", 20: "ossuary", 21: "samba", 22: "ossuary",
        24: "samba", 25: "ossuary", 26: "samba", 27: "ossuary", 29: "samba",
    },
    "cybersecurity": {
        1: "venus", 2: "samba", 3: "samba", 4: "ossuary", 5: "samba", 6: "samba",
        8: "ossuary", 9: "samba", 10: "venus", 11: "samba",
        13: "ossuary", 14: "samba", 15: "samba",
        16: "ossuary", 17: "ossuary",       # Dr. Vex and the brain: Cretaceous Dawn on spawn
    },
    "internet": {
        1: "ossuary", 2: "venus", 3: "venus", 4: "ossuary", 5: "venus", 7: "venus",
        8: "ossuary", 9: "samba", 11: "ossuary", 12: "venus", 13: "venus", 14: "ossuary", 15: "venus",
    },
    "secure-coding": {
        1: "venus", 2: "ossuary", 3: "samba", 4: "venus", 5: "ossuary", 6: "samba",
    },
}

BOSS_MUSIC = "cretaceous"

# The first level of each course's "lab": the white lab, the Python lab,
# the desk behind the HDMI port, the editor database.
LAB_ENTRANCE = {"python": 11, "cybersecurity": 4, "internet": 12, "secure-coding": 1}


def track_for(course_slug, lvl):
    """The level's track: the table first, then a rule based on the map."""
    if lvl.get("music"):
        return lvl["music"]
    if lvl["kind"] == "quiz":
        return None

    if LAB_ENTRANCE.get(course_slug) == lvl["number"]:
        return "rhino"

    listed = LEVEL_MUSIC.get(course_slug, {}).get(lvl["number"])
    if listed:
        return listed
    if lvl.get("obelisk") or lvl.get("boss"):
        return "ossuary"

    rows = lvl.get("map") or []
    bugs = sum(row.count(ch) for row in rows for ch in "cb")
    others = sum(row.count(ch) for row in rows for ch in "shz")
    if bugs:
        return "samba"
    if not others:
        return "venus"
    return "ossuary"


def boss_track_for(lvl):
    if lvl["kind"] == "quiz" or not lvl.get("boss"):
        return None
    return lvl.get("boss_music") or BOSS_MUSIC
