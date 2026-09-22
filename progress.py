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
import sqlite3
from datetime import datetime

from curriculum import COURSES, COURSE_ORDER, get_level

# Items the game may put in the inventory (validated before saving).
ITEM_NAMES = {"HINT CHIP", "DAGGER", "CANDY", "SWORD", "DOOR CODE", "VENT KEY"}
INVENTORY_SLOTS = 5
CHECKPOINT_MAX_BYTES = 16000


# ---------------------------------------------------------
# MIGRATIONS
# ---------------------------------------------------------

def _add_column(conn, table, definition):
    """
    ALTER TABLE that stays quiet when the column already exists: the
    Flask reloader (and several gunicorn workers) can run migrate() at
    the same moment.
    """
    try:
        conn.execute("ALTER TABLE %s ADD COLUMN %s" % (table, definition))
    except sqlite3.OperationalError as error:
        if "duplicate column" not in str(error):
            raise


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
        _add_column(conn, "users", "selected_course TEXT")

    if "character" not in existing:
        _add_column(conn, "users", "character TEXT")

    if "inventory" not in existing:
        _add_column(conn, "users", "inventory TEXT")

    if "language" not in existing:
        _add_column(conn, "users", "language TEXT")

    if "website_idea" not in existing:
        _add_column(conn, "users", "website_idea TEXT")

    if "kills" not in existing:
        _add_column(conn, "users", "kills TEXT")

    if "avatar" not in existing:
        _add_column(conn, "users", "avatar TEXT")

    if "privacy" not in existing:
        _add_column(conn, "users", "privacy TEXT")

    if "time_spent" not in existing:
        _add_column(conn, "users", "time_spent INTEGER NOT NULL DEFAULT 0")

    if "last_ping" not in existing:
        _add_column(conn, "users", "last_ping REAL")

    if "prefs" not in existing:
        _add_column(conn, "users", "prefs TEXT")

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

    # Blocks: one row per "user_id blocked blocked_id".
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            user_id INTEGER NOT NULL,
            blocked_id INTEGER NOT NULL,
            created_at TIMESTAMP,
            PRIMARY KEY (user_id, blocked_id)
        )
    """)

    # Reports about another player, read by the site owner.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER NOT NULL,
            reported_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP
        )
    """)

    # Failed-login counters per username and per address.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            key TEXT PRIMARY KEY,
            attempts INTEGER NOT NULL DEFAULT 0,
            first_at REAL,
            locked_until REAL
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
               users.id AS user_id,
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

    hidden = hidden_from_boards(conn)
    records = {}
    for row in rows:
        if row["user_id"] in hidden:
            continue
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
# PRIVACY, PROFILE PICTURES, TIME SPENT
# ---------------------------------------------------------

PRIVACY_DEFAULTS = {
    "search_visible": True,             # appear in the friends search
    "profile_visibility": "everyone",   # who can open /u/<name>
    "show_progress": "everyone",        # course progress and levels done
    "show_achievements": "everyone",    # badges, beams, secret achievement count
    "show_time": "friends",             # time spent
    "leaderboard_times": True,          # times on the leaderboard and level records
}
PRIVACY_LEVELS = ("everyone", "friends", "nobody")


def clean_privacy(values, from_form=False):
    """
    Returns a full settings dict. Unknown values fall back to the
    defaults. With from_form=True a missing checkbox means "off".
    """
    cleaned = {}
    for key, default in PRIVACY_DEFAULTS.items():
        if isinstance(default, bool):
            if from_form:
                cleaned[key] = key in values
            else:
                cleaned[key] = bool(values.get(key, default))
        else:
            value = values.get(key, default)
            cleaned[key] = value if value in PRIVACY_LEVELS else default
    return cleaned


def get_privacy(conn, user_id):
    raw = _user_field(conn, user_id, "privacy")
    stored = {}
    if raw:
        try:
            stored = json.loads(raw)
        except ValueError:
            stored = {}
    return clean_privacy(stored if isinstance(stored, dict) else {})


def set_privacy(conn, user_id, values, from_form=False):
    cleaned = clean_privacy(values, from_form=from_form)
    conn.execute("UPDATE users SET privacy = ? WHERE id = ?", (json.dumps(cleaned), user_id))
    return cleaned


