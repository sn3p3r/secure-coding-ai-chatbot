"""
Server-side answer checking for game challenges.

Nothing here executes player input. Python answers are matched
against regular expressions line by line, so the worst a player
can do is get a "not quite" message.

Feedback is deliberately sparse: it says WHICH line or blank is
wrong, not what the answer is. Learning happens in the lesson,
the hint chips, and SecureMentor.
"""

import re

MAX_ANSWER_LENGTH = 2000


def _normalise_text(text):
    return " ".join(str(text).lower().split())


def _normalise_code(text):
    """Trim, collapse inner spaces, and treat ' and \" as the same quote."""
    return " ".join(str(text).replace("'", '"').split())


def _code_lines(text):
    """Split code into lines, dropping blanks and comment-only lines."""
    lines = []
    for raw in str(text).replace("\r", "").split("\n"):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(raw.rstrip())
    return lines


def check_answer(challenge, answer):
    """
    Returns (correct: bool, feedback: str).

    `answer` is whatever JSON the browser sent for this challenge:
        mcq          -> int (option index)
        text_answer  -> str
        python_lines -> str (multi-line code)
        code_review  -> {"line": int, "why": int}
        fill_blank   -> {"blanks": [str, ...]}
        order_code   -> {"order": [int, ...]}  indices into the shown pieces
    """
    kind = challenge.get("type")

    if kind == "mcq":
        return _check_mcq(challenge, answer)

    if kind == "text_answer":
        return _check_text(challenge, answer)

    if kind == "python_lines":
        return _check_python_lines(challenge, answer)

    if kind == "code_review":
        return _check_code_review(challenge, answer)

    if kind == "fill_blank":
        return _check_fill_blank(challenge, answer)

    if kind == "order_code":
        return _check_order_code(challenge, answer)

    if kind == "quiz":
        return _check_quiz(challenge, answer)

    if kind == "walk":
        # Story levels: reaching the exit is the whole challenge.
        return True, ""

    if kind == "swipe":
        return _check_swipe(challenge, answer)

    if kind == "wires":
        return _check_wires(challenge, answer)

    if kind == "route_packets":
        return _check_route(challenge, answer)

    if kind == "ip_assign":
        return _check_ip(challenge, answer)

    if kind == "idea":
        return _check_idea(challenge, answer)

    if kind == "language":
        return _check_language(challenge, answer)

    return False, "This challenge type is not supported."


def _index_list(value, length, limit):
    """A list of `length` ints, each 0..limit-1, or None."""
    if not isinstance(value, list) or len(value) != length:
        return None
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool) or item < 0 or item >= limit:
            return None
    return value


def _check_wires(challenge, answer):
    if not isinstance(answer, dict):
        return False, "Connect every device first."

    mapping = _index_list(answer.get("map"), len(challenge["devices"]), len(challenge["ports"]))
    if mapping is None:
        return False, "Connect every device to one port."

    if len(set(mapping)) != len(mapping):
        return False, "Two devices share a port. One device per port."

    for device, port, wanted in zip(challenge["devices"], mapping, challenge["answer"]):
        if port != wanted:
            return False, device + " is on the wrong port. Check the plan."

    return True, ""


def _check_route(challenge, answer):
    if not isinstance(answer, dict):
        return False, "Deliver every packet first."

    mapping = _index_list(answer.get("map"), len(challenge["packets"]), len(challenge["machines"]))
    if mapping is None:
        return False, "Deliver every packet to one machine."

    for index, (packet, machine, wanted) in enumerate(zip(challenge["packets"], mapping, challenge["answer"]), 1):
        if machine != wanted:
            return False, "Packet %d (%s) went to the wrong machine." % (index, packet["label"])

    return True, ""


def _check_ip(challenge, answer):
    if not isinstance(answer, str) or len(answer) > 40:
        return False, "Type an address."

    value = answer.strip()
    parts = value.split(".")

    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return False, "That is not a valid IPv4 address: four numbers from 0 to 255, separated by dots."

    if not value.startswith(challenge["network"]):
        return False, "That address is not on this network. It has to start with %s" % challenge["network"]

    last = int(parts[3])
    if last < 1 or last > 254:
        return False, "The last number must be between 1 and 254 - 0 and 255 are reserved."

    if value in challenge["taken"]:
        return False, "That address is already in use on this network."

    return True, ""


