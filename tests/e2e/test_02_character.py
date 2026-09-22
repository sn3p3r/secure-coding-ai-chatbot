"""Character creation"""

import re

import pytest

from conftest import new_name, pick, signup


@pytest.fixture(scope="module")
def account(pg):
    return signup(pg, new_name())


def test_level_needs_a_character_first(pg, account, steps):
    """Opening a level before creating a character redirects to the character page"""
    steps("Open /curriculum/python/1 with a brand-new account")
    pg.goto("/curriculum/python/1")
    steps("Expect the character page")
    pg.wait_for_url(re.compile(r"/character"))
    assert pg.is_visible("#character-form")


def test_character_form_has_defaults_and_a_preview(pg, account, steps):
    """Every group starts with a default chip selected and the pixel preview is drawn"""
    steps("Open /character")
    pg.goto("/character")
    steps("Expect one checked chip in each of the four groups")
    for field in ("gender", "hair", "hair_color", "outfit"):
        assert pg.locator("input[name=%s]:checked" % field).count() == 1, field
    steps("Expect the preview canvas to have painted pixels")
    painted = pg.evaluate("""() => {
        const c = document.getElementById('preview-canvas');
        const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
        let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
        return n;
    }""")
    assert painted > 200, painted


def test_character_saved_and_level_opens(pg, account, steps):
    """Choosing every option saves the character and the level page renders"""
    steps("Pick gender, hair, hair colour and outfit by clicking the chips")
    for field, value in (("gender", "female"), ("hair", "spiky"), ("hair_color", "red"), ("outfit", "blue")):
        pick(pg, field, value)
    steps("Save")
    pg.click("button.large-button")
    pg.wait_for_url(re.compile(r"/$"))
    steps("Open /curriculum/python/1")
    pg.goto("/curriculum/python/1")
    steps("Expect the lesson popup with the START LEVEL button and the level title")
    assert pg.is_visible("#btn-start")
    assert "Speak to the Machine" in pg.text_content("main")
