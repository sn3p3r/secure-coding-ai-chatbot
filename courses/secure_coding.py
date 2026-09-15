"""
Secure Coding - The Editor.

Short and practical. The whole course is set inside a code editor's
database: dark panels, line numbers, columns of stored records. Level
one asks the player to pick a language (Python or JavaScript); every
code block after that is shown in the language they chose. A mentor
bot ('m') stands in the levels - press E and it opens SecureMentor
with a tip.

Map legend additions:

    m  mentor bot - E opens SecureMentor
"""

from courses.common import level, room, put, finish, obelisk_level

GUIDE = "LINT"


# ---------------------------------------------------------
# MAPS (dark editor panels)
# ---------------------------------------------------------

def editor(width):
    return room(width, wall="G")


def panel(rows, row, col, width=3):
    put(rows, row, col, "G" * width)


def editor_a():
    rows = editor(48)
    put(rows, 8, 2, "P")
    put(rows, 7, 6, "N")
    panel(rows, 7, 12); put(rows, 6, 13, "I")
    put(rows, 8, 18, "A"); put(rows, 8, 24, "A")
    put(rows, 8, 30, "m")
    put(rows, 8, 36, "B")
    put(rows, 8, 41, "C")
    put(rows, 7, 45, "D"); put(rows, 8, 45, "D"); put(rows, 8, 46, "X")
    return finish(rows)


def editor_b():
    rows = editor(56)
    put(rows, 8, 2, "P")
    put(rows, 7, 6, "N")
    put(rows, 8, 11, "A")
    panel(rows, 7, 14); panel(rows, 5, 18); put(rows, 4, 19, "I")
    put(rows, 8, 24, "h")
    put(rows, 8, 30, "m")
    put(rows, 8, 36, "K")
    put(rows, 8, 41, "B")
    put(rows, 8, 47, "C")
    put(rows, 7, 53, "D"); put(rows, 8, 53, "D"); put(rows, 8, 54, "X")
    return finish(rows)


def editor_c():
    rows = editor(56)
    put(rows, 8, 2, "P")
    put(rows, 7, 6, "N")
    panel(rows, 7, 10); panel(rows, 5, 14); put(rows, 4, 15, "I")
    put(rows, 8, 20, "b"); put(rows, 8, 32, "b")
    put(rows, 8, 26, "A")
    put(rows, 8, 38, "m")
    put(rows, 8, 43, "B")
    put(rows, 8, 48, "C")
    put(rows, 7, 53, "D"); put(rows, 8, 53, "D"); put(rows, 8, 54, "X")
    return finish(rows)


# ---------------------------------------------------------
# SHARED TEXT
# ---------------------------------------------------------

TIPS = [
    "Tip: treat every input as hostile until you've checked its type, length and range.",
    "Tip: never build a database query by gluing strings. Placeholders keep data as data.",
    "Tip: secrets live in environment variables, not in code. Code gets copied; .env doesn't.",
    "Tip: hash passwords with a real password hash. If you can decrypt it, it isn't hashed.",
    "Tip: AI-written code is a stranger's code. Read it, test it, then trust it.",
    "Tip: the safest feature is the one you didn't need to build. Keep the surface small.",
]

BUGS = [
    {"name": "TYPO", "fact": "Not every bug is a vulnerability - but every vulnerability is a bug."},
    {"name": "OFF-BY-ONE", "fact": "Loops that run one time too many are how buffers overflow."},
]


def deck(cards):
    return [dict(kind="code", **c) for c in cards]


