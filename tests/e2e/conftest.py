"""
Playwright end-to-end suite for Cyber Academy.

    python3 -m pytest tests/e2e -q            # run (Chromium, headless)
    python3 tests/e2e/build_report.py         # then build the PDF report

The suite starts its own copy of the app on a free port with a
throw-away database and the mentor switched off, drives it in a real
Chromium browser, records every step, and screenshots every test. The
results land in tests/report/ (git-ignored with the rest of tests/).
"""

import json
import os
import re
import socket
import struct
import subprocess
import sys
import tempfile
import time
import uuid
import zlib

import pytest
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

REPORT_DIR = os.path.join(ROOT, "tests", "report")
SHOT_DIR = os.path.join(REPORT_DIR, "shots")
RESULTS_FILE = os.path.join(REPORT_DIR, "results.json")

PASSWORD = "Academy!2026-Test"
VIEWPORT = {"width": 1300, "height": 820}

_results = []
_current = {"steps": [], "page": None}


# ---------------------------------------------------------------------
# The app under test
# ---------------------------------------------------------------------

def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def server():
    tempdir = tempfile.TemporaryDirectory(prefix="cyber-academy-e2e-")
    port = _free_port()
    env = dict(os.environ)
    env.update({
        "ACADEMY_DB": os.path.join(tempdir.name, "e2e.db"),
        "ACADEMY_IDEAS_FILE": os.path.join(tempdir.name, "ideas.jsonl"),
        "ACADEMY_REPORTS_FILE": os.path.join(tempdir.name, "reports.jsonl"),
        "ACADEMY_AVATARS_DIR": os.path.join(tempdir.name, "avatars"),
        "PORT": str(port),
        "FLASK_DEBUG": "0",
        "SECRET_KEY": "e2e-" + uuid.uuid4().hex,
        "ANTHROPIC_API_KEY": "",
    })
    log = open(os.path.join(tempdir.name, "server.log"), "w")
    process = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    url = "http://127.0.0.1:%d" % port

    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            if requests.get(url + "/login", timeout=2).status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(0.2)
    else:
        process.terminate()
        raise RuntimeError("the app did not start")

    yield {"url": url, "db": env["ACADEMY_DB"], "env": env}

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    log.close()
    tempdir.cleanup()


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    # Headless Chromium refuses autoplay without a gesture; the game starts
    # music on the START click, but the flag keeps the check deterministic.
    return {**browser_type_launch_args, "args": ["--autoplay-policy=no-user-gesture-required"]}


@pytest.fixture(scope="module")
def ctx(browser, server):
    """One browser context (one signed-in person) per test module."""
    context = browser.new_context(base_url=server["url"], viewport=VIEWPORT)
    yield context
    context.close()


@pytest.fixture(scope="module")
def pg(ctx):
    page = ctx.new_page()
    page.set_default_timeout(8000)
    yield page
    page.close()


@pytest.fixture(scope="module")
def other_ctx(browser, server):
    """A second person, for friends / privacy tests."""
    context = browser.new_context(base_url=server["url"], viewport=VIEWPORT)
    yield context
    context.close()


@pytest.fixture(scope="module")
def other(other_ctx):
    page = other_ctx.new_page()
    page.set_default_timeout(8000)
    yield page
    page.close()


# ---------------------------------------------------------------------
# Steps + screenshots + results (read by build_report.py)
# ---------------------------------------------------------------------

@pytest.fixture
def steps(request):
    """Call steps("...") before each action; the report lists them in order."""
    _current["steps"] = []
    started = time.time()

    def record(text):
        _current["steps"].append({"t": round(time.time() - started, 2), "text": text})

    return record


