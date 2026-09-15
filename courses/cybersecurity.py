"""
Cybersecurity - The Wire.

The twist: the player IS the attack. You are spat out of a wire into
a jungle, find a white lab, steal door codes off doctors, get past a
firewall gate, release caged malware, sort the lab's inbox, beat the
head of security, crawl through a vent and stomp the lab's brain.
Two seconds after it dies the lights go out: THIS IS CYBERSECURITY.

The first levels teach nothing on purpose (no_lesson=True). From the
lab onward every level opens with notes written from the defender's
side of what the player is doing.

Map legend additions (see courses/common.py for the rest):

    !  wire mouth (spawn effect)       k  locked door - needs a DOOR CODE
    c  doctor carrying a DOOR CODE     [  cage with a bug inside
    b  bug (malware)                   Y  doctor boss (drops the VENT KEY)
    v  vent exit - needs the VENT KEY  R  the brain (stomp it)
"""

from courses.common import level, obelisk_level


def grid(*rows):
    """A map: 12 rows, all the same width (40 or wider)."""
    width = len(rows[0])
    assert len(rows) == 12, "map needs 12 rows, got %d" % len(rows)
    for index, row in enumerate(rows):
        assert len(row) == width, "row %d is %d wide, expected %d" % (index, len(row), width)
    return list(rows)


# ---------------------------------------------------------
# MAPS
# ---------------------------------------------------------

JUNGLE_1 = grid(
    "................................................",
    "........LLL.............LLL.............LLL.....",
    ".......LLLLL...........LLLLL...........LLLLL....",
    "........LTL.............LTL.............LTL.....",
    "#####....T...............T...............T......",
    "#####....T...............T...............T......",
    "#####....T...............T.......I.......T......",
    "#####!...T...............T......###......T......",
    "#####..P.T...............T...............T...X..",
    "############################~~~#################",
    "################################################",
    "################################################",
)

JUNGLE_2 = grid(
    "................................................................",
    "....LLL..............LLL...............LLL..............LLL.....",
    "...LLLLL............LLLLL.............LLLLL............LLLLL....",
    "....LTL..............LTL...............LTL..............LTL.....",
    ".....T................T.................T................T......",
    ".....T................T.................T................T......",
    ".....T................T........I........T................T......",
    ".....T....V...........T.......###.......T......V.........T......",
    "..P..T....V.b.........T..........b......T..K...V....b....T....X.",
    "################################################################",
    "################################################################",
    "################################################################",
)

LAB_WALL = grid(
    "................................................",
    "....LLL..................GGGGGGGGGGGGGGGGGGGGGGG",
    "...LLLLL.................G.....................G",
    "....LTL..................G.....................G",
    ".....T...................G.....................G",
    ".....T...................G.....................G",
    ".....T.........I.........G.....................G",
    ".....T........###........k..........I......D...G",
    "..P..T...........c.......k..N....B.GGG..C..D.X.G",
    "#########################GGGGGGGGGGGGGGGGGGGGGGG",
    "#########################GGGGGGGGGGGGGGGGGGGGGGG",
    "#########################GGGGGGGGGGGGGGGGGGGGGGG",
)

LOBBY = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G......................................G",
    "G..P...................................G",
    "G......................................G",
    "G.........A.............A..............G",
    "G........GGG...........GGG.............G",
    "G....N...........I.............I.......G",
    "G..........h....GGG.......n...GGG....D.G",
    "G......K..........B......h......C....DXG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)

BADGE_CHECK = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G......................................................G",
    "G..P...................................................G",
    "G......................................................G",
    "G............A..................A......................G",
    "G...........GGG................GGG.....................G",
    "G.....N................I...............................G",
    "G..........c......k...GGG....c.......k......I........D.G",
    "G.........B.......k....n.....K.......k....CGGG.......DXG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)

VAULT = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G..............................................G",
    "G..P...........................................G",
    "G..............................................G",
    "G.........A..............A.....................G",
    "G........GGG............GGG....................G",
    "G...............I...................I..........G",
    "G......h....c..GGG..k.......N......GGG.......D.G",
    "G...B...........K...k.........h.....C........DXG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)

GATE = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G......................................G",
    "G..P...................................G",
    "G......................................G",
    "G.............A........................G",
    "G............GGG.......................G",
    "G....N.................................G",
    "G..........B.......C..I.D..........h...G",
    "G....n...............GGGD.....K......X.G",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)

RULEBOOK = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G..............................................G",
    "G..P...........................................G",
    "G..............................................G",
    "G.........A....................A...............G",
    "G.........A....................A...............G",
    "G...................I..........................G",
    "G.....c.......k....GGG.h............N........D.G",
    "G..B..........k.....K.......h....C...........DXG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)

CAGES = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G......................................................G",
    "G..P...................................................G",
    "G......................................................G",
    "G........A..........A..........A..........A............G",
    "G.......GGG........GGG........GGG........GGG...........G",
    "G..............................................I.......G",
    "G.....N.......................................GGG....D.G",
    "G........[....[....[....[....[....[......B.....K.....DXG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)


def build_corridor(width=160):
    """The long dark corridor: bugs every ~16 columns, two chip ledges."""
    inner = width - 2
    air = ["G" + "." * inner + "G" for _ in range(8)]      # rows 1-8
    row = [list(r) for r in air]

    def put(r, c, ch):
        row[r - 1][c] = ch

    put(8, 3, "P")
    put(8, 8, "B")
    put(8, 5, "N")
    for c in (18, 34, 50, 66, 82, 98, 114, 130):
        put(8, c, "b")
    for c in (40, 100):
        put(8, c, "K")
    for c in (60, 120):
        for dx in (0, 1, 2):
            put(7, c + dx, "G")
        put(6, c + 1, "I")
    for c in (25, 75, 125):
        put(5, c, "U")
        put(5, c + 1, "U")
    put(8, 150, "C")
    put(7, 155, "D")
    put(8, 155, "D")
    put(8, 156, "X")

    top = "G" * width
    floor = "G" * width
    return grid(top, *("".join(r) for r in row), floor, floor, floor)


CORRIDOR = build_corridor()

INBOX_A = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G......................................G",
    "G..P...................................G",
    "G......................................G",
    "G..........A...........A...............G",
    "G.........GGG.........GGG..............G",
    "G................I.....................G",
    "G.....N.........GGG..........I.......D.G",
    "G........h........B.......n.GGGC.....DXG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)

INBOX_B = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G......................................G",
    "G..P...................................G",
    "G......................................G",
    "G......A.....................A.........G",
    "G.....GGG...................GGG........G",
    "G.................I....................G",
    "G........c....k..GGG..N..............D.G",
    "G..B..........k....K........h....C...DXG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)

