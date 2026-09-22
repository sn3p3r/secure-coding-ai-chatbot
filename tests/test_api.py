"""
Automated HTTP tests for Cyber Academy, written with the `requests` library.

    python3 -m unittest tests.test_api

With no BASE_URL the module starts its own copy of the app on a free
port, with a throw-away database and the mentor switched off, and stops
it again at the end. Set BASE_URL to test a deployed copy instead:

    BASE_URL=https://cyber-academy.example python3 -m unittest tests.test_api

The tests create their own throw-away accounts (usernames start with
"t_") and never touch existing ones.
"""

import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from curriculum import COURSES, COURSE_ORDER, resolve_challenge  # noqa: E402

BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
PASSWORD = "Academy!2026-Test"
CHARACTER = {"gender": "female", "hair": "long", "hair_color": "blue", "outfit": "green"}

# Keys that must never appear in the level JSON the browser receives.
SECRET_KEYS = {"answer", "answers", "accepted", "patterns", "regex", "shuffle", "target_line", "why_answer", "scam", "why"}

# python_lines terminals cannot be solved from the data alone (they are
# regex-checked), so the code is typed out here.
PYTHON_TERMINALS = {
    1: 'print("open")',
    4: 'word = "descend"\nprint(word)',
    8: 'name = input("name? ")\nprint(name)',
    12: 'if badge == "red":\n    print("enter")\nelse:\n    print("denied")',
    22: 'doors["north"] = "open"\nprint(doors["north"])',
    24: 'def unlock():\n    print("unlocked")\nunlock()',
}

_server = None
_tempdir = None


# ---------------------------------------------------------------------
# A private server for the test run
# ---------------------------------------------------------------------

def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def setUpModule():
    global BASE_URL, _server, _tempdir

    if BASE_URL:
        return

    _tempdir = tempfile.TemporaryDirectory(prefix="cyber-academy-test-")
    port = _free_port()

    env = dict(os.environ)
    env.update({
        "ACADEMY_DB": os.path.join(_tempdir.name, "test.db"),
        "ACADEMY_IDEAS_FILE": os.path.join(_tempdir.name, "ideas.jsonl"),
        "PORT": str(port),
        "FLASK_DEBUG": "0",
        "SECRET_KEY": "test-" + uuid.uuid4().hex,
        # An empty key keeps the real .env key out of the test run: the
        # mentor must report OFFLINE and the game must still work.
        "ANTHROPIC_API_KEY": "",
    })

    log = open(os.path.join(_tempdir.name, "server.log"), "w")
    _server = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)

    BASE_URL = "http://127.0.0.1:%d" % port

    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            if requests.get(BASE_URL + "/login", timeout=2).status_code == 200:
                return
        except requests.ConnectionError:
            pass
        if _server.poll() is not None:
            break
        time.sleep(0.2)

    log.close()
    with open(os.path.join(_tempdir.name, "server.log")) as handle:
        raise RuntimeError("The test server did not start:\n" + handle.read())


def tearDownModule():
    if _server is not None:
        _server.terminate()
        try:
            _server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _server.kill()
    if _tempdir is not None:
        _tempdir.cleanup()


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def url(path):
    return BASE_URL + path


def new_user(prefix="t"):
    """Signs up a fresh account and returns (session, username)."""
    session = requests.Session()
    username = "%s_%s" % (prefix, uuid.uuid4().hex[:8])
    response = session.post(
        url("/signup"),
        data={"username": username, "password": PASSWORD, "confirm_password": PASSWORD},
        allow_redirects=False,
    )
    assert response.status_code == 302, response.text[:300]
    return session, username


def pick_character(session):
    response = session.post(url("/character"), data=CHARACTER, allow_redirects=False)
    assert response.status_code == 302, response.text[:300]


def embedded_json(html, element_id):
    match = re.search(r'<script id="%s" type="application/json">(.*?)</script>' % element_id, html, re.S)
    assert match, "no #%s on the page" % element_id
    return json.loads(match.group(1))


def level_page(session, course, number):
    response = session.get(url("/curriculum/%s/%d" % (course, number)))
    assert response.status_code == 200, (course, number, response.status_code)
    return response.text


def api(session, endpoint, **payload):
    return session.post(url("/api/level/" + endpoint), json=payload)


def course_list():
    return [COURSES[slug] for slug in COURSE_ORDER]


def solve(lvl, language):
    """The correct answer for a level, built from the private definition."""
    challenge = resolve_challenge(lvl, language)
    kind = challenge["type"]

    if kind == "mcq":
        return challenge["answer"]
    if kind == "text_answer":
        return challenge.get("accepted", [challenge.get("answer")])[0]
    if kind == "python_lines":
        return PYTHON_TERMINALS[lvl["number"]]
    if kind == "code_review":
        return {"line": challenge["target_line"], "why": challenge["why_answer"]}
    if kind == "fill_blank":
        return {"blanks": [accepted[0] for accepted in challenge["answers"]]}
    if kind == "order_code":
        shuffle = challenge["shuffle"]
        return {"order": [shuffle.index(k) for k in range(len(shuffle))]}
    if kind == "quiz":
        return {"answers": [q["answer"] for q in challenge["questions"]]}
    if kind == "swipe":
        return {"answers": [card["scam"] for card in challenge["cards"]]}
    if kind == "wires":
        return {"map": challenge["answer"]}
    if kind == "route_packets":
        return {"map": challenge["answer"]}
    if kind == "ip_assign":
        for last in range(2, 254):
            candidate = challenge["network"] + str(last)
            if candidate not in challenge["taken"]:
                return candidate
    if kind == "idea":
        return {"name": "Test Site", "pitch": "A site built by the automated tests.", "pages": ["Home", "About", "Contact"]}
    if kind == "language":
        return language
    if kind == "walk":
        return {"reached": True}
    raise AssertionError("no solver for challenge type " + kind)