@pytest.fixture(autouse=True)
def _capture(request):
    """After every test: screenshot the page the test used, record the outcome."""
    yield
    page = None
    for name in ("pg", "other"):
        if name in request.fixturenames:
            page = request.getfixturevalue(name)
            if name == "pg":
                break
    os.makedirs(SHOT_DIR, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", request.node.nodeid.lower()).strip("-")[-90:]
    shot = os.path.join(SHOT_DIR, slug + ".png")
    try:
        if page is not None and not page.is_closed():
            page.screenshot(path=shot, full_page=False)
        else:
            shot = None
    except Exception:
        shot = None
    report = getattr(request.node, "_report_call", None)
    _results.append({
        "nodeid": request.node.nodeid,
        "module": request.node.module.__name__,
        "suite": (request.node.module.__doc__ or request.node.module.__name__).strip().splitlines()[0],
        "name": request.node.name,
        "title": (request.node.function.__doc__ or request.node.name).strip().splitlines()[0],
        "doc": (request.node.function.__doc__ or "").strip(),
        "steps": list(_current["steps"]),
        "status": report.outcome if report else "unknown",
        "duration": round(report.duration, 2) if report else None,
        "error": (report.longreprtext[-1500:] if report and report.failed else ""),
        "screenshot": shot,
    })


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        item._report_call = report


def pytest_sessionfinish(session, exitstatus):
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as handle:
        json.dump({
            "generated": time.strftime("%Y-%m-%d %H:%M"),
            "exit_status": int(exitstatus),
            "results": _results,
        }, handle, indent=2)


# ---------------------------------------------------------------------
# Helpers the tests share
# ---------------------------------------------------------------------

def new_name(prefix="pw"):
    return "%s_%s" % (prefix, uuid.uuid4().hex[:6])


def signup(page, name, password=PASSWORD):
    """The real sign-up form; returns the username."""
    page.goto("/signup")
    page.fill("#username", name)
    page.fill("#password", password)
    page.fill("#confirm_password", password)
    page.click("button.login-submit")
    page.wait_for_url(re.compile(r"/$"))
    return name


def choose_character(page):
    page.goto("/character")
    for field, value in (("gender", "female"), ("hair", "long"), ("hair_color", "blue"), ("outfit", "green")):
        pick(page, field, value)
    page.click("button.large-button")
    page.wait_for_url(re.compile(r"/$"))


def pick(page, field, value):
    """The character radios are styled chips: click the chip, then confirm the radio took it."""
    page.click("label.option-chip:has(input[name=%s][value=%s])" % (field, value))
    assert page.is_checked("input[name=%s][value=%s]" % (field, value))


def open_level(page, course, number):
    page.goto("/curriculum/%s/%d" % (course, number))
    page.wait_for_selector("#btn-start")


def start_level(page):
    """Press START, skip the matrix intro and the story pages, return when the player has control."""
    page.click("#btn-start")
    page.wait_for_function("() => window.cyberGame !== undefined")
    for _ in range(30):
        phase = page.evaluate("() => cyberGame.state.phase")
        if phase == "play":
            return
        page.keyboard.press("Enter")
        page.wait_for_timeout(250)
    raise AssertionError("the level never reached the play phase (phase=%s)" % page.evaluate("() => cyberGame.state.phase"))


def game(page, expression):
    return page.evaluate("() => (%s)" % expression)


def teleport(page, entity_type, offset_x=-14, item=None):
    """Put the player next to an entity (the map is a canvas, so this stands in for walking)."""
    found = page.evaluate(
        """([kind, item, dx]) => {
            const g = cyberGame;
            const target = g.entities.find(e => e.type === kind && (!item || e.item === item));
            if (!target) return null;
            g.player.x = target.x + dx;
            g.player.y = target.y + (target.h || 16) - g.player.h;
            g.player.vy = 0;
            g.step(2);
            return { x: target.x, y: target.y };
        }""",
        [entity_type, item, offset_x],
    )
    assert found is not None, "no %s entity on this level" % entity_type
    return found


def press(page, key, hold_ms=0):
    if hold_ms:
        page.keyboard.down(key)
        page.wait_for_timeout(hold_ms)
        page.keyboard.up(key)
    else:
        page.keyboard.press(key)


def dialogue_text(page):
    return page.text_content("#dialogue-text") or ""


def close_dialogue(page):
    for _ in range(8):
        if game(page, "cyberGame.state.phase") != "dialogue":
            return
        page.keyboard.press("Enter")
        page.wait_for_timeout(120)


def expect_access_granted(page):
    """The terminal accepted the answer: result card up, level marked solved, door open."""
    page.wait_for_selector("#overlay-result:not(.hidden)")
    assert "ACCESS GRANTED" in page.text_content("#result-label")
    assert game(page, "cyberGame.state.solved") is True


def walk_out(page):
    """Close the result card and step onto the exit: the level ends with LEVEL COMPLETE!"""
    page.click("#result-actions button")
    page.wait_for_selector("#overlay-result", state="hidden")
    teleport(page, "exit", offset_x=0)
    page.wait_for_function("() => document.getElementById('hud-objective').textContent.includes('LEVEL COMPLETE')")


def tiny_png(path, colour=(58, 123, 213)):
    """A 64x64 PNG written with the standard library (for the picture test)."""
    width = height = 64
    raw = b"".join(b"\x00" + bytes(colour) * width for _ in range(height))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def grant_everything(server, username):
    """tools/grant_all.py against the suite's private database."""
    env = dict(server["env"])
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "grant_all.py"), username], env=env, check=True, capture_output=True)
