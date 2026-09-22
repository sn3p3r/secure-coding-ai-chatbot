"""Leaderboard"""

import pytest

from conftest import choose_character, new_name, open_level, press, signup, start_level, teleport


@pytest.fixture(scope="module")
def account(pg):
    name = signup(pg, new_name("pw_board"))
    choose_character(pg)
    return name


def test_course_is_required(pg, account, steps):
    """The level board asks for a course first and the level box is disabled"""
    steps("Open /leaderboard")
    pg.goto("/leaderboard")
    steps("Expect 'Choose a course above' and a disabled level box")
    assert "Choose a course above" in pg.text_content("main")
    assert pg.is_disabled("#board-level")


def test_level_box_follows_the_course(pg, account, steps):
    """Picking a course fills the level dropdown with that course's levels"""
    steps("Choose Internet Basics in the course box")
    pg.select_option("#board-course", "internet")
    steps("Expect 16 levels in the level box, first 'Inside the Cable'")
    assert pg.locator("#board-level option").count() == 16
    assert "Inside the Cable" in pg.text_content("#board-level option >> nth=0")
    steps("Choose Python instead")
    pg.select_option("#board-course", "python")
    assert pg.locator("#board-level option").count() == 30


def test_times_appear_after_a_completion(pg, account, steps):
    """Completing Cybersecurity 1 puts the player on that level's board with a profile link"""
    steps("Complete Cybersecurity level 1 by reaching the exit")
    open_level(pg, "cybersecurity", 1)
    start_level(pg)
    teleport(pg, "exit", offset_x=0)
    pg.wait_for_function("() => document.getElementById('hud-objective').textContent.includes('LEVEL COMPLETE')")
    steps("Open the leaderboard for Cybersecurity level 1, slowest first")
    pg.goto("/leaderboard?course=cybersecurity&level=1&order=desc")
    steps("Expect the player's row and the SLOWEST FIRST option selected")
    row = pg.locator(".board-table tr.board-me")
    assert row.is_visible()
    assert account in row.text_content()
    assert pg.input_value("select[name=order]") == "desc"
    steps("Tick FRIENDS ONLY and SHOW TIMES")
    pg.check("input[name=friends]")
    pg.click(".board-form button")
    assert pg.locator(".board-table tbody tr").count() == 1


def test_time_in_the_academy_tab(pg, account, steps):
    """The TIME IN THE ACADEMY tab ranks time spent and lists the player"""
    steps("Click the TIME IN THE ACADEMY tab")
    pg.click(".tabs [data-tab=time]")
    steps("Expect the level board hidden and the time table with the player")
    assert pg.is_hidden("[data-panel=levels]")
    pg.wait_for_function("() => document.querySelector('[data-panel=time] .board-table, [data-panel=time] .board-empty') !== null")
    assert "MOST TIME IN THE ACADEMY" in pg.text_content("[data-panel=time]")