PREF_DEFAULTS = {
    "now_playing": True,     # faint "now playing" line in the level HUD
}


def get_prefs(conn, user_id):
    stored = _parse_json(_user_field(conn, user_id, "prefs"))
    return {key: bool(stored.get(key, default)) for key, default in PREF_DEFAULTS.items()}


def set_prefs(conn, user_id, form):
    """Checkbox form: a missing key means off."""
    prefs = {key: key in form for key in PREF_DEFAULTS}
    conn.execute("UPDATE users SET prefs = ? WHERE id = ?", (json.dumps(prefs), user_id))
    return prefs


def allowed(setting, relation):
    """Can a viewer with this relation ('self', 'friend', 'other') see it?"""
    if relation == "self" or setting == "everyone":
        return True
    if setting == "friends":
        return relation == "friend"
    return False


def relation_between(conn, viewer_id, owner_id):
    if viewer_id == owner_id:
        return "self"
    return "friend" if are_friends(conn, viewer_id, owner_id) else "other"


def hidden_from_boards(conn):
    """Ids of everyone who switched leaderboard times off."""
    hidden = set()
    for row in conn.execute("SELECT id, privacy FROM users WHERE privacy IS NOT NULL").fetchall():
        try:
            stored = json.loads(row["privacy"])
        except ValueError:
            continue
        if isinstance(stored, dict) and stored.get("leaderboard_times") is False:
            hidden.add(row["id"])
    return hidden


def get_user_by_name(conn, username):
    return conn.execute(
        "SELECT id, username, avatar, time_spent FROM users WHERE username = ?", (username,)
    ).fetchone()


def get_avatar(conn, user_id):
    """The stored picture tag ("png-1726780000": extension + upload time) or None."""
    return _user_field(conn, user_id, "avatar") or None


def set_avatar(conn, user_id, tag):
    conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (tag, user_id))


def get_time_spent(conn, user_id):
    return int(_user_field(conn, user_id, "time_spent") or 0)


PING_MAX_GAP = 120        # seconds; a longer gap is idle time, not play time
TIME_IMPORT_CAP = 100 * 3600