def _check_idea(challenge, answer):
    if not isinstance(answer, dict):
        return False, "Fill in the form."

    name = answer.get("name")
    pitch = answer.get("pitch")
    pages = answer.get("pages")

    if not isinstance(name, str) or not name.strip():
        return False, "Give your website a name."
    if len(name) > 60:
        return False, "Keep the name under 60 characters."
    if not isinstance(pitch, str) or not pitch.strip():
        return False, "Say what the site does, in one sentence."
    if len(pitch) > 300:
        return False, "Keep the sentence under 300 characters."
    if not isinstance(pages, list) or len(pages) != 3 or not all(isinstance(p, str) for p in pages):
        return False, "List three pages."
    for index, page in enumerate(pages, 1):
        if not page.strip():
            return False, "Page %d is empty." % index
        if len(page) > 40:
            return False, "Keep page %d's name under 40 characters." % index

    return True, ""


def _check_language(challenge, answer):
    if not isinstance(answer, str) or answer not in challenge["options"]:
        return False, "Choose one of the languages."
    return True, ""


def swipe_card_verdict(challenge, index, said_scam):
    """
    One card at a time, for the tinder-style deck. Returns
    (correct, verdict, why) or None when the request is malformed.
    """
    cards = challenge.get("cards", [])

    if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(cards):
        return None

    if not isinstance(said_scam, bool):
        return None

    card = cards[index]
    return said_scam == card["scam"], ("scam" if card["scam"] else "legit"), card["why"]


def _check_swipe(challenge, answer):
    if not isinstance(answer, dict) or not isinstance(answer.get("answers"), list):
        return False, "Sort every message first."

    given = answer["answers"]
    cards = challenge["cards"]

    if len(given) != len(cards) or any(not isinstance(a, bool) for a in given):
        return False, "Sort every message first."

    wrong = [i + 1 for i, (a, card) in enumerate(zip(given, cards)) if a != card["scam"]]

    if wrong:
        return False, "Not yet. Look again at message " + ", ".join(str(n) for n in wrong) + "."

    return True, ""


def _check_quiz(challenge, answer):
    if not isinstance(answer, dict) or not isinstance(answer.get("answers"), list):
        return False, "Answer every question."

    given = answer["answers"]
    questions = challenge["questions"]

    if len(given) != len(questions):
        return False, "Answer every question."

    wrong = []
    for index, (choice, question) in enumerate(zip(given, questions)):
        if not isinstance(choice, int) or isinstance(choice, bool) or choice < 0 or choice >= len(question["options"]):
            return False, f"Question {index + 1} needs an answer."
        if choice != question["answer"]:
            wrong.append(index + 1)

    if wrong:
        return False, "Not yet. Look again at question " + ", ".join(str(n) for n in wrong) + "."

    return True, ""


def _reply_lines(text):
    """Lines of a mentor reply with markdown decoration stripped."""
    lines = []
    for raw in str(text).replace("\r", "").split("\n"):
        line = raw.strip().strip("`").strip()
        for prefix in ("- ", "* ", "> ", "1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. "):
            if line.startswith(prefix):
                line = line[len(prefix):].strip()
        if line:
            lines.append(line)
    return lines


def leaks_answer(challenge, text):
    """
    True when a mentor reply contains the exact code the terminal wants.
    Used as a safety net behind SecureMentor for the code challenges;
    multiple-choice concepts are left to the prompt rules.
    """
    kind = challenge.get("type")
    lines = _reply_lines(text)
    norm = [_normalise_code(line) for line in lines]
    flat = _normalise_code(" ".join(lines))

    if kind == "python_lines":
        # The required line anywhere in the reply, even mid-sentence.
        for line in lines:
            for pattern in challenge["patterns"]:
                if re.search(pattern["regex"], line):
                    return True
        return False

    if kind == "fill_blank":
        answers = iter(challenge["answers"])
        for code_line in challenge["code"]:
            if "___" not in code_line:
                continue
            filled = code_line
            while "___" in filled:
                filled = filled.replace("___", next(answers)[0], 1)
            if _normalise_code(filled) in flat:
                return True
        return False

    if kind == "order_code":
        seq = [_normalise_code(piece) for piece in challenge["pieces"]]
        for start in range(len(norm) - len(seq) + 1):
            if norm[start:start + len(seq)] == seq:
                return True
        return False

    return False


