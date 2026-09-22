"""Music, effects and credits"""

import pytest

from conftest import choose_character, game, new_name, open_level, press, signup, start_level


@pytest.fixture(scope="module")
def account(pg):
    name = signup(pg, new_name("pw_audio"))
    choose_character(pg)
    return name


def test_track_starts_and_now_playing_shows(pg, account, steps):
    """START starts the level's track and the faint 'now playing' line names it"""
    steps("Open Python level 1 and press START LEVEL")
    open_level(pg, "python", 1)
    start_level(pg)
    steps("Expect the track file in the level data and the now-playing line visible")
    assert game(pg, "cyberGame.level.music.file").endswith("ossuary-1-a-beginning.m4a")
    pg.wait_for_function("() => !document.getElementById('hud-music').hidden")
    assert "Ossuary 1 - A Beginning" in pg.text_content("#hud-music")


def test_m_key_and_button_toggle_sound(pg, account, steps):
    """M mutes everything and the ♪ button unmutes; the choice is stored on the device"""
    steps("Press M")
    press(pg, "m")
    steps("Expect the ♪ button crossed out, now-playing hidden, 'off' stored")
    assert "is-off" in pg.get_attribute("#music-btn", "class")
    pg.wait_for_function("() => document.getElementById('hud-music').hidden")
    assert pg.evaluate("() => localStorage.getItem('academyMusic')") == "off"
    steps("Click the ♪ button")
    pg.click("#music-btn")
    steps("Expect sound back on")
    assert "is-off" not in pg.get_attribute("#music-btn", "class")
    assert pg.evaluate("() => localStorage.getItem('academyMusic')") == "on"


def test_effects_are_listed_and_served(pg, account, steps):
    """The level carries the slash, crunch and win clips and each file is served"""
    steps("Read the effect list from the level data")
    sfx = game(pg, "cyberGame.level.sfx")
    assert set(sfx) == {"slash", "crunch", "win"}
    steps("Fetch each clip from the page")
    for name, file in sfx.items():
        status = pg.evaluate("f => fetch(f, {method: 'HEAD'}).then(r => r.status)", file)
        assert status == 200, (name, status)


def test_credits_tab_lists_every_artist(pg, account, steps):
    """The footer's CREDITS tab lists all tracks and effects with their licences"""
    steps("Scroll to the footer and click CREDITS")
    pg.click(".footer-tabs [data-tab=credits]")
    steps("Expect one entry per track and effect, every author, and the licence links")
    from curriculum import MUSIC, SFX
    assert pg.locator(".credit-list li").count() == len(MUSIC) + len(SFX)
    text = pg.text_content(".credit-list")
    for needle in ("Kevin MacLeod (incompetech.com)", "Artninja (freesound.org)", "theplax (freesound.org)", "EVRetro (freesound.org)"):
        assert needle in text, needle
    assert pg.locator(".credit-list a[href='http://creativecommons.org/licenses/by/4.0/']").count() == len(MUSIC) + len(SFX) - 1
    assert pg.locator(".credit-list a[href='https://creativecommons.org/publicdomain/zero/1.0/']").count() == 1
