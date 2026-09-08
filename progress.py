"""
Progress persistence for Cyber Academy.

All functions take an open sqlite3 connection (from app.get_db)
and never commit on their own except where noted, so the caller
controls the transaction.

Schema additions (all backward compatible):

    users.selected_course  TEXT   - the course the player is currently in
    users.character        TEXT   - JSON for the pixel character

    level_progress
        user_id, course, level_number, completed, attempts,
        best_time_seconds, completed_at
"""

import json
from datetime import datetime

from curriculum import COURSES, COURSE_ORDER


# ---------------------------------------------------------
# MIGRATIONS
# ---------------------------------------------------------

def migrate(conn):
    """Create new tables / columns if they do not exist yet."""

    conn.execute("""
        CREATE TABLE IF NOT EXISTS level_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course TEXT NOT NULL,
            level_number INTEGER NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 0,
            best_time_seconds INTEGER,
            completed_at TIMESTAMP,
            UNIQUE (user_id, course, level_number),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(users)").fetchall()
    }

    if "selected_course" not in existing:
        conn.execute("ALTER TABLE users ADD COLUMN selected_course TEXT")

    if "character" not in existing:
        conn.execute("ALTER TABLE users ADD COLUMN character TEXT")

    conn.commit()


# ---------------------------------------------------------
# READ
# ---------------------------------------------------------

def course_progress(conn, user_id, course_slug):
    """
    Returns a dict describing where the player is in one course:

        completed   set of completed level numbers
        current     number of the next unfinished level (or last level)
        percent     0-100
        total       number of levels
        finished    True when every level is done
        times       {level_number: best_time_seconds}
    """
    course = COURSES[course_slug]
    total = len(course["levels"])

    rows = conn.execute(
        """
        SELECT level_number, completed, best_time_seconds
        FROM level_progress
        WHERE user_id = ? AND course = ?
        """,
        (user_id, course_slug),
    ).fetchall()

    completed = {row["level_number"] for row in rows if row["completed"]}
    times = {
        row["level_number"]: row["best_time_seconds"]
        for row in rows
        if row["completed"] and row["best_time_seconds"] is not None
    }

    current = total
    for number in range(1, total + 1):
        if number not in completed:
            current = number
            break

    return {
        "completed": completed,
        "current": current,
        "percent": round(len(completed) / total * 100) if total else 0,
        "total": total,
        "finished": len(completed) == total,
        "times": times,
        "levels_done": len(completed),
    }


def all_progress(conn, user_id):
    """{course_slug: course_progress(...)} for every course, in display order."""
    return {slug: course_progress(conn, user_id, slug) for slug in COURSE_ORDER}


def is_unlocked(conn, user_id, course_slug, level_number):
    """Level 1 is always open; others need the previous level completed."""
    if level_number == 1:
        return True

    row = conn.execute(
        """
        SELECT completed FROM level_progress
        WHERE user_id = ? AND course = ? AND level_number = ?
        """,
        (user_id, course_slug, level_number - 1),
    ).fetchone()

    return bool(row and row["completed"])


def get_character(conn, user_id):
    row = conn.execute(
        "SELECT character FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    if not row or not row["character"]:
        return None

    try:
        return json.loads(row["character"])
    except ValueError:
        return None


# ---------------------------------------------------------
# WRITE
# ---------------------------------------------------------

def record_attempt(conn, user_id, course_slug, level_number):
    conn.execute(
        """
        INSERT INTO level_progress (user_id, course, level_number, attempts)
        VALUES (?, ?, ?, 1)
        ON CONFLICT (user_id, course, level_number)
        DO UPDATE SET attempts = attempts + 1
        """,
        (user_id, course_slug, level_number),
    )


def record_completion(conn, user_id, course_slug, level_number, seconds):
    """Marks a level done and keeps the best (lowest) time."""
    conn.execute(
        """
        INSERT INTO level_progress
            (user_id, course, level_number, completed, attempts,
             best_time_seconds, completed_at)
        VALUES (?, ?, ?, 1, 1, ?, ?)
        ON CONFLICT (user_id, course, level_number)
        DO UPDATE SET
            completed = 1,
            attempts = attempts + 1,
            best_time_seconds = CASE
                WHEN best_time_seconds IS NULL THEN excluded.best_time_seconds
                WHEN excluded.best_time_seconds IS NULL THEN best_time_seconds
                ELSE MIN(best_time_seconds, excluded.best_time_seconds)
            END,
            completed_at = COALESCE(completed_at, excluded.completed_at)
        """,
        (user_id, course_slug, level_number, seconds, datetime.utcnow().isoformat(timespec="seconds")),
    )


def set_selected_course(conn, user_id, course_slug):
    conn.execute(
        "UPDATE users SET selected_course = ? WHERE id = ?",
        (course_slug, user_id),
    )


def set_character(conn, user_id, character):
    conn.execute(
        "UPDATE users SET character = ? WHERE id = ?",
        (json.dumps(character), user_id),
    )


def badge_collection(conn, user_id):
    """
    Every badge in every course, marked earned or not, for the profile:
    [{"course": course, "earned": n, "badges": [{name, title, number, earned, master, kind}]}]
    """
    collection = []
    for slug in COURSE_ORDER:
        course = COURSES[slug]
        completed = course_progress(conn, user_id, slug)["completed"]
        badges = []
        for lvl in course["levels"]:
            badges.append({
                "number": lvl["number"],
                "title": lvl["title"],
                "name": lvl["reward"].split(" + ")[0],
                "earned": lvl["number"] in completed,
                "master": lvl["number"] == len(course["levels"]),
                "kind": lvl["kind"],
            })
        collection.append({
            "course": course,
            "badges": badges,
            "earned": sum(1 for b in badges if b["earned"]),
        })
    return collection


# ---------------------------------------------------------
# LEADERBOARD
# ---------------------------------------------------------

def leaderboard(conn, course_slug, limit=10):
    """
    Top players for a course: most levels completed first,
    then lowest total best time.
    """
    rows = conn.execute(
        """
        SELECT
            users.username AS username,
            COUNT(*) AS levels_done,
            SUM(level_progress.best_time_seconds) AS total_seconds
        FROM level_progress
        JOIN users ON users.id = level_progress.user_id
        WHERE level_progress.course = ? AND level_progress.completed = 1
        GROUP BY level_progress.user_id
        ORDER BY levels_done DESC, total_seconds ASC
        LIMIT ?
        """,
        (course_slug, limit),
    ).fetchall()

    return [
        {
            "username": row["username"],
            "levels_done": row["levels_done"],
            "total_seconds": row["total_seconds"] or 0,
        }
        for row in rows
    ]
