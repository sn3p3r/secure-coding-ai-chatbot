"""Friends, requests and blocking"""

import pytest

from conftest import new_name, signup


@pytest.fixture(scope="module")
def me(pg):
    return signup(pg, new_name("pw_me"))


@pytest.fixture(scope="module")
def them(other):
    return signup(other, new_name("pw_them"))


def test_search_finds_a_registered_account(pg, me, them, steps):
    """The Friends search lists another registered student with an ADD FRIEND button"""
    steps("Open /friends, SEARCH tab, search for %s" % them[:8])
    pg.goto("/friends?tab=search")
    pg.fill("input[name=q]", them[:8])
    pg.click(".friend-search button")
    steps("Expect a result card with ADD FRIEND")
    card = pg.locator(".friend-result[data-username='%s']" % them)
    assert card.is_visible()
    assert "ADD FRIEND" in card.text_content()


def test_request_waits_under_sent(pg, me, them, steps):
    """Sending a request lists them under SENT, not FRIENDS, with a flash message"""
    steps("Click ADD FRIEND on the result")
    pg.click(".friend-result[data-username='%s'] button" % them)
    steps("Expect the SENT tab with the request and the friends count at 0")
    assert "Friend request sent" in pg.text_content(".flash")
    assert pg.locator("[data-panel=sent] [data-username='%s']" % them).is_visible()
    assert "FRIENDS 0" in pg.text_content(".tabs")


def test_they_accept_and_both_are_friends(pg, other, me, them, steps):
    """The other person sees a badge and a request, accepts, and both lists show the pair"""
    steps("As the other person, open the home page")
    other.goto("/")
    steps("Expect a '1' badge next to FRIENDS in the top bar")
    assert other.text_content(".top-badge").strip() == "1"
    steps("Open /friends, REQUESTS tab, click ACCEPT")
    other.goto("/friends?tab=requests")
    other.click("[data-panel=requests] [data-username='%s'] .friend-accept" % me)
    steps("Expect 'You are now friends.' and the pair in both FRIENDS lists")
    assert "now friends" in other.text_content(".flash")
    assert other.locator("[data-panel=friends] [data-username='%s']" % me).is_visible()
    pg.goto("/friends")
    assert pg.locator("[data-panel=friends] [data-username='%s']" % them).is_visible()


def test_friend_card_links_to_their_profile(pg, me, them, steps):
    """A friend's card opens their profile page with progress visible"""
    steps("Click the friend's name")
    pg.click("[data-panel=friends] [data-username='%s'] .friend-name" % them)
    steps("Expect /u/<name> with OVERALL COMPLETION")
    pg.wait_for_url("**/u/" + them)
    assert "OVERALL COMPLETION" in pg.text_content("main")
    assert "REMOVE FRIEND" in pg.text_content(".user-actions")


def test_block_ends_the_friendship(pg, other, me, them, steps):
    """Blocking from the profile removes the friendship and hides the blocker from the other side"""
    steps("Click BLOCK on their profile and confirm the dialog")
    pg.once("dialog", lambda dialog: dialog.accept())
    pg.click(".user-actions form[action='/friends/block'] button")
    steps("Expect the BLOCKED tab listing them")
    assert pg.locator("[data-panel=blocked] [data-username='%s']" % them).is_visible()
    steps("As the other person, open /u/<me>")
    other.goto("/u/" + me)
    steps("Expect a private-profile notice and no friend card any more")
    assert "keeps this profile private" in other.text_content("main")
    other.goto("/friends")
    assert other.locator("[data-panel=friends] [data-username='%s']" % me).count() == 0