PY_DECK_1 = deck([
    {"from": "database.py", "subject": "", "body": "query = \"SELECT * FROM users WHERE name = '\" + name + \"'\"\ncursor.execute(query)", "scam": True, "why": "User input is glued into the SQL text, so a name like  ' OR 1=1 --  changes the query. Use a placeholder."},
    {"from": "database.py", "subject": "", "body": "cursor.execute(\"SELECT * FROM users WHERE name = ?\", (name,))", "scam": False, "why": "The ? placeholder keeps the name as data; it can never become part of the command."},
    {"from": "calculator.py", "subject": "", "body": "expression = input(\"Enter a sum: \")\nprint(eval(expression))", "scam": True, "why": "eval runs whatever the user types as Python - including deleting files."},
    {"from": "config.py", "subject": "", "body": "API_KEY = \"sk-live-9f3a1c...\"\nclient = Client(API_KEY)", "scam": True, "why": "A secret written into the code ends up in git history and every copy of the file."},
    {"from": "config.py", "subject": "", "body": "import os\nAPI_KEY = os.getenv(\"API_KEY\")", "scam": False, "why": "The key comes from the environment (.env), not from the code."},
    {"from": "signup.py", "subject": "", "body": "password_hash = generate_password_hash(password)\nstore(username, password_hash)", "scam": False, "why": "Only a salted hash is stored; a database leak does not reveal passwords."},
])

PY_DECK_2 = deck([
    {"from": "files.py", "subject": "", "body": "name = request.args.get(\"file\")\nreturn open(\"/data/\" + name).read()", "scam": True, "why": "A name like  ../../etc/passwd  walks out of /data. Validate the name or use a fixed allow-list."},
    {"from": "age.py", "subject": "", "body": "age = input(\"Age: \")\nif age.isdigit() and 0 < int(age) < 150:\n    save(int(age))", "scam": False, "why": "The input is checked for type and range before it is used."},
    {"from": "shell.py", "subject": "", "body": "folder = input(\"Folder: \")\nos.system(\"ls \" + folder)", "scam": True, "why": "A folder named  ; rm -rf /  becomes a second command. Never pass input to a shell string."},
    {"from": "shell.py", "subject": "", "body": "subprocess.run([\"ls\", folder])", "scam": False, "why": "Arguments are passed as a list with no shell, so the folder name is only ever a folder name."},
    {"from": "login.py", "subject": "", "body": "if user and (password == \"\" or check_password_hash(user.hash, password)):\n    login(user)", "scam": True, "why": "An empty password short-circuits the OR and logs anyone in."},
    {"from": "ai_helper.py", "subject": "", "body": "# generated by an AI assistant\ndef total(items):\n    return sum(item.price for item in items)", "scam": False, "why": "Plain arithmetic over trusted objects - fine. But you still read it before trusting it, right?"},
])

JS_DECK_1 = deck([
    {"from": "comments.js", "subject": "", "body": "list.innerHTML = \"<li>\" + comment + \"</li>\";", "scam": True, "why": "A comment containing <script> runs in every visitor's browser (XSS). Use textContent."},
    {"from": "comments.js", "subject": "", "body": "const li = document.createElement(\"li\");\nli.textContent = comment;\nlist.appendChild(li);", "scam": False, "why": "textContent shows the comment as plain text; tags inside it never run."},
    {"from": "api.js", "subject": "", "body": "app.post(\"/run\", (req, res) => {\n  res.send(eval(req.body.code));\n});", "scam": True, "why": "eval runs whatever the request contains on your server."},
    {"from": "db.js", "subject": "", "body": "db.query(\"SELECT * FROM users WHERE id = \" + req.params.id);", "scam": True, "why": "The id is glued into the SQL; an id of  1 OR 1=1  returns every user."},
    {"from": "db.js", "subject": "", "body": "db.query(\"SELECT * FROM users WHERE id = $1\", [req.params.id]);", "scam": False, "why": "The $1 placeholder keeps the id as data."},
    {"from": "config.js", "subject": "", "body": "const token = process.env.GITHUB_TOKEN;", "scam": False, "why": "The token comes from the environment, not from the source file."},
])

