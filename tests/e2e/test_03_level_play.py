"""Playing a level"""

import pytest

from conftest import (choose_character, close_dialogue, dialogue_text, expect_access_granted, game, new_name,
                      open_level, press, signup, start_level, teleport, walk_out)


@pytest.fixture(scope="module")
def account(pg):
    name = signup(pg, new_name())
    choose_character(pg)
    return name


def test_start_skips_intro_and_shows_hud(pg, account, steps):
    """START LEVEL runs the matrix intro, the story, and hands over control with the HUD live"""
    steps("Open Python level 1")
    open_level(pg, "python", 1)
    steps("Read the lesson popup, press START LEVEL, press Enter through intro and story")
    start_level(pg)
    steps("Expect play phase, six hearts, a running timer and the objective in the HUD")
    assert game(pg, "cyberGame.state.phase") == "play"
    assert pg.text_content("#hud-hearts").count("♥") == 6
    assert pg.text_content("#hud-objective").strip() != "—"
    pg.wait_for_function("() => document.getElementById('hud-timer').textContent !== '00:00'")


def test_walk_and_jump(pg, account, steps):
    """Holding D moves the player right; Space lifts them off the ground"""
    steps("Record the player's position")
    before = game(pg, "cyberGame.player.x")
    steps("Hold D for 400 ms")
    press(pg, "d", hold_ms=400)
    after = game(pg, "cyberGame.player.x")
    steps("Expect the player further right")
    assert after > before + 10, (before, after)
    steps("Press Space and sample the vertical speed")
    pg.keyboard.down(" ")
    pg.wait_for_timeout(80)
    pg.keyboard.up(" ")
    vy = game(pg, "cyberGame.player.vy")
    steps("Expect upward motion")
    assert vy < 0, vy


def test_guide_briefing_then_quips(pg, account, steps):
    """Talking to BYTE gives the briefing once, then a different quip each time"""
    steps("Stand next to BYTE and press E")
    teleport(pg, "npc")
    press(pg, "e")
    first = dialogue_text(pg)
    steps("Press Enter through the briefing")
    close_dialogue(pg)
    seen = set()
    steps("Press E three more times")
    for _ in range(3):
        press(pg, "e")
        pg.wait_for_timeout(100)
        seen.add(dialogue_text(pg))
        close_dialogue(pg)
    steps("Expect a briefing first and quips afterwards, never the same quip twice in a row")
    assert first and first not in seen
    assert len(seen) >= 2, seen


def test_terminal_solves_python_level_1(pg, account, steps):
    """The terminal accepts print("open") and the level completes with the win card"""
    steps("Stand at the terminal and press E")
    teleport(pg, "terminal", offset_x=-4)
    press(pg, "e")
    pg.wait_for_selector("#overlay-challenge:not(.hidden)")
    steps("Type a wrong line and RUN")
    pg.fill("textarea.challenge-code", 'print("closed")')
    pg.click("#btn-submit")
    steps("Expect a nudge that names the line but not the answer")
    pg.wait_for_function("() => document.getElementById('challenge-feedback').textContent.length > 0")
    feedback = pg.text_content("#challenge-feedback")
    assert "Line 1" in feedback and "open" not in feedback
    steps("Type print(\"open\") and RUN")
    pg.fill("textarea.challenge-code", 'print("open")')
    pg.click("#btn-submit")
    steps("Expect the ACCESS GRANTED card and the level marked solved")
    expect_access_granted(pg)
    steps("Click OPEN THE DOOR and walk to the exit")
    walk_out(pg)
    steps("Expect LEVEL COMPLETE! in the HUD")
    assert "LEVEL COMPLETE" in pg.text_content("#hud-objective")


def test_story_level_completes_at_the_exit(pg, account, steps):
    """Cybersecurity level 1 is a story level: reaching the exit completes it"""
    steps("Open Cybersecurity level 1 and start it")
    open_level(pg, "cybersecurity", 1)
    start_level(pg)
    steps("Walk onto the exit")
    teleport(pg, "exit", offset_x=0)
    pg.wait_for_timeout(300)
    steps("Expect the level to complete")
    pg.wait_for_function("() => document.getElementById('hud-objective').textContent.includes('LEVEL COMPLETE')")
    assert game(pg, "cyberGame.state.solved") is True


def test_items_candy_and_drop(pg, account, steps):
    """Cybersecurity level 2: pick up candy, eat only from its slot with F, drop the sword with Q"""
    steps("Open Cybersecurity level 2 (sword in hand) and start")
    open_level(pg, "cybersecurity", 2)
    start_level(pg)
    steps("Walk over the candy and the hint chip")
    teleport(pg, "item", offset_x=0, item="CANDY")
    pg.wait_for_timeout(150)
    teleport(pg, "item", offset_x=0, item="HINT CHIP")
    pg.wait_for_timeout(150)
    slots = pg.eval_on_selector_all(".inv-slot .inv-item", "els => els.map(e => e.textContent)")
    steps("Expect SWORD, CANDY and HINT CHIP in the inventory")
    assert "CANDY" in slots and "HINT CHIP" in slots and "SWORD" in slots, slots

    steps("Take damage (harness), press E with nothing nearby")
    pg.evaluate("() => { cyberGame.player.hp = 2; cyberGame.player.x = 60; cyberGame.player.y = 40; cyberGame.step(1); }")
    press(pg, "e")
    steps("Expect candy untouched and a reminder toast")
    assert game(pg, "cyberGame.player.hp") == 2
    assert "select its slot" in pg.text_content("#game-toast")

    steps("Select the candy slot and press F")
    candy_slot = slots.index("CANDY") + 1
    press(pg, str(candy_slot))
    press(pg, "f")
    steps("Expect +3 health and the candy gone")
    assert game(pg, "cyberGame.player.hp") == 5
    assert "Candy eaten" in pg.text_content("#game-toast")

    steps("Select the sword slot and press Q")
    press(pg, "1")
    press(pg, "q")
    steps("Expect the sword on the ground and a toast")
    assert "dropped" in pg.text_content("#game-toast")
    assert game(pg, "cyberGame.state.inventory[0]") is None


def test_hint_chip_is_never_wasted(pg, account, steps):
    """Python level 2: a hint chip shows the level's one hint, then the button locks instead of eating chips"""
    steps("Open Python level 2 and start")
    open_level(pg, "python", 2)
    start_level(pg)
    steps("Walk over the hint chip")
    teleport(pg, "item", offset_x=0, item="HINT CHIP")
    pg.wait_for_timeout(150)
    steps("Open the terminal and click USE HINT CHIP")
    teleport(pg, "terminal", offset_x=-4)
    press(pg, "e")
    pg.wait_for_selector("#overlay-challenge:not(.hidden)")
    assert "USE HINT CHIP (1)" in pg.text_content("#btn-hint")
    pg.click("#btn-hint")
    pg.wait_for_selector(".hint-line")
    steps("Expect the hint shown, the chip spent, and the button locked with 'NO MORE HINTS HERE'")
    assert pg.text_content("#btn-hint") == "NO MORE HINTS HERE"
    assert pg.is_disabled("#btn-hint")
    assert "HINT CHIP" not in pg.eval_on_selector_all(".inv-slot .inv-item", "els => els.map(e => e.textContent)")
