# Cyber Academy

> Basically this aims to build an ai chatbot that makes learning entertaining and tailored to you.

A browser-based 2D pixel story game that teaches beginners **Python**,
**Cybersecurity**, **Internet Fundamentals** and **Secure Coding**.
Every level opens with short lesson notes, drops you into a small
platformer map, and ends at a terminal challenge that is checked on the
server. Checkpoint quizzes sit between sections, and **SecureMentor**
(Claude) is available in a side panel for hints - it never hands over
the answer.

Built with Flask + SQLite + plain HTML/CSS/JavaScript. No frameworks,
no image assets: every sprite and badge is drawn with `fillRect`.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 app.py                     # http://127.0.0.1:5000
```

Create a `.env` file next to `app.py` (it is git-ignored) with these
values, or set them as environment variables:

| Variable            | Purpose                                                        |
|---------------------|----------------------------------------------------------------|
| `ANTHROPIC_API_KEY` | SecureMentor. Optional - without it the mentor shows OFFLINE.  |
| `SECRET_KEY`        | Signs session cookies. Required before deploying.              |
| `FLASK_DEBUG`       | `1` for development, `0` for deployment.                       |
| `PORT`              | Change if 5000 is taken (macOS AirPlay uses it).               |
| `ACADEMY_DB`        | Path of the SQLite file (default `academy.db`).                |
| `ACADEMY_AVATARS_DIR` | Folder for uploaded profile pictures (default `data/avatars`). |

The database (`academy.db`) is created automatically on first run and is
git-ignored because it holds user accounts.

## Playing

| Key            | Action                              |
|----------------|-------------------------------------|
| `A` / `D`      | move                                |
| `W` / `Space`  | jump                                |
| `E`            | talk / read / use terminal / door   |
| `F` or click   | use the selected item (swing, eat)  |
| `Q`            | drop the selected item              |
| `1` - `5`      | select inventory slot               |
| `Enter`        | next dialogue line                  |

Login → Home → choose a course → create your character → play. Each
course page shows the section map on the left (current level in bold),
the game window in the middle (fullscreen button bottom-right), and the
lesson notes below.

The **FRIENDS** tab in the top bar searches registered accounts by
username and sends a friend request; you are friends once the other
person adds you back (REQUESTS and SENT tabs). A friend's card shows
their levels, percent, lit beams and secret-achievement count, and links
to their profile page. The profile keeps the badges, the obelisk beams,
the secret-achievement count, the website idea from the Internet course
and the language chosen for Secure Coding. Its SETTINGS & PRIVACY tab
takes a profile picture (PNG/JPEG/GIF/WebP, 2 MB) and decides who can
open your profile, see your progress, achievements and time spent,
find you in search, and see your times on the leaderboard. The
leaderboard lists every player's best time on one chosen level, fastest
or slowest first, with a friends-only switch. A pending request shows as
a badge on FRIENDS. From another player's page you can block them (they
can no longer request, search or open you) or report them (stored in
the database and `data/reports.jsonl` for the site owner). The account
section changes the password or deletes the account with everything in
it. Five wrong passwords lock a username for five minutes. Uploaded
pictures are shrunk to a 256 px square when Pillow is installed. Every signed-in page ends with a short FAQ, and the
SecureMentor tab peeks up from the bottom-right corner on each page load.

## Project layout

```
app.py              Flask routes (auth, quiz, profile, curriculum, level API, mentor)
progress.py         SQLite progress, badges, leaderboard, migrations
challenges.py       Server-side answer checking (nothing the player types is executed)
curriculum.py       Assembles the courses; builds the public level JSON and mentor briefing
courses/            One data file per course + shared helpers and the map legend
mentor.py           SecureMentor (Anthropic client, system prompt, status ping)
check_levels.py     Validates every map and challenge - run it after editing a course
templates/          Jinja pages (course.html hosts the game window)
static/js/game.js   The 2D engine: tiles, physics, enemies, boss, challenge UIs
static/js/sprite.js Pixel character used by the game and the character page
static/js/badges.js Pixel badges on the profile
static/js/app.js    Site-wide: timer, quiz, SecureMentor panel
static/css/style.css
experiments/        Standalone entropy / hashing demos (not part of the app)
```

## Adding a level

1. Add a `level(...)` entry to the right file in `courses/` (see
   `courses/common.py` for the field list and the map legend).
2. Draw the map as 12 rows of 40+ characters (all rows the same width).
   `P` spawn, `N` guide, `C` terminal, `D` door, `k` locked door (needs a
   DOOR CODE), `X` exit, `v` vent exit (needs the VENT KEY), `!` wire mouth
   or HDMI port, `I`/`Q`/`K` items, `[` bug cage, `s`/`h`/`c`/`b`/`z` enemies
   (`z` = packet sniffer), `M`/`Y`/`R` bosses, `m` walkable mentor bot,
   `%` live data stream (deadly - the player is sent back to the last
   ledge), `O` obelisk and `@` its button (finale levels only).
   The engine adds a solid frame above every door so it cannot be jumped.
3. Run `python3 check_levels.py` - it verifies reachability with the
   player's real jump (2 tiles up, 3 across), interactable spacing, and
   that no answer keys leak.

Challenge types: `mcq`, `text_answer`, `python_lines` (regex per line),
`code_review`, `fill_blank`, `order_code`, `quiz`, `swipe` (a deck judged
one card at a time - scam-or-legit, or safe-or-unsafe code), `wires`
(drag each cable onto the right port), `route_packets` (drag packets to
the machine with the matching IP, optionally through DNS), `ip_assign`
(type a free, valid address on the network), `idea` (the player's website
idea - saved to the profile and to `data/website_ideas.jsonl`),
`language` (choose python or javascript for the Secure Coding course),
`walk` (story level - reach the exit). A level can carry
`challenge_by_language={"python": {...}, "javascript": {...}}` and the
server picks the variant matching the player's saved choice.

Level flags: `no_lesson` (story only), `dark` (lights fade until every bug
is dead), `door_by_bugs`, `gate`, `finale`, `bugs` (malware labels),
`guide` (name of the in-game voice), `start_items`, `mimic` (desk levels:
the monitor mirrors the player), `code_lines` (appear on the monitor as
the player runs), `obelisk` (the shared last level of every course: press
the button, watch the beam, the beam stays lit on every later visit).
Passing any door saves a checkpoint on the server; dying or reloading
resumes there. Inventories are kept per course.

Secret achievements live in `achievements.py` (kill counts, level records,
quizzes, the Completionist badge for lighting all four beams, and the
Collector for earning everything else). The profile shows only how many
exist and which ones are already earned.

## Deploying

The first deployment version runs under gunicorn:

```bash
pip install -r requirements.txt
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export FLASK_DEBUG=0 PORT=8000
gunicorn --preload --workers 2 --bind 0.0.0.0:$PORT app:app
```

* `Procfile` runs that same command on Heroku-style hosts (Render,
  Railway, Fly). Set `SECRET_KEY`, `FLASK_DEBUG=0` and optionally
  `ANTHROPIC_API_KEY` in the host's environment settings, never in git.
* `Dockerfile` builds the same thing as a container. Mount a volume at
  `/data` (the image sets `ACADEMY_DB=/data/academy.db`) so accounts
  survive redeploys.
* `ACADEMY_DB` points the SQLite file at a persistent disk; the tables
  are created and migrated automatically on start-up.
* Put HTTPS in front (the host's load balancer or a reverse proxy) -
  session cookies are `HttpOnly` and `SameSite=Lax`.
* Never commit `.env` or `academy.db` (both are in `.gitignore`).