JS_DECK_2 = deck([
    {"from": "config.js", "subject": "", "body": "const token = \"ghp_4Fj8...\";\noctokit.auth(token);", "scam": True, "why": "A hardcoded token is a leaked token the moment the file is shared or pushed."},
    {"from": "files.js", "subject": "", "body": "res.sendFile(\"./uploads/\" + req.query.name);", "scam": True, "why": "A name like  ../.env  reads files outside uploads. Validate or map names to safe paths."},
    {"from": "orders.js", "subject": "", "body": "const qty = Number(req.body.qty);\nif (!Number.isInteger(qty) || qty < 1 || qty > 100) {\n  return res.status(400).send(\"bad quantity\");\n}", "scam": False, "why": "The quantity is checked for type and range before use."},
    {"from": "auth.js", "subject": "", "body": "const hash = await bcrypt.hash(password, 12);\nawait users.insert({ email, hash });", "scam": False, "why": "bcrypt produces a slow, salted hash - the right way to store a password."},
    {"from": "auth.js", "subject": "", "body": "if (user.role === \"admin\" || req.query.admin === \"true\") {\n  showAdminPanel();\n}", "scam": True, "why": "Anyone can add ?admin=true to the URL. Never trust the client to say who it is."},
    {"from": "ai_helper.js", "subject": "", "body": "// generated by an AI assistant\nconst total = items.reduce((sum, item) => sum + item.price, 0);", "scam": False, "why": "Plain arithmetic over trusted data - fine. Still read AI code before trusting it."},
])


# ---------------------------------------------------------
# LEVELS
# ---------------------------------------------------------

