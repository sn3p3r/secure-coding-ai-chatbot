"""
Unit tests for the server-side answer checkers and the level data.

Run with:  python3 -m unittest tests.test_challenges
No server and no database are needed.
"""

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from challenges import check_answer, leaks_answer, swipe_card_verdict  # noqa: E402
from curriculum import COURSES, LANGUAGES, public_level, resolve_challenge  # noqa: E402


def all_courses():
    return list(COURSES.values()) if isinstance(COURSES, dict) else list(COURSES)


# Keys that must never reach the browser.
SECRET_KEYS = {
    "answer", "answers", "accepted", "patterns", "regex", "shuffle",
    "target_line", "why_answer", "scam", "why", "fixed",
}


class MultipleChoiceTests(unittest.TestCase):

    challenge = {"type": "mcq", "options": ["a", "b", "c"], "answer": 1, "wrong": "Nope."}

    def test_correct_option(self):
        self.assertEqual(check_answer(self.challenge, 1), (True, ""))

    def test_wrong_option_returns_the_level_feedback(self):
        self.assertEqual(check_answer(self.challenge, 0), (False, "Nope."))

    def test_rejects_non_integers_and_out_of_range(self):
        self.assertFalse(check_answer(self.challenge, "1")[0])
        self.assertFalse(check_answer(self.challenge, True)[0])
        self.assertFalse(check_answer(self.challenge, 7)[0])


class TextAnswerTests(unittest.TestCase):

    challenge = {"type": "text_answer", "accepted": ["https", "tls"]}

    def test_accepts_any_listed_answer_ignoring_case_and_spaces(self):
        self.assertTrue(check_answer(self.challenge, "  HTTPS ")[0])
        self.assertTrue(check_answer(self.challenge, "tls")[0])

    def test_rejects_other_text_and_non_strings(self):
        self.assertFalse(check_answer(self.challenge, "http")[0])
        self.assertFalse(check_answer(self.challenge, 5)[0])


class PythonLinesTests(unittest.TestCase):

    challenge = {
        "type": "python_lines",
        "patterns": [
            {"regex": r"word\s*=\s*([\"'])descend\1"},
            {"regex": r"print\(\s*word\s*\)"},
        ],
    }

    def test_matching_code_passes(self):
        self.assertTrue(check_answer(self.challenge, 'word = "descend"\nprint(word)')[0])

    def test_feedback_names_the_line_without_giving_the_answer(self):
        ok, feedback = check_answer(self.challenge, 'word = "up"\nprint(word)')
        self.assertFalse(ok)
        self.assertEqual(feedback, "Line 1 isn't right yet.")
        self.assertNotIn("descend", feedback)

    def test_missing_and_extra_lines(self):
        self.assertEqual(check_answer(self.challenge, 'word = "descend"')[1], "Line 2 is missing.")
        self.assertIn("expects 2 line(s)", check_answer(self.challenge, "a\nb\nc")[1])

    def test_empty_terminal(self):
        self.assertFalse(check_answer(self.challenge, "   \n")[0])


class FillBlankTests(unittest.TestCase):

    challenge = {"type": "fill_blank", "code": ["x = ___", "print(___)"], "answers": [["5"], ["x"]]}

    def test_correct_blanks(self):
        self.assertTrue(check_answer(self.challenge, {"blanks": ["5", " x "]})[0])

    def test_empty_blank_is_reported_by_number(self):
        self.assertEqual(check_answer(self.challenge, {"blanks": ["5", ""]})[1], "Blank 2 is empty.")

    def test_wrong_blank_count(self):
        self.assertFalse(check_answer(self.challenge, {"blanks": ["5"]})[0])


class OrderCodeTests(unittest.TestCase):

    challenge = {"type": "order_code", "pieces": ["a", "b", "c"], "shuffle": [2, 0, 1]}

    def test_correct_order_uses_indices_into_the_shuffled_view(self):
        # shuffled view is [c, a, b]; the player must place a (1), b (2), c (0)
        self.assertTrue(check_answer(self.challenge, {"order": [1, 2, 0]})[0])

    def test_wrong_order_points_at_the_first_wrong_line(self):
        ok, feedback = check_answer(self.challenge, {"order": [0, 1, 2]})
        self.assertFalse(ok)
        self.assertIn("line 1", feedback)

    def test_duplicates_are_rejected(self):
        self.assertFalse(check_answer(self.challenge, {"order": [1, 1, 0]})[0])


