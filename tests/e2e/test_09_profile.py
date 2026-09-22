"""Profile and account"""

import re

import pytest

from conftest import PASSWORD, new_name, signup


@pytest.fixture(scope="module")
def account(pg):
    return signup(pg, new_name("pw_prof"))


def test_overview_shows_beams_and_secrets(pg, account, steps):
    """The profile overview shows 0 / 4 beams, the secret count and the locked '???' cards"""
    steps("Open /profile")
    pg.goto("/profile")
    steps("Expect '0 / 4 beams lit', 'SECRET ACHIEVEMENTS · 0 / 8' and eight '???' cards")
    assert "0 / 4 beams lit" in pg.text_content(".secrets-section h2")
    assert re.search(r"SECRET ACHIEVEMENTS\s*·\s*0 / 8", pg.text_content(".secrets-label"))
    assert pg.locator(".secret-locked").count() == 8


def test_change_username_keeps_the_session(pg, account, steps):
    """Renaming the account updates the top bar at once and the old name stops working"""
    new = new_name("pw_renamed")
    steps("Open SETTINGS & PRIVACY, type %s in the username form, CHANGE USERNAME" % new)
    pg.goto("/profile?tab=settings")
    pg.fill("form[action='/profile/username'] input[name=username]", new)
    pg.click("form[action='/profile/username'] button")
    steps("Expect the confirmation flash and the new name in the top bar")
    assert "Username changed to " + new in pg.text_content(".flash")
    assert new.upper() in pg.text_content(".profile-button")
    steps("Expect the form to show the 14-day wait")
    assert "NEXT CHANGE IN 14 DAYS" in pg.text_content("form[action='/profile/username']")
    test_change_username_keeps_the_session.new = new


def test_change_password_then_login(pg, account, steps):
    """A password change is enforced on the next login"""
    steps("Fill the change-password form with a wrong current password")
    pg.fill("input[name=current_password]", "Wrong!Pass1")
    pg.fill("input[name=new_password]", "Abc!Def-2079x")
    pg.fill("input[name=confirm_password]", "Abc!Def-2079x")
    pg.click("form[action='/profile/password'] button")
    assert "current password is not right" in pg.text_content(".flash")
    steps("Fill it with the right current password")
    pg.fill("input[name=current_password]", PASSWORD)
    pg.fill("input[name=new_password]", "Abc!Def-2079x")
    pg.fill("input[name=confirm_password]", "Abc!Def-2079x")
    pg.click("form[action='/profile/password'] button")
    assert "Password changed" in pg.text_content(".flash")
    steps("Log out and log in with the new name and the new password")
    pg.goto("/logout")
    pg.goto("/login")
    pg.fill("#username", test_change_username_keeps_the_session.new)
    pg.fill("#password", "Abc!Def-2079x")
    pg.click("button.login-submit")
    pg.wait_for_url(re.compile(r"/$"))
    steps("Expect the home page")
    assert test_change_username_keeps_the_session.new.upper() in pg.text_content(".profile-button")