SECURE_LEVELS = [

    level(
        1, "Choose Your Language",
        section="What Is Secure Coding?",
        objective="Pick the language the rest of the course will use.",
        concepts=["Python", "JavaScript"],
        lesson={
            "title": "Welcome to the editor",
            "points": [
                "This course is short: what secure coding is, how to find weaknesses, and practice judging real code.",
                "Every code block from here on is shown in ONE language. Pick the one you write - or want to write.",
                "Python: the language this Academy is built in. JavaScript: the language of web pages and Node servers.",
                "You can change your mind later by replaying this level.",
            ],
            "example": "Python:      cursor.execute(\"... = ?\", (name,))\nJavaScript:  db.query(\"... = $1\", [name])",
        },
        story="Dark panels, line numbers glowing down the wall, tall columns of stored records. A boxy little robot rolls up: LINT. 'You're inside the editor's database. Everything you see is code somebody trusted. Pick your language.'",
        goal="Talk to LINT, then choose your language at the terminal.",
        gameplay="Walk right, meet the mentor bot (E opens SecureMentor), choose at the terminal.",
        guide=GUIDE,
        sign="settings.json: \"language\": null   <- pick one",
        npcs=TIPS,
        dialogue=[
            "Two languages on the menu. The ideas are the same; the spelling differs.",
            "The bot by the records opens SecureMentor. Ask it anything, any time.",
        ],
        challenge={
            "type": "language",
            "prompt": "Which language should the course use for its code?",
            "options": ["python", "javascript"],
        },
        reasoning="Personalise the rest of the course.",
        success="Language saved. The editor reloads.",
        failure="Choose one of the two.",
        explanation="Every later code block will be in the language you chose.",
        reward="Editor Badge I",
        mentor="Help the learner choose based on what they already write.",
        hints=["Pick the one you'd actually use."],
        map=editor_a(),
        theme="editor",
        intro=True,
    ),

    level(
        2, "What Is Secure Coding?",
        section="What Is Secure Coding?",
        objective="Understand that secure code manages trust.",
        concepts=["trust boundary", "input", "least privilege"],
        lesson={
            "title": "Bugs an attacker can use",
            "points": [
                "A BUG is code that does the wrong thing. A VULNERABILITY is a bug an attacker can use on purpose.",
                "Most vulnerabilities come from misplaced TRUST: believing input is safe, believing a secret stays hidden, skipping a check.",
                "A TRUST BOUNDARY is anywhere data crosses from 'outside' (users, the network, files) to 'inside'. Check at the boundary.",
                "Secure coding is not paranoia everywhere; it is care at the boundaries and small, honest defaults.",
            ],
            "example": "outside -> [check type, length, range] -> inside",
        },
        story="Records scroll past on the columns: usernames, orders, a few things that should not be in a database at all. LINT: 'Everything in here came through a door. Was anyone standing at it?'",
        goal="Tell the terminal where checks belong.",
        gameplay="Meet the bot, read the sign, answer the terminal.",
        guide=GUIDE,
        sign="INCIDENT 0042: input trusted at line 12. Cost: one weekend.",
        npcs=TIPS,
        dialogue=["Where does outside data become inside data? That's where you check it."],
        challenge={
            "type": "mcq",
            "prompt": "Where should input be validated?",
            "options": ["Nowhere - users can be trusted", "At the trust boundary, where data enters from outside", "Only in the database", "Only on the user's screen"],
            "answer": 1,
            "wrong": "Think about where outside data first arrives.",
        },
        reasoning="Locate validation at boundaries.",
        success="The record closes. Door opens.",
        failure="The terminal blinks: not that.",
        explanation="Validate where data crosses from outside to inside; that is the trust boundary.",
        reward="Editor Badge II",
        mentor="Use this app's signup validation as the boundary example.",
        hints=["Where does the outside meet the inside?"],
        map=editor_b(),
        theme="editor",
        start_items=["SWORD"],
    ),

    level(
        3, "Finding Weaknesses",
        section="Finding Weaknesses",
        objective="Find the line that lets an attacker in.",
        concepts=["code review", "bypass", "trace the flow"],
        lesson={
            "title": "Reading code like an attacker",
            "points": [
                "Trace every path that leads to something valuable (a login, a payment, a delete).",
                "Ask of each line: what if the input is empty? huge? contains quotes? is a lie?",
                "Look for OR conditions with an easy side, string-glued queries, input used as a path or a command.",
                "The reviewer's job is to find the path the author never imagined.",
            ],
            "example": "if password == \"\" or check(password):   # the left side is free",
        },
        story="One record is flagged red: a login function somebody pushed at 2 a.m. LINT: 'Find the line. Then tell me why.'",
        goal="Click the poisoned line and choose why it is dangerous.",
        gameplay="Squash the two bugs, read the sign, use the terminal.",
        guide=GUIDE,
        sign="commit message: 'quick fix for login, works on my machine'",
        npcs=TIPS,
        bugs=BUGS,
        dialogue=["Trace it with an empty password in your head. What happens?"],
        challenge_by_language={
            "python": {
                "type": "code_review",
                "label": "CODE",
                "prompt": "Click the dangerous line, then choose why.",
                "code": [
                    "user = find_user(username)",
                    "if user is None:",
                    "    return error(\"Username or password is incorrect.\")",
                    "if password == \"\" or check_password_hash(user.hash, password):",
                    "    session[\"user_id\"] = user.id",
                ],
                "target_line": 4,
                "why_options": [
                    "An empty password makes the OR true - the hash is never checked",
                    "find_user should be called twice",
                    "Error messages must say which field is wrong",
                    "session cannot hold an id",
                ],
                "why_answer": 0,
                "fixed": ["if check_password_hash(user.hash, password):", "    session[\"user_id\"] = user.id"],
            },
            "javascript": {
                "type": "code_review",
                "label": "CODE",
                "prompt": "Click the dangerous line, then choose why.",
                "code": [
                    "const user = await findUser(username);",
                    "if (!user) {",
                    "  return error(\"Username or password is incorrect.\");",
                    "}",
                    "if (password === \"\" || await bcrypt.compare(password, user.hash)) {",
                    "  req.session.userId = user.id;",
                    "}",
                ],
                "target_line": 5,
                "why_options": [
                    "An empty password makes the OR true - the hash is never checked",
                    "findUser should be called twice",
                    "Error messages must say which field is wrong",
                    "Sessions cannot hold an id",
                ],
                "why_answer": 0,
                "fixed": ["if (await bcrypt.compare(password, user.hash)) {", "  req.session.userId = user.id;", "}"],
            },
        },
        reasoning="Boolean short-circuit review.",
        success="The record is fixed. Door opens.",
        failure="The terminal says that isn't the problem.",
        explanation="With an empty password the left side of the OR is true, so the password is never checked.",
        reward="Editor Badge III",
        mentor="Ask the learner to evaluate the condition with an empty password.",
        hints=["Try an empty password in your head."],
        map=editor_c(),
        theme="editor",
        start_items=["SWORD"],
    ),

    level(
        4, "Safe or Unsafe? I",
        section="Practice",
        objective="Judge real code snippets: safe or unsafe.",
        concepts=["injection", "eval", "secrets", "hashing"],
        lesson={
            "title": "Snap judgements, with reasons",
            "points": [
                "Injection: input glued into SQL, HTML or a shell command. Placeholders and textContent keep data as data.",
                "eval and friends: running text as code is running the user's code.",
                "Secrets: in the environment, never in the file. Passwords: hashed, never stored.",
                "For each snippet: UNSAFE or SAFE. Wrong picks are explained; you redo them until the deck is clean.",
            ],
            "example": "glued string -> unsafe\nplaceholder  -> safe",
        },
        story="The columns open like drawers, each holding a snippet somebody once shipped. LINT: 'Six snippets. Trust or don't. Say why.'",
        goal="Sort all six snippets: UNSAFE or SAFE.",
        gameplay="Use the terminal; read each snippet; pick UNSAFE or SAFE (or the arrow keys).",
        guide=GUIDE,
        sign="REVIEW QUEUE: 6 items. Reviewer: you.",
        npcs=TIPS,
        challenge_by_language={
            "python": {"type": "swipe", "label": "REVIEW QUEUE", "prompt": "UNSAFE or SAFE? Sort all six snippets.", "labels": ["UNSAFE", "SAFE"], "cards": PY_DECK_1},
            "javascript": {"type": "swipe", "label": "REVIEW QUEUE", "prompt": "UNSAFE or SAFE? Sort all six snippets.", "labels": ["UNSAFE", "SAFE"], "cards": JS_DECK_1},
        },
        reasoning="Pattern recognition for the big four: injection, eval, secrets, password storage.",
        success="Queue clean. Door opens.",
        failure="Each wrong pick explains the pattern you missed.",
        explanation="Placeholders, textContent, environment secrets and hashing are the safe shapes.",
        reward="Editor Badge IV",
        mentor="Coach on the pattern (glued vs placeholder) without saying which card is which.",
        hints=["Is the input glued into something that gets executed?"],
        map=editor_a(),
        theme="editor",
        start_items=["SWORD"],
    ),

    level(
        5, "Safe or Unsafe? II",
        section="Practice",
        objective="Judge harder snippets: paths, shells, logic and AI-written code.",
        concepts=["path traversal", "command injection", "client trust", "AI code"],
        lesson={
            "title": "The subtle ones",
            "points": [
                "Input used as a PATH can walk out of the folder with ../. Input used in a SHELL string becomes a second command.",
                "Never let the client say who it is (?admin=true). The server decides roles.",
                "Validated input (type + range) is safe input. Unchecked input is not.",
                "AI-written code can be perfectly fine - or eval in disguise. Read it like a stranger's code.",
            ],
            "example": "\"/data/\" + name        -> unsafe (traversal)\n[\"ls\", folder] no shell -> safe",
        },
        story="Deeper drawers, older code. LINT: 'These fooled real reviewers. Six more.'",
        goal="Sort all six snippets: UNSAFE or SAFE.",
        gameplay="Pass the guard, use the terminal, sort the deck.",
        guide=GUIDE,
        sign="REVIEW QUEUE: 6 items. Two were written by an AI. It does not say which.",
        npcs=TIPS,
        challenge_by_language={
            "python": {"type": "swipe", "label": "REVIEW QUEUE", "prompt": "UNSAFE or SAFE? Six harder snippets.", "labels": ["UNSAFE", "SAFE"], "cards": PY_DECK_2},
            "javascript": {"type": "swipe", "label": "REVIEW QUEUE", "prompt": "UNSAFE or SAFE? Six harder snippets.", "labels": ["UNSAFE", "SAFE"], "cards": JS_DECK_2},
        },
        reasoning="Paths, shells, client trust, validation, AI code.",
        success="Queue clean. Door opens.",
        failure="Each wrong pick explains the pattern you missed.",
        explanation="Traversal, shell strings and client-supplied roles are unsafe; checked input and list-form commands are safe.",
        reward="Editor Badge V",
        mentor="Ask what an attacker controls in each snippet.",
        hints=["What does the user control, and where does it end up?"],
        map=editor_b(),
        theme="editor",
        start_items=["SWORD"],
    ),

    level(
        6, "Write It Safely",
        section="Practice",
        objective="Complete a safe database query yourself.",
        concepts=["placeholders", "parameterised queries"],
        lesson={
            "title": "The safe shape, from memory",
            "points": [
                "The query text holds a PLACEHOLDER where the value goes; the value is passed separately.",
                "The database then treats the value as data, whatever it contains.",
                "Python: cursor.execute(\"... WHERE name = ?\", (name,))",
                "JavaScript: db.query(\"... WHERE name = $1\", [name])",
            ],
            "example": "text with a placeholder  +  value passed separately",
        },
        story="A blank record waits with a cursor blinking in it. LINT: 'Last one. No queue this time - you write it.'",
        goal="Fill the blanks so the query uses a placeholder and passes the name separately.",
        gameplay="Use the terminal and fill the two blanks.",
        guide=GUIDE,
        sign="TODO: rewrite the lookup without string glue.",
        npcs=TIPS,
        bugs=BUGS,
        challenge_by_language={
            "python": {
                "type": "fill_blank",
                "prompt": "Fill the blanks: the placeholder in the query, then the value passed separately.",
                "code": ["cursor.execute(\"SELECT * FROM users WHERE name = ___\", (___,))"],
                "answers": [["?"], ["name"]],
                "bank": ["?", "name", "\"name\"", "+ name +", "%s"],
            },
            "javascript": {
                "type": "fill_blank",
                "prompt": "Fill the blanks: the placeholder in the query, then the value passed separately.",
                "code": ["db.query(\"SELECT * FROM users WHERE name = ___\", [___]);"],
                "answers": [["$1"], ["name"]],
                "bank": ["$1", "name", "\"name\"", "+ name +", "?"],
            },
        },
        reasoning="Produce the parameterised shape.",
        success="The record saves. The editor closes.",
        failure="The terminal names the blank that is wrong.",
        explanation="A placeholder in the text and the value passed separately: the database can never confuse the two.",
        reward="Editor Badge VI",
        mentor="Ask which part is the placeholder and which is the value.",
        hints=["The value goes outside the string."],
        map=editor_c(),
        theme="editor",
        start_items=["SWORD"],
    ),

    obelisk_level(
        7, "Secure Coding", "The Editor", "Editor Master Badge", GUIDE,
        "The editor's last panel slides away and you step onto a white plain. LINT rolls up beside the obelisk and, for once, has no tip. There is a button at its base.",
        [
            "Vulnerabilities are bugs an attacker can use; most come from trusting input.",
            "Placeholders, textContent, environment secrets, real password hashes, validated input.",
            "Read AI-written code like a stranger's code. The reviewer finds the path the author never imagined.",
        ],
    ),
]

for _index, _level in enumerate(SECURE_LEVELS, start=1):
    _level["number"] = _index
