"""
Extra lines for the people the player keeps bumping into.

A level's own `npcs` lines are said first. After that the game rotates
through the pool for the level's theme, in a shuffled order that never
repeats the line just heard. Guides (BYTE, VEX, PING, LINT) say their
level dialogue once; talking to them again gets a quip from their pool.
"""

# Idle doctors, by map theme. "lab" is the Python lab; the white lab of
# the Cybersecurity course uses "jungle"/"lab" too, so both pools exist.
DOCTORS = {
    "lab": [
        "Don't touch that tank. Last intern who did is now a variable.",
        "I've run this experiment 400 times. It's still a 'while' loop, apparently.",
        "The coffee machine asks for a password now. I miss 2019.",
        "If the specimen says 'hello world', do NOT answer.",
        "My badge says 'Senior Scientist'. My salary says 'intern'.",
        "We named the big snake 'Recursion'. It keeps calling itself.",
        "Have you seen my keys? Not the door ones. The dictionary ones.",
        "Somebody indented the whole lab by four spaces. Nothing lines up any more.",
        "I asked the AI for a cure. It gave me a poem. A good poem, but still.",
        "The lights flicker when the loop forgets to stop. That's most days.",
        "Rule one of the lab: never print the password. Rule two: see rule one.",
        "That door opens for the right code and nothing else. I've tried 'please'.",
        "Careful, the floor was mopped with something that isn't water.",
        "I'm not lost. The lab is just... larger than the map.",
        "My lunch is in the specimen fridge. Third shelf. Don't judge me.",
    ],
    "jungle": [
        "You're not supposed to be in here. Then again, neither am I.",
        "The firewall gate hums when it's angry. It's been humming all week.",
        "I filed a ticket about the malware cages. They closed it as 'working as intended'.",
        "Dr. Vex says the vents are sealed. Dr. Vex says a lot of things.",
        "My password is my dog's name. Don't tell anyone his name is Xk9#Tq2!.",
        "If a specimen offers you a free gift card, it's phishing. Even in a cage.",
        "I spilled coffee on the intrusion detector. Now it detects coffee.",
        "The brain upstairs thinks it's in charge. Technically the janitor is.",
        "Every corridor looks the same. That's on purpose. Also cheaper.",
        "We tried two-factor on the fridge. Nobody has eaten since Tuesday.",
        "I got locked out of my own office for typing the code too slowly. Three times.",
        "They said 'defence in depth'. I said 'it's a hallway'. We compromised.",
    ],
    "tower": [
        "The higher you climb, the more the code echoes. Try not to shout.",
        "Every floor has a bug. Every bug has a floor. It's a rental agreement.",
        "I built the stairs with a for loop. The last step is off by one.",
    ],
    "sewer": [
        "It's not a sewer, it's a 'data pipeline'. Smells the same.",
        "If you see a snake, it's a list. If it bites, it's a tuple.",
        "Somebody dropped a semicolon down here in 2007. We never found it.",
    ],
    "default": [
        "Keep moving. The terminal won't solve itself. I checked.",
        "I'd help, but the last time I helped, a door locked.",
        "Between you and me, the hint chips taste terrible.",
        "The guide says nice things about you. I've heard worse.",
        "Have you tried turning the level off and on again?",
    ],
}

# What a guide says when you talk to them again after the level briefing.
GUIDES = {
    "BYTE": [
        "Still here? The terminal's over there. I'm just decorative now.",
        "I'd tell you the answer, but then the Grove would delete me.",
        "Fun fact: I was compiled on a Tuesday. It explains a lot.",
        "You keep coming back. Is it my sprite? It's the sprite.",
        "Pro tip: read the notes. Second pro tip: read them again.",
        "If you press E once more I start charging by the word.",
        "I've seen a hundred recruits. You're at least top ninety.",
        "The snakes have a group chat. You're mentioned. Positively, I think.",
    ],
    "VEX": [
        "You're inside my lab. That's either brave or a typo in your career.",
        "Every alarm you trip is a lesson. Expensive lessons, for me.",
        "The cages are for the malware. The doors are for you. Keep the difference.",
        "I don't do hints. I do consequences. The terminal does hints.",
        "You remind me of an intrusion I once admired. Briefly.",
        "Yes, the coats are white. It hides the coffee.",
    ],
    "PING": [
        "Every packet you send has my name on it. No pressure.",
        "The stream below is live data. Very live. Do not swim.",
        "DNS is just the internet's phone book. Nobody's reads it either.",
        "Sniffers are sneaky. Loud, though. Listen for the crunching.",
        "I've routed a million packets today. You're my favourite so far. Top ten.",
        "If the cable smells hot, that's not the cable. That's the deadline.",
    ],
    # The lab's public-address system, before anyone in the white lab has a name.
    "STATIC": [
        "[static] Unauthorised movement in corridor B. Probably a cat. Probably.",
        "[static] Reminder: the vending machine accepts badges, not coins, not pleading.",
        "[static] All staff: the firewall gate is NOT a shortcut. Stop trying.",
        "[static] Lost: one door code, written on a hand. If found, wash the hand.",
        "[static] Today's password is yesterday's password. Security thanks you.",
        "[static] If you can hear this, you are inside. If you can't, carry on.",
        "[static] Specimen feeding is at noon. Do not be the feeding.",
    ],
    "LINT": [
        "I flagged a warning in your posture. Non-blocking.",
        "Every line you write, I read twice. It's not personal. It's my job.",
        "I once found a bug that was just a comment saying 'bug'.",
        "Semicolons in Python. I still have nightmares.",
        "Safe code is boring code. Boring code is the goal.",
        "Talk to the mentor bot. It has feelings. Simulated, but many.",
    ],
}


def doctor_lines(theme):
    return DOCTORS.get(theme, []) + DOCTORS["default"]


def guide_lines(guide):
    return GUIDES.get(guide, [])