class CodeReviewTests(unittest.TestCase):

    challenge = {
        "type": "code_review", "code": ["a", "b", "c"], "target_line": 2,
        "why_options": ["x", "y"], "why_answer": 1,
    }

    def test_right_line_and_reason(self):
        self.assertTrue(check_answer(self.challenge, {"line": 2, "why": 1})[0])

    def test_right_line_wrong_reason(self):
        self.assertEqual(check_answer(self.challenge, {"line": 2, "why": 0})[1], "Right line, but that isn't the reason.")

    def test_wrong_line(self):
        self.assertEqual(check_answer(self.challenge, {"line": 1, "why": 1})[1], "Line 1 is not the problem.")


class QuizAndSwipeTests(unittest.TestCase):

    quiz = {"type": "quiz", "questions": [
        {"prompt": "q1", "options": ["a", "b"], "answer": 0},
        {"prompt": "q2", "options": ["a", "b"], "answer": 1},
    ]}
    deck = {"type": "swipe", "cards": [
        {"kind": "email", "from": "x", "body": "y", "scam": True, "why": "fake link"},
        {"kind": "email", "from": "x", "body": "z", "scam": False, "why": "real"},
    ]}

    def test_quiz_reports_wrong_question_numbers_only(self):
        self.assertTrue(check_answer(self.quiz, {"answers": [0, 1]})[0])
        self.assertEqual(check_answer(self.quiz, {"answers": [1, 1]})[1], "Not yet. Look again at question 1.")

    def test_quiz_needs_every_answer(self):
        self.assertEqual(check_answer(self.quiz, {"answers": [0]})[1], "Answer every question.")

    def test_swipe_deck_as_a_whole(self):
        self.assertTrue(check_answer(self.deck, {"answers": [True, False]})[0])
        self.assertIn("message 2", check_answer(self.deck, {"answers": [True, True]})[1])

    def test_single_card_verdict(self):
        self.assertEqual(swipe_card_verdict(self.deck, 0, True), (True, "scam", "fake link"))
        self.assertEqual(swipe_card_verdict(self.deck, 1, True), (False, "legit", "real"))
        self.assertIsNone(swipe_card_verdict(self.deck, 5, True))
        self.assertIsNone(swipe_card_verdict(self.deck, 0, "yes"))


class NetworkPuzzleTests(unittest.TestCase):

    wires = {"type": "wires", "devices": ["LAPTOP", "PRINTER"], "ports": ["1", "2", "3"], "answer": [0, 2]}
    route = {
        "type": "route_packets",
        "machines": [{"name": "A", "ip": "10.0.0.1"}, {"name": "B", "ip": "10.0.0.2"}],
        "packets": [{"label": "one", "to": "10.0.0.2"}, {"label": "two", "to": "10.0.0.1"}],
        "answer": [1, 0],
    }
    ip = {"type": "ip_assign", "network": "192.168.1.", "taken": ["192.168.1.1", "192.168.1.10"]}

    def test_wires(self):
        self.assertTrue(check_answer(self.wires, {"map": [0, 2]})[0])
        self.assertEqual(check_answer(self.wires, {"map": [2, 2]})[1], "Two devices share a port. One device per port.")
        self.assertEqual(check_answer(self.wires, {"map": [1, 2]})[1], "LAPTOP is on the wrong port. Check the plan.")

    def test_route_packets(self):
        self.assertTrue(check_answer(self.route, {"map": [1, 0]})[0])
        self.assertEqual(check_answer(self.route, {"map": [0, 0]})[1], "Packet 1 (one) went to the wrong machine.")

    def test_ip_assign(self):
        self.assertTrue(check_answer(self.ip, "192.168.1.50")[0])
        self.assertIn("not a valid IPv4", check_answer(self.ip, "192.168.1")[1])
        self.assertIn("not on this network", check_answer(self.ip, "10.0.0.5")[1])
        self.assertIn("reserved", check_answer(self.ip, "192.168.1.255")[1])
        self.assertIn("already in use", check_answer(self.ip, "192.168.1.10")[1])


class IdeaAndLanguageTests(unittest.TestCase):

    def test_idea_validation(self):
        idea = {"type": "idea"}
        good = {"name": "Chess Club", "pitch": "Schedules and sign-ups.", "pages": ["Home", "Schedule", "Join"]}
        self.assertTrue(check_answer(idea, good)[0])
        self.assertEqual(check_answer(idea, dict(good, name=" "))[1], "Give your website a name.")
        self.assertEqual(check_answer(idea, dict(good, pages=["Home", "", "Join"]))[1], "Page 2 is empty.")
        self.assertEqual(check_answer(idea, dict(good, pages=["Home"]))[1], "List three pages.")
        self.assertFalse(check_answer(idea, dict(good, name="x" * 61))[0])

    def test_language_choice(self):
        lang = {"type": "language", "options": ["python", "javascript"]}
        self.assertTrue(check_answer(lang, "javascript")[0])
        self.assertFalse(check_answer(lang, "rust")[0])


