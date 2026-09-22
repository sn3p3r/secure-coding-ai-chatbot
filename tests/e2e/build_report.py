"""
Turns tests/report/results.json (written by the Playwright suite) into
a presentation-ready PDF, rendered by the same Chromium the tests use.

    python3 -m pytest tests/e2e -q
    python3 tests/e2e/build_report.py [--out path.pdf]
"""

import base64
import html
import json
import os
import platform
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT_DIR = os.path.join(ROOT, "tests", "report")
RESULTS = os.path.join(REPORT_DIR, "results.json")
DEFAULT_OUT = os.path.join(REPORT_DIR, "Cyber-Academy-Playwright-Test-Report.pdf")


def git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception:
        return "n/a"


def image_tag(path):
    if not path or not os.path.isfile(path):
        return ""
    with open(path, "rb") as handle:
        data = base64.b64encode(handle.read()).decode("ascii")
    return '<img class="shot" src="data:image/png;base64,%s" alt="">' % data


def esc(text):
    return html.escape(str(text))


def build_html(data):
    results = data["results"]
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    for r in results:
        counts[r["status"] if r["status"] in counts else "failed"] += 1
    total = len(results)
    duration = sum(r["duration"] or 0 for r in results)

    try:
        from playwright import __version__ as pw_version
    except Exception:
        pw_version = subprocess.check_output([sys.executable, "-m", "pip", "show", "playwright"], text=True).split("Version:")[1].split()[0]

    suites = []
    for r in results:
        if not suites or suites[-1]["name"] != r["suite"]:
            suites.append({"name": r["suite"], "tests": []})
        suites[-1]["tests"].append(r)

    verdict = "All %d tests passed." % total if counts["failed"] == 0 else "%d of %d tests failed." % (counts["failed"], total)

    parts = []
    parts.append("""
<style>
  @page { size: A4; margin: 18mm 16mm; }
  body { font-family: -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif; color: #111; font-size: 11pt; line-height: 1.45; margin: 0; }
  h1 { font-size: 26pt; margin: 0 0 4px; letter-spacing: -0.5px; }
  h2 { font-size: 16pt; margin: 28px 0 10px; border-bottom: 2px solid #111; padding-bottom: 4px; page-break-after: avoid; }
  h3 { font-size: 12.5pt; margin: 18px 0 6px; page-break-after: avoid; }
  .cover { page-break-after: always; padding-top: 60px; }
  .kicker { font-size: 10pt; letter-spacing: 2px; color: #666; text-transform: uppercase; }
  .meta { margin-top: 30px; border-collapse: collapse; }
  .meta td { padding: 5px 18px 5px 0; vertical-align: top; }
  .meta td:first-child { color: #666; width: 150px; }
  .summary { display: flex; gap: 12px; margin: 14px 0 6px; }
  .tile { flex: 1; border: 1px solid #ccc; padding: 10px 12px; }
  .tile b { display: block; font-size: 20pt; }
  .tile.pass { border-color: #2f8f4e; } .tile.fail { border-color: #b3261e; }
  table.tests { width: 100%; border-collapse: collapse; margin: 8px 0 14px; font-size: 10pt; }
  table.tests th { text-align: left; border-bottom: 1px solid #111; padding: 6px 6px; font-weight: 600; }
  table.tests td { border-bottom: 1px solid #ddd; padding: 6px 6px; vertical-align: top; }
  .status { display: inline-block; padding: 1px 8px; border-radius: 3px; font-size: 9pt; font-weight: 600; color: #fff; }
  .status.passed { background: #2f8f4e; } .status.failed { background: #b3261e; } .status.skipped { background: #888; }
  .case { page-break-inside: avoid; margin: 0 0 18px; border: 1px solid #ddd; padding: 12px 14px; }
  .case h3 { margin: 0 0 4px; }
  .case .id { color: #666; font-size: 9.5pt; }
  ol.steps { margin: 8px 0 8px 18px; padding: 0; font-size: 10pt; }
  ol.steps li { margin: 2px 0; }
  .expect { font-size: 10pt; margin: 4px 0; }
  .shot { display: block; width: auto; max-width: 100%; max-height: 300px; border: 1px solid #ddd; margin-top: 8px; }
  pre.err { background: #fbeaea; border: 1px solid #b3261e; padding: 8px; font-size: 8.5pt; white-space: pre-wrap; }
  ul.plain { margin: 6px 0 6px 18px; padding: 0; }
  code { font-family: Menlo, Consolas, monospace; font-size: 9.5pt; background: #f1f1f1; padding: 1px 4px; }
  .small { font-size: 9.5pt; color: #444; }
</style>
""")

    parts.append("""
<div class="cover">
  <div class="kicker">End-to-end test report</div>
  <h1>Cyber Academy</h1>
  <div class="small">Playwright (Python) · Chromium · automated browser tests</div>
  <table class="meta">
    <tr><td>Project</td><td>Cyber Academy — an educational 2D pixel story game (Flask + SQLite + HTML/CSS/JavaScript)</td></tr>
    <tr><td>Build under test</td><td><code>%(commit)s</code> on branch <code>%(branch)s</code></td></tr>
    <tr><td>Run date</td><td>%(date)s</td></tr>
    <tr><td>Tool</td><td>Playwright for Python %(pw)s with pytest-playwright, headless Chromium (Playwright's bundled build)</td></tr>
    <tr><td>Environment</td><td>%(os)s · Python %(py)s · viewport 1300 × 820</td></tr>
    <tr><td>Test data</td><td>A private copy of the app on a free port with an empty database; every account, friendship and level time in this report was created by the tests themselves. SecureMentor was switched off (no API key), so the game ran in its offline mode.</td></tr>
    <tr><td>Result</td><td><b>%(verdict)s</b></td></tr>
  </table>
</div>
""" % {
        "commit": git("rev-parse", "--short", "HEAD") + " · " + git("log", "-1", "--format=%s"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "date": data.get("generated", time.strftime("%Y-%m-%d %H:%M")),
        "pw": pw_version, "os": platform.platform(), "py": platform.python_version(), "verdict": esc(verdict),
    })

    parts.append("<h2>1. Summary</h2>")
    parts.append('<div class="summary"><div class="tile"><b>%d</b>tests</div><div class="tile pass"><b>%d</b>passed</div><div class="tile fail"><b>%d</b>failed</div><div class="tile"><b>%d</b>skipped</div><div class="tile"><b>%.0f s</b>total test time</div></div>'
                 % (total, counts["passed"], counts["failed"], counts["skipped"], duration))
    parts.append("<p>%s Each test opens the real site in Chromium, fills the real forms, presses the real keys and reads back what the page shows. Steps, expected results, outcomes and a screenshot taken at the end of every test follow in section 3.</p>" % esc(verdict))

    parts.append("<h2>2. Scope</h2>")
    parts.append("""
<p><b>Covered</b></p>
<ul class="plain">
  <li>Sign-up rules (live password checklist, username rule), login, logout, session protection</li>
  <li>Character creation and the gate in front of the first level</li>
  <li>Playing a level: matrix intro, story pages, HUD, movement and jumping, guide dialogue rotation, terminal answers, story-level exits, items (candy, hint chips, dropping with Q)</li>
  <li>Puzzle terminals of the Internet course: multiple choice, wire board, IP assignment, packet routing</li>
  <li>Friends: search, requests, accepting, profile links, blocking, the top-bar badge</li>
  <li>Profile settings: privacy controls, picture upload (real and fake files), username change with the 14-day rule, password change</li>
  <li>Leaderboard: course/level filter, sort order, friends-only view, time-in-the-Academy board</li>
  <li>Audio: level track and now-playing line, mute with M and ♪, effect files, the credits tab</li>
  <li>The obelisk finale and a finished player's profile</li>
</ul>
<p><b>Not covered by browser tests</b></p>
<ul class="plain">
  <li>Whether sound is audible: headless Chromium has no audio output. The tests check that the right file is loaded and reported as playing.</li>
  <li>Walking across a whole map. The map is a canvas, so tests place the player next to the thing under test through the game's own debug handle and then press the real keys. Movement itself is tested separately.</li>
  <li>SecureMentor answers, which need a live API key. The offline behaviour is covered by the HTTP suite.</li>
  <li>Server-side rules in isolation (answer checking, rate limiting, privacy filtering): these are covered by the separate unit and HTTP suites (63 tests), not repeated here.</li>
</ul>
""")

    parts.append("<h2>3. Results by suite</h2>")
    for index, suite in enumerate(suites, 1):
        parts.append("<h3>3.%d %s</h3>" % (index, esc(suite["name"])))
        parts.append('<table class="tests"><tr><th style="width:52px">ID</th><th>Test</th><th style="width:70px">Result</th><th style="width:60px">Time</th></tr>')
        for j, r in enumerate(suite["tests"], 1):
            parts.append('<tr><td>%d.%d</td><td>%s</td><td><span class="status %s">%s</span></td><td>%.1f s</td></tr>'
                         % (index, j, esc(r["title"]), r["status"], r["status"].upper(), r["duration"] or 0))
        parts.append("</table>")

    parts.append("<h2>4. Test cases</h2>")
    parts.append('<p class="small">Steps are listed in the order the test performed them; the screenshot is the state of the page when the test finished.</p>')
    for index, suite in enumerate(suites, 1):
        for j, r in enumerate(suite["tests"], 1):
            parts.append('<div class="case">')
            parts.append('<div class="id">%d.%d · %s · <code>%s</code></div>' % (index, j, esc(suite["name"]), esc(r["name"])))
            parts.append('<h3>%s <span class="status %s">%s</span></h3>' % (esc(r["title"]), r["status"], r["status"].upper()))
            if r["steps"]:
                parts.append('<ol class="steps">')
                for step in r["steps"]:
                    text = step["text"]
                    if text.startswith("Expect "):
                        text = "<b>Expected:</b> " + esc(text[len("Expect "):])
                    else:
                        text = esc(text)
                    parts.append("<li>%s</li>" % text)
                parts.append("</ol>")
            parts.append('<div class="expect small">Duration %.1f s</div>' % (r["duration"] or 0))
            if r["error"]:
                parts.append('<pre class="err">%s</pre>' % esc(r["error"]))
            parts.append(image_tag(r["screenshot"]))
            parts.append("</div>")

    parts.append("<h2>5. Defects and follow-ups</h2>")
    failed = [r for r in results if r["status"] != "passed"]
    if failed:
        parts.append("<ul class='plain'>")
        for r in failed:
            parts.append("<li><b>%s</b> — see its error in section 4.</li>" % esc(r["title"]))
        parts.append("</ul>")
    else:
        parts.append("<p>No defects were found in this run. While the suite was being written, two expectations had to be corrected because they described the game wrongly (a solved terminal shows the ACCESS GRANTED card and opens the door; the level only reads LEVEL COMPLETE at the exit), and one selector because the wire board draws curved paths, not straight lines. No change to the application was needed.</p>")

    parts.append("<h2>6. How to run</h2>")
    parts.append("""
<pre><code>pip install -r requirements-dev.txt        # includes pytest-playwright
python3 -m playwright install chromium     # once
python3 -m pytest tests/e2e -q             # runs the suite, writes tests/report/results.json + screenshots
python3 tests/e2e/build_report.py          # renders this PDF</code></pre>
<p class="small">The suite lives in <code>tests/e2e/</code>: <code>conftest.py</code> starts the app and records steps, one file per suite holds the tests. Add <code>--headed</code> to watch the browser.</p>
""")
    return "\n".join(parts)


def main():
    out = DEFAULT_OUT
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    with open(RESULTS, encoding="utf-8") as handle:
        data = json.load(handle)
    page_html = build_html(data)
    html_path = os.path.join(REPORT_DIR, "report.html")
    with open(html_path, "w", encoding="utf-8") as handle:
        handle.write("<!doctype html><html><head><meta charset='utf-8'><title>Cyber Academy test report</title></head><body>" + page_html + "</body></html>")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("file://" + html_path)
        page.wait_for_timeout(300)
        page.pdf(path=out, format="A4", print_background=True, margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
                 display_header_footer=True,
                 header_template="<div></div>",
                 footer_template="<div style='font-size:8px;color:#777;width:100%;text-align:center;font-family:Helvetica,Arial'>Cyber Academy · Playwright test report · page <span class='pageNumber'></span> of <span class='totalPages'></span></div>")
        browser.close()
    print("wrote", out, "(%d results)" % len(data["results"]))


if __name__ == "__main__":
    main()
