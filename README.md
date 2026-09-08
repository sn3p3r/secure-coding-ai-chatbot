# Cyber Academy

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
cp .env.example .env               # then fill in the values
python3 app.py                     # http://127.0.0.1:5000
```

`.env` values:

| Variable            | Purpose                                                        |
|---------------------|----------------------------------------------------------------|
| `ANTHROPIC_API_KEY` | SecureMentor. Optional - without it the mentor shows OFFLINE.  |
| `SECRET_KEY`        | Signs session cookies. Required before deploying.              |
| `FLASK_DEBUG`       | `1` for development, `0` for deployment.                       |
| `PORT`              | Change if 5000 is taken (macOS AirPlay uses it).               |

The database (`academy.db`) is created automatically on first run and is
git-ignored because it holds user accounts.

## Playing

| Key            | Action                              |
|----------------|-------------------------------------|
| `A` / `D`      | move                                |
| `W` / `Space`  | jump                                |
| `E`            | talk / read / use terminal          |
| `F` or click   | use the item in the selected slot   |
| `1` - `5`      | select inventory slot               |
| `Enter`        | next dialogue line                  |

Login → Home → choose a course → create your character → play. Each
course page shows the section map on the left (current level in bold),
the game window in the middle (fullscreen button bottom-right), and the
lesson notes below.

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
2. Draw the map as 12 rows of 40 characters. `P` spawn, `N` BYTE,
   `C` terminal, `D` door, `X` exit, `I`/`Q`/`K` items, `s`/`h`/`M` enemies.
3. Run `python3 check_levels.py` - it verifies reachability with the
   player's real jump (2 tiles up, 3 across) and that no answer keys leak.

Challenge types: `mcq`, `text_answer`, `python_lines` (regex per line),
`code_review`, `fill_blank`, `order_code`, `quiz`.

## Deploying

* Set a real `SECRET_KEY` and `FLASK_DEBUG=0`.
* Serve with a WSGI server (e.g. `gunicorn app:app`) behind HTTPS -
  `app.run` is for development only.
* Never commit `.env` or `academy.db` (both are in `.gitignore`).