INBOX_C = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G..............................................G",
    "G..P...........................................G",
    "G..............................................G",
    "G........A..........A..........A...............G",
    "G.......GGG........GGG........GGG..............G",
    "G..............................................G",
    "G.....N.......b........h.......b......I......D.G",
    "G..........B.......K..........n.....CGGG.....DXG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)

BOSS_ROOM = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G..............................................G",
    "G..........................................v...G",
    "G........................................GGGGG.G",
    "G....................................GGG.......G",
    "G..............................................G",
    "G................................GGG...........G",
    "G............................GGG...............G",
    "G..P..N....K............Y......................G",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)

BRAIN_ROOM = grid(
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "G......................................G",
    "G.P....................................G",
    "GGGGG..................................G",
    "G......................................G",
    "G......................................G",
    "G..................R...................G",
    "G......................................G",
    "G...............GGGGGGGG...............G",
    "G......................................G",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
)


# ---------------------------------------------------------
# SHARED TEXT
# ---------------------------------------------------------

GUIDE = "STATIC"   # the voice in your ear until the twist

DOCTOR_LINES = [
    "You're not on the visitor list. There is no visitor list. Please leave.",
    "I'd call security but I *am* security. Part-time. Tuesdays.",
    "Don't touch the cages. Some of those bugs are still in beta.",
    "We keep the password on a sticky note. It's very secure. Nobody reads sticky notes.",
    "The firewall gate has been 'temporarily open' since 2019.",
    "If you're the pen tester, you're early. If you're not, you're very early.",
    "Dr. Vex says the mainframe is unhackable. Dr. Vex also says the coffee is fine.",
    "Every door here opens with a code. Every doctor here loses their code. Weekly.",
]

BUGS = [
    {"name": "VIRUS", "fact": "A virus hides inside another file and spreads when that file is opened."},
    {"name": "WORM", "fact": "A worm copies itself across a network on its own - nobody has to click."},
    {"name": "TROJAN", "fact": "A trojan looks like something useful and does damage once you run it."},
    {"name": "RANSOMWARE", "fact": "Ransomware encrypts your files and demands money for the key."},
    {"name": "SPYWARE", "fact": "Spyware quietly records what you type and where you go."},
    {"name": "ADWARE", "fact": "Adware floods you with ads and often opens the door to worse."},
    {"name": "ROOTKIT", "fact": "A rootkit buries itself deep in the system so antivirus can't see it."},
    {"name": "BOTNET", "fact": "A bot makes your machine take orders - thousands together become a botnet."},
]


def email(sender, subject, body, scam, why):
    return {"kind": "email", "from": sender, "subject": subject, "body": body, "scam": scam, "why": why}


def sms(sender, body, scam, why):
    return {"kind": "sms", "from": sender, "subject": "", "body": body, "scam": scam, "why": why}


def call(sender, body, scam, why):
    return {"kind": "call", "from": sender, "subject": "", "body": body, "scam": scam, "why": why}


INBOX_DECK = [
    email("Cyber Academy IT <it-support@cyber-acadmey.help>",
          "Your mailbox is 99% full - act within 2 hours",
          "Click here to upgrade your storage or your account will be suspended tonight:\nhttp://mail-upgrade.cyber-acadmey.help/login",
          True, "Three signs at once: a misspelled lookalike domain (acadmey), a two-hour deadline, and a link that wants you to log in."),
    email("GitHub <noreply@github.com>",
          "[GitHub] A new SSH key was added to your account",
          "If this was you, no action is needed. If not, review your keys under Settings > SSH keys.",
          False, "Real domain, no pressure, and it tells you to go to your settings yourself instead of clicking a link."),
    email("Prize Department <winner@lottery-global-win.co>",
          "CONGRATULATIONS - you have been selected",
          "You have won 950,000 EUR in the International Email Lottery. Reply with your full name, address and bank details to claim.",
          True, "You cannot win a lottery you never entered, and no real prize needs your bank details by email."),
    email("City Library <notifications@library.city.gov>",
          "Reminder: 2 items due on Friday",
          "Two items are due back on Friday. Renew from your account or at the desk. No payment is needed.",
          False, "Expected sender, no urgency, no link demanding a login or a payment."),
    email("PayPaI Security <security@paypal-verify-center.com>",
          "Unusual sign-in detected",
          "We blocked a sign-in from another country. Confirm your identity now at verify-paypal-center.com. Enter your password and card number to restore access.",
          True, "The name uses a capital I to look like an l, the domain is not paypal.com, and it asks for your password AND card number."),
    email("Sam <sam@yourschool.edu>",
          "Slides for tomorrow",
          "Attached the slides we worked on this afternoon. Ping me if the file doesn't open.",
          False, "A known person, a message you were expecting, about work you actually did together. Still: only open attachments you expect."),
    email("CEO <ceo.office.urgent@gmail.com>",
          "Are you at your desk? Need a quick favour",
          "I'm in a meeting and can't talk. Buy five 100 EUR gift cards and send me the codes. Keep this between us for now.",
          True, "A 'CEO' writing from gmail, asking for gift cards and secrecy - the classic boss scam. Real bosses don't need gift-card codes."),
    email("Cyber Academy <no-reply@cyberacademy.example>",
          "New badge earned: Wire Badge III",
          "You earned a new badge. You can see it on your profile page whenever you like.",
          False, "Matches something you actually did, asks for nothing, and does not push you to click anything."),
]

PHONE_DECK = [
    sms("+1 (555) 013-2288",
        "USPS: your parcel is waiting. Pay the $1.99 redelivery fee within 24h: usps-redeliver-now.info",
        True, "A tiny fee is bait to collect your card details; the link is not usps.com, and it has a deadline."),
    sms("Your bank (usual short code)",
        "Your one-time code is 483920. It expires in 10 minutes. We will never call you to ask for it.",
        False, "You just tried to log in and this arrived. A real one-time code is normal - the scam is anyone who ASKS you for it."),
    call("Unknown number",
         "This is the tax office. You owe back taxes. A warrant will be issued today unless you pay now with gift cards.",
         True, "Tax offices write letters; they do not threaten arrest by phone or accept gift cards."),
    sms("Unknown number",
        "hey it's me, new number - old phone broke. can you send 300 EUR for the repair? pay you back friday",
        True, "'New number' plus an immediate money request. Call the old number to check - the real person will pick up."),
    sms("Dental practice",
        "Your appointment is tomorrow at 10:30. Reply C to confirm or call the practice to reschedule.",
        False, "You do have that appointment, it asks for nothing sensitive, and it points you to the practice's own phone."),
    call("Unknown number",
         "Hi, Microsoft support here. Your computer is sending us virus alerts. Let us connect remotely to fix it.",
         True, "Microsoft does not phone people about viruses. Remote access would hand your whole computer over."),
    sms("Netflix",
        "Your payment failed. Update your card within 12 hours to keep watching: netflix-billing-update.co",
        True, "Wrong domain, a deadline, and a request to enter card details from a text. Check inside the real app instead."),
    sms("Courier you ordered from",
        "Your order #48213 will arrive today between 14:00 and 16:00. No action needed.",
        False, "Your real order number, no link, nothing to pay, nothing to do."),
]

