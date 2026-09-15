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

from curriculum import COURSES, COURSE_ORDER, get_level

# Items the game may put in the inventory (validated before saving).
ITEM_NAMES = {"HINT CHIP", "DAGGER", "CANDY", "SWORD", "DOOR CODE", "VENT KEY"}
INVENTORY_SLOTS = 5
CHECKPOINT_MAX_BYTES = 16000


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

    if "inventory" not in existing:
        conn.execute("ALTER TABLE users ADD COLUMN inventory TEXT")

    if "language" not in existing:
        conn.execute("ALTER TABLE users ADD COLUMN language TEXT")

    if "website_idea" not in existing:
        conn.execute("ALTER TABLE users ADD COLUMN website_idea TEXT")

    if "kills" not in existing:
        conn.execute("ALTER TABLE users ADD COLUMN kills TEXT")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            earned_at TIMESTAMP,
            PRIMARY KEY (user_id, key)
        )
    """)

    # Friends: one row per "user_id added friend_id".
    conn.execute("""
        CREATE TABLE IF NOT EXISTS friends (
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            added_at TIMESTAMP,
            PRIMARY KEY (user_id, friend_id)
        )
    """)

    # Mid-level saves: written every time the player passes a door.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS level_checkpoints (
            user_id INTEGER NOT NULL,
            course TEXT NOT NULL,
            level_number INTEGER NOT NULL,
            data TEXT NOT NULL,
            elapsed INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP,
            PRIMARY KEY (user_id, course, level_number)
        )
    """)

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
    """
    Level 1 is always open; others need the previous level completed.
    Checkpoint quizzes are always open - they are a study tool - but
    the level after a quiz still needs the quiz passed.
    """
    if level_number == 1:
        return True

    lvl = get_level(course_slug, level_number)
    if lvl is not None and lvl["kind"] == "quiz":
        return True

    row = conn.execute(
        """
        SELECT completed FROM level_progress
        WHERE user_id = ? AND course = ? AND level_number = ?
        """,
        (user_id, course_slug, level_number - 1),
    ).fetchone()

    return bool(row and row["completed"])


