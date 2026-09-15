"""
Internet Fundamentals - The Backbone.

You are a packet. The whole course happens inside white internet
cables: sewer-like tunnels of cable sheath, a live data stream at the
bottom you must not fall into, and cable strands to parkour across.
Near the end you leave the machine through an HDMI port, land on a
desk, walk across the keyboard while the monitor mirrors you, and
finally write down an idea for a website of your own.

Map legend additions:

    %  live data stream - touching it costs a heart and puts you
       back on the last ledge you stood on
    z  sniffer (man-in-the-middle) - patrols a cable
"""

from courses.common import level, room, open_ground, put, finish, obelisk_level

GUIDE = "PING"


# ---------------------------------------------------------
# MAPS
# ---------------------------------------------------------

def tunnel(width):
    """A cable tunnel: sheath walls, a floor with data-stream pits."""
    rows = room(width)
    return rows


def pit(rows, col, width=2):
    for x in range(col, col + width):
        rows[9][x] = "%"
        rows[10][x] = "%"


def ledge(rows, row, col, width=3):
    put(rows, row, col, "G" * width)


def cable_a():
    rows = tunnel(56)
    put(rows, 8, 2, "P")
    put(rows, 7, 5, "N")
    pit(rows, 9); ledge(rows, 7, 11)
    ledge(rows, 5, 15); put(rows, 4, 16, "I")
    pit(rows, 21); ledge(rows, 7, 22); ledge(rows, 6, 25); put(rows, 5, 26, "I")
    pit(rows, 33); ledge(rows, 7, 34)
    put(rows, 8, 41, "B")
    put(rows, 8, 46, "C")
    put(rows, 7, 53, "D"); put(rows, 8, 53, "D"); put(rows, 8, 54, "X")
    return finish(rows)


def cable_b():
    rows = tunnel(64)
    put(rows, 8, 2, "P")
    put(rows, 7, 6, "N")
    pit(rows, 10, 2); ledge(rows, 7, 12)
    ledge(rows, 5, 16); ledge(rows, 3, 20); put(rows, 2, 21, "I")
    pit(rows, 18, 2); pit(rows, 24, 2)
    ledge(rows, 7, 26); put(rows, 8, 31, "K")
    pit(rows, 36, 2); ledge(rows, 7, 38); ledge(rows, 5, 42); put(rows, 4, 43, "I")
    put(rows, 8, 47, "B")
    put(rows, 8, 52, "C")
    put(rows, 7, 61, "D"); put(rows, 8, 61, "D"); put(rows, 8, 62, "X")
    return finish(rows)


def cable_c():
    rows = tunnel(56)
    put(rows, 8, 2, "P")
    put(rows, 7, 5, "N")
    ledge(rows, 7, 9); ledge(rows, 5, 13); ledge(rows, 3, 17); put(rows, 2, 18, "I")
    pit(rows, 12, 2); pit(rows, 16, 2); pit(rows, 20, 2)
    ledge(rows, 5, 22); ledge(rows, 7, 26)
    put(rows, 8, 31, "K")
    put(rows, 8, 36, "B")
    put(rows, 6, 38, "U"); put(rows, 6, 39, "U")
    put(rows, 8, 42, "C")
    put(rows, 7, 53, "D"); put(rows, 8, 53, "D"); put(rows, 8, 54, "X")
    return finish(rows)


def cable_sniffer():
    rows = tunnel(64)
    put(rows, 8, 2, "P")
    put(rows, 7, 5, "N")
    ledge(rows, 7, 10); ledge(rows, 5, 14, 6); put(rows, 4, 16, "z")
    pit(rows, 12, 2)
    ledge(rows, 7, 22); put(rows, 8, 26, "z")
    pit(rows, 30, 2); ledge(rows, 7, 32); ledge(rows, 5, 36); put(rows, 4, 37, "I")
    put(rows, 8, 41, "z")
    put(rows, 8, 46, "B")
    put(rows, 8, 51, "K")
    put(rows, 8, 55, "C")
    put(rows, 7, 61, "D"); put(rows, 8, 61, "D"); put(rows, 8, 62, "X")
    return finish(rows)


def cable_flood():
    rows = tunnel(72)
    put(rows, 8, 2, "P")
    put(rows, 7, 5, "N")
    for col in (14, 22, 30, 38, 46, 54):
        put(rows, 8, col, "b")
    ledge(rows, 7, 18); ledge(rows, 7, 34); ledge(rows, 5, 38); put(rows, 4, 39, "I")
    ledge(rows, 7, 50)
    put(rows, 8, 26, "K"); put(rows, 8, 44, "K")
    put(rows, 8, 58, "B")
    put(rows, 8, 63, "C")
    put(rows, 7, 69, "D"); put(rows, 8, 69, "D"); put(rows, 8, 70, "X")
    return finish(rows)


def cable_port():
    """The last stretch of cable: the exit is an HDMI port."""
    rows = tunnel(64)
    put(rows, 8, 2, "P")
    put(rows, 7, 5, "N")
    ledge(rows, 7, 9); ledge(rows, 5, 13); ledge(rows, 7, 17)
    pit(rows, 11, 2); pit(rows, 15, 2); pit(rows, 19, 2)
    ledge(rows, 7, 22); ledge(rows, 6, 25); put(rows, 5, 26, "I")
    pit(rows, 28, 2); ledge(rows, 7, 30); pit(rows, 34, 2); ledge(rows, 7, 36)
    put(rows, 8, 42, "K")
    put(rows, 8, 48, "B")
    put(rows, 8, 54, "C")
    put(rows, 7, 61, "D"); put(rows, 8, 61, "D"); put(rows, 8, 62, "X")
    return finish(rows)