MIXED_DECK = [
    email("HR <hr@yourcompany.com>",
          "Updated holiday policy",
          "The holiday policy was updated. You can read it on the intranet at intranet.yourcompany.com.",
          False, "Real company domain and a link to the company's own intranet - nothing to enter, nothing urgent."),
    email("HR <hr@yourcompany-portal.com>",
          "Sign your new contract today",
          "Please sign the new contract at the link below. Log in with your work password to view it.",
          True, "yourcompany-portal.com is a lookalike, not the real domain, and it wants your work password."),
    sms("Your bank (usual short code)",
        "Two-factor code: 118204. If you did not request this, someone has your password - change it now.",
        False, "A real two-factor code with real advice. Nobody is asking you to send the code anywhere."),
    call("Unknown number",
         "Grandma? It's me. I'm in jail abroad and need bail money wired tonight. Please don't tell my parents.",
         True, "Panic, secrecy, and wiring money - the 'family emergency' scam. Hang up and call the family member directly."),
    email("Supplier accounts <accounts@supplier-you-use.com>",
          "Invoice 2291 - NEW bank details",
          "Please pay invoice 2291 to our new bank account (details below). The old account is closed.",
          True, "A changed bank account on a real-looking invoice is invoice fraud. Confirm by phone on a number you already have."),
    email("Discord <safety@discord-verify-account.com>",
          "You have been reported",
          "Your account was reported for abuse. Verify it within 24 hours or it will be deleted.",
          True, "Fear plus a deadline plus a non-discord.com domain. Real platforms show warnings inside the app."),
    email("University registrar <registrar@university.edu>",
          "Course registration opens Monday",
          "Registration opens Monday at 09:00. Log in through the student portal as usual to choose courses.",
          False, "Real domain, expected news, and it tells you to use the portal you already know - no link to follow."),
    sms("Recruiter (DM)",
        "We pay $300/day for simple online tasks. Just cover the $50 registration fee to get started.",
        True, "A real job never charges you to start. Easy money plus an upfront fee is a scam."),
    email("IT Helpdesk <helpdesk@yourcompany.com>",
          "Your password expires in 3 days",
          "To KEEP your current password, click 'Keep password' below and confirm it.",
          True, "Even from a real-looking address, no system needs you to type your password to keep it. This is a credential phish."),
    sms("Alex (known number)",
        "running 10 min late - order me a coffee?",
        False, "A known number, a normal request, nothing to click or pay."),
]


# ---------------------------------------------------------
# LEVELS
# ---------------------------------------------------------

