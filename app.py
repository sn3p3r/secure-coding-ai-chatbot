from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
import math
import io
import os
import re
import time
from collections import Counter

from dotenv import load_dotenv

from curriculum import COURSES, COURSE_ORDER, QUIZ_TO_COURSE, get_course, get_level, public_level, course_sections, mentor_briefing, resolve_challenge, music_credits
from challenges import check_answer, leaks_answer, swipe_card_verdict
import progress as progress_db
import achievements

IDEAS_FILE = os.getenv("ACADEMY_IDEAS_FILE", os.path.join("data", "website_ideas.jsonl"))

load_dotenv()

# SecureMentor is optional: the game must stay playable without it.
try:
    from mentor import ask_mentor, mentor_available, mentor_status
except ImportError as import_error:
    print("SecureMentor disabled:", import_error)
    ask_mentor = None

    def mentor_available():
        return False

    def mentor_status():
        return {"configured": False, "reachable": False, "detail": "The anthropic package is not installed."}

app = Flask(__name__)

# Used to keep users logged in.
# Set SECRET_KEY in .env for deployment; the fallback is for local development only.
app.secret_key = os.getenv("SECRET_KEY", "change-this-to-a-random-secret-key")

if not os.getenv("SECRET_KEY"):
    print("WARNING: SECRET_KEY is not set in .env - using the development fallback. "
          "Generate one before deploying (see the README).")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# ACADEMY_DB lets a deployment keep the database on a persistent disk.
DATABASE = os.getenv("ACADEMY_DB", "academy.db")

# Profile pictures live next to the database, never in git.
AVATAR_DIR = os.getenv("ACADEMY_AVATARS_DIR", os.path.join("data", "avatars"))
AVATAR_MAX_BYTES = 2 * 1024 * 1024
AVATAR_TYPES = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}

# Requests bigger than this are refused before any view runs.
app.config["MAX_CONTENT_LENGTH"] = AVATAR_MAX_BYTES + 256 * 1024

# Uploaded pictures are shrunk to this square (PNG) when Pillow is installed.
AVATAR_SIZE = 256

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
except ImportError:  # the game still works; pictures are then stored as uploaded
    Image = None

# Reports about players are also appended here for the site owner.
REPORTS_FILE = os.getenv("ACADEMY_REPORTS_FILE", os.path.join("data", "reports.jsonl"))

# Browsers want audio/mp4 for .m4a; Python's guess is audio/mp4a-latm.
import mimetypes
mimetypes.add_type("audio/mp4", ".m4a")

# Usernames: plain letters, digits and underscores, 3 to 20 long.
USERNAME_RE = re.compile(r"[A-Za-z0-9_]{3,20}")

# Allowed values for the pixel character (validated server-side).
CHARACTER_OPTIONS = {
    "gender": ["male", "female", "nonbinary"],
    "hair": ["short", "long", "spiky", "buzz"],
    "hair_color": ["black", "brown", "blonde", "red", "blue", "green"],
    "outfit": ["dark", "grey", "green", "blue"],
}


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            quiz_completed INTEGER DEFAULT 0,
            recommended_course TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Adds the progress table and new user columns if missing.
    progress_db.migrate(conn)

    conn.close()


# ---------------------------------------------------------
# ACCOUNT CONTEXT (top bar avatar + time, on every page)
# ---------------------------------------------------------

def avatar_url_for(user_id, tag):
    """URL of a stored picture; the tag doubles as a cache-buster."""
    if not tag:
        return None
    return url_for("avatar", user_id=user_id) + "?v=" + tag


@app.context_processor
def inject_credits():
    return {"music_credits": music_credits()}


