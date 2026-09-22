# Cyber Academy - test cases

Two automated suites plus a short manual checklist for things only a
person can judge (feel, readability, pixel art).

```bash
pip install -r requirements-dev.txt
python3 check_levels.py                  # map + answer-leak validator
python3 -m unittest discover -s tests    # unit tests + HTTP tests
```

`tests/test_api.py` starts a private copy of the app (throw-away
database, mentor forced offline) and drives it with `requests`. Set
`BASE_URL` to run the same cases against a deployed copy.

## A. Server-side answer checking (unit, `tests/test_challenges.py`)

| ID  | Area          | Case                                                                 | Expected                                              | Automated |
|-----|---------------|----------------------------------------------------------------------|-------------------------------------------------------|-----------|
| A1  | mcq           | correct index / wrong index / string / out of range                  | True / level's `wrong` text / False / False           | yes       |
| A2  | text_answer   | accepted word with odd case and spaces; unrelated word; non-string   | True; False; False                                    | yes       |
| A3  | python_lines  | matching code; wrong first line; missing line; extra lines; empty    | True; "Line 1 isn't right yet." (never the answer); "Line 2 is missing."; line-count message; False | yes |
| A4  | fill_blank    | correct blanks; empty blank; wrong blank count                       | True; "Blank 2 is empty."; False                      | yes       |
| A5  | order_code    | correct order via shuffled indices; wrong order; duplicate indices   | True; points at first wrong line; False               | yes       |
| A6  | code_review   | right line + reason; right line wrong reason; wrong line             | True; "Right line, but..."; "Line 1 is not the problem." | yes    |
| A7  | quiz          | all right; one wrong; missing answers                                | True; names only the wrong question; "Answer every question." | yes |
| A8  | swipe         | whole deck; single-card verdicts; malformed card index / verdict     | True / message number; (correct, verdict, why); None  | yes       |
| A9  | wires         | correct; two devices on one port; wrong port                         | True; shared-port message; names the device           | yes       |
| A10 | route_packets | correct; wrong machine                                               | True; "Packet 1 (label) went to the wrong machine."   | yes       |
| A11 | ip_assign     | valid free address; malformed; off-network; reserved .255; taken     | True; four specific messages                          | yes       |
| A12 | idea          | valid; blank name; empty page; two pages; 61-char name               | True; four specific messages                          | yes       |
| A13 | language      | listed language; unknown language                                    | True; False                                           | yes       |
| A14 | mentor filter | reply containing the exact terminal line; harmless nudge             | flagged; not flagged                                  | yes       |
| A15 | curriculum    | every level, every language variant: public JSON has no answer keys  | no `answer/patterns/shuffle/target_line/scam/why/...` | yes       |
| A16 | curriculum    | `challenge_by_language` variants differ per language                 | python and javascript resolve to different code       | yes       |
| A17 | curriculum    | every playable level has lesson notes (unless `no_lesson`)           | non-empty `lesson.points`                             | yes       |
| A18 | banter        | every level's public JSON                                            | non-empty doctor pool for the theme, non-empty quips for the guide, no duplicate lines | yes |
| A19 | soundtrack    | every playable level                                                 | a track (quizzes none), obelisks loop, bosses carry a boss track, Rhinoceros exactly once per course, no track twice in a row, no track over 60 % of a course, every key known | yes |
| A20 | maps          | `check_levels.py`                                                    | exit 0, "All levels OK."                              | yes       |

## B. HTTP behaviour (`tests/test_api.py`, Python `requests`)