def desk(width, keys_from, keys_to):
    """A desk: wood surface, a raised keyboard block of keycaps ('S')."""
    rows = open_ground(width, ground="#")
    for x in range(keys_from, keys_to):
        rows[8][x] = "S"
    return rows


def desk_a():
    rows = desk(56, 12, 44)
    put(rows, 8, 2, "!"); put(rows, 8, 4, "P")
    put(rows, 7, 8, "N")
    put(rows, 6, 20, "I")
    put(rows, 7, 26, "B")
    put(rows, 7, 34, "C")
    put(rows, 7, 40, "K")
    put(rows, 7, 50, "D"); put(rows, 8, 50, "D"); put(rows, 8, 52, "X")
    return finish(rows)


def desk_b():
    rows = desk(64, 8, 52)
    put(rows, 8, 3, "P")
    put(rows, 7, 10, "N")
    put(rows, 6, 18, "GGG"); put(rows, 5, 19, "I")
    put(rows, 7, 24, "B")
    put(rows, 6, 30, "GGG"); put(rows, 5, 31, "K")
    put(rows, 7, 40, "C")
    put(rows, 7, 58, "D"); put(rows, 8, 58, "D"); put(rows, 8, 60, "X")
    return finish(rows)


def desk_c():
    rows = desk(72, 8, 60)
    put(rows, 8, 3, "P")
    put(rows, 7, 10, "N")
    put(rows, 6, 22, "I")
    put(rows, 7, 30, "B")
    put(rows, 6, 44, "K")
    put(rows, 7, 52, "C")
    put(rows, 7, 66, "D"); put(rows, 8, 66, "D"); put(rows, 8, 68, "X")
    return finish(rows)


# ---------------------------------------------------------
# SHARED TEXT
# ---------------------------------------------------------

REQUESTS = [{"name": "REQUEST", "fact": "One of thousands of fake requests aimed at the same server at once."}] * 6

HTML_STORY_LINES = [
    "<!DOCTYPE html>",
    "<html>",
    "  <head>",
    "    <title>My Site</title>",
    "  </head>",
    "  <body>",
    "    <h1>Hello, web</h1>",
    "    <p>Built by a recruit.</p>",
    "  </body>",
    "</html>",
]

JS_STORY_LINES = [
    "// index.js",
    "const button = document.querySelector('button');",
    "button.addEventListener('click', () => {",
    "  document.title = 'Clicked!';",
    "});",
    "// ready.",
]


# ---------------------------------------------------------
# LEVELS
# ---------------------------------------------------------