def add_time(conn, user_id, now, claimed=None):
    """
    Called by the browser every 30 s. Adds the real gap since the last
    ping (only when it is short). The very first ping may import the
    browser's old local counter once, capped.
    """
    row = conn.execute("SELECT time_spent, last_ping FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return 0

    total = int(row["time_spent"] or 0)
    last = row["last_ping"]

    if last is not None:
        gap = now - float(last)
        if 0 < gap <= PING_MAX_GAP:
            total += int(gap)
    elif claimed and total == 0:
        total = int(min(max(claimed, 0), TIME_IMPORT_CAP))

    conn.execute("UPDATE users SET time_spent = ?, last_ping = ? WHERE id = ?", (total, now, user_id))
    return total


# ---------------------------------------------------------
# FRIENDS (a friendship = both people added each other)
# ---------------------------------------------------------

def user_summary(conn, user_id, username, avatar=None):
    """What a friend card shows: levels, percent, beams, secret count."""
    progress = all_progress(conn, user_id)
    total = sum(p["total"] for p in progress.values())
    done = sum(p["levels_done"] for p in progress.values())
    beams = [slug for slug, p in progress.items() if p["finished"]]
    return {
        "id": user_id,
        "username": username,
        "avatar": avatar,
        "levels_done": done,
        "total": total,
        "percent": round(done / total * 100) if total else 0,
        "beams": beams,
        "secrets": len(get_achievements(conn, user_id)),
    }


def _summaries(conn, rows):
    return [user_summary(conn, row["id"], row["username"], row["avatar"]) for row in rows]


def _has_row(conn, user_id, friend_id):
    return conn.execute(
        "SELECT 1 FROM friends WHERE user_id = ? AND friend_id = ?", (user_id, friend_id)
    ).fetchone() is not None


def are_friends(conn, a, b):
    return _has_row(conn, a, b) and _has_row(conn, b, a)


def friend_state(conn, user_id, other_id):
    """'friends', 'sent' (waiting for them), 'incoming' (waiting for you) or 'none'."""
    mine = _has_row(conn, user_id, other_id)
    theirs = _has_row(conn, other_id, user_id)
    if mine and theirs:
        return "friends"
    if mine:
        return "sent"
    if theirs:
        return "incoming"
    return "none"


def friends_of(conn, user_id):
    rows = conn.execute(
        """
        SELECT users.id, users.username, users.avatar
        FROM friends AS mine
        JOIN friends AS theirs ON theirs.user_id = mine.friend_id AND theirs.friend_id = mine.user_id
        JOIN users ON users.id = mine.friend_id
        WHERE mine.user_id = ?
        ORDER BY users.username
        """,
        (user_id,),
    ).fetchall()
    return _summaries(conn, rows)


def incoming_requests(conn, user_id):
    rows = conn.execute(
        """
        SELECT users.id, users.username, users.avatar
        FROM friends
        JOIN users ON users.id = friends.user_id
        WHERE friends.friend_id = ?
          AND NOT EXISTS (
              SELECT 1 FROM friends AS mine
              WHERE mine.user_id = ? AND mine.friend_id = friends.user_id
          )
        ORDER BY friends.added_at DESC
        """,
        (user_id, user_id),
    ).fetchall()
    return _summaries(conn, rows)


def sent_requests(conn, user_id):
    rows = conn.execute(
        """
        SELECT users.id, users.username, users.avatar
        FROM friends
        JOIN users ON users.id = friends.friend_id
        WHERE friends.user_id = ?
          AND NOT EXISTS (
              SELECT 1 FROM friends AS theirs
              WHERE theirs.user_id = friends.friend_id AND theirs.friend_id = ?
          )
        ORDER BY friends.added_at DESC
        """,
        (user_id, user_id),
    ).fetchall()
    return _summaries(conn, rows)


def search_users(conn, user_id, query, limit=20):
    """
    Registered accounts whose username contains `query` (never the
    searcher, never anyone who switched search visibility off).
    """
    text = (query or "").strip()
    if not text:
        return []

    # Escape LIKE wildcards so "%" and "_" in the search mean themselves.
    pattern = "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    rows = conn.execute(
        """
        SELECT id, username, avatar, privacy FROM users
        WHERE username LIKE ? ESCAPE '\\' AND id != ?
        ORDER BY username
        LIMIT ?
        """,
        (pattern, user_id, limit * 3),
    ).fetchall()

    hidden = blocked_ids(conn, user_id)
    results = []
    for row in rows:
        if row["id"] in hidden:
            continue
        if not clean_privacy(_parse_json(row["privacy"]))["search_visible"]:
            continue
        summary = user_summary(conn, row["id"], row["username"], row["avatar"])
        summary["state"] = friend_state(conn, user_id, row["id"])
        results.append(summary)
        if len(results) == limit:
            break
    return results


def _parse_json(raw):
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def add_friend(conn, user_id, friend_id):
    """
    Records "user_id wants friend_id". Returns "self", "missing",
    "friends" (they had already added you - you are friends now) or
    "sent" (a request is waiting for them). Repeats are harmless.
    """
    if friend_id == user_id:
        return "self"
    if conn.execute("SELECT 1 FROM users WHERE id = ?", (friend_id,)).fetchone() is None:
        return "missing"
    if is_blocked(conn, user_id, friend_id):
        return "blocked"
    conn.execute(
        "INSERT OR IGNORE INTO friends (user_id, friend_id, added_at) VALUES (?, ?, ?)",
        (user_id, friend_id, datetime.utcnow().isoformat(timespec="seconds")),
    )
    return "friends" if _has_row(conn, friend_id, user_id) else "sent"


def decline_request(conn, user_id, other_id):
    """Drops the other person's request to you."""
    conn.execute("DELETE FROM friends WHERE user_id = ? AND friend_id = ?", (other_id, user_id))


def remove_friend(conn, user_id, other_id):
    """Ends a friendship, or cancels a request you sent."""
    conn.execute(
        "DELETE FROM friends WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)",
        (user_id, other_id, other_id, user_id),
    )


# ---------------------------------------------------------
# LEADERBOARD TIMES
# ---------------------------------------------------------