def _all_inventories(conn, user_id):
    """{course_slug: [slots]} - one inventory per course, never shared."""
    row = conn.execute(
        "SELECT inventory FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    if not row or not row["inventory"]:
        return {}

    try:
        stored = json.loads(row["inventory"])
    except ValueError:
        return {}

    # Older saves held a single list, which belonged to the Python course.
    if isinstance(stored, list):
        return {"python": stored}

    return stored if isinstance(stored, dict) else {}


def get_inventory(conn, user_id, course_slug):
    """Saved inventory for one course as a list of slot values, or None if never saved."""
    items = _all_inventories(conn, user_id).get(course_slug)
    if items is None:
        return None
    return clean_inventory(items)


def clean_inventory(items):
    """Keeps only known item names, padded/trimmed to the slot count."""
    if not isinstance(items, list):
        return None

    cleaned = [item if item in ITEM_NAMES else None for item in items[:INVENTORY_SLOTS]]
    cleaned += [None] * (INVENTORY_SLOTS - len(cleaned))
    return cleaned


def set_inventory(conn, user_id, course_slug, items):
    inventories = _all_inventories(conn, user_id)
    inventories[course_slug] = items
    conn.execute(
        "UPDATE users SET inventory = ? WHERE id = ?",
        (json.dumps(inventories), user_id),
    )


# ---------------------------------------------------------
# PER-USER SETTINGS AND COUNTERS
# ---------------------------------------------------------

def _user_field(conn, user_id, column):
    row = conn.execute("SELECT %s AS value FROM users WHERE id = ?" % column, (user_id,)).fetchone()
    return row["value"] if row else None


def get_language(conn, user_id):
    value = _user_field(conn, user_id, "language")
    return value if value in ("python", "javascript") else None


def set_language(conn, user_id, language):
    conn.execute("UPDATE users SET language = ? WHERE id = ?", (language, user_id))


def get_idea(conn, user_id):
    raw = _user_field(conn, user_id, "website_idea")
    if not raw:
        return None
    try:
        idea = json.loads(raw)
    except ValueError:
        return None
    return idea if isinstance(idea, dict) else None


def set_idea(conn, user_id, idea):
    conn.execute("UPDATE users SET website_idea = ? WHERE id = ?", (json.dumps(idea), user_id))


def get_kills(conn, user_id):
    raw = _user_field(conn, user_id, "kills")
    if not raw:
        return {}
    try:
        kills = json.loads(raw)
    except ValueError:
        return {}
    return kills if isinstance(kills, dict) else {}


KILL_TYPES = {"snake", "hostile", "bug", "sniffer", "boss", "vex", "brain"}


def add_kills(conn, user_id, delta):
    """Adds a {type: count} delta from the game; ignores anything odd."""
    if not isinstance(delta, dict):
        return
    kills = get_kills(conn, user_id)
    changed = False
    for kind, count in delta.items():
        if kind in KILL_TYPES and isinstance(count, int) and not isinstance(count, bool) and 0 < count <= 500:
            kills[kind] = kills.get(kind, 0) + count
            changed = True
    if changed:
        conn.execute("UPDATE users SET kills = ? WHERE id = ?", (json.dumps(kills), user_id))


def finished_courses(conn, user_id):
    """Slugs of every course the player has completed, in display order."""
    return [slug for slug in COURSE_ORDER if course_progress(conn, user_id, slug)["finished"]]


def get_achievements(conn, user_id):
    rows = conn.execute("SELECT key FROM achievements WHERE user_id = ?", (user_id,)).fetchall()
    return {row["key"] for row in rows}


def award_achievement(conn, user_id, key):
    conn.execute(
        "INSERT OR IGNORE INTO achievements (user_id, key, earned_at) VALUES (?, ?, ?)",
        (user_id, key, datetime.utcnow().isoformat(timespec="seconds")),
    )


# ---------------------------------------------------------
# CHECKPOINTS (saved when the player passes a door)
# ---------------------------------------------------------

def get_checkpoint(conn, user_id, course_slug, level_number):
    row = conn.execute(
        """
        SELECT data, elapsed FROM level_checkpoints
        WHERE user_id = ? AND course = ? AND level_number = ?
        """,
        (user_id, course_slug, level_number),
    ).fetchone()

    if not row:
        return None

    try:
        data = json.loads(row["data"])
    except ValueError:
        return None

    if not isinstance(data, dict):
        return None

    return {"data": data, "elapsed": row["elapsed"]}


def set_checkpoint(conn, user_id, course_slug, level_number, data, elapsed):
    """Returns False when the payload is not a reasonably small dict."""
    if not isinstance(data, dict):
        return False

    encoded = json.dumps(data)
    if len(encoded) > CHECKPOINT_MAX_BYTES:
        return False

    conn.execute(
        """
        INSERT INTO level_checkpoints (user_id, course, level_number, data, elapsed, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT (user_id, course, level_number)
        DO UPDATE SET data = excluded.data, elapsed = excluded.elapsed, updated_at = excluded.updated_at
        """,
        (user_id, course_slug, level_number, encoded, int(elapsed or 0),
         datetime.utcnow().isoformat(timespec="seconds")),
    )
    return True


def clear_checkpoint(conn, user_id, course_slug, level_number):
    conn.execute(
        "DELETE FROM level_checkpoints WHERE user_id = ? AND course = ? AND level_number = ?",
        (user_id, course_slug, level_number),
    )


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

def level_records(conn, course_slug):
    """
    The fastest recorded time for every level of a course:
    {level_number: {"seconds": s, "username": who}}. Ties go to
    whoever set the time first.
    """
    rows = conn.execute(
        """
        SELECT level_progress.level_number AS level_number,
               level_progress.best_time_seconds AS seconds,
               users.username AS username
        FROM level_progress
        JOIN users ON users.id = level_progress.user_id
        WHERE level_progress.course = ?
          AND level_progress.completed = 1
          AND level_progress.best_time_seconds IS NOT NULL
        ORDER BY level_progress.level_number ASC,
                 level_progress.best_time_seconds ASC,
                 level_progress.completed_at ASC
        """,
        (course_slug,),
    ).fetchall()

    records = {}
    for row in rows:
        if row["level_number"] not in records:
            records[row["level_number"]] = {"seconds": row["seconds"], "username": row["username"]}
    return records


def progress_ranking(conn, course_slug, limit=5):
    """Who has completed the most levels of a course."""
    rows = conn.execute(
        """
        SELECT users.username AS username, COUNT(*) AS levels_done
        FROM level_progress
        JOIN users ON users.id = level_progress.user_id
        WHERE level_progress.course = ? AND level_progress.completed = 1
        GROUP BY level_progress.user_id
        ORDER BY levels_done DESC, MAX(level_progress.completed_at) ASC
        LIMIT ?
        """,
        (course_slug, limit),
    ).fetchall()

    return [{"username": row["username"], "levels_done": row["levels_done"]} for row in rows]


# ---------------------------------------------------------
# FRIENDS
# ---------------------------------------------------------

def user_summary(conn, user_id, username):
    """What a friend card shows: levels, percent, beams, secret count."""
    progress = all_progress(conn, user_id)
    total = sum(p["total"] for p in progress.values())
    done = sum(p["levels_done"] for p in progress.values())
    beams = [slug for slug, p in progress.items() if p["finished"]]
    return {
        "id": user_id,
        "username": username,
        "levels_done": done,
        "total": total,
        "percent": round(done / total * 100) if total else 0,
        "beams": beams,
        "secrets": len(get_achievements(conn, user_id)),
    }


def friend_ids(conn, user_id):
    return {
        row["friend_id"]
        for row in conn.execute("SELECT friend_id FROM friends WHERE user_id = ?", (user_id,)).fetchall()
    }


def search_users(conn, user_id, query, limit=20):
    """Registered accounts whose username contains `query` (not the searcher)."""
    text = (query or "").strip()
    if not text:
        return []

    # Escape LIKE wildcards so "%" and "_" in the search mean themselves.
    pattern = "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    rows = conn.execute(
        """
        SELECT id, username FROM users
        WHERE username LIKE ? ESCAPE '\\' AND id != ?
        ORDER BY username
        LIMIT ?
        """,
        (pattern, user_id, limit),
    ).fetchall()

    added = friend_ids(conn, user_id)
    results = []
    for row in rows:
        summary = user_summary(conn, row["id"], row["username"])
        summary["added"] = row["id"] in added
        results.append(summary)
    return results


def friends_of(conn, user_id):
    rows = conn.execute(
        """
        SELECT users.id, users.username FROM friends
        JOIN users ON users.id = friends.friend_id
        WHERE friends.user_id = ?
        ORDER BY users.username
        """,
        (user_id,),
    ).fetchall()
    return [user_summary(conn, row["id"], row["username"]) for row in rows]


def add_friend(conn, user_id, friend_id):
    """Returns "self", "missing" or "ok". Adding twice is harmless."""
    if friend_id == user_id:
        return "self"
    if conn.execute("SELECT 1 FROM users WHERE id = ?", (friend_id,)).fetchone() is None:
        return "missing"
    conn.execute(
        "INSERT OR IGNORE INTO friends (user_id, friend_id, added_at) VALUES (?, ?, ?)",
        (user_id, friend_id, datetime.utcnow().isoformat(timespec="seconds")),
    )
    return "ok"


def remove_friend(conn, user_id, friend_id):
    conn.execute("DELETE FROM friends WHERE user_id = ? AND friend_id = ?", (user_id, friend_id))