# ---------------------------------------------------------------------
# Tests (numbered: they share one account and run in this order)
# ---------------------------------------------------------------------

class ApiFlowTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.session, cls.username = new_user()

    # -- auth ---------------------------------------------------------

    def test_01_protected_pages_redirect_to_login(self):
        anonymous = requests.Session()
        for path in ("/", "/profile", "/leaderboard", "/friends", "/u/someone", "/curriculum/python/1", "/api/mentor/status"):
            response = anonymous.get(url(path), allow_redirects=False)
            self.assertEqual(response.status_code, 302, path)
            self.assertTrue(response.headers["Location"].endswith("/login"), path)

        response = anonymous.post(url("/api/level/submit"), json={"course": "python", "level": 1, "answer": "x"}, allow_redirects=False)
        self.assertEqual(response.status_code, 302)

    def test_02_signup_rejects_weak_passwords(self):
        anonymous = requests.Session()
        cases = [
            ({"username": "t_weak", "password": "password", "confirm_password": "password"}, "uppercase letter"),
            ({"username": "t_weak", "password": "Password", "confirm_password": "Password"}, "contain a number"),
            ({"username": "t_weak", "password": "Passw0rd", "confirm_password": "Passw0rd"}, "special character"),
            ({"username": "t_weak", "password": "Sh0rt!", "confirm_password": "Sh0rt!"}, "at least 8 characters"),
            ({"username": "t_weak", "password": PASSWORD, "confirm_password": "Different!1"}, "do not match"),
            ({"username": "ab", "password": PASSWORD, "confirm_password": PASSWORD}, "letters, numbers and underscores"),
            ({"username": "http://evil.example", "password": PASSWORD, "confirm_password": PASSWORD}, "letters, numbers and underscores"),
            ({"username": "cool\U0001F600name", "password": PASSWORD, "confirm_password": PASSWORD}, "letters, numbers and underscores"),
            ({"username": "two words", "password": PASSWORD, "confirm_password": PASSWORD}, "letters, numbers and underscores"),
            ({"username": "<b>bold</b>", "password": PASSWORD, "confirm_password": PASSWORD}, "letters, numbers and underscores"),
            ({"username": "x" * 21, "password": PASSWORD, "confirm_password": PASSWORD}, "letters, numbers and underscores"),
            ({"username": "t_weak", "password": "Aaaaaaa1!", "confirm_password": "Aaaaaaa1!"}, "entropy"),
        ]
        for form, expected in cases:
            response = anonymous.post(url("/signup"), data=form)
            self.assertEqual(response.status_code, 200)
            self.assertIn(expected, response.text, form["password"])

        # The account must not exist afterwards.
        response = anonymous.post(url("/login"), data={"username": "t_weak", "password": "password"})
        self.assertIn("incorrect", response.text)

        # Names that differ only in case count as taken.
        response = anonymous.post(url("/signup"), data={"username": self.username.upper(), "password": PASSWORD, "confirm_password": PASSWORD})
        self.assertIn("already taken", response.text)

    def test_03_login_logout(self):
        fresh = requests.Session()

        response = fresh.post(url("/login"), data={"username": self.username, "password": "Wrong!Pass1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Username or password is incorrect.", response.text)

        response = fresh.post(url("/login"), data={"username": self.username, "password": PASSWORD}, allow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.username.upper(), fresh.get(url("/")).text)

        fresh.get(url("/logout"))
        self.assertEqual(fresh.get(url("/profile"), allow_redirects=False).status_code, 302)

    def test_04_password_is_stored_hashed(self):
        if _tempdir is None:
            self.skipTest("only checked against the private test database")
        conn = sqlite3.connect(os.path.join(_tempdir.name, "test.db"))
        stored = conn.execute("SELECT password_hash FROM users WHERE username = ?", (self.username,)).fetchone()[0]
        conn.close()
        self.assertNotIn(PASSWORD, stored)
        self.assertTrue(stored.startswith(("scrypt:", "pbkdf2:")), stored[:20])

    # -- pages --------------------------------------------------------

    def test_05_level_page_needs_a_character_first(self):
        response = self.session.get(url("/curriculum/python/1"), allow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/character", response.headers["Location"])

        # Invalid option is rejected server-side.
        response = self.session.post(url("/character"), data=dict(CHARACTER, hair="mohawk"))
        self.assertIn("pick one option", response.text)

        pick_character(self.session)
        html = level_page(self.session, "python", 1)
        self.assertIn(COURSES["python"]["levels"][0]["title"], html)

    def test_06_level_json_is_public_only(self):
        html = level_page(self.session, "python", 1)
        data = embedded_json(html, "level-data")
        self.assertEqual(data["number"], 1)
        self.assertEqual(data["challenge"]["type"], "python_lines")
        self.assertFalse(SECRET_KEYS & set(data["challenge"]))

        # Lesson notes are rendered by the template before play.
        lesson = COURSES["python"]["levels"][0]["lesson"]
        self.assertIn('class="lesson-points"', html)
        self.assertIn(lesson["points"][0][:40], html)

    # -- level API ----------------------------------------------------

    def test_07_level_api_validation(self):
        response = self.session.post(url("/api/level/start"), data="not json", headers={"Content-Type": "text/plain"})
        self.assertEqual(response.status_code, 400)

        self.assertEqual(api(self.session, "start", course="nope", level=1).status_code, 404)
        self.assertEqual(api(self.session, "start", course="python", level="1").status_code, 400)
        self.assertEqual(api(self.session, "start", course="python", level=True).status_code, 400)

        # Checkpoint quizzes are always open (they are a study tool)...
        quiz = next(l for l in COURSES["python"]["levels"] if l["kind"] == "quiz")
        self.assertEqual(api(self.session, "submit", course="python", level=quiz["number"], answer="x").status_code, 200)

        # ...but a playable level past the current one is locked.
        locked_level = next(l for l in COURSES["python"]["levels"] if l["number"] > 2 and l["kind"] == "level")
        locked = api(self.session, "submit", course="python", level=locked_level["number"], answer="x")
        self.assertEqual(locked.status_code, 403)
        self.assertIn("locked", locked.json()["error"])

    def test_08_wrong_answer_then_right_answer(self):
        self.assertTrue(api(self.session, "start", course="python", level=1).json()["success"])

        wrong = api(self.session, "submit", course="python", level=1, answer='print("closed")').json()
        self.assertTrue(wrong["success"])
        self.assertFalse(wrong["correct"])
        self.assertEqual(wrong["feedback"], "Line 1 isn't right yet.")
        self.assertNotIn("open", wrong["feedback"])

        right = api(
            self.session, "submit", course="python", level=1,
            answer=PYTHON_TERMINALS[1], inventory=["DAGGER", None, None, None, None], kills={"snake": 1},
        ).json()
        self.assertTrue(right["correct"])
        self.assertIsInstance(right["elapsed"], int)
        self.assertEqual(right["next_level"]["number"], 2)
        self.assertEqual(right["levels_done"], 1)
        self.assertIn("First Blood", [a["title"] for a in right["new_achievements"]])

    def test_09_inventory_is_kept_per_course(self):
        python_items = embedded_json(level_page(self.session, "python", 2), "inventory-data")
        self.assertIn("DAGGER", python_items)

        cyber_items = embedded_json(level_page(self.session, "cybersecurity", 1), "inventory-data")
        self.assertNotIn("DAGGER", cyber_items or [])

    def test_10_checkpoint_roundtrip(self):
        state = {"player": {"x": 300, "y": 128}, "inventory": ["DAGGER", None, None, None, None], "passed": [True]}
        saved = api(self.session, "checkpoint", course="python", level=2, state=state).json()
        self.assertTrue(saved["success"])

        restored = embedded_json(level_page(self.session, "python", 2), "checkpoint-data")
        self.assertEqual(restored["data"]["player"], state["player"])
        self.assertIsInstance(restored["elapsed"], int)

        too_big = api(self.session, "checkpoint", course="python", level=2, state={"blob": "x" * 20000})
        self.assertEqual(too_big.status_code, 400)

        cleared = api(self.session, "checkpoint", course="python", level=2, clear=True).json()
        self.assertTrue(cleared["cleared"])
        self.assertIsNone(embedded_json(level_page(self.session, "python", 2), "checkpoint-data"))

    def test_11_play_every_course_to_the_obelisk(self):
        language = "javascript"
        finished = []

        for course in course_list():
            for lvl in course["levels"]:
                html = level_page(self.session, course["slug"], lvl["number"])
                public = embedded_json(html, "level-data")
                self.assertFalse(SECRET_KEYS & set(public["challenge"]), (course["slug"], lvl["number"]))

                if course["slug"] == "secure-coding" and lvl["number"] == 3:
                    # The language chosen on level 1 must switch the code shown.
                    self.assertEqual(public["language"], language)
                    self.assertEqual(public["challenge"]["code"], resolve_challenge(lvl, language)["code"])

                self.assertTrue(api(self.session, "start", course=course["slug"], level=lvl["number"]).json()["success"])
                result = api(self.session, "submit", course=course["slug"], level=lvl["number"], answer=solve(lvl, language)).json()
                self.assertTrue(result.get("correct"), (course["slug"], lvl["number"], result))

            self.assertTrue(result["course_finished"], course["slug"])
            finished.append(course["slug"])
            self.assertEqual(result["beams"], finished)

        profile = self.session.get(url("/profile")).text
        self.assertIn("4 / 4 beams lit", profile)
        self.assertIn("Completionist", profile)

    def test_12_profile_shows_idea_language_and_secret_count(self):
        profile = self.session.get(url("/profile")).text
        self.assertIn("Test Site", profile)
        self.assertIn("Javascript", profile)
        self.assertRegex(profile, r"SECRET ACHIEVEMENTS · \d+ / \d+")
        self.assertIn("???", profile)  # locked ones stay hidden

    def test_13_leaderboard_lists_the_player(self):
        response = self.session.get(url("/leaderboard"), params={"course": "python", "level": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.username, response.text)

    # -- mentor -------------------------------------------------------

    def test_14_mentor_offline_keeps_the_game_playable(self):
        status = self.session.get(url("/api/mentor/status")).json()
        self.assertIn("reachable", status)
        if _tempdir is not None:
            self.assertFalse(status["reachable"])
            response = self.session.post(url("/api/mentor"), json={"question": "hint?", "course": "python", "level": 1})
            self.assertEqual(response.status_code, 503)
            self.assertFalse(response.json()["success"])
            self.assertIn("offline", response.json()["error"])

        # Malformed requests are rejected whatever the mentor's state.
        self.assertEqual(self.session.post(url("/api/mentor"), json={}).status_code, 400)

    # -- friends ------------------------------------------------------

    @staticmethod
    def panel(html, name):
        """The HTML of one tab panel on the friends page."""
        match = re.search(r'<div data-panel="%s"(.*?)(?=<div data-panel=|<section class="account-actions")' % name, html, re.S)
        return match.group(1) if match else ""

    def test_15_friend_requests_need_both_sides(self):
        other_session, other = new_user("t_friend")

        page = self.session.get(url("/friends"), params={"q": other[:10], "tab": "search"}).text
        self.assertIn(other, page)
        self.assertIn("ADD FRIEND", page)

        self.assertEqual(self.session.post(url("/friends/add"), data={"friend_id": "abc"}).status_code, 400)
        self.assertEqual(self.session.post(url("/friends/add"), data={"friend_id": "999999"}).status_code, 404)

        other_id = re.search(r'data-username="%s" data-user-id="(\d+)"' % other, page).group(1)
        my_id = re.search(r'data-me="(\d+)"', page).group(1)

        response = self.session.post(url("/friends/add"), data={"friend_id": my_id})
        self.assertIn("yourself", response.text)

        # 1. I send a request: it sits under SENT, not under FRIENDS.
        response = self.session.post(url("/friends/add"), data={"friend_id": other_id}, allow_redirects=False)
        self.assertEqual(response.status_code, 302)
        mine = self.session.get(url("/friends")).text
        self.assertIn('data-username="%s"' % other, self.panel(mine, "sent"))
        self.assertNotIn('data-username="%s"' % other, self.panel(mine, "friends"))
        self.assertIn("Friend request sent", mine)

        # 2. They see it under REQUESTS and accept by adding me back.
        theirs = other_session.get(url("/friends")).text
        self.assertIn('data-username="%s"' % self.username, self.panel(theirs, "requests"))
        response = other_session.post(url("/friends/add"), data={"friend_id": my_id}, allow_redirects=False)
        self.assertEqual(response.status_code, 302)

        # 3. Now both sides list each other as friends; the search shows FRIENDS.
        mine = self.session.get(url("/friends")).text
        self.assertIn('data-username="%s"' % other, self.panel(mine, "friends"))
        self.assertNotIn('data-username="%s"' % other, self.panel(mine, "sent"))
        theirs = other_session.get(url("/friends")).text
        self.assertIn('data-username="%s"' % self.username, self.panel(theirs, "friends"))
        search = self.session.get(url("/friends"), params={"q": other[:10]}).text
        self.assertIn("FRIENDS</span>", search)

        # 4. Removing ends it for both.
        response = self.session.post(url("/friends/remove"), data={"friend_id": other_id}, allow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('data-username="%s"' % other, self.panel(self.session.get(url("/friends")).text, "friends"))
        self.assertNotIn('data-username="%s"' % self.username, self.panel(other_session.get(url("/friends")).text, "friends"))

        # 5. A declined request disappears on both sides.
        other_session.post(url("/friends/add"), data={"friend_id": my_id})
        self.assertIn('data-username="%s"' % other, self.panel(self.session.get(url("/friends")).text, "requests"))
        self.session.post(url("/friends/decline"), data={"friend_id": other_id})
        self.assertNotIn('data-username="%s"' % other, self.panel(self.session.get(url("/friends")).text, "requests"))
        self.assertNotIn('data-username="%s"' % self.username, self.panel(other_session.get(url("/friends")).text, "sent"))

    # -- profile picture ----------------------------------------------

    def test_16_profile_picture_upload_and_remove(self):
        import base64, zlib, struct

        def png(width=4, height=4):
            raw = b"".join(b"\x00" + b"\xff\xff\xff" * width for _ in range(height))
            def chunk(kind, body):
                return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xffffffff)
            return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                    + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

        my_id = re.search(r'data-me="(\d+)"', self.session.get(url("/friends")).text).group(1)

        # A text file with a .png name is refused: the bytes are what count.
        response = self.session.post(url("/profile/picture"), files={"picture": ("fake.png", b"hello world", "image/png")})
        self.assertIn("not a PNG", response.text)

        response = self.session.post(url("/profile/picture"), files={"picture": ("me.png", png(), "image/png")}, allow_redirects=False)
        self.assertEqual(response.status_code, 302)

        profile = self.session.get(url("/profile")).text
        self.assertIn("Profile picture updated", profile)
        self.assertIn('class="avatar-img" src="/avatar/%s?v=png-' % my_id, profile)

        image = self.session.get(url("/avatar/%s" % my_id))
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image.headers["Content-Type"], "image/png")
        self.assertEqual(image.headers["X-Content-Type-Options"], "nosniff")
        self.assertTrue(image.content.startswith(b"\x89PNG"))
        width, height = struct.unpack(">II", image.content[16:24])
        self.assertIn((width, height), [(256, 256), (4, 4)])   # 256 with Pillow, original without

        # Oversized uploads are refused (before or after reading, either way with a message).
        response = self.session.post(url("/profile/picture"), files={"picture": ("big.png", png() + b"\x00" * (2 * 1024 * 1024), "image/png")})
        self.assertIn("2 MB", response.text)

        response = self.session.post(url("/profile/picture/remove"), allow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("avatar-img", self.session.get(url("/profile")).text)
        self.assertEqual(self.session.get(url("/avatar/%s" % my_id)).status_code, 404)

    # -- privacy + public profile --------------------------------------

    def test_17_privacy_controls_what_others_see(self):
        viewer, _viewer_name = new_user("t_viewer")
        mine = "/u/" + self.username

        # Defaults: profile open, progress + achievements visible, time only for friends.
        page = viewer.get(url(mine)).text
        self.assertEqual(viewer.get(url(mine)).status_code, 200)
        self.assertIn("OVERALL COMPLETION", page)
        self.assertIn("100%", page)
        self.assertIn("beams lit", page)
        self.assertIn("HIDDEN", page)          # time spent
        self.assertIn("ADD FRIEND", page)

        # My own name redirects to my profile; unknown names are 404.
        self.assertEqual(self.session.get(url(mine), allow_redirects=False).status_code, 302)
        self.assertEqual(viewer.get(url("/u/nobody_here_xyz")).status_code, 404)

        # Lock everything down.
        response = self.session.post(url("/profile/privacy"), data={
            "profile_visibility": "nobody", "show_progress": "nobody", "show_achievements": "nobody",
            "show_time": "nobody",   # checkboxes absent = off
        }, allow_redirects=False)
        self.assertEqual(response.status_code, 302)
        settings = self.session.get(url("/profile"), params={"tab": "settings"}).text
        self.assertIn("Privacy settings saved", settings)

        page = viewer.get(url(mine)).text
        self.assertIn("keeps this profile private", page)
        self.assertNotIn("OVERALL COMPLETION", page)
        self.assertNotIn('href="/u/%s"' % self.username, viewer.get(url("/leaderboard"), params={"board": "time"}).text)

        search = viewer.get(url("/friends"), params={"q": self.username[:10]}).text
        self.assertNotIn('data-username="%s"' % self.username, search)

        board = viewer.get(url("/leaderboard"), params={"course": "python", "level": 1}).text
        self.assertNotIn(self.username, board.split("board-table")[-1] if "board-table" in board else board)
        own = self.session.get(url("/leaderboard"), params={"course": "python", "level": 1}).text
        self.assertIn("hidden from the leaderboard", own)

        # Friends-only progress: visible once we are friends.
        self.session.post(url("/profile/privacy"), data={
            "profile_visibility": "everyone", "show_progress": "friends", "show_achievements": "friends",
            "show_time": "friends", "search_visible": "on", "leaderboard_times": "on",
        })
        page = viewer.get(url(mine)).text
        self.assertIn("OVERALL COMPLETION", page)
        self.assertIn("HIDDEN", page)
        self.assertNotIn("100%", page)

        viewer_id = re.search(r'data-me="(\d+)"', viewer.get(url("/friends")).text).group(1)
        my_id = re.search(r'data-me="(\d+)"', self.session.get(url("/friends")).text).group(1)
        viewer.post(url("/friends/add"), data={"friend_id": my_id})
        self.session.post(url("/friends/add"), data={"friend_id": viewer_id})
        page = viewer.get(url(mine)).text
        self.assertIn("YOUR FRIEND", page)
        self.assertIn("100%", page)
        self.assertNotIn("HIDDEN", page)

        # Back to the defaults for the later tests.
        self.session.post(url("/profile/privacy"), data={
            "profile_visibility": "everyone", "show_progress": "everyone", "show_achievements": "everyone",
            "show_time": "friends", "search_visible": "on", "leaderboard_times": "on",
        })

    # -- leaderboard ----------------------------------------------------

    def test_18_leaderboard_needs_a_course_and_filters_by_level(self):
        page = self.session.get(url("/leaderboard")).text
        self.assertIn("Choose a course above", page)
        self.assertIn('id="board-course"', page)

        self.assertIn("Choose a course first.", self.session.get(url("/leaderboard"), params={"course": ""}).text)
        self.assertIn("Choose a course first.", self.session.get(url("/leaderboard"), params={"course": "nope"}).text)
        self.assertIn("does not exist", self.session.get(url("/leaderboard"), params={"course": "python", "level": "999"}).text)

        page = self.session.get(url("/leaderboard"), params={"course": "python", "level": "1"}).text
        self.assertIn("LEVEL 01", page)
        self.assertIn(self.username, page)
        self.assertIn("Your best on this level", page)
        self.assertIn("PLAY THIS LEVEL", page)
        self.assertIn('href="/u/%s"' % self.username, page)

        page = self.session.get(url("/leaderboard"), params={"course": "internet", "level": "2", "order": "desc"}).text
        self.assertIn('value="desc" selected', page)
        self.assertIn("LEVEL 02", page)

    # -- time spent -----------------------------------------------------

    def test_19_time_ping_counts_on_the_server(self):
        first = self.session.post(url("/api/time/ping"), json={"seconds": 120}).json()
        self.assertTrue(first["success"])
        self.assertEqual(first["seconds"], 120)            # the browser's old counter is imported once

        second = self.session.post(url("/api/time/ping"), json={"seconds": 999999}).json()
        self.assertLess(second["seconds"], 125)            # later claims are ignored; only real seconds count
        self.assertGreaterEqual(second["seconds"], first["seconds"])

        self.assertIn('data-seconds="%d"' % second["seconds"], self.session.get(url("/profile")).text)

        if _tempdir is None:
            return

        # Simulate gaps by rewinding the last ping in the private database.
        conn = sqlite3.connect(os.path.join(_tempdir.name, "test.db"))
        def rewind(seconds):
            conn.execute("UPDATE users SET last_ping = last_ping - ? WHERE username = ?", (seconds, self.username))
            conn.commit()

        before = second["seconds"]
        rewind(50)                                          # a normal 30 s tick that ran a bit late
        after_short = self.session.post(url("/api/time/ping"), json={}).json()["seconds"]
        self.assertGreaterEqual(after_short - before, 50)
        self.assertLess(after_short - before, 55)

        rewind(600)                                         # tab closed / laptop asleep for ten minutes
        after_long = self.session.post(url("/api/time/ping"), json={}).json()["seconds"]
        self.assertLess(after_long - after_short, 3)        # idle time is not counted
        conn.close()

        # The time board lists the player with that total.
        board = self.session.get(url("/leaderboard"), params={"board": "time"}).text
        self.assertIn("MOST TIME IN THE ACADEMY", board)
        self.assertIn('href="/u/%s"' % self.username, board)
        self.assertIn("%02d:%02d:%02d" % (after_long // 3600, (after_long % 3600) // 60, after_long % 60), board)

    def test_20_faq_and_mentor_dock_on_every_page(self):
        for path in ("/", "/profile", "/friends", "/leaderboard", "/curriculum/python/1"):
            html = self.session.get(url(path)).text
            self.assertIn("Where do I find SecureMentor?", html, path)
            self.assertIn("usable on a phone or iPad", html, path)
            self.assertIn('id="mentor-dock"', html, path)

    # -- request badge, blocks, reports ----------------------------------

    def test_20b_music_credits_and_now_playing_setting(self):
        # Level JSON carries the track; quizzes carry none; obelisk levels loop.
        python = embedded_json(level_page(self.session, "python", 1), "level-data")["music"]
        self.assertEqual(python["file"], "/static/audio/music/ossuary-1-a-beginning.m4a")
        self.assertFalse(python["loop"])
        self.assertIn("Ossuary", python["title"])
        lab = embedded_json(level_page(self.session, "python", 11), "level-data")
        self.assertEqual(lab["music"]["title"], "Rhinoceros")                 # first time in the lab
        boss = embedded_json(level_page(self.session, "python", 17), "level-data")
        self.assertEqual(boss["boss_music"]["title"], "Cretaceous Dawn")
        self.assertTrue(boss["boss_music"]["loop"])
        self.assertIsNone(python.get("boss_music"))
        self.assertEqual(embedded_json(level_page(self.session, "python", 6), "level-data")["music"]["title"], "Blobby Samba")
        self.assertEqual(embedded_json(level_page(self.session, "internet", 2), "level-data")["music"]["title"], "Vibing Over Venus")
        quiz = next(l for l in COURSES["python"]["levels"] if l["kind"] == "quiz")
        self.assertIsNone(embedded_json(level_page(self.session, "python", quiz["number"]), "level-data")["music"])
        obelisk = COURSES["python"]["levels"][-1]
        self.assertTrue(embedded_json(level_page(self.session, "python", obelisk["number"]), "level-data")["music"]["loop"])

        # The files and the player script are served with browser-friendly types.
        track = self.session.head(url(python["file"]))
        self.assertEqual(track.status_code, 200)
        self.assertEqual(track.headers["Content-Type"], "audio/mp4")
        self.assertEqual(self.session.get(url("/static/js/audio.js")).status_code, 200)

        sfx = embedded_json(level_page(self.session, "python", 1), "level-data")["sfx"]
        self.assertEqual(sfx["slash"], "/static/audio/sfx/blade-slice.mp3")
        clip = self.session.head(url(sfx["slash"]))
        self.assertEqual(clip.status_code, 200)
        self.assertIn("audio/mpeg", clip.headers["Content-Type"])
        self.assertEqual(embedded_json(level_page(self.session, "python", quiz["number"]), "level-data")["sfx"]["win"], "/static/audio/sfx/win.wav")
        self.assertEqual(self.session.head(url(sfx["win"])).status_code, 200)
        crunch = self.session.head(url(sfx["crunch"]))
        self.assertEqual(crunch.status_code, 200)
        self.assertIn("audio/", crunch.headers["Content-Type"])
        self.assertEqual(embedded_json(level_page(self.session, "python", 13), "level-data")["music"]["title"], "Twisting")

        # Credits with the licence link sit in the footer of every page.
        for path in ("/", "/profile", "/friends"):
            html = self.session.get(url(path)).text
            for title in ("Ossuary 1 - A Beginning", "Vibing Over Venus", "Blobby Samba", "Cretaceous Dawn", "Rhinoceros", "Twisting", "Hiding Your Reality", "The Britons", "crunch 7"):
                self.assertIn(title, html, path)
            self.assertIn("Kevin MacLeod (incompetech.com)", html, path)
            self.assertIn("Blade_Slice_Metal_01", html, path)
            self.assertIn("Artninja (freesound.org)", html, path)
            self.assertIn("theplax (freesound.org)", html, path)
            self.assertIn("EVRetro (freesound.org)", html, path)
            self.assertIn("https://creativecommons.org/publicdomain/zero/1.0/", html, path)
            self.assertIn("http://creativecommons.org/licenses/by/4.0/", html, path)

        # The now-playing line follows the game setting.
        html = level_page(self.session, "python", 1)
        self.assertIn('id="hud-music"', html)
        self.assertIn('id="music-btn"', html)
        response = self.session.post(url("/profile/prefs"), data={})          # checkbox off
        self.assertIn("Game settings saved", response.text)
        self.assertNotIn('id="hud-music"', level_page(self.session, "python", 1))
        self.session.post(url("/profile/prefs"), data={"now_playing": "on"})
        self.assertIn('id="hud-music"', level_page(self.session, "python", 1))

    def test_20c_username_change_keeps_friends(self):
        friend_session, friend = new_user("t_rename")
        my_id = re.search(r'data-me="(\d+)"', self.session.get(url("/friends")).text).group(1)
        friend_id = re.search(r'data-me="(\d+)"', friend_session.get(url("/friends")).text).group(1)
        self.session.post(url("/friends/add"), data={"friend_id": friend_id})
        friend_session.post(url("/friends/add"), data={"friend_id": my_id})

        old_name = self.username
        new_name = "t_new_" + uuid.uuid4().hex[:6]

        response = self.session.post(url("/profile/username"), data={"username": "bad name!"})
        self.assertIn("letters, numbers and underscores", response.text)
        response = self.session.post(url("/profile/username"), data={"username": friend.upper()})
        self.assertIn("already taken", response.text)

        response = self.session.post(url("/profile/username"), data={"username": new_name})
        self.assertIn("Username changed to " + new_name, response.text)
        self.assertIn(new_name.upper(), response.text)                      # top bar follows the session

        # Friendship, progress and the friend's view survive the rename.
        self.assertIn('data-username="%s"' % new_name, self.panel(friend_session.get(url("/friends")).text, "friends"))
        self.assertIn('data-username="%s"' % friend, self.panel(self.session.get(url("/friends")).text, "friends"))
        self.assertEqual(friend_session.get(url("/u/" + new_name)).status_code, 200)
        self.assertEqual(friend_session.get(url("/u/" + old_name)).status_code, 404)
        self.assertIn("4 / 4 beams lit", self.session.get(url("/profile")).text)

        # A second change must wait 14 days; the settings tab says so.
        response = self.session.post(url("/profile/username"), data={"username": "t_again_" + uuid.uuid4().hex[:4]})
        self.assertIn("again in 14 days", response.text)
        self.assertIn("NEXT CHANGE IN 14 DAYS", self.session.get(url("/profile"), params={"tab": "settings"}).text)

        # Login works with the new name, not the old one.
        fresh = requests.Session()
        self.assertEqual(fresh.post(url("/login"), data={"username": new_name, "password": PASSWORD}, allow_redirects=False).status_code, 302)
        self.assertIn("incorrect", requests.post(url("/login"), data={"username": old_name, "password": PASSWORD}).text)

        type(self).username = new_name
        self.session.post(url("/friends/remove"), data={"friend_id": friend_id})

    def test_21_request_badge_block_and_report(self):
        other_session, other = new_user("t_block")
        my_id = re.search(r'data-me="(\d+)"', self.session.get(url("/friends")).text).group(1)
        other_id = re.search(r'data-me="(\d+)"', other_session.get(url("/friends")).text).group(1)

        # A pending request shows as a badge next to FRIENDS in the top bar.
        other_session.post(url("/friends/add"), data={"friend_id": my_id})
        self.assertIn('<span class="top-badge">1</span>', self.session.get(url("/")).text)

        # Blocking removes the request and hides both sides from each other.
        response = self.session.post(url("/friends/block"), data={"friend_id": other_id}, allow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("top-badge", self.session.get(url("/")).text)
        self.assertIn('data-username="%s"' % other, self.panel(self.session.get(url("/friends")).text, "blocked"))
        self.assertIn("keeps this profile private", other_session.get(url("/u/" + self.username)).text)
        self.assertNotIn('data-username="%s"' % self.username, other_session.get(url("/friends"), params={"q": self.username[:10]}).text)
        self.assertIn("add this person", other_session.post(url("/friends/add"), data={"friend_id": my_id}).text)
        mine = self.session.get(url("/u/" + other)).text
        self.assertIn("UNBLOCK", mine)
        self.assertNotIn("ADD FRIEND", mine)

        # Unblocking restores the normal state.
        self.session.post(url("/friends/unblock"), data={"friend_id": other_id})
        self.assertIn("ADD FRIEND", self.session.get(url("/u/" + other)).text)

        # Reports need a listed reason; a valid one is stored and acknowledged.
        response = other_session.post(url("/u/%s/report" % self.username), data={"reason": "nonsense"})
        self.assertIn("Pick a reason", response.text)
        response = other_session.post(url("/u/%s/report" % self.username), data={"reason": "spam", "note": "test report"})
        self.assertIn("report was sent", response.text)
        if _tempdir is not None:
            conn = sqlite3.connect(os.path.join(_tempdir.name, "test.db"))
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM reports WHERE reason = 'spam'").fetchone()[0], 1)
            conn.close()

    def test_22_friends_only_leaderboard(self):
        page = self.session.get(url("/leaderboard"), params={"course": "python", "level": "1", "friends": "1"}).text
        self.assertIn('name="friends" value="1" checked', page)
        rows = re.findall(r'<a class="board-player" href="/u/([^"]+)"', self.panel(page, "levels"))
        self.assertEqual(rows, [self.username])   # only me: no friends yet

    # -- password change, rate limit, deletion ---------------------------

    def test_23_change_password(self):
        response = self.session.post(url("/profile/password"), data={"current_password": "wrong", "new_password": "Abc!Def-2079x", "confirm_password": "Abc!Def-2079x"})
        self.assertIn("current password is not right", response.text)

        response = self.session.post(url("/profile/password"), data={"current_password": PASSWORD, "new_password": "weak", "confirm_password": "weak"})
        self.assertIn("at least 8 characters", response.text)

        response = self.session.post(url("/profile/password"), data={"current_password": PASSWORD, "new_password": "Abc!Def-2079x", "confirm_password": "Abc!Def-2079y"})
        self.assertIn("do not match", response.text)

        response = self.session.post(url("/profile/password"), data={"current_password": PASSWORD, "new_password": "Abc!Def-2079x", "confirm_password": "Abc!Def-2079x"})
        self.assertIn("Password changed", response.text)

        fresh = requests.Session()
        self.assertIn("incorrect", fresh.post(url("/login"), data={"username": self.username, "password": PASSWORD}).text)
        self.assertEqual(fresh.post(url("/login"), data={"username": self.username, "password": "Abc!Def-2079x"}, allow_redirects=False).status_code, 302)

    def test_24_login_rate_limit(self):
        _session, victim = new_user("t_limit")
        attacker = requests.Session()
        for _ in range(9):
            self.assertIn("incorrect", attacker.post(url("/login"), data={"username": victim, "password": "Nope!1234x"}).text)
        # the tenth failure locks the name; the right password is refused until the lock ends
        self.assertIn("Too many attempts", attacker.post(url("/login"), data={"username": victim, "password": "Nope!1234x"}).text)
        self.assertIn("Too many attempts", attacker.post(url("/login"), data={"username": victim, "password": PASSWORD}).text)
        # other accounts are not affected
        self.assertEqual(requests.post(url("/login"), data={"username": self.username, "password": "Abc!Def-2079x"}, allow_redirects=False).status_code, 302)

    def test_25_delete_account(self):
        doomed, name = new_user("t_doomed")
        self.assertIn("Tick the box", doomed.post(url("/profile/delete"), data={"password": PASSWORD}).text)
        self.assertIn("not right", doomed.post(url("/profile/delete"), data={"password": "Wrong!Pass1", "confirm": "on"}).text)

        response = doomed.post(url("/profile/delete"), data={"password": PASSWORD, "confirm": "on"})
        self.assertIn("account and all its progress were deleted", response.text)
        self.assertEqual(doomed.get(url("/profile"), allow_redirects=False).status_code, 302)
        self.assertIn("incorrect", requests.post(url("/login"), data={"username": name, "password": PASSWORD}).text)
        self.assertEqual(self.session.get(url("/u/" + name)).status_code, 404)

    def test_26_logout_clears_the_session(self):
        self.session.get(url("/logout"))
        self.assertEqual(self.session.get(url("/profile"), allow_redirects=False).status_code, 302)
        response = self.session.post(url("/api/level/start"), json={"course": "python", "level": 1}, allow_redirects=False)
        self.assertEqual(response.status_code, 302)


if __name__ == "__main__":
    unittest.main()