def level_times(conn, course_slug, level_number, descending=False, viewer_id=None, only_ids=None):
    """
    Every player's best time on one level, minus those who opted out,
    minus anyone blocked either way by the viewer, and limited to
    `only_ids` when given (the friends-only view).
    """
    rows = conn.execute(
        """
        SELECT users.id AS user_id, users.username AS username, users.avatar AS avatar,
               level_progress.best_time_seconds AS seconds,
               level_progress.completed_at AS completed_at
        FROM level_progress
        JOIN users ON users.id = level_progress.user_id
        WHERE level_progress.course = ?
          AND level_progress.level_number = ?
          AND level_progress.completed = 1
          AND level_progress.best_time_seconds IS NOT NULL
        ORDER BY level_progress.best_time_seconds %s, level_progress.completed_at ASC
        """ % ("DESC" if descending else "ASC"),
        (course_slug, level_number),
    ).fetchall()

    hidden = hidden_from_boards(conn)
    if viewer_id is not None:
        hidden |= blocked_ids(conn, viewer_id)
    return [
        {
            "user_id": row["user_id"],
            "username": row["username"],
            "avatar": row["avatar"],
            "seconds": row["seconds"],
            "completed_at": (row["completed_at"] or "")[:10],
        }
        for row in rows
        if row["user_id"] not in hidden and (only_ids is None or row["user_id"] in only_ids)
    ]


def time_ranking(conn, viewer_id, limit=25):
    """
    Who has spent the most time in the Academy, as this viewer may see
    it: people who switched leaderboard times off are skipped, "friends"
    time visibility needs a friendship, "nobody" shows only to its owner,
    and blocked pairs never see each other.
    """
    rows = conn.execute(
        """
        SELECT id, username, avatar, time_spent, privacy FROM users
        WHERE time_spent > 0
        ORDER BY time_spent DESC, username ASC
        """
    ).fetchall()

    hidden = blocked_ids(conn, viewer_id)
    friends = {person["id"] for person in friends_of(conn, viewer_id)}
    ranking = []

    for row in rows:
        if row["id"] in hidden:
            continue
        settings = clean_privacy(_parse_json(row["privacy"]))
        relation = "self" if row["id"] == viewer_id else ("friend" if row["id"] in friends else "other")
        if relation != "self" and not settings["leaderboard_times"]:
            continue
        if not allowed(settings["show_time"], relation):
            continue
        ranking.append({
            "user_id": row["id"],
            "username": row["username"],
            "avatar": row["avatar"],
            "seconds": int(row["time_spent"] or 0),
        })
        if len(ranking) == limit:
            break

    return ranking


# ---------------------------------------------------------
# BLOCKS AND REPORTS
# ---------------------------------------------------------

REPORT_REASONS = ("spam", "harassment", "inappropriate name or picture", "cheating", "other")


def is_blocked(conn, a, b):
    """True when either person blocked the other."""
    return conn.execute(
        "SELECT 1 FROM blocks WHERE (user_id = ? AND blocked_id = ?) OR (user_id = ? AND blocked_id = ?)",
        (a, b, b, a),
    ).fetchone() is not None


def blocked_by_me(conn, user_id, other_id):
    return conn.execute(
        "SELECT 1 FROM blocks WHERE user_id = ? AND blocked_id = ?", (user_id, other_id)
    ).fetchone() is not None


def blocked_ids(conn, user_id):
    """Everyone this user blocked or was blocked by."""
    ids = set()
    for row in conn.execute(
        "SELECT user_id, blocked_id FROM blocks WHERE user_id = ? OR blocked_id = ?", (user_id, user_id)
    ).fetchall():
        ids.add(row["blocked_id"] if row["user_id"] == user_id else row["user_id"])
    return ids


def block_user(conn, user_id, other_id):
    """Blocking also ends any friendship or pending request between the two."""
    if other_id == user_id:
        return "self"
    if conn.execute("SELECT 1 FROM users WHERE id = ?", (other_id,)).fetchone() is None:
        return "missing"
    conn.execute(
        "INSERT OR IGNORE INTO blocks (user_id, blocked_id, created_at) VALUES (?, ?, ?)",
        (user_id, other_id, datetime.utcnow().isoformat(timespec="seconds")),
    )
    remove_friend(conn, user_id, other_id)
    return "ok"