@app.context_processor
def inject_account():
    if "user_id" not in session:
        return {}

    conn = get_db()
    row = conn.execute(
        "SELECT id, username, avatar, time_spent FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    pending = progress_db.pending_request_count(conn, session["user_id"]) if row else 0
    conn.close()

    if row is None:
        return {}

    return {
        "username": row["username"],
        "me": row["id"],
        "avatar_url": avatar_url_for(row["id"], row["avatar"]),
        "time_spent": int(row["time_spent"] or 0),
        "pending_requests": pending,
    }


def shrink_picture(data):
    """
    Returns (png_bytes, "png") for a picture cut to a centred
    AVATAR_SIZE square, or None when the bytes are not a readable image.
    Without Pillow the original bytes are kept.
    """
    extension = sniff_image(data[:16])
    if extension is None:
        return None

    if Image is None:
        return data, extension

    try:
        with Image.open(io.BytesIO(data)) as picture:
            picture.load()
            picture = ImageOps.exif_transpose(picture)
            picture = picture.convert("RGBA")
            picture = ImageOps.fit(picture, (AVATAR_SIZE, AVATAR_SIZE), method=Image.Resampling.LANCZOS)
            output = io.BytesIO()
            picture.save(output, format="PNG", optimize=True)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        return None

    return output.getvalue(), "png"


def sniff_image(head):
    """Image type from the first bytes - the file name is never trusted."""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def avatar_path(user_id, tag):
    return os.path.join(AVATAR_DIR, "%d.%s" % (user_id, tag.split("-")[0]))


def delete_avatar_files(user_id):
    for extension in AVATAR_TYPES:
        path = os.path.join(AVATAR_DIR, "%d.%s" % (user_id, extension))
        if os.path.isfile(path):
            os.remove(path)


# ---------------------------------------------------------
# PASSWORD RULES
# ---------------------------------------------------------

def password_problem(password):
    """The sign-up rule a password breaks, or None when it is acceptable."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(char.isupper() for char in password):
        return "Password must contain an uppercase letter."
    if not any(char.islower() for char in password):
        return "Password must contain a lowercase letter."
    if not any(char.isdigit() for char in password):
        return "Password must contain a number."
    if not any(not char.isalnum() for char in password):
        return "Password must contain a special character."
    if calculate_entropy(password) < 3.5:
        return "Password entropy must be at least 3.5 bits per character."
    return None


def client_address():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()[:64]

def calculate_entropy(text):
    """
    Calculate Shannon entropy in bits per character.
    """
    if not text:
        return 0.0

    counts = Counter(text)
    total = len(text)

    entropy = 0.0

    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log2(probability)

    return entropy


# ---------------------------------------------------------
# LOGIN HELPER
# ---------------------------------------------------------

def login_required(route_function):
    @wraps(route_function)
    def wrapped_route(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapped_route


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template(
                "login.html",
                error="Please enter both your username and password."
            )

        conn = get_db()

        # Too many wrong passwords lock this username (from this address)
        # for a few minutes; a flood from one address locks the address.
        now = time.time()
        address = client_address()
        keys = {"user": "user:%s|%s" % (address, username.lower()), "ip": "ip:" + address}

        wait = max(progress_db.login_lock_remaining(conn, key, now) for key in keys.values())
        if wait:
            conn.close()
            return render_template(
                "login.html",
                error="Too many attempts. Try again in %d minute%s." % ((wait + 59) // 60, "" if wait <= 60 else "s")
            )

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            locked = max(progress_db.login_failed(conn, key, kind, now) for kind, key in keys.items())
            conn.commit()
            conn.close()
            if locked:
                return render_template(
                    "login.html",
                    error="Too many attempts. Try again in %d minutes." % ((locked + 59) // 60)
                )
            return render_template(
                "login.html",
                error="Username or password is incorrect."
            )

        for key in keys.values():
            progress_db.login_succeeded(conn, key)
        conn.commit()
        conn.close()

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return redirect(url_for("home"))

    return render_template("login.html")


# ---------------------------------------------------------
# SIGN UP
# ---------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Basic fields
        if not username or not password:
            return render_template(
                "signup.html",
                error="Please fill in all fields."
            )

        # Letters, digits and underscores only: no spaces, links, emoji or markup.
        if not USERNAME_RE.fullmatch(username):
            return render_template(
                "signup.html",
                error="Usernames can only use letters, numbers and underscores (3 to 20 characters)."
            )

        # Length, character classes and Shannon entropy
        problem = password_problem(password)

        if problem:
            return render_template(
                "signup.html",
                error=problem
            )

        # Confirm password
        if password != confirm_password:
            return render_template(
                "signup.html",
                error="Passwords do not match."
            )

        # Hash password BEFORE storing it
        password_hash = generate_password_hash(password)

        conn = get_db()

        # "Alice" and "alice" would look like the same person to others.
        if conn.execute("SELECT 1 FROM users WHERE lower(username) = lower(?)", (username,)).fetchone():
            conn.close()
            return render_template(
                "signup.html",
                error="That username is already taken."
            )

        try:

            cursor = conn.execute(
                """
                INSERT INTO users (
                    username,
                    password_hash
                )
                VALUES (?, ?)
                """,
                (username, password_hash)
            )

            conn.commit()

            user_id = cursor.lastrowid

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "signup.html",
                error="That username is already taken."
            )

        conn.close()

        # Automatically log the user in after signup.
        session["user_id"] = user_id
        session["username"] = username

        return redirect(url_for("home"))

    return render_template("signup.html")


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
@login_required
def home():

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    # If the session refers to a user that no longer exists
    # in the database, clear the stale session and send the
    # user back to the login page.
    if user is None:

        session.clear()

        return redirect(url_for("login"))

    show_quiz_prompt = user["quiz_completed"] == 0

    conn = get_db()
    all_progress = progress_db.all_progress(conn, user["id"])
    conn.close()

    return render_template(
        "home.html",
        username=user["username"],
        show_quiz_prompt=show_quiz_prompt,
        courses=[COURSES[slug] for slug in COURSE_ORDER],
        progress=all_progress,
        recommended=QUIZ_TO_COURSE.get(user["recommended_course"]),
    )
# ---------------------------------------------------------
# QUIZ
# ---------------------------------------------------------

@app.route("/quiz")
@login_required
def quiz():

    return render_template("quiz.html")

@app.route("/save-quiz", methods=["POST"])
@login_required
def save_quiz():

    data = request.get_json()

    recommended_course = data.get("recommended_course")

    allowed_courses = {
        "python",
        "cybersecurity",
        "internet",
        "secure"
    }

    if recommended_course not in allowed_courses:
        return {
            "success": False,
            "error": "Invalid course recommendation."
        }, 400

    conn = get_db()

    conn.execute(
        """
        UPDATE users
        SET quiz_completed = 1,
            recommended_course = ?
        WHERE id = ?
        """,
        (
            recommended_course,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return {
        "success": True
    }


# ---------------------------------------------------------
# PROFILE
# ---------------------------------------------------------

@app.route("/profile")
@login_required
def profile():

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if user is None:

        session.clear()

        return redirect(url_for("login"))

    conn = get_db()
    all_progress = progress_db.all_progress(conn, user["id"])
    badges = progress_db.badge_collection(conn, user["id"])
    secrets = achievements.profile_view(conn, user["id"])
    idea = progress_db.get_idea(conn, user["id"])
    language = progress_db.get_language(conn, user["id"])
    beams = progress_db.finished_courses(conn, user["id"])
    privacy = progress_db.get_privacy(conn, user["id"])
    prefs = progress_db.get_prefs(conn, user["id"])
    rename_wait = progress_db.username_change_wait(conn, user["id"], time.time())
    conn.close()

    total_levels = sum(p["total"] for p in all_progress.values())
    levels_done = sum(p["levels_done"] for p in all_progress.values())

    return render_template(
        "profile.html",
        user=user,
        courses=[COURSES[slug] for slug in COURSE_ORDER],
        progress=all_progress,
        badges=badges,
        secrets=secrets,
        secrets_earned=sum(1 for s in secrets if s["earned"]),
        idea=idea,
        language=language,
        beams=beams,
        privacy=privacy,
        prefs=prefs,
        rename_wait_days=(rename_wait + 86399) // 86400,
        privacy_levels=progress_db.PRIVACY_LEVELS,
        tab="settings" if request.args.get("tab") == "settings" else "overview",
        levels_done=levels_done,
        overall_percent=round(levels_done / total_levels * 100) if total_levels else 0,
    )


# ---------------------------------------------------------
# PROFILE PICTURE + PRIVACY + PUBLIC PROFILE
# ---------------------------------------------------------

@app.route("/avatar/<int:user_id>")
@login_required
def avatar(user_id):
    conn = get_db()
    tag = progress_db.get_avatar(conn, user_id)
    conn.close()

    extension = (tag or "").split("-")[0]
    if extension not in AVATAR_TYPES:
        abort(404)

    path = avatar_path(user_id, tag)
    if not os.path.isfile(path):
        abort(404)

    response = send_file(os.path.abspath(path), mimetype=AVATAR_TYPES[extension], max_age=3600)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Disposition"] = "inline"
    return response


@app.errorhandler(413)
def upload_too_large(_error):
    flash("That file is too big. Pictures must be 2 MB or smaller.", "error")
    return redirect(url_for("profile", tab="settings"))


@app.route("/profile/picture", methods=["POST"])
@login_required
def profile_picture():
    upload = request.files.get("picture")

    if upload is None or not upload.filename:
        flash("Choose an image file first.", "error")
        return redirect(url_for("profile", tab="settings"))

    data = upload.read(AVATAR_MAX_BYTES + 1)

    if len(data) > AVATAR_MAX_BYTES:
        flash("That file is too big. Pictures must be 2 MB or smaller.", "error")
        return redirect(url_for("profile", tab="settings"))

    shrunk = shrink_picture(data)
    if shrunk is None:
        flash("That file is not a PNG, JPEG, GIF or WebP image.", "error")
        return redirect(url_for("profile", tab="settings"))

    data, extension = shrunk
    user_id = session["user_id"]
    tag = "%s-%d" % (extension, int(time.time()))

    os.makedirs(AVATAR_DIR, exist_ok=True)
    delete_avatar_files(user_id)
    with open(avatar_path(user_id, tag), "wb") as handle:
        handle.write(data)

    conn = get_db()
    progress_db.set_avatar(conn, user_id, tag)
    conn.commit()
    conn.close()

    flash("Profile picture updated.")
    return redirect(url_for("profile", tab="settings"))


@app.route("/profile/picture/remove", methods=["POST"])
@login_required
def profile_picture_remove():
    user_id = session["user_id"]
    delete_avatar_files(user_id)

    conn = get_db()
    progress_db.set_avatar(conn, user_id, None)
    conn.commit()
    conn.close()

    flash("Profile picture removed.")
    return redirect(url_for("profile", tab="settings"))


@app.route("/profile/prefs", methods=["POST"])
@login_required
def profile_prefs():
    conn = get_db()
    progress_db.set_prefs(conn, session["user_id"], request.form)
    conn.commit()
    conn.close()

    flash("Game settings saved.")
    return redirect(url_for("profile", tab="settings"))


@app.route("/profile/privacy", methods=["POST"])
@login_required
def profile_privacy():
    conn = get_db()
    progress_db.set_privacy(conn, session["user_id"], request.form, from_form=True)
    conn.commit()
    conn.close()

    flash("Privacy settings saved.")
    return redirect(url_for("profile", tab="settings"))


@app.route("/profile/username", methods=["POST"])
@login_required
def profile_username():
    """Rename the account: once every 14 days, same rules as sign-up."""
    new_name = request.form.get("username", "").strip()
    user_id = session["user_id"]
    now = time.time()

    conn = get_db()

    wait = progress_db.username_change_wait(conn, user_id, now)
    if wait:
        conn.close()
        flash("You can change your username again in %d day%s." % ((wait + 86399) // 86400, "" if wait <= 86400 else "s"), "error")
        return redirect(url_for("profile", tab="settings"))

    if not USERNAME_RE.fullmatch(new_name):
        conn.close()
        flash("Usernames can only use letters, numbers and underscores (3 to 20 characters).", "error")
        return redirect(url_for("profile", tab="settings"))

    if new_name == session.get("username"):
        conn.close()
        flash("That is already your username.", "error")
        return redirect(url_for("profile", tab="settings"))

    if progress_db.username_taken(conn, new_name, except_id=user_id):
        conn.close()
        flash("That username is already taken.", "error")
        return redirect(url_for("profile", tab="settings"))

    progress_db.set_username(conn, user_id, new_name, now)
    conn.commit()
    conn.close()

    session["username"] = new_name
    flash("Username changed to %s. Your friends, progress and times are untouched." % new_name)
    return redirect(url_for("profile", tab="settings"))


@app.route("/profile/password", methods=["POST"])
@login_required
def profile_password():
    current = request.form.get("current_password", "")
    new = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")

    conn = get_db()
    user = conn.execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if user is None or not check_password_hash(user["password_hash"], current):
        conn.close()
        flash("Your current password is not right.", "error")
        return redirect(url_for("profile", tab="settings"))

    problem = password_problem(new) or ("New passwords do not match." if new != confirm else None)
    if problem:
        conn.close()
        flash(problem, "error")
        return redirect(url_for("profile", tab="settings"))

    progress_db.set_password_hash(conn, session["user_id"], generate_password_hash(new))
    conn.commit()
    conn.close()

    flash("Password changed.")
    return redirect(url_for("profile", tab="settings"))


@app.route("/profile/delete", methods=["POST"])
@login_required
def profile_delete():
    password = request.form.get("password", "")

    if request.form.get("confirm") != "on":
        flash("Tick the box to confirm you want to delete the account.", "error")
        return redirect(url_for("profile", tab="settings"))

    conn = get_db()
    user = conn.execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        conn.close()
        flash("Your password is not right, so nothing was deleted.", "error")
        return redirect(url_for("profile", tab="settings"))

    user_id = session["user_id"]
    delete_avatar_files(user_id)
    progress_db.delete_user(conn, user_id)
    conn.commit()
    conn.close()

    session.clear()
    flash("Your account and all its progress were deleted.")
    return redirect(url_for("login"))


@app.route("/friends/block", methods=["POST"])
@login_required
def friends_block():
    other_id = friend_id_from_form()

    conn = get_db()
    outcome = progress_db.block_user(conn, session["user_id"], other_id)
    conn.commit()
    conn.close()

    if outcome == "missing":
        abort(404)
    if outcome == "self":
        return render_friends(error="You can't block yourself.")

    flash("Blocked. They can't send you requests or open your profile any more.")
    return redirect(url_for("friends", tab="blocked"))


@app.route("/friends/unblock", methods=["POST"])
@login_required
def friends_unblock():
    other_id = friend_id_from_form()

    conn = get_db()
    progress_db.unblock_user(conn, session["user_id"], other_id)
    conn.commit()
    conn.close()

    return redirect(url_for("friends", tab="blocked"))


@app.route("/u/<username>/report", methods=["POST"])
@login_required
def report_user(username):
    conn = get_db()
    person = progress_db.get_user_by_name(conn, username)

    if person is None or person["id"] == session["user_id"]:
        conn.close()
        abort(404)

    reason = request.form.get("reason", "")
    note = request.form.get("note", "")

    if not progress_db.add_report(conn, session["user_id"], person["id"], reason, note):
        conn.close()
        flash("Pick a reason and keep the note under 300 characters.", "error")
        return redirect(url_for("public_profile", username=username))

    conn.commit()
    conn.close()

    save_report_to_file(session.get("username", ""), username, reason, note)

    flash("Thanks. The report was sent to the Academy staff.")
    return redirect(url_for("public_profile", username=username))


def save_report_to_file(reporter, reported, reason, note):
    """Appends the report to data/reports.jsonl (git-ignored) for the site owner."""
    import json as _json
    try:
        os.makedirs(os.path.dirname(REPORTS_FILE), exist_ok=True)
        with open(REPORTS_FILE, "a", encoding="utf-8") as handle:
            handle.write(_json.dumps({
                "reporter": reporter,
                "reported": reported,
                "reason": reason,
                "note": (note or "").strip(),
                "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }, ensure_ascii=False) + "\n")
    except OSError as error:
        print("Could not write the reports file:", error)


@app.route("/u/<username>")
@login_required
def public_profile(username):
    conn = get_db()
    person = progress_db.get_user_by_name(conn, username)

    if person is None:
        conn.close()
        abort(404)

    if person["id"] == session["user_id"]:
        conn.close()
        return redirect(url_for("profile"))

    privacy = progress_db.get_privacy(conn, person["id"])
    relation = progress_db.relation_between(conn, session["user_id"], person["id"])
    state = progress_db.friend_state(conn, session["user_id"], person["id"])
    blocked_by_me = progress_db.blocked_by_me(conn, session["user_id"], person["id"])
    blocked = blocked_by_me or progress_db.is_blocked(conn, session["user_id"], person["id"])

    # Someone who blocked you (or whom you blocked) is simply private to you.
    view = {"visible": (not blocked) and progress_db.allowed(privacy["profile_visibility"], relation)}

    if view["visible"]:
        if progress_db.allowed(privacy["show_progress"], relation):
            all_progress = progress_db.all_progress(conn, person["id"])
            total = sum(p["total"] for p in all_progress.values())
            done = sum(p["levels_done"] for p in all_progress.values())
            view["progress"] = all_progress
            view["levels_done"] = done
            view["percent"] = round(done / total * 100) if total else 0

        if progress_db.allowed(privacy["show_achievements"], relation):
            secrets = achievements.profile_view(conn, person["id"])
            view["badges"] = progress_db.badge_collection(conn, person["id"])
            view["beams"] = progress_db.finished_courses(conn, person["id"])
            view["secrets_earned"] = sum(1 for item in secrets if item["earned"])
            view["secrets_total"] = len(secrets)

        if progress_db.allowed(privacy["show_time"], relation):
            view["time"] = int(person["time_spent"] or 0)

    conn.close()

    return render_template(
        "user.html",
        person=person,
        person_avatar=avatar_url_for(person["id"], person["avatar"]),
        relation=relation,
        state="blocked" if blocked else state,
        blocked_by_me=blocked_by_me,
        view=view,
        report_reasons=progress_db.REPORT_REASONS,
        courses=[COURSES[slug] for slug in COURSE_ORDER],
    )


@app.route("/api/time/ping", methods=["POST"])
@login_required
def time_ping():
    """The browser calls this every 30 s while a page is open."""
    data = request.get_json(silent=True) or {}
    claimed = data.get("seconds")
    if isinstance(claimed, bool) or not isinstance(claimed, (int, float)):
        claimed = None

    conn = get_db()
    total = progress_db.add_time(conn, session["user_id"], time.time(), claimed)
    conn.commit()
    conn.close()

    return jsonify({"success": True, "seconds": total})

# ---------------------------------------------------------
# GAME
# ---------------------------------------------------------

@app.route("/game")
@login_required
def game():
    """
    CONTINUE GAME: jump to the level the player is on in their
    selected course. New players go to course selection first.
    """

    conn = get_db()

    user = conn.execute(
        "SELECT selected_course, recommended_course FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    course_slug = None

    if user is not None:
        course_slug = user["selected_course"] or QUIZ_TO_COURSE.get(user["recommended_course"])

    if course_slug not in COURSES:
        return redirect(url_for("home") + "#courses")

    return redirect(url_for("course_home", course_slug=course_slug))

# ---------------------------------------------------------
# AI MENTOR
# ---------------------------------------------------------

@app.route("/api/mentor", methods=["POST"])
@login_required
def mentor():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "Invalid request."
        }), 400

    question = str(data.get("question", "")).strip()

    code = str(data.get("code", "") or "")

    # The level briefing is built here from curriculum data, so the
    # browser cannot inject its own "context" into the prompt.
    context = ""
    course_slug = data.get("course")
    number = data.get("level")
    lvl = None
    language = None

    if isinstance(course_slug, str) and isinstance(number, int) and not isinstance(number, bool):
        course = get_course(course_slug)
        lvl = get_level(course_slug, number)
        if course and lvl:
            conn = get_db()
            language = progress_db.get_language(conn, session["user_id"])
            conn.close()
            context = mentor_briefing(course, lvl, language)

    if ask_mentor is None or not mentor_available():
        return jsonify({
            "success": False,
            "error": "SecureMentor is offline right now. Use the in-game hints to keep going."
        }), 503

    if not question:
        return jsonify({
            "success": False,
            "error": "Please enter a question."
        }), 400

    # Basic request-size protection
    if len(question) > 5000:
        return jsonify({
            "success": False,
            "error": "Question is too long."
        }), 400

    if len(code) > 12000:
        return jsonify({
            "success": False,
            "error": "Code submission is too large."
        }), 400

    try:

        answer = ask_mentor(
            question,
            code,
            context
        )

        # Safety net: even if a clever prompt gets past the rules, the
        # exact terminal code never reaches the player.
        if context and leaks_answer(resolve_challenge(lvl, language), answer):
            nudge = lvl["hints"][0] if lvl["hints"] else "re-read the lesson notes above the terminal."
            answer = (
                "I nearly handed that over, and Academy rules don't allow it. "
                "Here's a nudge instead: " + nudge
            )

        return jsonify({
            "success": True,
            "answer": answer
        })

    except Exception as error:

        print("Claude API error:", error)

        return jsonify({
            "success": False,
            "error": "The mentor is temporarily unavailable."
        }), 500


_mentor_status_cache = {"checked": 0.0, "value": None}


@app.route("/api/mentor/status")
@login_required
def mentor_status_route():
    """
    Tells the mentor panel whether the AI is reachable. The check is
    token-free but still a network call, so it is cached for a minute.
    """
    now = time.time()

    if _mentor_status_cache["value"] is None or now - _mentor_status_cache["checked"] > 60:
        _mentor_status_cache["value"] = mentor_status()
        _mentor_status_cache["checked"] = now

    return jsonify(_mentor_status_cache["value"])


# ---------------------------------------------------------
# CHARACTER CUSTOMISATION
# ---------------------------------------------------------

def safe_next_url(value):
    """Only allow redirects back into the curriculum area of this site."""
    if isinstance(value, str) and value.startswith("/curriculum/") and "//" not in value:
        return value
    return url_for("home")


@app.route("/character", methods=["GET", "POST"])
@login_required
def character():

    next_url = safe_next_url(request.values.get("next"))

    conn = get_db()

    if request.method == "POST":

        chosen = {}

        for field, allowed in CHARACTER_OPTIONS.items():
            value = request.form.get(field, "")
            if value not in allowed:
                current = progress_db.get_character(conn, session["user_id"]) or {}
                conn.close()
                return render_template(
                    "character.html",
                    options=CHARACTER_OPTIONS,
                    current=current,
                    next_url=next_url,
                    error="Please pick one option in every group.",
                )
            chosen[field] = value

        progress_db.set_character(conn, session["user_id"], chosen)
        conn.commit()
        conn.close()

        return redirect(next_url)

    current = progress_db.get_character(conn, session["user_id"]) or {}
    conn.close()

    return render_template(
        "character.html",
        options=CHARACTER_OPTIONS,
        current=current,
        next_url=next_url,
    )


# ---------------------------------------------------------
# CURRICULUM / COURSE PAGES
# ---------------------------------------------------------

@app.route("/curriculum/<course_slug>")
@login_required
def course_home(course_slug):

    course = get_course(course_slug)

    if course is None:
        abort(404)

    conn = get_db()
    course_progress = progress_db.course_progress(conn, session["user_id"], course_slug)
    conn.close()

    return redirect(url_for(
        "course_level",
        course_slug=course_slug,
        number=course_progress["current"],
    ))


@app.route("/curriculum/<course_slug>/<int:number>")
@login_required
def course_level(course_slug, number):

    course = get_course(course_slug)
    lvl = get_level(course_slug, number)

    if course is None or lvl is None:
        abort(404)

    conn = get_db()

    character_data = progress_db.get_character(conn, session["user_id"])

    if character_data is None:
        conn.close()
        return redirect(url_for("character", next=request.path))

    course_progress = progress_db.course_progress(conn, session["user_id"], course_slug)
    unlocked = progress_db.is_unlocked(conn, session["user_id"], course_slug, number)
    inventory = progress_db.get_inventory(conn, session["user_id"], course_slug)
    record = progress_db.level_records(conn, course_slug).get(number)
    checkpoint = progress_db.get_checkpoint(conn, session["user_id"], course_slug, number)
    language = progress_db.get_language(conn, session["user_id"])
    beams = progress_db.finished_courses(conn, session["user_id"])
    prefs = progress_db.get_prefs(conn, session["user_id"])

    progress_db.set_selected_course(conn, session["user_id"], course_slug)
    conn.commit()
    conn.close()

    def status_of(n):
        if n in course_progress["completed"]:
            return "done"
        if n == course_progress["current"]:
            return "current"
        return "locked"

    sidebar = []
    for section in course_sections(course):
        sidebar.append({
            "name": section["name"],
            "levels": [
                {"number": item["number"], "title": item["title"], "kind": item["kind"], "status": status_of(item["number"])}
                for item in section["levels"]
            ],
        })

    return render_template(
        "course.html",
        course=course,
        level=lvl,
        level_json=public_level(course, lvl, language, beams),
        character_json=character_data,
        inventory_json=inventory,
        checkpoint_json=checkpoint,
        prefs=prefs,
        record=record,
        sidebar=sidebar,
        course_progress=course_progress,
        unlocked=unlocked,
        is_current=(number == course_progress["current"]),
        username=session.get("username", "U"),
        mentor_online=mentor_available(),
    )


# ---------------------------------------------------------
# FRIENDS
# ---------------------------------------------------------

def render_friends(query="", error=None, tab=None):
    user_id = session["user_id"]
    conn = get_db()
    results = progress_db.search_users(conn, user_id, query) if query else None
    friends = progress_db.friends_of(conn, user_id)
    incoming = progress_db.incoming_requests(conn, user_id)
    sent = progress_db.sent_requests(conn, user_id)
    blocked = progress_db.blocked_users(conn, user_id)
    conn.close()

    if tab not in ("friends", "requests", "sent", "search", "blocked"):
        tab = "search" if query else "friends"

    return render_template(
        "friends.html",
        query=query,
        results=results,
        friends=friends,
        incoming=incoming,
        sent=sent,
        blocked=blocked,
        tab=tab,
        courses=[COURSES[slug] for slug in COURSE_ORDER],
        error=error,
    )


@app.route("/friends")
@login_required
def friends():
    query = request.args.get("q", "").strip()[:30]
    return render_friends(query, tab=request.args.get("tab"))


def friend_id_from_form():
    value = request.form.get("friend_id", "")
    if not value.isdigit():
        abort(400)
    return int(value)


@app.route("/friends/add", methods=["POST"])
@login_required
def friends_add():
    friend_id = friend_id_from_form()

    conn = get_db()
    outcome = progress_db.add_friend(conn, session["user_id"], friend_id)
    conn.commit()
    conn.close()

    if outcome == "missing":
        abort(404)
    if outcome == "self":
        return render_friends(error="You can't add yourself - you're already on your own side.")
    if outcome == "blocked":
        return render_friends(error="You can't add this person.")

    if outcome == "friends":
        flash("You are now friends.")
        return redirect(url_for("friends", tab="friends"))

    flash("Friend request sent. You'll be friends once they add you back.")
    return redirect(url_for("friends", tab="sent"))


@app.route("/friends/decline", methods=["POST"])
@login_required
def friends_decline():
    friend_id = friend_id_from_form()

    conn = get_db()
    progress_db.decline_request(conn, session["user_id"], friend_id)
    conn.commit()
    conn.close()

    return redirect(url_for("friends", tab="requests"))


@app.route("/friends/remove", methods=["POST"])
@login_required
def friends_remove():
    """Ends a friendship or cancels a request you sent."""
    friend_id = friend_id_from_form()

    conn = get_db()
    progress_db.remove_friend(conn, session["user_id"], friend_id)
    conn.commit()
    conn.close()

    return redirect(url_for("friends", tab=request.form.get("tab", "friends")))


@app.route("/leaderboard")
@login_required
def leaderboard():
    """
    Every player's best time on one level. A course must be chosen;
    the level defaults to the first one; times sort fastest-first
    unless order=desc.
    """
    course_slug = request.args.get("course", "")
    course = get_course(course_slug) if course_slug else None
    descending = request.args.get("order") == "desc"
    friends_only = request.args.get("friends") == "1"
    submitted = "course" in request.args

    error = None
    level = None
    times = []
    mine = None

    if submitted and course is None:
        error = "Choose a course first."

    conn = get_db()
    privacy = progress_db.get_privacy(conn, session["user_id"])
    time_board = progress_db.time_ranking(conn, session["user_id"])

    if course is not None:
        raw = request.args.get("level", "")
        level = get_level(course_slug, int(raw)) if raw.isdigit() else course["levels"][0]
        if level is None:
            error = "That level does not exist in this course."
        else:
            only_ids = None
            if friends_only:
                only_ids = {person["id"] for person in progress_db.friends_of(conn, session["user_id"])}
                only_ids.add(session["user_id"])
            times = progress_db.level_times(
                conn, course_slug, level["number"], descending,
                viewer_id=session["user_id"], only_ids=only_ids,
            )
            mine = progress_db.course_progress(conn, session["user_id"], course_slug)["times"].get(level["number"])

    conn.close()

    levels_by_course = {
        slug: [{"number": lvl["number"], "title": lvl["title"], "kind": lvl["kind"]} for lvl in COURSES[slug]["levels"]]
        for slug in COURSE_ORDER
    }

    return render_template(
        "leaderboard.html",
        courses=[COURSES[slug] for slug in COURSE_ORDER],
        levels_by_course=levels_by_course,
        course=course,
        level=level,
        descending=descending,
        friends_only=friends_only,
        times=times,
        mine=mine,
        time_board=time_board,
        board="time" if request.args.get("board") == "time" else "levels",
        hidden_me=not privacy["leaderboard_times"],
        error=error,
    )


# ---------------------------------------------------------
# LEVEL API (timer + answer checking, all server-side)
# ---------------------------------------------------------

def load_level_request():
    """
    Shared validation for the level API. Returns
    (course, level, error_response). Only JSON bodies are accepted,
    which also keeps cross-site form posts out.
    """
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return None, None, None, (jsonify({"success": False, "error": "Invalid request."}), 400)

    course_slug = data.get("course")
    number = data.get("level")

    if not isinstance(number, int) or isinstance(number, bool):
        return None, None, None, (jsonify({"success": False, "error": "Invalid level."}), 400)

    course = get_course(course_slug) if isinstance(course_slug, str) else None
    lvl = get_level(course_slug, number) if course else None

    if course is None or lvl is None:
        return None, None, None, (jsonify({"success": False, "error": "Unknown level."}), 404)

    return course, lvl, data, None


@app.route("/api/level/start", methods=["POST"])
@login_required
def level_start():

    course, lvl, data, error = load_level_request()

    if error:
        return error

    conn = get_db()

    if not progress_db.is_unlocked(conn, session["user_id"], course["slug"], lvl["number"]):
        conn.close()
        return jsonify({"success": False, "error": "This level is still locked."}), 403

    # Resuming from a door checkpoint keeps the time already spent. The
    # offset comes from the server's own record, not from the browser.
    offset = 0
    if data.get("resume") is True:
        checkpoint = progress_db.get_checkpoint(conn, session["user_id"], course["slug"], lvl["number"])
        if checkpoint:
            offset = max(0, min(int(checkpoint["elapsed"]), 24 * 3600))

    conn.close()

    # The timer lives in the signed session cookie, so the browser
    # cannot shorten it.
    session["level_timer"] = {
        "course": course["slug"],
        "level": lvl["number"],
        "started": time.time() - offset,
    }

    return jsonify({"success": True, "elapsed": offset})


def timer_elapsed(course_slug, number):
    """Seconds since /api/level/start for this level, or None if the timer is not running."""
    timer = session.get("level_timer")

    if (
        isinstance(timer, dict)
        and timer.get("course") == course_slug
        and timer.get("level") == number
    ):
        elapsed = int(time.time() - float(timer.get("started", time.time())))
        return max(0, min(elapsed, 24 * 3600))

    return None


@app.route("/api/level/checkpoint", methods=["POST"])
@login_required
def level_checkpoint():
    """
    Saves (or clears) the mid-level state the game sends when the
    player passes a door. Game state only - it is never trusted for
    completion or timing.
    """
    course, lvl, data, error = load_level_request()

    if error:
        return error

    user_id = session["user_id"]
    conn = get_db()

    if not progress_db.is_unlocked(conn, user_id, course["slug"], lvl["number"]):
        conn.close()
        return jsonify({"success": False, "error": "This level is still locked."}), 403

    if data.get("clear") is True:
        progress_db.clear_checkpoint(conn, user_id, course["slug"], lvl["number"])
        conn.commit()
        conn.close()
        return jsonify({"success": True, "cleared": True})

    elapsed = timer_elapsed(course["slug"], lvl["number"]) or 0
    saved = progress_db.set_checkpoint(conn, user_id, course["slug"], lvl["number"], data.get("state"), elapsed)

    if not saved:
        conn.close()
        return jsonify({"success": False, "error": "Checkpoint data is invalid or too large."}), 400

    conn.commit()
    conn.close()

    return jsonify({"success": True, "elapsed": elapsed})


@app.route("/api/level/submit", methods=["POST"])
@login_required
def level_submit():

    course, lvl, data, error = load_level_request()

    if error:
        return error

    user_id = session["user_id"]
    conn = get_db()

    if not progress_db.is_unlocked(conn, user_id, course["slug"], lvl["number"]):
        conn.close()
        return jsonify({"success": False, "error": "This level is still locked."}), 403

    answer = data.get("answer")
    language = progress_db.get_language(conn, user_id)
    challenge = resolve_challenge(lvl, language)

    # Sorting decks give feedback one card at a time; that never completes the level.
    if challenge.get("type") == "swipe" and isinstance(answer, dict) and "card" in answer:
        verdict = swipe_card_verdict(challenge, answer.get("card"), answer.get("scam"))
        conn.close()
        if verdict is None:
            return jsonify({"success": False, "error": "Invalid card."}), 400
        card_correct, actual, why = verdict
        return jsonify({"success": True, "card": answer["card"], "correct": card_correct, "verdict": actual, "why": why, "partial": True})

    correct, feedback = check_answer(challenge, answer)

    # The inventory travels with the player between levels of ONE course.
    # It is game state, not a security boundary, so it only needs to be well-formed.
    inventory = progress_db.clean_inventory(data.get("inventory"))
    if inventory is not None:
        progress_db.set_inventory(conn, user_id, course["slug"], inventory)

    # Enemy kills feed the secret achievements; the game sends the delta since its last report.
    progress_db.add_kills(conn, user_id, data.get("kills"))

    if not correct:
        progress_db.record_attempt(conn, user_id, course["slug"], lvl["number"])
        conn.commit()
        conn.close()
        return jsonify({"success": True, "correct": False, "feedback": feedback})

    if challenge.get("type") == "language":
        progress_db.set_language(conn, user_id, answer)

    if challenge.get("type") == "idea":
        idea = {
            "name": answer["name"].strip(),
            "pitch": answer["pitch"].strip(),
            "pages": [p.strip() for p in answer["pages"]],
        }
        progress_db.set_idea(conn, user_id, idea)
        save_idea_to_file(session.get("username", ""), idea)

    previous_record = progress_db.level_records(conn, course["slug"]).get(lvl["number"])

    elapsed = timer_elapsed(course["slug"], lvl["number"])

    progress_db.record_completion(conn, user_id, course["slug"], lvl["number"], elapsed)
    progress_db.set_selected_course(conn, user_id, course["slug"])
    progress_db.clear_checkpoint(conn, user_id, course["slug"], lvl["number"])
    conn.commit()

    course_progress = progress_db.course_progress(conn, user_id, course["slug"])
    record = progress_db.level_records(conn, course["slug"]).get(lvl["number"])
    new_achievements = achievements.evaluate(conn, user_id)
    beams = progress_db.finished_courses(conn, user_id)
    conn.commit()
    conn.close()

    new_record = (
        elapsed is not None
        and (previous_record is None or elapsed < previous_record["seconds"])
    )

    session.pop("level_timer", None)

    next_level = None
    if lvl["number"] < course_progress["total"]:
        next_level = {
            "number": lvl["number"] + 1,
            "title": course["levels"][lvl["number"]]["title"],
            "url": url_for("course_level", course_slug=course["slug"], number=lvl["number"] + 1),
        }

    response = {
        "success": True,
        "correct": True,
        "explanation": lvl["explanation"],
        "reward": lvl["reward"],
        "elapsed": elapsed,
        "best": course_progress["times"].get(lvl["number"]),
        "next_level": next_level,
        "course_finished": course_progress["finished"],
        "percent": course_progress["percent"],
        "record": record,
        "new_record": new_record,
        "levels_done": course_progress["levels_done"],
        "level_count": course_progress["total"],
        "new_achievements": [{"title": a["title"], "desc": a["desc"]} for a in new_achievements],
        "beams": beams,
    }

    if challenge.get("type") == "code_review":
        response["fixed"] = challenge.get("fixed", [])

    return jsonify(response)


def save_idea_to_file(username, idea):
    """Appends the idea to data/website_ideas.jsonl (git-ignored) so it can be read later."""
    import json as _json
    try:
        os.makedirs(os.path.dirname(IDEAS_FILE), exist_ok=True)
        with open(IDEAS_FILE, "a", encoding="utf-8") as handle:
            handle.write(_json.dumps({
                "username": username,
                "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "idea": idea,
            }, ensure_ascii=False) + "\n")
    except OSError as error:
        print("Could not write the ideas file:", error)


# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------

# Create / migrate the database on import so WSGI servers (gunicorn)
# get the tables too, not only `python3 app.py`.
init_db()


if __name__ == "__main__":

    # PORT can be set in .env if 5000 is taken (macOS AirPlay uses it).
    # FLASK_DEBUG=0 turns the debugger off for deployment.
    app.run(
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
        port=int(os.getenv("PORT", "5000")),
    )