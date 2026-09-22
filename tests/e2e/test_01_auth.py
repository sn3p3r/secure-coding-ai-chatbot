"""Sign-up and login"""

import re

from conftest import PASSWORD, new_name, signup


def test_signup_rejects_a_weak_password(pg, steps):
    """A weak password keeps the sign-up button locked and flags the broken rules live"""
    steps("Open /signup")
    pg.goto("/signup")
    steps("Fill username 'pw_weak' and type 'password' in both password fields")
    pg.fill("#username", "pw_weak")
    pg.fill("#password", "password")
    pg.fill("#confirm_password", "password")
    steps("Expect the submit button disabled and the uppercase / number / symbol rules unmet")
    assert pg.is_disabled("button.login-submit")
    for rule in ("req-upper", "req-number", "req-special"):
        assert "requirement-good" not in (pg.get_attribute("#" + rule, "class") or ""), rule
    assert "requirement-good" in (pg.get_attribute("#req-lower", "class") or "")
    steps("Type a strong password instead")
    pg.fill("#password", PASSWORD)
    pg.fill("#confirm_password", PASSWORD)
    steps("Expect every rule met and the button enabled")
    assert pg.is_enabled("button.login-submit")
    assert pg.locator(".requirement-good").count() >= 6


def test_signup_rejects_a_bad_username(pg, steps):
    """A username with spaces, links or emoji is refused"""
    steps("Open /signup")
    pg.goto("/signup")
    steps("Fill username 'http://evil.example' with a strong password")
    pg.fill("#username", "http://evil.example")
    pg.fill("#password", PASSWORD)
    pg.fill("#confirm_password", PASSWORD)
    steps("Submit the form")
    pg.click("button.login-submit")
    steps("Expect the letters-numbers-underscores rule")
    assert "letters, numbers and underscores" in pg.text_content(".login-error")


def test_signup_then_home(pg, steps):
    """A valid sign-up lands on the home page, signed in"""
    name = new_name()
    steps("Open /signup and fill a valid account (%s)" % name)
    signup(pg, name)
    steps("Expect the home page with the username in the top bar")
    assert pg.url.endswith("/")
    assert name.upper() in pg.text_content(".profile-button")
    test_signup_then_home.name = name


def test_logout_locks_the_pages(pg, steps):
    """After logout, protected pages redirect to the login form"""
    steps("Open /logout")
    pg.goto("/logout")
    steps("Open /profile")
    pg.goto("/profile")
    steps("Expect to land on /login")
    pg.wait_for_url(re.compile(r"/login$"))
    assert pg.is_visible("#username")


def test_login_wrong_then_right(pg, steps):
    """A wrong password is refused; the right one signs in"""
    name = test_signup_then_home.name
    steps("Open /login and try %s with a wrong password" % name)
    pg.goto("/login")
    pg.fill("#username", name)
    pg.fill("#password", "Wrong!Pass1")
    pg.click("button.login-submit")
    steps("Expect 'Username or password is incorrect.'")
    assert "incorrect" in pg.text_content(".login-error")
    steps("Try again with the right password")
    pg.fill("#username", name)
    pg.fill("#password", PASSWORD)
    pg.click("button.login-submit")
    steps("Expect the home page")
    pg.wait_for_url(re.compile(r"/$"))
    assert name.upper() in pg.text_content(".profile-button")