def unblock_user(conn, user_id, other_id):
    conn.execute("DELETE FROM blocks WHERE user_id = ? AND blocked_id = ?", (user_id, other_id))


def blocked_users(conn, user_id):
    rows = conn.execute(
        """
        SELECT users.id, users.username, users.avatar
        FROM blocks JOIN users ON users.id = blocks.blocked_id
        WHERE blocks.user_id = ?
        ORDER BY users.username
        """,
        (user_id,),
    ).fetchall()
    return _summaries(conn, rows)


def add_report(conn, reporter_id, reported_id, reason, note):
    """Returns False for an unknown reason or a note that is too long."""
    if reason not in REPORT_REASONS or reporter_id == reported_id:
        return False
    note = (note or "").strip()
    if len(note) > 300:
        return False
    conn.execute(
        "INSERT INTO reports (reporter_id, reported_id, reason, note, created_at) VALUES (?, ?, ?, ?, ?)",
        (reporter_id, reported_id, reason, note, datetime.utcnow().isoformat(timespec="seconds")),
    )
    return True


def pending_request_count(conn, user_id):
    row = conn.execute(
        """
        SELECT COUNT(*) AS n FROM friends
        WHERE friends.friend_id = ?
          AND NOT EXISTS (
              SELECT 1 FROM friends AS mine
              WHERE mine.user_id = ? AND mine.friend_id = friends.user_id
          )
        """,
        (user_id, user_id),
    ).fetchone()
    return row["n"] if row else 0


# ---------------------------------------------------------
# LOGIN RATE LIMITING
# ---------------------------------------------------------

# kind: (failed attempts allowed, counting window, lock length) in seconds
LOGIN_LIMITS = {
    "user": (10, 5 * 60, 5 * 60),      # ten wrong passwords for one username within five minutes
    "ip": (150, 15 * 60, 15 * 60),     # everything from one address (shared school networks are large)
}


def login_lock_remaining(conn, key, now):
    """Seconds until this key may try again, or 0."""
    row = conn.execute("SELECT locked_until FROM login_attempts WHERE key = ?", (key,)).fetchone()
    if row and row["locked_until"] and row["locked_until"] > now:
        return int(row["locked_until"] - now) + 1
    return 0


def login_failed(conn, key, kind, now):
    """Counts one failure; returns the lock length in seconds when the limit is hit."""
    limit, window, lock = LOGIN_LIMITS[kind]
    row = conn.execute("SELECT attempts, first_at FROM login_attempts WHERE key = ?", (key,)).fetchone()

    if row and row["first_at"] and now - row["first_at"] <= window:
        attempts = row["attempts"] + 1
        first_at = row["first_at"]
    else:
        attempts = 1
        first_at = now

    locked_until = now + lock if attempts >= limit else None
    conn.execute(
        """
        INSERT INTO login_attempts (key, attempts, first_at, locked_until) VALUES (?, ?, ?, ?)
        ON CONFLICT (key) DO UPDATE SET attempts = excluded.attempts,
                                       first_at = excluded.first_at,
                                       locked_until = excluded.locked_until
        """,
        (key, attempts, first_at, locked_until),
    )
    return lock if locked_until else 0


def login_succeeded(conn, key):
    conn.execute("DELETE FROM login_attempts WHERE key = ?", (key,))


# ---------------------------------------------------------
# ACCOUNT
# ---------------------------------------------------------

def set_password_hash(conn, user_id, password_hash):
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))


def delete_user(conn, user_id):
    """Removes the account and everything that points at it."""
    for table, column in (
        ("level_progress", "user_id"),
        ("level_checkpoints", "user_id"),
        ("achievements", "user_id"),
        ("reports", "reporter_id"),
    ):
        conn.execute("DELETE FROM %s WHERE %s = ?" % (table, column), (user_id,))
    conn.execute("DELETE FROM friends WHERE user_id = ? OR friend_id = ?", (user_id, user_id))
    conn.execute("DELETE FROM blocks WHERE user_id = ? OR blocked_id = ?", (user_id, user_id))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