def _check_mcq(challenge, answer):
    if not isinstance(answer, int) or isinstance(answer, bool):
        return False, "Choose one of the options."

    if answer < 0 or answer >= len(challenge["options"]):
        return False, "Choose one of the options."

    if answer == challenge["answer"]:
        return True, ""

    return False, challenge.get("wrong", "Not quite. Think it through again.")


def _check_text(challenge, answer):
    if not isinstance(answer, str):
        return False, "Type an answer."

    if len(answer) > MAX_ANSWER_LENGTH:
        return False, "That answer is too long."

    given = _normalise_text(answer)

    if not given:
        return False, "Type an answer."

    accepted = [_normalise_text(a) for a in challenge["accepted"]]

    if given in accepted:
        return True, ""

    return False, challenge.get("wrong", "Not quite. Think it through again.")


def _check_python_lines(challenge, answer):
    if not isinstance(answer, str):
        return False, "Type your code."

    if len(answer) > MAX_ANSWER_LENGTH:
        return False, "That code is too long for this terminal."

    lines = _code_lines(answer)
    patterns = challenge["patterns"]

    if not lines:
        return False, "The terminal is empty. Type your code first."

    if len(lines) > len(patterns):
        return False, f"This terminal expects {len(patterns)} line(s). You wrote {len(lines)}."

    for index, pattern in enumerate(patterns):
        if index >= len(lines):
            return False, f"Line {index + 1} is missing."

        if not re.fullmatch(pattern["regex"], lines[index]):
            return False, f"Line {index + 1} isn't right yet."

    return True, ""


def _check_code_review(challenge, answer):
    if not isinstance(answer, dict):
        return False, "Pick a line and a reason."

    line = answer.get("line")
    why = answer.get("why")

    if not isinstance(line, int) or isinstance(line, bool):
        return False, "Click the line you think is the problem."

    if line < 1 or line > len(challenge["code"]):
        return False, "Click one of the lines shown."

    if line != challenge["target_line"]:
        return False, f"Line {line} is not the problem."

    if not isinstance(why, int) or isinstance(why, bool):
        return False, "Right line. Now choose why it is a problem."

    if why < 0 or why >= len(challenge["why_options"]):
        return False, "Choose one of the reasons."

    if why != challenge["why_answer"]:
        return False, "Right line, but that isn't the reason."

    return True, ""


def _check_fill_blank(challenge, answer):
    if not isinstance(answer, dict) or not isinstance(answer.get("blanks"), list):
        return False, "Fill in the blanks."

    blanks = answer["blanks"]
    expected = challenge["answers"]

    if len(blanks) != len(expected):
        return False, "Fill in every blank."

    for index, (given, accepted) in enumerate(zip(blanks, expected)):
        if not isinstance(given, str) or len(given) > 200:
            return False, f"Blank {index + 1} isn't right yet."

        if not given.strip():
            return False, f"Blank {index + 1} is empty."

        if _normalise_code(given) not in [_normalise_code(a) for a in accepted]:
            return False, f"Blank {index + 1} isn't right yet."

    return True, ""


def _check_order_code(challenge, answer):
    if not isinstance(answer, dict) or not isinstance(answer.get("order"), list):
        return False, "Arrange the lines first."

    order = answer["order"]
    shuffle = challenge["shuffle"]
    count = len(challenge["pieces"])

    if len(order) != count or any(
        not isinstance(i, int) or isinstance(i, bool) or i < 0 or i >= count for i in order
    ) or len(set(order)) != count:
        return False, "Arrange every line exactly once."

    # order[k] is the index (into the shuffled view) of the piece the player
    # placed at position k. The piece at shuffled index j is pieces[shuffle[j]].
    placed = [shuffle[j] for j in order]

    if placed == list(range(count)):
        return True, ""

    for position, original_index in enumerate(placed):
        if original_index != position:
            return False, f"The order isn't right yet. Look at line {position + 1}."

    return False, "The order isn't right yet."
