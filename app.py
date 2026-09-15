from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
import math
import os
import time
from collections import Counter

from dotenv import load_dotenv

from curriculum import COURSES, COURSE_ORDER, QUIZ_TO_COURSE, get_course, get_level, public_level, course_sections, mentor_briefing, resolve_challenge
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
# PASSWORD ENTROPY
# ---------------------------------------------------------

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

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user is None:
            return render_template(
                "login.html",
                error="Username or password is incorrect."
            )

        if not check_password_hash(
            user["password_hash"],
            password
        ):
            return render_template(
                "login.html",
                error="Username or password is incorrect."
            )

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

        # Username length
        if len(username) < 3:
            return render_template(
                "signup.html",
                error="Username must be at least 3 characters."
            )

        # Password length
        if len(password) < 8:
            return render_template(
                "signup.html",
                error="Password must be at least 8 characters."
            )

        # Uppercase requirement
        if not any(char.isupper() for char in password):
            return render_template(
                "signup.html",
                error="Password must contain an uppercase letter."
            )

        # Lowercase requirement
        if not any(char.islower() for char in password):
            return render_template(
                "signup.html",
                error="Password must contain a lowercase letter."
            )

        # Number requirement
        if not any(char.isdigit() for char in password):
            return render_template(
                "signup.html",
                error="Password must contain a number."
            )

        # Special-character requirement
        if not any(not char.isalnum() for char in password):
            return render_template(
                "signup.html",
                error="Password must contain a special character."
            )

        # Shannon entropy requirement
        password_entropy = calculate_entropy(password)

        if password_entropy < 3.5:
            return render_template(
                "signup.html",
                error=(
                    "Password entropy must be at least "
                    "3.5 bits per character."
                )
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
        levels_done=levels_done,
        overall_percent=round(levels_done / total_levels * 100) if total_levels else 0,
    )

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

def render_friends(query="", error=None):
    conn = get_db()
    results = progress_db.search_users(conn, session["user_id"], query) if query else None
    friends = progress_db.friends_of(conn, session["user_id"])
    conn.close()

    return render_template(
        "friends.html",
        username=session.get("username", "U"),
        me=session["user_id"],
        query=query,
        results=results,
        friends=friends,
        courses=[COURSES[slug] for slug in COURSE_ORDER],
        error=error,
    )


@app.route("/friends")
@login_required
def friends():
    query = request.args.get("q", "").strip()[:30]
    return render_friends(query)


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

    return redirect(url_for("friends"))


@app.route("/friends/remove", methods=["POST"])
@login_required
def friends_remove():
    friend_id = friend_id_from_form()

    conn = get_db()
    progress_db.remove_friend(conn, session["user_id"], friend_id)
    conn.commit()
    conn.close()

    return redirect(url_for("friends"))


@app.route("/leaderboard")
@login_required
def leaderboard():

    conn = get_db()

    boards = []
    for slug in COURSE_ORDER:
        course = COURSES[slug]
        records = progress_db.level_records(conn, slug)
        mine = progress_db.course_progress(conn, session["user_id"], slug)["times"]
        boards.append({
            "course": course,
            "levels": [
                {
                    "number": lvl["number"],
                    "title": lvl["title"],
                    "kind": lvl["kind"],
                    "record": records.get(lvl["number"]),
                    "mine": mine.get(lvl["number"]),
                }
                for lvl in course["levels"]
            ],
            "ranking": progress_db.progress_ranking(conn, slug),
        })

    conn.close()

    return render_template(
        "leaderboard.html",
        boards=boards,
        username=session.get("username", "U"),
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