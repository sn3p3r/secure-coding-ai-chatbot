"""
Secret achievements.

They are hidden on the profile until earned (the profile shows how
many exist and how many the player has). `evaluate()` runs after
every level completion and awards anything newly earned.
"""

from curriculum import COURSES, COURSE_ORDER
import progress as progress_db

ACHIEVEMENTS = [
    {"key": "first_blood", "title": "First Blood", "desc": "Defeat your first enemy."},
    {"key": "bug_spray", "title": "Bug Spray", "desc": "Squash 25 bugs."},
    {"key": "exterminator", "title": "Exterminator", "desc": "Defeat 100 enemies in total."},
    {"key": "boss_hunter", "title": "Boss Hunter", "desc": "Defeat every boss in the Academy: the big snake, Dr. Vex and the brain."},
    {"key": "record_holder", "title": "Record Holder", "desc": "Hold the level record on five levels at the same time."},
    {"key": "quiz_whiz", "title": "Quiz Whiz", "desc": "Pass every checkpoint quiz in the Academy."},
    {"key": "completionist", "title": "Completionist", "desc": "Complete all four courses and light all four beams."},
    {"key": "collector", "title": "Collector", "desc": "Collect every badge and every other secret achievement."},
]

BY_KEY = {a["key"]: a for a in ACHIEVEMENTS}


def _records_held(conn, user_id):
    row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return 0
    username = row["username"]
    held = 0
    for slug in COURSE_ORDER:
        for record in progress_db.level_records(conn, slug).values():
            if record["username"] == username:
                held += 1
    return held


def _quizzes_done(conn, user_id):
    total = 0
    done = 0
    for slug in COURSE_ORDER:
        completed = progress_db.course_progress(conn, user_id, slug)["completed"]
        for lvl in COURSES[slug]["levels"]:
            if lvl["kind"] == "quiz":
                total += 1
                if lvl["number"] in completed:
                    done += 1
    return done, total


def evaluate(conn, user_id):
    """Awards newly earned achievements and returns their definitions."""
    have = progress_db.get_achievements(conn, user_id)
    kills = progress_db.get_kills(conn, user_id)
    total_kills = sum(kills.values())
    finished = progress_db.finished_courses(conn, user_id)
    quizzes_done, quizzes_total = _quizzes_done(conn, user_id)

    conditions = {
        "first_blood": total_kills >= 1,
        "bug_spray": kills.get("bug", 0) >= 25,
        "exterminator": total_kills >= 100,
        "boss_hunter": all(kills.get(k, 0) >= 1 for k in ("boss", "vex", "brain")),
        "record_holder": _records_held(conn, user_id) >= 5,
        "quiz_whiz": quizzes_total > 0 and quizzes_done == quizzes_total,
        "completionist": len(finished) == len(COURSE_ORDER),
    }

    new = []
    for key, earned in conditions.items():
        if earned and key not in have:
            progress_db.award_achievement(conn, user_id, key)
            have.add(key)
            new.append(BY_KEY[key])

    others = {a["key"] for a in ACHIEVEMENTS if a["key"] != "collector"}
    if "collector" not in have and others <= have:
        progress_db.award_achievement(conn, user_id, "collector")
        have.add("collector")
        new.append(BY_KEY["collector"])

    return new


def profile_view(conn, user_id):
    """Every achievement with an `earned` flag; unearned ones stay secret in the template."""
    have = progress_db.get_achievements(conn, user_id)
    return [dict(a, earned=a["key"] in have) for a in ACHIEVEMENTS]
