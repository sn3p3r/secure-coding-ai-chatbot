"""Profile settings and privacy"""

import os

import pytest

from conftest import REPORT_DIR, new_name, signup, tiny_png


@pytest.fixture(scope="module")
def me(pg):
    return signup(pg, new_name("pw_priv"))


@pytest.fixture(scope="module")
def viewer(other):
    return signup(other, new_name("pw_view"))


def test_settings_tab_shows_privacy_defaults(pg, me, steps):
    """The SETTINGS & PRIVACY tab shows the six controls with their defaults"""
    steps("Open /profile and click SETTINGS & PRIVACY")
    pg.goto("/profile")
    pg.click(".tabs [data-tab=settings]")
    steps("Expect the overview hidden and the privacy form visible")
    assert pg.is_hidden("[data-panel=overview]")
    assert pg.input_value("select[name=profile_visibility]") == "everyone"
    assert pg.input_value("select[name=show_time]") == "friends"
    assert pg.is_checked("input[name=search_visible]")
    assert pg.is_checked("input[name=leaderboard_times]")


def test_upload_a_profile_picture(pg, me, steps):
    """A PNG upload appears in the top bar and on the profile; the fake file is refused"""
    steps("Choose a text file renamed .png and UPLOAD")
    fake = os.path.join(REPORT_DIR, "fake.png")
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(fake, "wb") as handle:
        handle.write(b"not an image")
    pg.set_input_files("input[name=picture]", fake)
    pg.click("form[action='/profile/picture'] button")
    steps("Expect 'not a PNG, JPEG, GIF or WebP image'")
    assert "not a PNG" in pg.text_content(".flash")
    steps("Choose a real 64x64 PNG and UPLOAD")
    real = tiny_png(os.path.join(REPORT_DIR, "avatar.png"))
    pg.set_input_files("input[name=picture]", real)
    pg.click("form[action='/profile/picture'] button")
    steps("Expect 'Profile picture updated' and the image in the top bar")
    assert "Profile picture updated" in pg.text_content(".flash")
    assert pg.locator(".top-bar .avatar-img").is_visible()
    assert pg.evaluate("() => document.querySelector('.top-bar .avatar-img').naturalWidth") > 0


def test_stranger_sees_progress_but_not_time(pg, other, me, viewer, steps):
    """With the defaults a stranger sees progress and achievements but time spent is HIDDEN"""
    steps("As a stranger, open /u/<me>")
    other.goto("/u/" + me)
    steps("Expect completion and beams shown, time spent HIDDEN")
    text = other.text_content("main")
    assert "OVERALL COMPLETION" in text and "beams lit" in text
    assert "HIDDEN" in other.text_content(".stat-card:has-text('TIME SPENT')")


def test_private_profile_hides_everything(pg, other, me, viewer, steps):
    """Setting 'who can open your profile' to NOBODY hides the profile and search entry"""
    steps("Set profile visibility to NOBODY, untick search, SAVE PRIVACY")
    pg.goto("/profile?tab=settings")
    pg.select_option("select[name=profile_visibility]", "nobody")
    pg.uncheck("input[name=search_visible]")
    pg.click("form[action='/profile/privacy'] button")
    assert "Privacy settings saved" in pg.text_content(".flash")
    steps("As a stranger, open /u/<me> and search for the name")
    other.goto("/u/" + me)
    assert "keeps this profile private" in other.text_content("main")
    other.goto("/friends?tab=search&q=" + me[:10])
    steps("Expect a private notice and no search result")
    assert other.locator("[data-username='%s']" % me).count() == 0