class MentorLeakFilterTests(unittest.TestCase):

    challenge = {"type": "python_lines", "patterns": [{"regex": r"print\(\s*([\"'])open\1\s*\)"}]}

    def test_reply_containing_the_exact_line_is_caught(self):
        self.assertTrue(leaks_answer(self.challenge, "Try this:\n```\nprint(\"open\")\n```"))

    def test_nudge_without_the_line_passes(self):
        self.assertFalse(leaks_answer(self.challenge, "Which function prints text to the screen?"))


class LevelDataTests(unittest.TestCase):
    """The curriculum as a whole: nothing secret leaks, every variant resolves."""

    def test_public_level_never_contains_answer_keys(self):
        for course in all_courses():
            for lvl in course["levels"]:
                for language in (None,) + tuple(LANGUAGES):
                    public = public_level(course, lvl, language=language, beams=[])
                    challenge = public["challenge"]
                    leaked = SECRET_KEYS & set(challenge.keys())
                    self.assertFalse(leaked, f"{course['slug']} {lvl['number']} leaks {leaked}")
                    if challenge.get("type") == "quiz":
                        for question in challenge["questions"]:
                            self.assertNotIn("answer", question)
                    if challenge.get("type") == "swipe":
                        for card in challenge["cards"]:
                            self.assertNotIn("scam", card)
                            self.assertNotIn("why", card)
                    json.dumps(public)  # must be serialisable for the template

    def test_language_variants_resolve_to_different_code(self):
        for course in all_courses():
            for lvl in course["levels"]:
                if not lvl.get("challenge_by_language"):
                    continue
                py = resolve_challenge(lvl, "python")
                js = resolve_challenge(lvl, "javascript")
                self.assertEqual(py["type"], js["type"])
                self.assertNotEqual(json.dumps(py, sort_keys=True), json.dumps(js, sort_keys=True))

    def test_every_playable_level_opens_with_lesson_notes_or_is_story_only(self):
        for course in all_courses():
            for lvl in course["levels"]:
                if lvl["kind"] != "level" or lvl.get("no_lesson"):
                    continue
                self.assertTrue(lvl["lesson"]["points"], f"{course['slug']} {lvl['number']} has no lesson notes")

    def test_every_level_ships_banter_pools(self):
        for course in all_courses():
            for lvl in course["levels"]:
                public = public_level(course, lvl, language=None, beams=[])
                self.assertTrue(public["banter"]["doctor"], f"{course['slug']} {lvl['number']} has no doctor banter")
                self.assertTrue(public["banter"]["guide"], f"{course['slug']} {lvl['number']} guide {lvl['guide']} has no quips")
                self.assertEqual(len(set(public["banter"]["doctor"])), len(public["banter"]["doctor"]), "duplicate doctor lines")

    def test_soundtrack_covers_every_playable_level(self):
        from courses.soundtrack import LEVEL_MUSIC, LAB_ENTRANCE
        from curriculum import MUSIC
        for course in all_courses():
            titles = []
            for lvl in course["levels"]:
                public = public_level(course, lvl, language=None, beams=[])
                if lvl["kind"] == "quiz":
                    self.assertIsNone(public["music"])
                    continue
                self.assertIsNotNone(public["music"], f"{course['slug']} {lvl['number']} has no music")
                self.assertEqual(public["music"]["loop"], bool(lvl["obelisk"]))
                self.assertEqual(bool(public["boss_music"]), bool(lvl["boss"]))
                titles.append(public["music"]["title"])
            self.assertEqual(titles.count("Rhinoceros"), 1, f"{course['slug']}: Rhinoceros must play on exactly one level")
            for a, b in zip(titles, titles[1:]):
                self.assertNotEqual(a, b, f"{course['slug']}: '{a}' plays on two levels in a row")
            self.assertLessEqual(max(titles.count(t) for t in set(titles)) / len(titles), 0.6, f"{course['slug']}: one track repeats too much")
        for slug, table in LEVEL_MUSIC.items():
            for number, key in table.items():
                self.assertIn(key, MUSIC, f"{slug} {number}: unknown track {key}")
        self.assertEqual(set(LAB_ENTRANCE), set(COURSES))

    def test_check_levels_passes(self):
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "check_levels.py")],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("All levels OK.", result.stdout)


if __name__ == "__main__":
    unittest.main()