INTERNET_LEVELS = [

    # ===================== NETWORKS =====================

    level(
        1, "Inside the Cable",
        section="Networks",
        objective="Understand what a network is and where you are.",
        concepts=["network", "connection", "protocol"],
        lesson={
            "title": "You are a packet",
            "points": [
                "A NETWORK is two or more machines that can talk to each other.",
                "The internet is a network of networks: your home, your school, the coffee shop, all joined.",
                "Machines talk in agreed rules called PROTOCOLS - the same way everyone here says 'hello' the same way.",
                "You are travelling as a PACKET: a small envelope of data with an address on the front.",
                "The blue glow under the floor is the live stream. Fall in and you'll be bounced back to the last ledge - minus a heart.",
            ],
            "example": "Your laptop -> home router -> ISP -> ... -> a server far away, hop by hop.",
        },
        story="White walls curve around you like the inside of a hose. Blue light pulses along the floor. A small round drone - PING - bobs up beside you: 'New packet! Welcome to the backbone. Try not to fall in.'",
        goal="Cross the tunnel, talk to PING, and answer the terminal by the door.",
        gameplay="Jump the pits (2 wide), climb the strands for chips, use the terminal.",
        guide=GUIDE,
        sign="CABLE 7 - MAINTENANCE: Do not touch the stream while live. It is always live.",
        dialogue=[
            "Everything in here is a machine talking to another machine. That's all a network is.",
            "The rules they agree on are called protocols. Same words, same order, every time.",
            "Terminal's by the door. First question is an easy one.",
        ],
        challenge={
            "type": "mcq",
            "prompt": "What is the internet?",
            "options": ["One giant computer that everyone logs in to", "A network of networks that share the same rules", "A single company's cables", "Another word for the web browser"],
            "answer": 1,
            "wrong": "No single machine owns it. Think plural.",
        },
        reasoning="Replace the one-big-computer model with connected networks.",
        success="The cable hums and the door slides open.",
        failure="The terminal blinks: not that.",
        explanation="The internet is many independent networks joined together, all speaking agreed protocols.",
        reward="Backbone Badge I",
        mentor="Use the postal-system analogy; explain protocols as agreed rules.",
        hints=["Think plural."],
        map=cable_a(),
        theme="cable",
        intro=True,
    ),

    level(
        2, "The Junction",
        section="Networks",
        objective="Connect devices to the right ports on a switch.",
        concepts=["switch", "ports", "cables"],
        lesson={
            "title": "Plugging things in",
            "points": [
                "A SWITCH is a box with numbered PORTS; every cable from a device goes into one port.",
                "The switch learns which device sits on which port and sends data only where it belongs.",
                "Labels matter: a printer plugged into the wrong port still works - but the wiring plan is wrong, and the next person will be lost.",
                "In the puzzle: click a device, then click its port (or drag the device onto the port).",
            ],
            "example": "LAPTOP  -> port 1\nPRINTER -> port 4\nPHONE   -> port 2\nSERVER  -> port 3",
        },
        story="The tunnel opens into a junction: a switch the size of a house, four ports glowing, four loose cables on the floor. PING: 'Somebody yanked everything out. The wiring plan is on the sign.'",
        goal="Reconnect all four devices to the ports the sign lists.",
        gameplay="Parkour up the strands for the chips, read the sign, use the terminal and wire the switch.",
        guide=GUIDE,
        sign="WIRING PLAN: LAPTOP -> port 1. PHONE -> port 2. SERVER -> port 3. PRINTER -> port 4.",
        dialogue=[
            "Four devices, four ports, one plan. Follow the plan, not your instinct.",
        ],
        challenge={
            "type": "wires",
            "prompt": "Connect each device to the port the wiring plan gives it.",
            "devices": ["LAPTOP", "PRINTER", "PHONE", "SERVER"],
            "ports": ["port 1", "port 2", "port 3", "port 4"],
            "answer": [0, 3, 1, 2],
        },
        reasoning="Follow a wiring plan exactly; one device per port.",
        success="Four lights go green. The junction door opens.",
        failure="The terminal says which device is on the wrong port.",
        explanation="Each device gets its own port; the plan on the sign is the source of truth.",
        reward="Backbone Badge II",
        mentor="Ask the learner to read the plan aloud, device by device.",
        hints=["The sign lists every pair."],
        map=cable_b(),
        theme="cable",
        start_items=["SWORD"],
    ),

    # ===================== IP ADDRESSES =====================

    level(
        3, "Addresses",
        section="IP Addresses",
        objective="Give a computer a valid, unused IP address on its network.",
        concepts=["IPv4", "octets", "network range", "reserved addresses"],
        lesson={
            "title": "IP addresses - a home for every machine",
            "points": [
                "An IPv4 address is four numbers from 0 to 255, separated by dots: 192.168.1.10",
                "Machines on the same network share the first part (here 192.168.1.) and differ in the last number.",
                "Two rules: the last number is 1-254 (0 and 255 are reserved), and no two machines may share an address.",
                "The router usually takes .1. Check the sign for addresses already in use.",
            ],
            "example": "Network: 192.168.1.x\nRouter:  192.168.1.1\nIn use:  .10  .11  .12\nFree:    anything else from .2 to .254",
        },
        story="A new machine hangs off the cable with no address at all - packets for it just fall into the stream. PING: 'Give it a home. Same network, nobody else's number.'",
        goal="Type a valid, unused address for the new machine.",
        gameplay="Read the sign for the network and the addresses in use, then use the terminal.",
        guide=GUIDE,
        sign="NETWORK 192.168.1.x - router 192.168.1.1 - in use: 192.168.1.10, 192.168.1.11, 192.168.1.12",
        dialogue=[
            "Four numbers, dots between. First three match the network. Last one is yours - if nobody has it.",
        ],
        challenge={
            "type": "ip_assign",
            "prompt": "Assign the new machine a valid IPv4 address on this network that nobody is using.",
            "placeholder": "192.168.1.___",
            "network": "192.168.1.",
            "taken": ["192.168.1.1", "192.168.1.10", "192.168.1.11", "192.168.1.12"],
        },
        reasoning="Apply the address format, the network prefix, the reserved endpoints and uniqueness.",
        success="The machine lights up with its new address.",
        failure="The terminal says exactly which rule the address breaks.",
        explanation="A valid address matches the network prefix, ends in 1-254, and is not already taken.",
        reward="Backbone Badge III",
        mentor="Explain octets and the reserved endpoints; do not name a specific free address.",
        hints=["Which numbers does the sign say are already used?"],
        map=cable_c(),
        theme="cable",
        start_items=["SWORD"],
    ),

    level(
        4, "Packet Post",
        section="IP Addresses",
        objective="Deliver packets to the machines whose IP addresses they carry.",
        concepts=["destination address", "delivery"],
        lesson={
            "title": "Reading the address on the envelope",
            "points": [
                "Every packet carries a DESTINATION IP address on the front.",
                "Delivery is simple matching: the packet goes to the machine with exactly that address.",
                "One digit different is a different machine - or nobody at all.",
                "Drag each packet onto the machine with the matching address (or click packet, then machine).",
            ],
            "example": "Packet to 192.168.1.30  ->  SERVER (192.168.1.30)",
        },
        story="A sorting office in the cable: three machines waiting, a pile of packets on the floor, each stamped with an address. PING: 'Match the stamp to the machine. Exactly.'",
        goal="Drop every packet on the machine with the matching IP address.",
        gameplay="Grab the candy on the way; use the terminal to sort the packets.",
        guide=GUIDE,
        sign="SORTING OFFICE - match the destination address exactly. .10 is not .11.",
        dialogue=["Match the stamp to the machine. Exactly. Digits matter."],
        challenge={
            "type": "route_packets",
            "prompt": "Deliver each packet to the machine with the matching IP address.",
            "machines": [
                {"name": "ADA-PC", "ip": "192.168.1.10"},
                {"name": "PRINTER", "ip": "192.168.1.20"},
                {"name": "SERVER", "ip": "192.168.1.30"},
            ],
            "packets": [
                {"label": "photo.jpg", "to": "192.168.1.10"},
                {"label": "report.pdf", "to": "192.168.1.20"},
                {"label": "upload.zip", "to": "192.168.1.30"},
                {"label": "notes.txt", "to": "192.168.1.10"},
                {"label": "backup.tar", "to": "192.168.1.30"},
            ],
            "answer": [0, 1, 2, 0, 2],
        },
        reasoning="Exact string matching of destination to machine address.",
        success="Every packet lands. The office door opens.",
        failure="The terminal names the packet that went to the wrong machine.",
        explanation="Delivery is exact matching of the destination address to a machine's address.",
        reward="Backbone Badge IV",
        mentor="Ask the learner to compare the last number of each address.",
        hints=["Compare the last number of the address."],
        map=cable_a(),
        theme="cable",
        start_items=["SWORD"],
    ),

    # ===================== DNS =====================

    level(
        5, "The Phone Book",
        section="DNS",
        objective="Use DNS to turn names into addresses before delivering.",
        concepts=["DNS", "domain name", "lookup"],
        lesson={
            "title": "DNS - names for humans, numbers for machines",
            "points": [
                "People remember NAMES (printer.lab); machines deliver to NUMBERS (192.168.1.20).",
                "DNS is the phone book that translates a name into an address.",
                "Delivery is two steps: look the name up, then match the address.",
                "If the phone book is wrong or poisoned, you deliver to the wrong machine without noticing.",
            ],
            "example": "printer.lab -> DNS -> 192.168.1.20 -> PRINTER",
        },
        story="These packets are stamped with names, not numbers. A dusty phone book hangs on the wall. PING: 'Look it up first. Then deliver. Two steps, every time.'",
        goal="Look each name up in the DNS table, then deliver the packet to the right machine.",
        gameplay="Read the DNS table on the sign, then sort the packets at the terminal.",
        guide=GUIDE,
        sign="DNS TABLE: ada.lab = 192.168.1.10   printer.lab = 192.168.1.20   files.lab = 192.168.1.30",
        dialogue=["Name to number, then number to machine. Never skip the lookup."],
        challenge={
            "type": "route_packets",
            "prompt": "Look each name up in the DNS table, then deliver the packet to that machine.",
            "dns": {"ada.lab": "192.168.1.10", "printer.lab": "192.168.1.20", "files.lab": "192.168.1.30"},
            "machines": [
                {"name": "ADA-PC", "ip": "192.168.1.10"},
                {"name": "PRINTER", "ip": "192.168.1.20"},
                {"name": "FILE SERVER", "ip": "192.168.1.30"},
            ],
            "packets": [
                {"label": "invoice.pdf", "to": "printer.lab"},
                {"label": "homework.doc", "to": "ada.lab"},
                {"label": "photos.zip", "to": "files.lab"},
                {"label": "poster.png", "to": "printer.lab"},
            ],
            "answer": [1, 0, 2, 1],
        },
        reasoning="Two-step resolution: name -> address -> machine.",
        success="Names resolve, packets land, door opens.",
        failure="The terminal names the packet that went astray.",
        explanation="DNS maps names to addresses; delivery still happens by address.",
        reward="Backbone Badge V",
        mentor="Phone-book analogy; ask what happens if the book is wrong.",
        hints=["The table on the sign has every name."],
        map=cable_b(),
        theme="cable",
        start_items=["SWORD"],
    ),

    level(
        0, "Checkpoint: Networks & Addresses",
        kind="quiz",
        section="DNS",
        objective="Prove you remember networks, IP addresses and DNS.",
        concepts=["network", "IP", "DNS"],
        lesson={
            "title": "Checkpoint - Networks & Addresses",
            "points": [
                "Networks are machines that talk; the internet joins networks with shared protocols.",
                "IPv4: four numbers 0-255; same network = same first part; last number 1-254 and unique.",
                "DNS turns names into addresses; delivery matches addresses exactly.",
            ],
            "example": "printer.lab -> 192.168.1.20 -> PRINTER",
        },
        story="PING hovers in front of a junction box. 'Quick check before the deep cable. Six questions.'",
        goal="Get every question right to continue.",
        gameplay="Answer six questions.",
        guide=GUIDE,
        dialogue=["Six questions, then the deep cable."],
        challenge={
            "type": "quiz",
            "prompt": "Answer every question. Wrong answers only tell you which question to look at again.",
            "questions": [
                {"prompt": "Which of these is a VALID IPv4 address?", "options": ["192.168.1.300", "192.168.1", "192.168.1.42", "printer.lab"], "answer": 2},
                {"prompt": "Two machines on the same network must NOT:", "options": ["Share the first three numbers", "Share the exact same address", "Use port 443", "Use DNS"], "answer": 1},
                {"prompt": "What does DNS do?", "options": ["Encrypts packets", "Turns a name like files.lab into an IP address", "Chooses the fastest cable", "Blocks scam emails"], "answer": 1},
                {"prompt": "A packet is stamped 192.168.1.20. It is delivered to:", "options": ["Every machine", "The machine whose address is exactly 192.168.1.20", "The router only", "The nearest machine"], "answer": 1},
                {"prompt": "A switch port is:", "options": ["A numbered socket a device's cable plugs into", "A type of virus", "A password", "A website"], "answer": 0},
                {"prompt": "What is a protocol?", "options": ["A brand of cable", "The agreed rules machines use to talk", "A kind of firewall", "A DNS server"], "answer": 1},
            ],
        },
        reasoning="Retrieval practice.",
        success="All six correct.",
        failure="The drill says which question is wrong, nothing more.",
        explanation="Networks, valid addresses, DNS, exact delivery, ports, protocols.",
        reward="Checkpoint Pin I",
        mentor="Coach with questions; never state the answer.",
        hints=["Re-read the lesson notes for the first five levels."],
        theme="cable",
        start_items=["SWORD"],
    ),

    # ===================== PACKETS & THREATS =====================

    level(
        7, "Packet Trail",
        section="Packets",
        objective="Put the journey of a packet in order.",
        concepts=["packets", "routers", "hops", "reassembly"],
        lesson={
            "title": "The trip, hop by hop",
            "points": [
                "Big messages are cut into PACKETS, each numbered so they can be reassembled.",
                "Each ROUTER reads the destination and forwards the packet one HOP closer - it never knows the whole path.",
                "Packets may take different routes and arrive out of order; the receiver puts them back together.",
                "Lose one packet and only that one is resent.",
            ],
            "example": "type name -> DNS lookup -> packets sent -> routers forward -> receiver reassembles -> page shows",
        },
        story="The deepest part of the cable: parkour over three pits, and a console that has the journey scrambled. PING: 'Put my trip back in order. I've done it a billion times and I still can't explain it.'",
        goal="Cross the pits and order the six steps of a packet's journey.",
        gameplay="Careful jumps (the stream bites). Terminal at the end.",
        guide=GUIDE,
        sign="ROUTER LOG: forwarded packet 3/5 to next hop. I do not know where it ends up. That's not my job.",
        dialogue=["Six steps. Start from the moment someone types a name."],
        challenge={
            "type": "order_code",
            "prompt": "Drag the six steps into the order they happen.",
            "pieces": [
                "1. You type a site's name into the browser",
                "2. DNS turns the name into an IP address",
                "3. Your request is cut into numbered packets",
                "4. Routers forward each packet one hop at a time",
                "5. The server receives the packets and reassembles them",
                "6. The reply comes back the same way and the page appears",
            ],
            "shuffle": [3, 0, 5, 1, 4, 2],
        },
        reasoning="Sequence the request path.",
        success="The trail makes sense again. Door opens.",
        failure="The console says the order isn't right.",
        explanation="Name, lookup, packets, hops, reassembly, reply.",
        reward="Backbone Badge VI",
        mentor="Ask which step must happen before packets can be addressed.",
        hints=["Nothing can be addressed before the name is looked up."],
        map=cable_port(),
        theme="cable",
        start_items=["SWORD"],
    ),

    level(
        8, "Man in the Middle",
        section="Packets",
        objective="Recognise interception and what stops it.",
        concepts=["man-in-the-middle", "encryption", "HTTPS"],
        lesson={
            "title": "Someone is reading the mail",
            "points": [
                "A MAN-IN-THE-MIDDLE sits on the path and reads, or changes, packets passing through.",
                "Public Wi-Fi, a poisoned DNS entry, or a fake router are all ways to get in the middle.",
                "Plain HTTP packets are readable by anyone on the path. HTTPS wraps them in ENCRYPTION so the middle sees only noise.",
                "The sniffers on these cables are exactly that. Jump over them or cut them down.",
            ],
            "example": "http://  -> readable at every hop\nhttps:// -> sealed; the middle sees nothing useful",
        },
        story="Hooded figures crouch on the strands, tapping the cable with little black clips. PING, very quietly: 'Sniffers. They read everything that isn't sealed.'",
        goal="Get past the sniffers and tell the terminal what stops them reading your packets.",
        gameplay="Sniffers patrol; they hurt on touch. Sword works. Terminal at the end.",
        guide=GUIDE,
        sign="TAP LOG: 3 packets read in plain text. 40 packets sealed - contents unknown.",
        dialogue=["They can only read what's sent in the clear. Seal it and they get noise."],
        challenge={
            "type": "text_answer",
            "prompt": "Which protocol seals web traffic so a man-in-the-middle sees only noise?",
            "placeholder": "protocol name",
            "accepted": ["https", "tls", "https (tls)", "encryption", "ssl"],
            "wrong": "Plain http is readable. The sealed version has one extra letter.",
        },
        reasoning="Connect interception to encryption.",
        success="The taps go dark. Door opens.",
        failure="The terminal blinks: not that.",
        explanation="HTTPS (TLS) encrypts traffic so anyone in the middle sees nothing useful.",
        reward="Backbone Badge VII",
        mentor="Explain the padlock and why login pages must be HTTPS.",
        hints=["It's the padlock in the address bar."],
        map=cable_sniffer(),
        theme="cable",
        start_items=["SWORD"],
    ),

    level(
        9, "Flood",
        section="Packets",
        objective="Recognise a DDoS attack and its defences.",
        concepts=["DDoS", "botnet", "rate limiting"],
        lesson={
            "title": "Too many at once",
            "points": [
                "A DoS (denial of service) attack floods a server with more requests than it can answer.",
                "DDoS = Distributed: thousands of infected machines (a botnet) flood it at the same time.",
                "Nothing is stolen - the server just can't serve real people. Availability is the target.",
                "Defences: rate limiting, filtering junk traffic, spreading the load across many servers (CDNs).",
            ],
            "example": "1 request/s  -> fine\n100,000 fake requests/s -> nobody real gets through",
        },
        story="The cable shakes. A swarm of identical grey packets pours down the tunnel, all stamped REQUEST, all headed for the same server. PING: 'That's not traffic. That's a flood.'",
        goal="Survive the swarm and tell the terminal what the flood is doing.",
        gameplay="Six request-bugs rush you. Cut them down. Terminal at the end.",
        guide=GUIDE,
        sign="SERVER STATUS: 99,812 requests/second - 12 real. Response time: never.",
        dialogue=["None of them carry anything. They just take up the whole road."],
        npcs=[],
        bugs=REQUESTS,
        challenge={
            "type": "mcq",
            "prompt": "A server gets 100,000 identical requests per second from thousands of machines and stops answering real users. This is:",
            "options": ["A man-in-the-middle attack", "A DDoS attack - the target is availability", "A DNS lookup", "Normal Monday traffic"],
            "answer": 1,
            "wrong": "Nothing is stolen or read - the server is simply drowned.",
        },
        reasoning="Identify DDoS by its effect: availability lost.",
        success="The swarm thins. Door opens.",
        failure="The terminal blinks: not that.",
        explanation="A DDoS floods a service until real users can't get through; defences limit and filter traffic.",
        reward="Backbone Badge VIII",
        mentor="Contrast DDoS (availability) with theft (confidentiality).",
        hints=["What did the sign say the real users got?"],
        map=cable_flood(),
        theme="cable",
        start_items=["SWORD"],
    ),

    level(
        0, "Checkpoint: Packets & Threats",
        kind="quiz",
        section="Packets",
        objective="Prove you remember packets, interception and floods.",
        concepts=["packets", "routers", "HTTPS", "DDoS"],
        lesson={
            "title": "Checkpoint - Packets & Threats",
            "points": [
                "Messages travel as numbered packets, forwarded hop by hop by routers, reassembled at the end.",
                "A man-in-the-middle reads packets on the path; HTTPS encryption makes them unreadable.",
                "A DDoS floods a server with fake requests so real users can't get through.",
            ],
            "example": "https:// = sealed. 100,000 fake requests = flood.",
        },
        story="PING: 'Last check before we leave the machine. Six questions.'",
        goal="Get every question right to reach the port.",
        gameplay="Answer six questions.",
        guide=GUIDE,
        dialogue=["Six questions. Then the port."],
        challenge={
            "type": "quiz",
            "prompt": "Answer every question. Wrong answers only tell you which question to look at again.",
            "questions": [
                {"prompt": "What does a router do with a packet?", "options": ["Reads it and rewrites it", "Forwards it one hop toward its destination", "Stores it forever", "Deletes it"], "answer": 1},
                {"prompt": "Why are messages split into packets?", "options": ["To make them slower", "So pieces can travel separately and a lost piece is resent alone", "Because cables are short", "To hide them from DNS"], "answer": 1},
                {"prompt": "Which traffic can a man-in-the-middle read?", "options": ["Only HTTPS", "Plain HTTP - unencrypted", "None", "Only DNS"], "answer": 1},
                {"prompt": "A DDoS attack mainly harms:", "options": ["Confidentiality - secrets leak", "Availability - the service stops responding", "The DNS phone book", "Your password"], "answer": 1},
                {"prompt": "Earlier: the address 192.168.1.255 is:", "options": ["A normal machine address", "Reserved - not for a machine", "The DNS server", "A domain name"], "answer": 1},
                {"prompt": "Earlier: before a packet can be addressed to files.lab, what must happen?", "options": ["A firewall check", "A DNS lookup turning the name into an address", "A backup", "A password change"], "answer": 1},
            ],
        },
        reasoning="Retrieval practice with two cumulative questions.",
        success="All six correct.",
        failure="The drill says which question is wrong, nothing more.",
        explanation="Routers forward, packets split, HTTPS seals, DDoS drowns.",
        reward="Checkpoint Pin II",
        mentor="Coach with questions; never state the answer.",
        hints=["Re-read the notes for the deep-cable levels."],
        theme="cable",
        start_items=["SWORD"],
    ),

    # ===================== OUT OF THE MACHINE =====================

    level(
        11, "The HDMI Port",
        section="Out of the Machine",
        objective="Understand how a request becomes a web page on a screen.",
        concepts=["client", "server", "request", "response", "browser"],
        lesson={
            "title": "How a web page reaches a screen",
            "points": [
                "Your browser is the CLIENT: it sends a REQUEST ('give me this page').",
                "A SERVER answers with a RESPONSE: HTML, images, scripts - as packets.",
                "The browser rebuilds the packets into files and draws the page on the screen.",
                "The screen is the last hop of all: the port you're about to leave through.",
            ],
            "example": "Browser --request--> Server --response--> Browser draws the page",
        },
        story="The cable ends in a wall of gold pins: an HDMI port, the way out. PING: 'Everything we carried ends up as light on a screen. Last stretch.'",
        goal="Reach the port and order the client-server exchange.",
        gameplay="Three quick pits, then the terminal before the port.",
        guide=GUIDE,
        sign="PORT 1 - HDMI. Output only. What goes through here becomes pixels.",
        dialogue=["Client asks, server answers, browser draws. That's a web page."],
        challenge={
            "type": "order_code",
            "prompt": "Drag the five steps into the order a web page is delivered.",
            "pieces": [
                "1. The browser (client) sends a request for the page",
                "2. The request travels as packets to the server",
                "3. The server sends back a response: HTML and files",
                "4. The browser reassembles the response",
                "5. The browser draws the page on the screen",
            ],
            "shuffle": [2, 4, 0, 3, 1],
        },
        reasoning="Sequence client, server, response, render.",
        success="The pins light up. You are pulled through the port.",
        failure="The console says the order isn't right.",
        explanation="Request out, response back, browser draws.",
        reward="Backbone Badge IX",
        mentor="Point at this app's own Flask routes as a real server.",
        hints=["Who asks first?"],
        map=cable_port(),
        theme="cable",
        start_items=["SWORD"],
    ),

    level(
        12, "On the Desk",
        section="Out of the Machine",
        objective="Understand what HTML is and what a page is made of.",
        concepts=["HTML", "tags", "elements"],
        no_lesson=False,
        mimic=True,
        lesson={
            "title": "HTML - the skeleton of a page",
            "points": [
                "A web page is a text file written in HTML: content wrapped in TAGS like <h1>Title</h1>.",
                "Tags come in pairs: an opening <p> and a closing </p>. What's between them is the element's content.",
                "The browser reads the tags and decides what is a heading, a paragraph, a link, an image.",
                "Look at the monitor: it mirrors you. Everything you do out here shows up in there.",
            ],
            "example": "<h1>Hello, web</h1>\n<p>My first paragraph.</p>",
        },
        story="You tumble out of the port onto a wooden desk the size of a football pitch. A keyboard rises like a mountain range. On the monitor, a tiny figure moves when you move. PING: 'That's you. The screen shows what the machine sees.'",
        goal="Cross the desk and tell the terminal which tag makes a heading.",
        gameplay="Climb onto the keys. Watch the monitor. Terminal near the far end.",
        guide=GUIDE,
        sign="STICKY NOTE ON THE MONITOR: h1 = big heading. p = paragraph. a = link. img = picture.",
        dialogue=["Tags wrap content. The browser reads the tags and decides what each piece is."],
        challenge={
            "type": "mcq",
            "prompt": "Which HTML tag makes the main heading of a page?",
            "options": ["<p>", "<h1>", "<img>", "<head>"],
            "answer": 1,
            "wrong": "Read the sticky note on the monitor again.",
        },
        reasoning="Basic tag recognition.",
        success="The monitor flashes a big heading. Door opens.",
        failure="The terminal blinks: not that.",
        explanation="<h1> is the main heading; <p> is a paragraph; <img> a picture; <head> holds page info, not content.",
        reward="Backbone Badge X",
        mentor="Show tiny tag examples; ask what each wraps.",
        hints=["The sticky note lists it first."],
        map=desk_a(),
        theme="desk",
        start_items=["SWORD"],
    ),

    # ===================== BUILDING THE WEB =====================

    level(
        13, "The Skeleton",
        section="Building the Web",
        objective="Arrange the structure of a complete HTML page.",
        concepts=["doctype", "html", "head", "body", "nesting"],
        mimic=True,
        code_lines=HTML_STORY_LINES,
        lesson={
            "title": "Every page has the same bones",
            "points": [
                "<!DOCTYPE html> first: it tells the browser this is modern HTML.",
                "<html> wraps everything. Inside it: <head> (info about the page, like the title) then <body> (what people see).",
                "Tags close in reverse order of opening - the last opened is the first closed.",
                "Run across the keys and watch the monitor: the page writes itself as you go.",
            ],
            "example": "<!DOCTYPE html>\n<html>\n  <head><title>My Site</title></head>\n  <body><h1>Hello</h1></body>\n</html>",
        },
        story="The monitor is blank. As you run across the keys, lines of HTML appear on it, one after another. PING: 'You're typing. Sort of. Now put the page in the right order.'",
        goal="Run across the keyboard, then order the ten lines of a page at the terminal.",
        gameplay="Every few keys you cross adds a line to the screen. Terminal on the far side.",
        guide=GUIDE,
        sign="KEYBOARD: 104 keys. Cats have walked here. Their HTML did not validate.",
        dialogue=["Doctype, html, head, body. Open in order, close in reverse."],
        challenge={
            "type": "order_code",
            "prompt": "Drag the ten lines into a valid page: doctype, html, head with a title, body with a heading and a paragraph.",
            "pieces": HTML_STORY_LINES,
            "shuffle": [5, 1, 9, 0, 6, 3, 2, 8, 4, 7],
        },
        reasoning="Nesting and closing order.",
        success="The page renders on the monitor. Door opens.",
        failure="The terminal says the order isn't right.",
        explanation="Doctype, html, head/title, body/content, closing in reverse.",
        reward="Backbone Badge XI",
        mentor="Ask which tag must close last.",
        hints=["The first tag to open is the last to close."],
        map=desk_b(),
        theme="desk",
        start_items=["SWORD"],
    ),

    level(
        14, "Tags",
        section="Building the Web",
        objective="Write the right tags for a heading, a paragraph and a link.",
        concepts=["h1", "p", "a href", "attributes"],
        mimic=True,
        code_lines=JS_STORY_LINES,
        lesson={
            "title": "Filling the skeleton",
            "points": [
                "<h1>...</h1> heading, <p>...</p> paragraph.",
                "A link is <a href=\"https://...\">text</a> - href is an ATTRIBUTE: extra information inside the opening tag.",
                "Every opening tag needs its closing tag with a slash: </p>.",
                "Scripts (JavaScript) make pages react to clicks - the monitor shows one as you run.",
            ],
            "example": "<h1>Cyber Academy</h1>\n<p>Learn by playing.</p>\n<a href=\"https://example.com\">Visit</a>",
        },
        story="The monitor now shows a small script waiting for a click. PING: 'Structure first, then content, then behaviour. Fill in the tags.'",
        goal="Fill the blanks so the snippet has a heading, a paragraph and a working link.",
        gameplay="Cross the keys, use the terminal, fill three blanks.",
        guide=GUIDE,
        sign="REMINDER (in Sharpie on the desk): a link needs href. h1 is the heading. Close your tags.",
        dialogue=["Three blanks: the heading tag, the paragraph's closing tag, the link's attribute."],
        challenge={
            "type": "fill_blank",
            "prompt": "Fill the blanks: the heading tag, the paragraph's closing tag, and the attribute that holds a link's address.",
            "code": ["<___>Cyber Academy</h1>", "<p>Learn by playing.</___>", "<a ___=\"https://example.com\">Visit</a>"],
            "answers": [["h1"], ["p"], ["href"]],
            "bank": ["h1", "p", "href", "src", "head", "body"],
        },
        reasoning="Tag names, closing tags, attributes.",
        success="The page gets its heading, its paragraph and a working link.",
        failure="The terminal names the blank that is wrong.",
        explanation="h1 opens the heading, </p> closes the paragraph, href carries the link address.",
        reward="Backbone Badge XII",
        mentor="Explain attributes as settings inside a tag.",
        hints=["Which blank is a closing tag?"],
        map=desk_c(),
        theme="desk",
        start_items=["SWORD"],
    ),

    level(
        15, "Your Own Site",
        section="Building the Web",
        objective="Know the tools and write down an idea for a website of your own.",
        concepts=["editor", "browser", "idea", "pages"],
        mimic=True,
        code_lines=HTML_STORY_LINES + JS_STORY_LINES,
        lesson={
            "title": "Starting a real website",
            "points": [
                "You need two things: a code EDITOR (VS Code is free) and a BROWSER to open your files in.",
                "Save a file as index.html, write your skeleton, open it in the browser. That's a website - on your machine.",
                "Before code, an IDEA: who is it for, what does it do, which pages does it need?",
                "Write your idea down now. The Academy keeps it on your profile so you can build it later.",
            ],
            "example": "Idea: a page for my chess club\nPages: Home, Schedule, Join",
        },
        story="The desk ends at the edge of the monitor. Every line you ran across is on the screen now: a whole small page. PING: 'That one's mine. What's yours going to be?'",
        goal="Write down your website idea: a name, what it does, and three pages.",
        gameplay="Cross the keys one last time, then fill in the idea form at the terminal.",
        guide=GUIDE,
        sign="NOTE TO SELF: install VS Code. Make index.html. Open it in the browser. Then the hard part: decide what it's for.",
        dialogue=["A name, one sentence about what it does, three pages. Nothing else yet."],
        challenge={
            "type": "idea",
            "prompt": "Your website. Give it a name, say what it does in one sentence, and list three pages it needs.",
        },
        reasoning="Turn the course into a concrete next step the learner owns.",
        success="Your idea is saved to your profile.",
        failure="The form says which field is missing.",
        explanation="An editor, a browser, an index.html and an idea - that's how every website starts.",
        reward="Backbone Badge XIII",
        mentor="Help the learner sharpen the idea with questions: who is it for, what is the one thing it does?",
        hints=["Who is the site for? Start there."],
        map=desk_c(),
        theme="desk",
        start_items=["SWORD"],
    ),

    obelisk_level(
        16, "Internet Basics", "The Backbone", "Backbone Master Badge", GUIDE,
        "The monitor's light swallows you and you land on a white plain under a pale sky. An obelisk stands ahead. PING, for once, says nothing. There is a button at its base.",
        [
            "Networks talk in protocols; IP addresses are homes; DNS turns names into numbers.",
            "Packets hop router to router and are rebuilt at the end; HTTPS keeps the middle blind; floods attack availability.",
            "A page is HTML: skeleton, tags, content. An editor, a browser and an idea are all you need to start.",
        ],
    ),
]

for _index, _level in enumerate(INTERNET_LEVELS, start=1):
    _level["number"] = _index