CYBER_LEVELS = [

    # ===================== THE WIRE (no info) =====================

    level(
        1, "Spat Out",
        section="The Wire",
        no_lesson=True,
        objective="Get your bearings. Walk east.",
        concepts=[],
        story="Static. Pressure. A wire in the side of a hill coughs once and spits you out into wet jungle air. Sparks crawl along the cable behind you. Something in your ear says: keep moving.",
        goal="Follow the jungle east until the sim tells you otherwise.",
        gameplay="Walk right. Jump the ledge for the chip. There is nothing to read here yet.",
        guide=GUIDE,
        dialogue=[],
        challenge={"type": "walk", "prompt": "Reach the far side of the jungle."},
        reasoning="Pure orientation: movement, the jump, one pickup.",
        success="You reach the end of the clearing.",
        failure="-",
        explanation="You came out of a wire. Remember that.",
        reward="Wire Badge I",
        mentor="No lesson here. If asked, keep it atmospheric and say the teaching starts at the lab.",
        hints=["Keep walking east."],
        map=JUNGLE_1,
        theme="jungle",
        start_items=["SWORD"],
        intro=False,
    ),

    level(
        2, "Deeper In",
        section="The Wire",
        no_lesson=True,
        objective="Learn to fight. Reach the tree line.",
        concepts=[],
        story="The jungle thickens. Vines block the path and small black things skitter in the leaf litter - bugs, with too many legs and glowing eyes. The voice: 'You have a sword. Use it.'",
        goal="Cut the vines, deal with the bugs, keep going east.",
        gameplay="Select the sword (1), swing with F or a click. Cut vines, squash bugs, grab the candy if they bite.",
        guide=GUIDE,
        dialogue=[],
        challenge={"type": "walk", "prompt": "Reach the far edge of the jungle."},
        reasoning="Combat basics before anything is at stake.",
        success="The trees thin out and something white glints ahead.",
        failure="-",
        explanation="Whatever those bugs were, they came from the same direction you're going.",
        reward="Wire Badge II",
        mentor="No lesson here. If asked, explain the sword and candy controls only.",
        hints=["Bugs die to one swing. Vines too."],
        map=JUNGLE_2,
        theme="jungle",
        start_items=["SWORD"],
        bugs=BUGS[:3],
    ),

    # ===================== ONLINE THREATS =====================

    level(
        3, "The White Wall",
        section="Online Threats",
        objective="Understand what a threat is, and where attacks get in.",
        concepts=["asset", "threat", "attack surface"],
        lesson={
            "title": "You are the threat",
            "points": [
                "An ASSET is anything worth protecting: data, accounts, machines, people's time.",
                "A THREAT is anything that could harm an asset. Right now, that's you.",
                "The ATTACK SURFACE is every way in: doors, wires, logins, inboxes, people.",
                "Attackers rarely break the wall. They find the one door, and the one person who holds the code.",
                "Defenders count their doors. Most breaches start at a door nobody was watching.",
            ],
            "example": "Wall: solid.\nDoor: locked - needs a code.\nDoctor with the code: outside, alone.\nWeakest point: the doctor.",
        },
        story="A wall. Perfectly white, perfectly clean, in the middle of a jungle. One door, locked. One doctor in a coat pacing outside it, badge on a lanyard. The voice: 'Walls are for show. Doors are for people. Get the code.'",
        goal="Take the door code from the doctor, get inside, and answer the terminal by the inner door.",
        gameplay="Fight the doctor (c) - he drops a DOOR CODE. Press E at the locked door to use it. Inside, read the sign, talk to STATIC, use the terminal.",
        guide=GUIDE,
        sign="LAB ENTRANCE - AUTHORISED PERSONNEL ONLY. Lost your code? Ask Dr. Vex. Do not tape it to the door again.",
        dialogue=[
            "Inside. Nobody stopped you - because nobody watches the doors that 'nobody uses'.",
            "Everything in this lab is an asset. Everything you touch from now on is an attack.",
            "The terminal wants to know where the wall was weakest. You already know.",
        ],
        npcs=DOCTOR_LINES,
        challenge={
            "type": "mcq",
            "prompt": "You just got in. What was the lab's weakest point?",
            "options": [
                "The white wall - it could be climbed",
                "The doctor outside, carrying the code for the door",
                "The jungle - it hid your approach",
                "The terminal - it was switched on",
            ],
            "answer": 1,
            "wrong": "Think about what actually let you through the door.",
        },
        reasoning="Naming the human factor as the weakest part of an attack surface.",
        success="The inner door unlocks.",
        failure="The terminal blinks: not that.",
        explanation="The wall was fine. The door was locked. The person holding the code was the weak point - and people are where most attacks start.",
        reward="Wire Badge III",
        mentor="Frame everything from the defender's view: what would have stopped the player?",
        hints=["Walls don't hand out codes."],
        map=LAB_WALL,
        theme="jungle",
        start_items=["SWORD"],
    ),

    level(
        4, "The Lobby",
        section="Online Threats",
        objective="Name the five ways attackers usually get in.",
        concepts=["phishing", "weak passwords", "malware", "social engineering", "unpatched software"],
        lesson={
            "title": "The usual ways in",
            "points": [
                "PHISHING - a fake message that steals a login or delivers malware.",
                "WEAK OR REUSED PASSWORDS - guessed, leaked, or the same one everywhere.",
                "MALWARE - software that does harm once it runs (you'll meet it in cages later).",
                "SOCIAL ENGINEERING - tricking a person: fake authority, urgency, a favour.",
                "UNPATCHED SOFTWARE - a known hole nobody bothered to fix.",
                "Most real breaches use two of these together.",
            ],
            "example": "Phish -> steals a password -> password reused on the admin panel -> malware installed.",
        },
        story="A lobby full of doctors who don't look up. One does. Sticky notes on monitors. A vending machine. The voice: 'Look around. Everything here is a way in. Pick the one they'd never expect.'",
        goal="Cross the lobby and tell the terminal which way in needs no hacking at all.",
        gameplay="Talk to the idle doctors (E) - they leak more than they know. Fight the hostile ones. Terminal at the end.",
        guide=GUIDE,
        sign="STAFF NOTICE: password for the shared printer is on the sticky note by the kettle. Please stop asking.",
        dialogue=[
            "Sticky notes. A shared password. A doctor who will tell a stranger anything.",
            "You didn't need a single line of code to learn all that. That's the point.",
        ],
        npcs=DOCTOR_LINES,
        challenge={
            "type": "mcq",
            "prompt": "Which way in needs NO technical skill at all?",
            "options": [
                "Exploiting unpatched software",
                "Writing malware",
                "Social engineering - talking a person into helping you",
                "Cracking a password hash",
            ],
            "answer": 2,
            "wrong": "Which of these is a conversation, not a program?",
        },
        reasoning="Distinguishing human attacks from technical ones.",
        success="The lobby door releases.",
        failure="The terminal blinks: not that.",
        explanation="Social engineering attacks the person, not the machine. Sticky notes, chatty staff and shared passwords are what defenders must train away.",
        reward="Wire Badge IV",
        mentor="Ask which attacks need code and which need a conversation.",
        hints=["Read the staff notice again."],
        map=LOBBY,
        theme="lab",
        start_items=["SWORD"],
    ),

    # ===================== AUTHENTICATION =====================

    level(
        5, "Badge Check",
        section="Authentication",
        objective="Understand authentication and its three factors.",
        concepts=["authentication", "something you know / have / are", "MFA"],
        lesson={
            "title": "Authentication - proving who you are",
            "points": [
                "Authentication answers one question: are you who you claim to be?",
                "Three kinds of proof: something you KNOW (password), HAVE (badge, phone), ARE (fingerprint).",
                "One factor can be stolen. That door code you took? A 'have' factor - now yours.",
                "MFA (multi-factor) asks for two kinds. A stolen badge without the PIN is just plastic.",
                "Defender's rule: the more a door protects, the more factors it should ask for.",
            ],
            "example": "Door 1: code only        -> stolen code opens it.\nDoor 2: code + fingerprint -> stolen code is useless.",
        },
        story="Two locked doors in a row. Two doctors, each with a code on a lanyard, each convinced the other one is watching the corridor. The voice: 'Badges are just plastic. Take them.'",
        goal="Take both door codes, pass both doors, and tell the terminal which factor you stole.",
        gameplay="Each c doctor drops a DOOR CODE. E at each locked door uses one. Passing a door saves a checkpoint.",
        guide=GUIDE,
        sign="SECURITY REMINDER: badges must be worn at all times. (Badges must not be lent, lost, or 'borrowed by the new guy'.)",
        dialogue=[
            "Two doors, two codes, zero questions asked. Each door trusted one thing.",
            "If either door had asked for a second proof, you'd still be in the lobby.",
        ],
        npcs=DOCTOR_LINES,
        challenge={
            "type": "mcq",
            "prompt": "The door codes you took from the doctors are which kind of factor?",
            "options": [
                "Something you KNOW",
                "Something you HAVE",
                "Something you ARE",
                "Not a factor - codes are not authentication",
            ],
            "answer": 1,
            "wrong": "You carried it in your inventory. Which factor is carried?",
        },
        reasoning="Classifying a physical credential as a possession factor and seeing why one factor is weak.",
        success="The second door releases.",
        failure="The terminal blinks: not that.",
        explanation="A code card is something you HAVE. Anything you have can be taken - which is why important doors also ask for something you know or are.",
        reward="Wire Badge V",
        mentor="Relate know/have/are to the app's own login and to MFA on a phone.",
        hints=["You are literally holding the factor in slot 2 or 3."],
        map=BADGE_CHECK,
        theme="lab",
        start_items=["SWORD"],
    ),

    level(
        6, "The Vault",
        section="Authentication",
        objective="Judge password strength and know what makes a login hard to steal.",
        concepts=["password length", "reuse", "password managers", "MFA"],
        lesson={
            "title": "Passwords - what actually makes them strong",
            "points": [
                "Length beats cleverness: every extra character multiplies the guesses needed.",
                "Variety helps (upper, lower, digits, symbols) but a long passphrase beats a short 'clever' one.",
                "Never reuse: one leak on a forum shouldn't open a bank. Password managers make unique ones painless.",
                "MFA turns a stolen password into a useless one.",
                "The password you're about to find is on a sticky note. That is the defender's real problem.",
            ],
            "example": "grove2024      -> weak: short, guessable, a word + year\nTr3e-Lantern!Vault9 -> strong: long and varied",
        },
        story="A vault door with a keypad, and beside it a monitor with a sticky note: 'vault pw: grove2024 (DON'T SHARE)'. The voice laughs. 'They wrote it down. They always write it down.'",
        goal="Take the code from the doctor, open the vault, and tell the terminal which password would have stopped you.",
        gameplay="Fight the doctors, use the DOOR CODE, read the sign, answer the terminal.",
        guide=GUIDE,
        sign="vault pw: grove2024   (DON'T SHARE)   - Dr. Vex",
        dialogue=[
            "A vault with a sticky note. A short password with a year in it.",
            "Ask the terminal: of the four options, which one would you never have guessed?",
        ],
        npcs=DOCTOR_LINES,
        challenge={
            "type": "mcq",
            "prompt": "Which password would have kept you OUT of the vault?",
            "options": ["grove2024", "Vault123!", "password", "Tr3e-Lantern!Vault9"],
            "answer": 3,
            "wrong": "Think length first, then variety. Words plus a year are guessed instantly.",
        },
        reasoning="Applying length and variety, and recognising the sticky-note problem.",
        success="The vault hisses open.",
        failure="The terminal blinks: not that.",
        explanation="Tr3e-Lantern!Vault9 is long and mixed; the others are short, common, or a word plus a year. And no password survives being written on the monitor.",
        reward="Wire Badge VI",
        mentor="Connect to the entropy meter on the signup page; never ask for real passwords.",
        hints=["Count the characters."],
        map=VAULT,
        theme="lab",
        start_items=["SWORD"],
    ),

    level(
        0, "Checkpoint: Threats & Authentication",
        kind="quiz",
        section="Authentication",
        objective="Prove you remember threats and authentication before going deeper.",
        concepts=["attack surface", "social engineering", "factors", "MFA"],
        lesson={
            "title": "Checkpoint - Threats & Authentication",
            "points": [
                "Assets are what's worth protecting; threats are what could harm them; the attack surface is every way in.",
                "The five usual ways in: phishing, weak/reused passwords, malware, social engineering, unpatched software.",
                "Authentication proves who you are with something you know, have, or are. MFA asks for two.",
                "Long, unique passwords in a manager; never on a sticky note.",
            ],
            "example": "Stolen badge (have) + no PIN (know) = open door.\nStolen badge + PIN required = plastic.",
        },
        story="The voice goes quiet for a moment. 'Before the gate: prove you were paying attention. Six questions.'",
        goal="Get every question right to reach the firewall gate.",
        gameplay="Answer six questions. Two reach back to the lab entrance.",
        guide=GUIDE,
        dialogue=["Six questions. Then the gate."],
        challenge={
            "type": "quiz",
            "prompt": "Answer every question. Wrong answers only tell you which question to look at again.",
            "questions": [
                {"prompt": "What is an attack surface?", "options": ["The strongest wall of a building", "Every possible way into a system - doors, logins, inboxes, people", "A type of malware", "The password database"], "answer": 1},
                {"prompt": "A stranger phones and, using authority and urgency, talks a receptionist into reading out a door code. This is:", "options": ["Malware", "Social engineering", "A firewall failure", "Unpatched software"], "answer": 1},
                {"prompt": "A fingerprint is which authentication factor?", "options": ["Something you know", "Something you have", "Something you are", "Not a factor"], "answer": 2},
                {"prompt": "Why does MFA stop a stolen password from working?", "options": ["It makes passwords longer", "The attacker still needs a second, different kind of proof", "It deletes the password after use", "It hides the login page"], "answer": 1},
                {"prompt": "Which is the STRONGEST password?", "options": ["lab2024", "Doctor!", "Blue-Kettle-Sings-At-9am", "12345678"], "answer": 2},
                {"prompt": "Earlier: why was the doctor outside the wall the weakest point?", "options": ["He was slow", "He carried the credential the door trusted, and nobody was watching him", "He had no sword", "The wall was cracked"], "answer": 1},
            ],
        },
        reasoning="Retrieval practice on threats and authentication.",
        success="All six correct - the gate is ahead.",
        failure="The drill says which question is wrong, nothing more.",
        explanation="Attack surface, social engineering, three factors, MFA, long passwords: the defender's first toolkit.",
        reward="Checkpoint Pin I",
        mentor="Coach with questions; never state the answer.",
        hints=["Re-read the lesson notes of the four lab levels."],
        theme="lab",
    ),

    # ===================== FIREWALLS =====================

    level(
        8, "The Gate",
        section="Firewalls",
        objective="Understand what a firewall does and why 'default deny' matters.",
        concepts=["firewall", "rules", "ports", "default deny"],
        lesson={
            "title": "Firewalls - the gate with a rulebook",
            "points": [
                "A firewall checks every connection against a list of rules: who, where to, which port.",
                "A PORT is a numbered door on a machine: 443 = secure web, 80 = plain web, 22 = remote admin.",
                "ALLOW rules let matching traffic through. DENY rules block it.",
                "DEFAULT DENY: anything no rule allows is blocked. That is the safe setting.",
                "A gate left 'temporarily open' is not a gate. Attackers love temporary.",
            ],
            "example": "ALLOW  anyone -> web server : 443\nDENY   everything else          <- default deny",
        },
        story="A glowing orange gate across the corridor, humming. A rulebook terminal beside it. A doctor, idle: 'It's been temporarily open since 2019.' The voice: 'Then it isn't a gate.'",
        goal="Decide what the gate should do with traffic that matches no rule, and it will let you pass.",
        gameplay="Read the sign, talk to STATIC, use the rulebook terminal, pass the gate.",
        guide=GUIDE,
        gate=True,
        sign="GATE RULES: ALLOW web (443). ALLOW admin from inside (22). Everything else: ??? (TODO - Dr. Vex)",
        dialogue=[
            "The rulebook has a hole in it. 'Everything else: TODO'.",
            "A defender fills that line with one word. You know which.",
        ],
        npcs=DOCTOR_LINES,
        challenge={
            "type": "text_answer",
            "prompt": "Unknown traffic arrives at the gate. No rule mentions it. What should the gate do: allow or deny?",
            "placeholder": "allow / deny",
            "accepted": ["deny", "denied", "block", "blocked", "drop", "deny it", "block it"],
            "wrong": "If nothing explicitly allows it, the safe default is the other one.",
        },
        reasoning="Applying default-deny.",
        success="The gate drops its glow and lets you through - for now.",
        failure="The terminal blinks: not that.",
        explanation="Default deny: allow only what is needed, block everything else. A gate that lets unknown traffic through is open.",
        reward="Wire Badge VII",
        mentor="Explain allow-lists vs deny-lists and why 'temporarily open' is dangerous.",
        hints=["What is the safe default when no rule matches?"],
        map=GATE,
        theme="lab",
        start_items=["SWORD"],
    ),

    level(
        9, "The Rule Book",
        section="Firewalls",
        objective="Write a minimal firewall rule set.",
        concepts=["allow rule", "deny all", "least access"],
        lesson={
            "title": "Writing the rules",
            "points": [
                "Rules are read top to bottom; the first match wins.",
                "Allow only the doors the lab actually needs (the public web server: port 443).",
                "Then one final rule: DENY everything else.",
                "Fewer allow rules = smaller attack surface. Every extra open port is a door to watch.",
            ],
            "example": "1. ALLOW  port 443   (public web)\n2. DENY   all        (everything else)",
        },
        story="Inside the gate, the real rulebook: two blank lines. The voice: 'Write it properly and the next door thinks you're the admin.'",
        goal="Complete the two rules: allow only the public web port, then deny everything else.",
        gameplay="Take the doctor's code for the side door, reach the terminal, fill both blanks.",
        guide=GUIDE,
        sign="Public web server: port 443. Admin port 22 must NOT be reachable from outside.",
        dialogue=[
            "Two lines. One opens the smallest door the lab needs. The other closes every other door.",
        ],
        npcs=DOCTOR_LINES,
        challenge={
            "type": "fill_blank",
            "prompt": "Fill the blanks: rule 1 allows only the public web port from the sign; rule 2 denies everything else.",
            "code": ["1. ALLOW  port ___", "2. DENY   ___"],
            "answers": [["443"], ["all", "everything", "everything else", "*"]],
            "bank": ["443", "22", "80", "all", "none"],
        },
        reasoning="Least access: one allow, one deny-all.",
        success="The rulebook accepts and the admin door opens.",
        failure="The terminal names the blank that is wrong.",
        explanation="ALLOW port 443 then DENY all: the public web works, the admin port is unreachable from outside, and nothing else gets in.",
        reward="Wire Badge VIII",
        mentor="Ask which port the sign says is public, and what the last rule should catch.",
        hints=["The sign gives you the only number you need."],
        map=RULEBOOK,
        theme="lab",
        start_items=["SWORD"],
    ),

    # ===================== MALWARE =====================

    level(
        10, "Specimen Cages",
        section="Malware",
        objective="Recognise the main types of malware by what they do.",
        concepts=["virus", "worm", "trojan", "ransomware", "spyware", "adware"],
        lesson={
            "title": "Malware - a field guide",
            "points": [
                "MALWARE = malicious software. Different types, different behaviour:",
                "VIRUS hides in a file and spreads when it's opened. WORM spreads across a network by itself.",
                "TROJAN pretends to be useful. RANSOMWARE encrypts your files and demands payment.",
                "SPYWARE watches and records you. ADWARE floods you with ads and opens the door to worse.",
                "Defence is the same for all: updates, backups, don't run what you didn't expect.",
                "The cages in this room are labelled. When they open, read the labels.",
            ],
            "example": "Files renamed .locked + a payment note  -> ransomware\nSame file appears on every PC overnight  -> worm",
        },
        story="A specimen room. Six cages along the wall, each holding one black bug with a label. The exit is a heavy door with a motion sensor. The voice: 'Open the door. What could go wrong.'",
        goal="Try the door, survive what gets out, and the lock will release when the room is clear.",
        gameplay="Press E at the far door. The cages burst. Kill every bug (one swing each). The door opens when none are left.",
        guide=GUIDE,
        door_by_bugs=True,
        sign="SPECIMEN ROOM - DO NOT open the corridor door while cages are occupied. Sensor linked. (Whose idea was this?)",
        dialogue=[
            "Six cages. Six kinds of malware. Read the label as each one dies - that's the lesson.",
        ],
        npcs=DOCTOR_LINES,
        bugs=BUGS[:6],
        challenge={"type": "walk", "prompt": "Clear the specimen room and go through the door."},
        reasoning="Learning the types through labelled encounters instead of a list.",
        success="The room is clear. The lock releases.",
        failure="-",
        explanation="Six types, six behaviours. Knowing what each one does tells a defender where to look.",
        reward="Wire Badge IX",
        mentor="Ask what each bug's label means; relate to real examples (WannaCry = worm + ransomware).",
        hints=["One swing per bug. Keep moving."],
        map=CAGES,
        theme="lab",
        start_items=["SWORD"],
    ),

    level(
        11, "The Long Dark",
        section="Malware",
        objective="Identify malware from its behaviour and know the defences.",
        concepts=["rootkit", "botnet", "backups", "updates"],
        lesson={
            "title": "In the dark",
            "points": [
                "Two more: a ROOTKIT hides deep so antivirus can't see it; a BOTNET makes machines take orders together.",
                "Malware wants the dark: unseen, unpatched, unbacked-up.",
                "Defences: keep software UPDATED, keep BACKUPS offline, use antivirus, never run unexpected files.",
                "Ransomware loses its power the moment you have a backup you can restore.",
            ],
            "example": "Lights on  = updates, backups, monitoring.\nLights off = nobody looking.",
        },
        story="A corridor that goes on far too long. The lights die one by one as you walk. Things click and scuttle beyond the edge of your lamp. The voice: 'Clear it. All of it. Then the lights come back.'",
        goal="Kill every bug in the corridor; the lights return. Then answer the terminal at the end.",
        gameplay="Walk east. Your light is small. Bugs rush you when close - swing early. Candy on the way. When the last one dies the lights come on.",
        guide=GUIDE,
        dark=True,
        sign="CORRIDOR C - LIGHTS ON MOTION TIMER. Report failures to maintenance. (Maintenance is Dr. Vex.)",
        dialogue=[
            "Eight bugs. The lights are tied to the sensors. Clear the corridor and they come back.",
        ],
        npcs=DOCTOR_LINES,
        bugs=BUGS,
        challenge={
            "type": "mcq",
            "prompt": "Every file on a lab PC is renamed .locked and a note demands payment. What is it, and what saves the day?",
            "options": [
                "Spyware - reinstall the browser",
                "Ransomware - restore from an offline backup",
                "Adware - close the pop-ups",
                "A worm - unplug the keyboard",
            ],
            "answer": 1,
            "wrong": "Encrypted files plus a payment note is one specific type. What makes paying unnecessary?",
        },
        reasoning="Behaviour -> type -> the defence that removes the attacker's leverage.",
        success="The terminal logs the incident. The corridor door opens.",
        failure="The terminal blinks: not that.",
        explanation="Encrypt + demand = ransomware. An offline backup means you restore instead of pay.",
        reward="Wire Badge X",
        mentor="Explain why backups must be offline and why updates close known holes.",
        hints=["Which option mentions getting the files back without paying?"],
        map=CORRIDOR,
        theme="lab",
        start_items=["SWORD"],
    ),

    level(
        0, "Checkpoint: Firewalls & Malware",
        kind="quiz",
        section="Malware",
        objective="Prove you remember firewalls and malware before the inbox.",
        concepts=["default deny", "ports", "malware types", "backups"],
        lesson={
            "title": "Checkpoint - Firewalls & Malware",
            "points": [
                "Firewalls apply rules; ports are numbered doors; default deny blocks what no rule allows.",
                "Virus, worm, trojan, ransomware, spyware, adware, rootkit, botnet - know them by behaviour.",
                "Updates close known holes; offline backups defeat ransomware.",
            ],
            "example": "ALLOW 443 / DENY all\nFiles .locked -> ransomware -> restore backup",
        },
        story="The lights hum. 'Six more questions,' says the voice. 'Then the inbox.'",
        goal="Get every question right to reach the inbox.",
        gameplay="Answer six questions. Two reach back to authentication.",
        guide=GUIDE,
        dialogue=["Six questions. Then the inbox."],
        challenge={
            "type": "quiz",
            "prompt": "Answer every question. Wrong answers only tell you which question to look at again.",
            "questions": [
                {"prompt": "A firewall receives a connection that matches none of its rules. With default deny, it will:", "options": ["Allow it", "Block it", "Ask the user", "Log it and allow it"], "answer": 1},
                {"prompt": "Port 443 is normally used for:", "options": ["Remote admin (SSH)", "Email", "Secure web (HTTPS)", "Printing"], "answer": 2},
                {"prompt": "Malware that copies itself across a network with no clicks needed is a:", "options": ["Trojan", "Worm", "Adware", "Rootkit"], "answer": 1},
                {"prompt": "A free 'PDF converter' that secretly installs a keylogger is a:", "options": ["Trojan", "Worm", "Virus", "Botnet"], "answer": 0},
                {"prompt": "The single best defence against ransomware is:", "options": ["A longer password", "An offline backup you can restore", "Closing pop-ups", "A faster computer"], "answer": 1},
                {"prompt": "Earlier: a stolen door code is 'something you have'. What would have made it useless to the thief?", "options": ["A longer code", "Requiring a second factor, like a PIN", "A bigger door", "Writing it on a sticky note"], "answer": 1},
            ],
        },
        reasoning="Retrieval practice on firewalls and malware plus cumulative authentication.",
        success="All six correct - the inbox is ahead.",
        failure="The drill says which question is wrong, nothing more.",
        explanation="Default deny, ports, malware by behaviour, backups, MFA.",
        reward="Checkpoint Pin II",
        mentor="Coach with questions; never state the answer.",
        hints=["Re-read the lesson notes of the gate and the cages."],
        theme="lab",
    ),

    # ===================== SCAMS =====================

    level(
        13, "The Inbox",
        section="Scams",
        objective="Spot phishing emails from their tells.",
        concepts=["phishing", "lookalike domains", "urgency", "credential requests"],
        lesson={
            "title": "Phishing - reading an email like a defender",
            "points": [
                "Check the real SENDER address, letter by letter. Lookalikes: acadmey, paypaI (capital I), company-portal.",
                "URGENCY is the pressure: 'within 2 hours', 'tonight', 'or lose your account'.",
                "A link that wants you to LOG IN, or a request for a password, card number or bank details = stop.",
                "Legit messages ask for little, don't rush you, and point you to a place you already know.",
                "When unsure: don't click. Open the site yourself, or phone a number you already have.",
            ],
            "example": "SCAM:  security@paypal-verify-center.com  'confirm within 2h'  -> enter password + card\nLEGIT: noreply@github.com  'if this wasn't you, check Settings'",
        },
        story="The lab's mail server. Eight messages waiting. The voice: 'Half of these are yours. Sort them and the server will trust you as staff.' The terminal shows one message at a time.",
        goal="Swipe each message: SCAM or LEGIT. Get them all right to gain staff access.",
        gameplay="Reach the mail terminal. Read each card; press LEGIT or SCAM (or the arrow keys). Wrong picks are explained; redo them until the deck is clean.",
        guide=GUIDE,
        sign="MAIL ROOM - 'Report suspicious mail to IT.' IT is on holiday.",
        dialogue=[
            "You wrote some of these. Now read them the way the victims should have.",
        ],
        npcs=DOCTOR_LINES,
        challenge={
            "type": "swipe",
            "label": "MAIL TERMINAL",
            "prompt": "Is this message a SCAM or LEGIT? Sort all eight.",
            "cards": INBOX_DECK,
        },
        reasoning="Pattern-matching sender, urgency and credential requests across real-looking emails.",
        success="The server marks you as staff. The door opens.",
        failure="Each wrong swipe explains the tell you missed.",
        explanation="Sender address, urgency, and what the message asks for - three checks catch almost every phish.",
        reward="Wire Badge XI",
        mentor="Coach on the three checks; do not say which card is which.",
        hints=["Read the sender's domain letter by letter."],
        map=INBOX_A,
        theme="lab",
        start_items=["SWORD"],
    ),

    level(
        14, "The Phone",
        section="Scams",
        objective="Spot scam texts and calls.",
        concepts=["smishing", "vishing", "one-time codes", "family emergency scam"],
        lesson={
            "title": "Texts and calls - the same tricks, smaller screen",
            "points": [
                "SMISHING = scam texts. VISHING = scam calls. Same pressure, less room to check.",
                "Tiny fees ('pay $1.99') exist to collect your card. Real deliveries don't charge by text.",
                "A one-time code arriving is normal. Anyone ASKING you for it is the scam.",
                "'New number, need money' and 'family emergency, keep it secret' - hang up, call the person on the number you already have.",
                "Real support does not phone you first, and never needs remote access to 'fix' a virus.",
            ],
            "example": "SCAM:  'USPS fee $1.99, 24h, usps-redeliver-now.info'\nLEGIT: 'Your code is 483920. We will never call to ask for it.'",
        },
        story="A drawer of confiscated phones, all buzzing. The voice: 'Different channel, same game. Sort them.'",
        goal="Swipe each text or call: SCAM or LEGIT.",
        gameplay="Take the doctor's code for the side door, reach the terminal, sort the deck.",
        guide=GUIDE,
        sign="LOST PROPERTY - phones. Do NOT answer them. (One of them is Dr. Vex's. Definitely don't answer that one.)",
        dialogue=[
            "Calls and texts. The tells are the same: pressure, money, and someone asking for a code.",
        ],
        npcs=DOCTOR_LINES,
        challenge={
            "type": "swipe",
            "label": "PHONE DRAWER",
            "prompt": "Is this text or call a SCAM or LEGIT? Sort all eight.",
            "cards": PHONE_DECK,
        },
        reasoning="Transferring the phishing checks to SMS and voice.",
        success="The drawer locks. The door opens.",
        failure="Each wrong swipe explains the tell you missed.",
        explanation="Fees, codes, secrecy and 'support' calls are the four phone tells.",
        reward="Wire Badge XII",
        mentor="Coach on verifying through a channel you already trust.",
        hints=["Who is asking for what - and how fast?"],
        map=INBOX_B,
        theme="lab",
        start_items=["SWORD"],
    ),

    level(
        15, "Mixed Signals",
        section="Scams",
        objective="Sort a harder mixed deck where the sender can look real.",
        concepts=["invoice fraud", "credential phishing", "advance-fee scams"],
        lesson={
            "title": "The hard ones",
            "points": [
                "A REAL-looking sender can still be a scam: an invoice with 'new bank details' is invoice fraud - confirm by phone.",
                "'Click to KEEP your password' is credential phishing even from an internal-looking address.",
                "Any job or prize that needs a fee from you first is an advance-fee scam.",
                "Legit messages: real domain, expected, and they send you to a place you already use.",
            ],
            "example": "Invoice 2291 - NEW bank details -> phone the supplier on the old number.",
        },
        story="Dr. Vex's own inbox, mixed with the lab's chat and phone logs. Ten messages. The voice: 'Get these right and the mainframe door thinks you're Vex.'",
        goal="Sort all ten messages: SCAM or LEGIT.",
        gameplay="Fight through the bugs and doctors, then sort the deck at the terminal.",
        guide=GUIDE,
        sign="Dr. Vex's desk. Coffee: cold. Inbox: 10 unread. Password: still on the monitor.",
        dialogue=[
            "Ten messages. Some senders are real. Ask what each one wants you to DO.",
        ],
        npcs=DOCTOR_LINES,
        bugs=BUGS[6:] + BUGS[:1],
        challenge={
            "type": "swipe",
            "label": "VEX'S INBOX",
            "prompt": "SCAM or LEGIT? Ten messages, some from real addresses.",
            "cards": MIXED_DECK,
        },
        reasoning="Judging by the requested action, not only the sender.",
        success="The mainframe door accepts Dr. Vex's credentials. Yours, now.",
        failure="Each wrong swipe explains the tell you missed.",
        explanation="Ask what the message wants you to do - pay a new account, type a password, send a fee - and where it sends you.",
        reward="Wire Badge XIII",
        mentor="Focus on the requested action; never state a card's verdict.",
        hints=["What does the message want you to do?"],
        map=INBOX_C,
        theme="lab",
        start_items=["SWORD"],
    ),

    # ===================== THE MAINFRAME =====================

    level(
        16, "Dr. Vex",
        section="The Mainframe",
        objective="See incident response from the defender's side - and survive it.",
        concepts=["incident response", "identify", "contain", "eradicate"],
        lesson={
            "title": "The lab fights back",
            "points": [
                "When a breach is spotted, defenders run INCIDENT RESPONSE: identify, contain, eradicate, recover, learn.",
                "CONTAIN first: cut the attacker off before cleaning up. That's what Dr. Vex is doing to you now.",
                "Dr. Vex throws syringes in bursts, then staggers. He is only vulnerable while staggered.",
                "The vent above is the only way to the brain. Vex has the key.",
            ],
            "example": "1 identify  2 contain  3 eradicate  4 recover  5 learn",
        },
        story="The mainframe hall. Screens everywhere. Dr. Vex, head of security, stands between you and a vent grille high on the wall. 'You've been in my lab for twenty minutes,' he says. 'That's nineteen too long.' The voice, quieter than before: 'He's containing you. Don't let him.'",
        goal="Defeat Dr. Vex, take the VENT KEY he drops, climb the ledges and enter the vent.",
        gameplay="Dodge the syringe bursts (jump). Hit Vex while STAGGERED. Pick up the key. Jump the ledges to the vent and press E.",
        guide=GUIDE,
        dialogue=[
            "He's the defence. Identify, contain, eradicate - you're the thing he's eradicating.",
            "He throws, then he staggers. That's your window. Then the vent.",
        ],
        npcs=[],
        challenge={"type": "walk", "prompt": "Beat Dr. Vex and enter the vent."},
        reasoning="Experiencing containment from the attacker's side.",
        success="The grille swings open. Warm air, and a low hum from above.",
        failure="-",
        explanation="Vex did what defenders do: identify, contain, try to eradicate. You got past him - this time.",
        reward="Wire Badge XIV + Vent Key",
        mentor="Explain the response phases; give fight tips only in general terms.",
        hints=["Only swing while he is STAGGERED."],
        map=BOSS_ROOM,
        theme="lab",
        start_items=["SWORD"],
        boss=True,
    ),

    level(
        17, "The Brain",
        section="The Mainframe",
        objective="See the whole attack at once - and what cybersecurity is.",
        concepts=["confidentiality", "integrity", "availability", "defence in depth"],
        lesson={
            "title": "What you did",
            "points": [
                "You took a credential (authentication), walked through a gate (firewall), released malware, sorted scams to steal access, and beat the response.",
                "Every asset has three things to protect: CONFIDENTIALITY (secret), INTEGRITY (correct), AVAILABILITY (working).",
                "Destroying the brain kills availability. The lab stops. That is the damage.",
                "Cybersecurity is every layer you passed - and the people who should have been watching each one.",
                "Stomp the brain from above. Its side is dangerous. Five jumps.",
            ],
            "example": "Confidentiality: stolen codes\nIntegrity: rewritten firewall rules\nAvailability: the brain",
        },
        story="The vent drops you onto a platform above a vast pink mass wired into every wall - the lab's brain. It pulses. The voice says nothing at all.",
        goal="Kill the brain by jumping on it. Five stomps.",
        gameplay="Drop from the ledge onto the brain. Bounce and land again. Avoid the thoughts it throws. Its sides bite.",
        guide=GUIDE,
        dialogue=[],
        npcs=[],
        finale=True,
        challenge={"type": "walk", "prompt": "Stomp the brain."},
        reasoning="The reveal: the player has performed a full attack; the ending names it.",
        success="The lights go out.",
        failure="-",
        explanation="Everything you just did is what cybersecurity exists to stop. The next courses teach the other side.",
        reward="Wire Master Badge",
        mentor="After the reveal, explain the CIA triad and defence in depth; connect each level to a defence.",
        hints=["Land on top of it. Jump the moment you touch."],
        map=BRAIN_ROOM,
        theme="lab",
        start_items=["SWORD"],
        boss=True,
    ),

    obelisk_level(
        18, "Cybersecurity", "The Wire", "Wire Master Badge II", "BYTE",
        "When the lights come back you are somewhere else: a white plain, a pale sky, an obelisk. The voice in your ear is different now - warmer. 'This is BYTE. That was a simulation. You played the attacker so you'd recognise one. Press the button.'",
        [
            "Assets, threats, attack surface; phishing, weak passwords, malware, social engineering, unpatched software.",
            "Authentication factors and MFA; firewalls with default deny; malware by behaviour; scams by sender, urgency and what they ask for.",
            "Incident response: identify, contain, eradicate, recover, learn. Confidentiality, integrity, availability.",
        ],
    ),
]

# Renumber so the quizzes slot in cleanly.
for _index, _level in enumerate(CYBER_LEVELS, start=1):
    _level["number"] = _index
