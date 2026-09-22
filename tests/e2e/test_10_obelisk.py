"""The obelisk finale"""

import pytest

from conftest import choose_character, game, grant_everything, new_name, open_level, press, signup, start_level, teleport


@pytest.fixture(scope="module")
def account(pg, server):
    name = signup(pg, new_name("pw_obelisk"))
    choose_character(pg)
    grant_everything(server, name)     # every level and badge, like a finished player
    return name


def test_obelisk_button_lights_the_beam(pg, account, steps):
    """Pressing the obelisk button plays the cutscene and completes the course"""
    steps("Open Python level 30 (The Obelisk) as a player who finished everything, and start")
    open_level(pg, "python", 30)
    start_level(pg)
    steps("Expect the obelisk sky with the other courses' beams already lit")
    assert game(pg, "cyberGame.level.obelisk") is True
    assert set(game(pg, "cyberGame.level.beams")) >= {"cybersecurity", "internet", "secure-coding"}
    steps("Stand at the button and press E")
    teleport(pg, "button", offset_x=-12)
    press(pg, "e")
    steps("Expect the cutscene phase, then LEVEL COMPLETE within six seconds")
    assert game(pg, "cyberGame.state.phase") == "cutscene"
    pg.wait_for_function("() => document.getElementById('hud-objective').textContent.includes('LEVEL COMPLETE')", timeout=9000)
    pg.wait_for_selector("#overlay-result:not(.hidden)")
    steps("Expect a COURSE COMPLETE card")
    assert "COURSE COMPLETE" in pg.text_content("#result-label")


def test_profile_shows_four_beams(pg, account, steps):
    """The profile shows 4 / 4 beams lit and every secret achievement"""
    steps("Open /profile")
    pg.goto("/profile")
    steps("Expect '4 / 4 beams lit' and 8 / 8 secret achievements")
    assert "4 / 4 beams lit" in pg.text_content(".secrets-section h2")
    assert "8 / 8" in pg.text_content(".secrets-label")
    assert pg.locator(".secret-earned").count() == 8