| ID  | Area        | Case                                                                       | Expected                                                        | Automated |
|-----|-------------|----------------------------------------------------------------------------|-----------------------------------------------------------------|-----------|
| B1  | auth        | anonymous GET of home, profile, leaderboard, friends, a level, mentor status; anonymous POST to the level API | 302 to `/login`                         | yes       |
| B2  | signup      | no uppercase / no digit / no special char / too short / mismatch / low entropy; usernames that are too short, a link, an emoji, two words, markup, 21 chars; same name in other case | 200 with the matching error, account not created; "letters, numbers and underscores"; "already taken" | yes |
| B3  | login       | wrong password; right password; logout                                     | error text; 302 home + username shown; profile protected again  | yes       |
| B4  | storage     | password row in SQLite                                                     | hashed (`scrypt:`/`pbkdf2:`), plaintext absent                  | yes (private DB only) |
| B5  | character   | level page before choosing a character; invalid option; valid choice       | 302 to `/character`; error; level page renders with its title   | yes       |
| B6  | level JSON  | `#level-data` on Python level 1                                            | type `python_lines`, no secret keys, lesson notes present       | yes       |
| B7  | level API   | non-JSON body; unknown course; level as string / boolean; a checkpoint quiz ahead; a playable level ahead | 400; 404; 400; 200 (quizzes are always open); 403 "locked" | yes |
| B8  | level API   | wrong answer then right answer on Python 1 with a reported kill            | `correct:false` + line feedback without the answer; then `correct:true`, `next_level` 2, First Blood unlocked | yes |
| B9  | inventory   | dagger saved on Python, then open Cybersecurity                            | dagger present on Python level 2, absent on Cybersecurity       | yes       |
| B10 | checkpoint  | save, reload page, oversize payload, clear                                 | restored on the page; 400; cleared (`null`)                     | yes       |
| B11 | playthrough | every level of all four courses via the API (JavaScript picked for Secure Coding) | every submit correct, level JSON never leaks, language variant shown on Secure Coding 3, beams grow course by course, profile "4 / 4 beams lit" + Completionist | yes |
| B12 | profile     | after the playthrough                                                      | website idea, language, "SECRET ACHIEVEMENTS · n / m", locked ones as "???" | yes |
| B13 | leaderboard | after completions                                                          | 200, player listed                                              | yes       |
| B14 | mentor      | no API key: status; question; malformed request                            | `reachable:false`; 503 with "offline"; 400                      | yes       |
| B15 | friends     | search; bad / unknown id; add self; send request; other side accepts; both listed; remove; decline | listed with ADD FRIEND; 400 / 404; "yourself"; under SENT not FRIENDS; under their REQUESTS; FRIENDS on both sides; gone on both; declined request vanishes for both | yes |
| B16 | picture     | text file named .png; real PNG; served image; 2 MB + file; remove         | "not a PNG"; 302 and `avatar-img` on the profile; 200 image/png + nosniff, shrunk to 256 px; "2 MB" message; 404 afterwards | yes |
| B17 | privacy     | defaults for a stranger; nobody; friends-only; after becoming friends      | progress shown, time HIDDEN; "keeps this profile private", gone from search and leaderboard; progress HIDDEN until friends; everything shown to a friend | yes |
| B18 | leaderboard | no course; empty / unknown course; unknown level; python 1; internet 2 slowest-first | prompt; "Choose a course first."; "does not exist"; table with the player and a profile link; desc selected | yes |
| B19 | time        | first ping with the browser counter; huge claim; 50 s gap; 10 min gap; time board | imported once; ignored; +50 s; +0 s (idle not counted); player listed with the same total | yes |
| B20 | FAQ / dock  | home, profile, friends, leaderboard, a level                               | FAQ questions and the mentor dock on every page                  | yes       |
| B20b| audio       | level JSON (level / quiz / obelisk / boss / lab); m4a, slash mp3 and audio.js served; credits in the footer; now-playing setting off / on | file + loop flags right; 200 audio/mp4 and audio/mpeg; every title, both artists and the licence link on every page; HUD line disappears and returns | yes |
| B20c| account     | rename: bad name / taken (other case) / valid; friend's list, profile URLs, progress; second rename; login old vs new | errors; both friend lists keep the pair, new URL 200 / old 404, beams intact; "again in 14 days" + settings note; new name logs in, old does not | yes |
| B21 | social      | pending request badge; block; blocked side's view, search and requests; unblock; report with bad / good reason | badge "1" then gone; BLOCKED tab lists them; private profile, not in search, "can't add"; ADD FRIEND back; error / stored + thanks | yes |
| B22 | leaderboard | friends-only box                                                           | only the player (no friends) listed, box stays checked         | yes       |
| B23 | account     | change password: wrong current / weak / mismatch / valid                   | three errors; then old password fails and new one logs in       | yes       |
| B24 | auth        | ten wrong passwords for one username within five minutes                   | tenth and later attempts say "Too many attempts", even with the right password; other accounts unaffected | yes |
| B25 | account     | delete: no tick / wrong password / valid                                   | two errors; then session gone, login fails, profile page 404    | yes       |
| B26 | session     | logout                                                                     | profile and level API both redirect to login                    | yes       |

## C. In the browser (manual)

| ID  | Area        | Steps                                                                              | Expected                                                                 |
|-----|-------------|------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| C1  | intro       | open a course for the first time                                                   | matrix rain forms the character, controls popup lists WASD/E/F/Q/1-5; the SECUREMENTOR tab peeks up for ~3 s |
| C2  | movement    | A/D, W/Space over the first gap                                                    | jumps clear 2 tiles up / 3 across, no clipping into walls               |
| C3  | items       | walk over candy and a hint chip                                                    | inventory slots fill, pickup toast names the key to use                 |
| C4  | candy       | press E with nothing nearby while hurt; then select the candy slot and press F     | E does nothing but show a toast; F heals +3 and removes one candy       |
| C5  | drop        | select a slot, press Q; walk away and back                                         | item lands in front of you, cannot be re-grabbed instantly, then can    |
| C6  | hint chips  | at a terminal use every hint, then click again                                     | button reads "NO MORE HINTS HERE" and no chip is spent                  |
| C7  | combat      | swing at a snake / sniffer / bug                                                   | hit flash, stun, enemy removed, kill counted (First Blood on the card)  |
| C8  | hazard      | Internet course: fall into the white data stream                                   | -1 heart, returned to the last ledge with a toast                       |
| C9  | puzzles     | wires, IP, packet routing, idea form                                               | drag/drop works with the mouse, wrong answers give a short nudge only   |
| C10 | desk        | walk on the keyboard, run right                                                    | monitor mirrors the player, code lines appear one by one                |
| C11 | mentor bot  | press E on the Secure Coding bot                                                   | tip dialogue, then the SecureMentor panel opens; closing it returns keyboard focus to the game |
| C12 | obelisk     | press the button on the last level of a course                                     | flash, beam, confetti, LEVEL COMPLETE; beam still lit on the next visit |
| C13 | mentor      | ask "what is the answer?" at a terminal with the API key set                       | a nudge, never the terminal line                                        |
| C14 | fullscreen  | click the corner button                                                            | game fills the screen, keys still work, Esc returns                     |
| C15 | responsive  | 375 px wide viewport                                                               | sidebar stacks above the game, no horizontal scrolling                  |
