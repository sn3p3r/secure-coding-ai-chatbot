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

    return False, "This challenge type is not supported."


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
