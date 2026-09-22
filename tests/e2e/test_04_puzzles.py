"""Internet puzzles"""

import pytest

from conftest import choose_character, expect_access_granted, game, new_name, open_level, press, signup, start_level, teleport
from curriculum import COURSES, resolve_challenge


def level(course, number):
    return next(l for l in COURSES[course]["levels"] if l["number"] == number)


@pytest.fixture(scope="module")
def account(pg):
    name = signup(pg, new_name())
    choose_character(pg)
    return name


def open_terminal(pg):
    teleport(pg, "terminal", offset_x=-4)
    press(pg, "e")
    pg.wait_for_selector("#overlay-challenge:not(.hidden)")


def expect_complete(pg):
    expect_access_granted(pg)


def test_multiple_choice(pg, account, steps):
    """Internet 1: a wrong option gives feedback, the right one completes the level"""
    steps("Open Internet level 1, start, open the terminal")
    open_level(pg, "internet", 1)
    start_level(pg)
    open_terminal(pg)
    answer = resolve_challenge(level("internet", 1))["answer"]
    wrong = (answer + 1) % len(resolve_challenge(level("internet", 1))["options"])
    steps("Click a wrong option and ANSWER")
    pg.click(".choice-button >> nth=%d" % wrong)
    pg.click("#btn-submit")
    pg.wait_for_function("() => document.getElementById('challenge-feedback').textContent.length > 0")
    steps("Expect feedback without the level completing")
    assert game(pg, "cyberGame.state.solved") is False
    steps("Click the right option and ANSWER")
    pg.click(".choice-button >> nth=%d" % answer)
    pg.click("#btn-submit")
    steps("Expect the ACCESS GRANTED card")
    expect_complete(pg)


def test_wires_by_clicking(pg, account, steps):
    """Internet 2: connect each device to its port by clicking, then CONNECT"""
    steps("Open Internet level 2, start, open the junction board")
    open_level(pg, "internet", 2)
    start_level(pg)
    open_terminal(pg)
    challenge = resolve_challenge(level("internet", 2))
    steps("Click LAPTOP then its port, and so on for every device")
    for index, port in enumerate(challenge["answer"]):
        pg.click(".wire-device >> nth=%d" % index)
        pg.click(".wire-port >> nth=%d" % port)
    steps("Expect four drawn wires, then CONNECT")
    assert pg.eval_on_selector_all("svg.wire-lines path", "els => els.length") == len(challenge["devices"])
    pg.click("#btn-submit")
    steps("Expect the ACCESS GRANTED card")
    expect_complete(pg)


def test_assign_a_valid_ip(pg, account, steps):
    """Internet 3: a taken address is refused, a free one on the network is accepted"""
    steps("Open Internet level 3, start, open the terminal")
    open_level(pg, "internet", 3)
    start_level(pg)
    open_terminal(pg)
    challenge = resolve_challenge(level("internet", 3))
    steps("Type a taken address and ASSIGN")
    pg.fill(".ip-input", challenge["taken"][0])
    pg.click("#btn-submit")
    pg.wait_for_function("() => document.getElementById('challenge-feedback').textContent.length > 0")
    assert "already in use" in pg.text_content("#challenge-feedback")
    free = next(challenge["network"] + str(n) for n in range(2, 254) if challenge["network"] + str(n) not in challenge["taken"])
    steps("Type %s and ASSIGN" % free)
    pg.fill(".ip-input", free)
    pg.click("#btn-submit")
    steps("Expect the ACCESS GRANTED card")
    expect_complete(pg)


def test_route_packets(pg, account, steps):
    """Internet 4: deliver every packet to the machine with its IP"""
    steps("Open Internet level 4, start, open the post room")
    open_level(pg, "internet", 4)
    start_level(pg)
    open_terminal(pg)
    challenge = resolve_challenge(level("internet", 4))
    steps("Click each packet, then the name of the machine it belongs to")
    for packet, machine in zip(challenge["packets"], challenge["answer"]):
        pg.click(".packet-chip:has-text('%s')" % packet["label"])
        pg.click(".machine-box >> nth=%d >> .machine-name" % machine)
    steps("Expect the tray empty, then DELIVER")
    assert pg.locator(".packet-tray .packet-chip").count() == 0
    pg.click("#btn-submit")
    steps("Expect the ACCESS GRANTED card")
    expect_complete(pg)
