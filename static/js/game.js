/* =========================================================
   CYBER ACADEMY - 2D PIXEL GAME ENGINE

   One engine for every course. The level (map, dialogue,
   challenge, hints) comes from the JSON the server puts in
   #level-data. Answers are never checked here - they go to
   /api/level/submit and the server decides.

   Controls:  A / D move    W / SPACE jump    E talk / read / use
              F or click = use the item in the selected slot
              Q drop the selected item    1-5 select slot
              ENTER continue dialogue    M sound on / off
========================================================= */

(function () {

    const levelElement = document.getElementById("level-data");

    if (!levelElement) {
        return;
    }

    const LEVEL = JSON.parse(levelElement.textContent);
    const CHARACTER = JSON.parse(document.getElementById("character-data").textContent) || {};
    const inventoryElementData = document.getElementById("inventory-data");
    const SAVED_INVENTORY = inventoryElementData ? JSON.parse(inventoryElementData.textContent) : null;
    const checkpointElementData = document.getElementById("checkpoint-data");
    const SAVED_CHECKPOINT = checkpointElementData ? JSON.parse(checkpointElementData.textContent) : null;
    const GUIDE = LEVEL.guide || "BYTE";

    // SecureMentor follows the game into fullscreen (only the fullscreen
    // element is visible, so the dock and panel move inside it).
    document.addEventListener("fullscreenchange", function () {
        const dock = document.getElementById("mentor-dock");
        const panel = document.getElementById("mentor-panel");
        const window_ = document.getElementById("game-window");
        if (!dock || !panel || !window_) return;
        const target = document.fullscreenElement === window_ ? window_ : document.body;
        target.appendChild(dock);
        target.appendChild(panel);
    });

    // Give SecureMentor the level context (app.js sends it with questions).
    window.mentorContext =
        "Course: " + LEVEL.course_title + " (" + LEVEL.zone + "). " +
        "Section: " + LEVEL.section + ". Level " + LEVEL.number + ": " + LEVEL.title + ". " +
        "Objective: " + LEVEL.objective + " " +
        "Challenge: " + LEVEL.challenge.prompt;

    // Checkpoint quizzes have no map: a small question form replaces the engine.
    if (LEVEL.kind === "quiz") {
        runQuiz();
        return;
    }

    function runQuiz() {
        const overlay = document.getElementById("overlay-lesson");
        const panel = document.getElementById("quiz-panel");
        const timer = document.getElementById("hud-timer");
        const objective = document.getElementById("hud-objective");
        const resultOverlay = document.getElementById("overlay-result");
        const questions = LEVEL.challenge.questions;
        const chosen = questions.map(() => null);
        let started = null;
        let finalElapsed = null;
        let sending = false;

        function el(tag, className, text) {
            const node = document.createElement(tag);
            if (className) node.className = className;
            if (text !== undefined) node.textContent = text;
            return node;
        }

        function fmt(seconds) {
            return String(Math.floor(seconds / 60)).padStart(2, "0") + ":" + String(seconds % 60).padStart(2, "0");
        }

        setInterval(() => {
            if (finalElapsed !== null) timer.textContent = fmt(finalElapsed);
            else if (started !== null) timer.textContent = fmt(Math.floor((performance.now() - started) / 1000));
        }, 500);

        objective.textContent = "Read the recap, then press START QUIZ";

        const feedback = el("p", "quiz-feedback", "");
        const blocks = [];

        questions.forEach((question, qi) => {
            const block = el("div", "quiz-question");
            block.appendChild(el("h3", "", (qi + 1) + ". " + question.prompt));
            question.options.forEach((option, oi) => {
                const button = el("button", "choice-button", option);
                button.type = "button";
                button.addEventListener("click", () => {
                    chosen[qi] = oi;
                    block.querySelectorAll(".choice-button").forEach((b) => b.classList.remove("choice-selected"));
                    button.classList.add("choice-selected");
                    block.classList.remove("quiz-wrong");
                });
                block.appendChild(button);
            });
            blocks.push(block);
            panel.appendChild(block);
        });

        panel.appendChild(feedback);
        const actions = el("div", "quiz-actions");
        const submit = el("button", "large-button", "CHECK ANSWERS");
        submit.type = "button";
        actions.appendChild(submit);
        panel.appendChild(actions);

        document.getElementById("btn-start").addEventListener("click", async function () {
            overlay.classList.add("hidden");
            panel.classList.remove("hidden");
            objective.textContent = LEVEL.goal;
            try {
                await fetch("/api/level/start", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ course: LEVEL.course, level: LEVEL.number })
                });
            } catch (error) { /* timer may be missing; the quiz still works */ }
            started = performance.now();
        });

        submit.addEventListener("click", async function () {
            if (sending) return;
            if (chosen.some((c) => c === null)) {
                feedback.textContent = "Answer every question first.";
                return;
            }
            sending = true;
            submit.disabled = true;
            try {
                const response = await fetch("/api/level/submit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ course: LEVEL.course, level: LEVEL.number, answer: { answers: chosen } })
                });
                const data = await response.json();
                if (!data.success) { feedback.textContent = data.error || "The drill did not respond."; return; }
                if (!data.correct) {
                    feedback.textContent = data.feedback;
                    const numbers = (data.feedback.match(/\d+/g) || []).map(Number);
                    blocks.forEach((b, i) => b.classList.toggle("quiz-wrong", numbers.includes(i + 1)));
                    return;
                }
                finalElapsed = data.elapsed;
                panel.classList.add("hidden");
                showQuizResult(data);
            } catch (error) {
                feedback.textContent = "Connection lost. Try again.";
            } finally {
                sending = false;
                submit.disabled = false;
            }
        });

        function stat(label, value) {
            const box = el("div", "result-stat");
            box.appendChild(el("span", "stat-label", label));
            box.appendChild(el("strong", "stat-value", value));
            return box;
        }

        function showQuizResult(data) {
            const box = resultOverlay.querySelector(".overlay-box");
            document.getElementById("result-label").textContent = data.course_finished ? "COURSE COMPLETE" : (data.new_record ? "CHECKPOINT PASSED · NEW RECORD" : "CHECKPOINT PASSED");
            document.getElementById("result-title").textContent = LEVEL.title;
            document.getElementById("result-text").textContent = data.explanation || "";
            document.getElementById("result-code").classList.add("hidden");
            const stats = document.getElementById("result-stats");
            const actionsBox = document.getElementById("result-actions");
            stats.textContent = "";
            actionsBox.textContent = "";
            stats.appendChild(stat("TIME", data.elapsed === null ? "--:--" : fmt(data.elapsed)));
            stats.appendChild(stat("REWARD", data.reward || ""));
            stats.appendChild(stat("COURSE", (data.levels_done || 0) + " / " + (data.level_count || "?")));
            if (data.next_level) {
                const next = el("a", "large-button", "NEXT: " + data.next_level.title.toUpperCase());
                next.href = data.next_level.url;
                actionsBox.appendChild(next);
            } else {
                const back = el("a", "large-button", "BACK TO COURSE");
                back.href = "/curriculum/" + LEVEL.course;
                actionsBox.appendChild(back);
            }
            box.classList.add("celebrate", "pop-in");
            box.classList.remove("ready");
            resultOverlay.classList.remove("hidden");
            setTimeout(() => box.classList.add("ready"), 900);
        }
    }


    /* -----------------------------------------------------
       CONSTANTS
    ----------------------------------------------------- */

    const TILE = 16;
    const VIEW_W = 320;
    const VIEW_H = 192;

    const GRAVITY = 0.32;
    const MAX_FALL = 6;
    const JUMP_SPEED = -5.4;
    const RUN_ACCEL = 0.45;
    const RUN_MAX = 1.7;
    const INTERACT_RANGE = 22;

    const MAX_HP = 6;
    const CANDY_HEAL = 3;

    const ATTACK_REACH = 18;      // px in front of the player
    const ATTACK_COOLDOWN = 30;   // frames (0.5 s) between swings
    const STUN_FRAMES = 24;       // a hit freezes an enemy for 0.4 s
    const SNAKE_SPEED = 0.4;
    const DOCTOR_SPEED = 0.6;

    const BYTE_QUIPS = [
        "Nice. Even the snakes looked impressed.",
        "That door never stood a chance.",
        "Textbook. Well - lesson-notes-book.",
        "Logged, badged, and slightly smug. Carry on.",
        "The sim just updated your file: 'promising'.",
        "You're getting faster. The Grove noticed.",
        "One more idea that will actually stick."
    ];

    const ITEM_CHIP = "HINT CHIP";
    const ITEM_DAGGER = "DAGGER";
    const ITEM_CANDY = "CANDY";
    const ITEM_SWORD = "SWORD";
    const ITEM_CODE = "DOOR CODE";
    const ITEM_KEY = "VENT KEY";

    const WEAPONS = {
        "DAGGER": { reach: ATTACK_REACH, damage: 1, cooldown: ATTACK_COOLDOWN },
        "SWORD":  { reach: 26, damage: 2, cooldown: 34 }
    };

    const BUG_SPEED = 0.55;
    const BUG_RUSH = 1.15;
    const VEX_SPEED = 0.7;

    const ENEMY_HP = { boss: 8, hostile: 3, snake: 2, bug: 1, vex: 12, brain: 5, sniffer: 2 };
    const BOSS_TYPES = ["boss", "vex", "brain"];

    // One beam slot per course on the obelisk, in course order.
    const BEAM_SLOTS = ["cybersecurity", "python", "internet", "secure-coding"];
    const BEAM_COLORS = { cybersecurity: "#e0c04b", python: "#4be07a", internet: "#4bd0e0", "secure-coding": "#ff8a4b" };
    const KEYCAPS = "QWERTYUIOPASDFGHJKLZXCVBNM";

    const STATIC_QUIPS = [
        "Clean. Nobody even looked up.",
        "Another door that trusted a piece of plastic.",
        "They'll find the logs in a week. Maybe.",
        "You're getting good at this. That should worry someone.",
        "Keep moving. The lab thinks you're staff now."
    ];

    const THEMES = {
        jungle:  { skyTop: "#08150c", skyBottom: "#1b4a2c", ground: "#3d2b1a", grass: "#4c9a3a", stone: "#4a4a52", wall: "#5a3a1e", panel: "#eef1f3", trunk: "#5a3a1e", leaves: "#1f6a2a", leavesLight: "#3aa04a", far: "#0c2a18", accent: "#7bff8a", water: "#1a5a5a", door: "#dbe2e6", glow: true },
        forest:  { skyTop: "#070c18", skyBottom: "#0f2a2a", ground: "#3b2a1e", grass: "#3f7a2f", stone: "#4a4a52", wall: "#5a4630", panel: "#d9dde0", trunk: "#4a3220", leaves: "#1f5a2a", leavesLight: "#2c7a3a", far: "#0b1a1a", accent: "#4be07a", water: "#123f3a", door: "#2a2a30", glow: true },
        sewer:   { skyTop: "#05100b", skyBottom: "#0c2416", ground: "#2f3b2c", grass: "#3f5a34", stone: "#3a4638", wall: "#2c3a30", panel: "#dfe6ea", trunk: "#2c3a30", leaves: "#1f4a2a", leavesLight: "#2c6a3a", far: "#08170f", accent: "#7bd66b", water: "#0d3f3a", door: "#3a2f22", glow: true },
        lab:     { skyTop: "#e9eef1", skyBottom: "#cfd8dd", ground: "#f2f4f5", grass: "#bfc8ce", stone: "#c9d1d6", wall: "#eef1f3", panel: "#f4f6f7", trunk: "#c0c8cd", leaves: "#b9c2c8", leavesLight: "#cfd6da", far: "#b3bdc3", accent: "#12a9c0", water: "#9fc9d6", door: "#dbe2e6", glow: false },
        tower:   { skyTop: "#0b0912", skyBottom: "#221a33", ground: "#3a3a44", grass: "#5b5b6b", stone: "#4a4a52", wall: "#5a5a66", panel: "#d9dde0", trunk: "#3a3a44", leaves: "#2c2c3a", leavesLight: "#3b3b4d", far: "#151222", accent: "#e0c04b", water: "#1c2436", door: "#2a2a30", glow: true },
        relay:   { skyTop: "#050a16", skyBottom: "#0f1e3a", ground: "#2b3340", grass: "#3e7ea8", stone: "#3a4250", wall: "#4a5262", panel: "#d9dde0", trunk: "#2b3340", leaves: "#1f4a6a", leavesLight: "#2c6a90", far: "#0a1426", accent: "#4bd0e0", water: "#12304a", door: "#2a2a30", glow: true },
        foundry: { skyTop: "#120808", skyBottom: "#2a1010", ground: "#3a2020", grass: "#8a3a2a", stone: "#4a3a3a", wall: "#5a4444", panel: "#d9dde0", trunk: "#3a2020", leaves: "#4a2a1a", leavesLight: "#6a3a22", far: "#1c0c0c", accent: "#ff8a4b", water: "#3a1a1a", door: "#2a2a30", glow: true },
        cable:   { skyTop: "#e4ecf3", skyBottom: "#c3d3e2", ground: "#f2f5f8", grass: "#dbe4ec", stone: "#c9d1d6", wall: "#f4f7fa", panel: "#eef2f6", trunk: "#c0c8cd", leaves: "#b9c2c8", leavesLight: "#cfd6da", far: "#b8c6d4", accent: "#2f9be8", water: "#8fd0ff", door: "#dbe2e6", glow: false },
        desk:    { skyTop: "#2b2f36", skyBottom: "#4a4f58", ground: "#8a5a32", grass: "#a56d3c", stone: "#e8e8ea", wall: "#6b4a2b", panel: "#f4f4f4", trunk: "#6b4a2b", leaves: "#3a3a44", leavesLight: "#4a4a55", far: "#3a3e46", accent: "#4bd0e0", water: "#3a3a44", door: "#2a2a30", glow: false },
        editor:  { skyTop: "#1e1e1e", skyBottom: "#232326", ground: "#2d2d30", grass: "#3c3c41", stone: "#3a3d41", wall: "#2d2d30", panel: "#2b2b2f", trunk: "#3c3c41", leaves: "#264f78", leavesLight: "#3a6ea0", far: "#2a2a2e", accent: "#4ec9b0", water: "#264f78", door: "#3c3c41", glow: false },
        obelisk: { skyTop: "#dfe7ee", skyBottom: "#f7f9fb", ground: "#e6e9ec", grass: "#d3d9de", stone: "#d3d9de", wall: "#eef1f3", panel: "#f4f6f7", trunk: "#c0c8cd", leaves: "#c9d1d6", leavesLight: "#dfe4e8", far: "#cdd5dc", accent: "#ffffff", water: "#c3d3e2", door: "#dbe2e6", glow: false }
    };

    const theme = THEMES[LEVEL.theme] || THEMES.forest;


    /* -----------------------------------------------------
       DOM
    ----------------------------------------------------- */

    const gameWindow = document.getElementById("game-window");
    const canvas = document.getElementById("game-canvas");
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = false;

    const hudTimer = document.getElementById("hud-timer");
    const hudHearts = document.getElementById("hud-hearts");
    const hudObjective = document.getElementById("hud-objective");
    const inventoryElement = document.getElementById("game-inventory");
    const toastElement = document.getElementById("game-toast");

    const overlayLesson = document.getElementById("overlay-lesson");
    const overlayDialogue = document.getElementById("overlay-dialogue");
    const overlayChallenge = document.getElementById("overlay-challenge");
    const overlayResult = document.getElementById("overlay-result");

    const dialogueName = document.getElementById("dialogue-name");
    const dialogueText = document.getElementById("dialogue-text");

    const challengeLabel = document.getElementById("challenge-label");
    const challengePrompt = document.getElementById("challenge-prompt");
    const challengeBody = document.getElementById("challenge-body");
    const challengeFeedback = document.getElementById("challenge-feedback");
    const challengeHints = document.getElementById("challenge-hints");
    const buttonSubmit = document.getElementById("btn-submit");
    const buttonHint = document.getElementById("btn-hint");
    const buttonChallengeClose = document.getElementById("btn-challenge-close");

    const resultLabel = document.getElementById("result-label");
    const resultTitle = document.getElementById("result-title");
    const resultText = document.getElementById("result-text");
    const resultCode = document.getElementById("result-code");
    const resultStats = document.getElementById("result-stats");
    const resultActions = document.getElementById("result-actions");

    const buttonStart = document.getElementById("btn-start");
    const buttonFullscreen = document.getElementById("fullscreen-btn");

    const SLOT_COUNT = inventoryElement.querySelectorAll(".inv-slot").length;


    /* -----------------------------------------------------
       SMALL HELPERS (DOM built with textContent - no HTML injection)
    ----------------------------------------------------- */

    function element(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function clear(node) {
        while (node.firstChild) node.removeChild(node.firstChild);
    }

    function formatTime(seconds) {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
    }

    function setObjective(text) {
        hudObjective.textContent = text;
    }

    let toastTimer = null;

    function toast(text) {
        toastElement.textContent = text;
        toastElement.classList.remove("hidden");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toastElement.classList.add("hidden"), 2200);
    }

    function overlaps(a, b) {
        return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
    }


    /* -----------------------------------------------------
       MAP + ENTITIES
    ----------------------------------------------------- */

    const rows = LEVEL.map;
    const MAP_H = rows.length;
    const MAP_W = rows[0].length;

    const tiles = [];
    const entities = [];
    const enemies = [];
    const doorCells = [];
    const lockedCells = [];
    const tileChanges = [];      // [tx, ty, ch] - replayed when a checkpoint is restored
    let spawn = { x: 2 * TILE, y: 8 * TILE };
    let doctorLine = 0;
    let bugLabel = 0;

    function nextBug() {
        const list = LEVEL.bugs && LEVEL.bugs.length ? LEVEL.bugs : [{ name: "BUG", fact: "" }];
        const entry = list[bugLabel % list.length];
        bugLabel += 1;
        return entry;
    }

    for (let y = 0; y < MAP_H; y++) {
        tiles[y] = [];
        for (let x = 0; x < MAP_W; x++) {
            const cell = rows[y][x];
            let tile = ".";
            const px = x * TILE, py = y * TILE;

            switch (cell) {
                case "#": case "S": case "W": case "T": case "L": case "G": case "V": case "U": case "A": case "~": case "%":
                    tile = cell;
                    break;
                case "z":
                    enemies.push(makeEnemy("sniffer", px + 2, py, 12, 16));
                    break;
                case "m":
                    entities.push({ type: "mentorbot", name: "MENTOR BOT", x: px + 2, y: py, w: 12, h: 16, tip: 0 });
                    break;
                case "O":
                    entities.push({ type: "obelisk", name: "OBELISK", x: px - 8, y: py - 80, w: 32, h: 96 });
                    break;
                case "@":
                    entities.push({ type: "button", name: "BUTTON", x: px, y: py, w: 16, h: 16, pressed: false });
                    break;
                case "D":
                    tile = "D";
                    doorCells.push({ x: x, y: y });
                    break;
                case "k":
                    tile = "k";
                    lockedCells.push({ x: x, y: y });
                    break;
                case "[": {
                    tile = "[";
                    const label = nextBug();
                    entities.push({ type: "cage", x: px, y: py, w: 16, h: 16, tx: x, ty: y, label: label, broken: false });
                    break;
                }
                case "!":
                    entities.push({ type: "wire", x: px, y: py, w: 16, h: 16 });
                    break;
                case "v":
                    entities.push({ type: "vent", name: "VENT", x: px, y: py, w: 16, h: 16 });
                    break;
                case "P":
                    spawn = { x: px + 4, y: py + 1 };
                    break;
                case "N":
                    entities.push({ type: "npc", name: GUIDE, x: px, y: py, w: 16, h: 16 });
                    break;
                case "c": {
                    const doctor = makeEnemy("hostile", px + 2, py, 12, 16);
                    doctor.carries = ITEM_CODE;
                    doctor.hp = doctor.maxHp = 4;
                    enemies.push(doctor);
                    break;
                }
                case "b": {
                    const bug = makeEnemy("bug", px + 3, py + 10, 10, 6);
                    bug.label = nextBug();
                    enemies.push(bug);
                    break;
                }
                case "Y":
                    enemies.push(makeEnemy("vex", px + 1, py - 2, 14, 18));
                    break;
                case "R":
                    enemies.push(makeEnemy("brain", px - 12, py, 40, 24));
                    break;
                case "n":
                    entities.push({ type: "doctor", name: "DOCTOR", x: px + 2, y: py, w: 12, h: 16, line: doctorLine++ });
                    break;
                case "B":
                    entities.push({ type: "sign", name: "SIGN", x: px, y: py, w: 16, h: 16 });
                    break;
                case "C":
                    entities.push({ type: "terminal", name: "TERMINAL", x: px, y: py, w: 16, h: 16 });
                    break;
                case "I":
                    entities.push({ type: "item", item: ITEM_CHIP, x: px + 4, y: py + 6, w: 8, h: 8, taken: false });
                    break;
                case "Q":
                    entities.push({ type: "item", item: ITEM_DAGGER, x: px + 3, y: py + 6, w: 10, h: 8, taken: false });
                    break;
                case "K":
                    entities.push({ type: "item", item: ITEM_CANDY, x: px + 4, y: py + 6, w: 8, h: 8, taken: false });
                    break;
                case "X":
                    entities.push({ type: "exit", name: "EXIT", x: px, y: py - TILE, w: 16, h: 32 });
                    break;
                case "s":
                    enemies.push(makeEnemy("snake", px + 1, py + 8, 14, 8));
                    break;
                case "h":
                    enemies.push(makeEnemy("hostile", px + 2, py, 12, 16));
                    break;
                case "M":
                    enemies.push(makeEnemy("boss", px - 12, py + TILE - 24, 40, 24));
                    break;
            }
            tiles[y][x] = tile;
        }
    }

    function makeEnemy(type, x, y, w, h) {
        const hp = ENEMY_HP[type] || 2;
        return {
            type: type, x: x, y: y, w: w, h: h, spawnX: x, spawnY: y,
            vx: 0, vy: 0, dir: -1, onGround: false,
            hp: hp, maxHp: hp, alive: true, hitFlash: 0, stun: 0,
            state: type === "vex" ? "chase" : "charge", timer: 0, shots: 0
        };
    }

    function setTile(tx, ty, ch) {
        tiles[ty][tx] = ch;
        tileChanges.push([tx, ty, ch]);
    }

    // Doors are two tiles tall with air above them; without a frame the
    // player could simply jump over a closed door and skip the terminal.
    function applyDoorFrames() {
        const all = doorCells.concat(lockedCells);
        const columns = new Set(all.map((c) => c.x));
        columns.forEach((tx) => {
            const stack = all.filter((c) => c.x === tx);
            // Only upright doors (two tiles stacked) get a frame; a trapdoor
            // lying in the floor is walked over, not jumped over.
            if (stack.length < 2) return;
            let ty = Math.min.apply(null, stack.map((c) => c.y)) - 1;
            while (ty >= 0 && tiles[ty][tx] === ".") {
                tiles[ty][tx] = "F";
                ty -= 1;
            }
        });
    }

    // Static characters drop to the nearest floor so map authors can
    // place them anywhere in a column.
    function settle(body) {
        let guard = 0;
        while (!rectHitsSolid(body.x, body.y + body.h, body.w, 1) && body.y < MAP_H * TILE && guard < 200) {
            body.y += 1;
            guard += 1;
        }
    }

    entities.forEach((entity) => {
        if (["doctor", "sign", "terminal", "mentorbot", "button", "obelisk"].includes(entity.type)) settle(entity);
    });

    enemies.forEach((enemy) => {
        if (BOSS_TYPES.includes(enemy.type)) {
            settle(enemy);
            enemy.spawnY = enemy.y;
        }
    });

    if (doorCells.length) {
        const minX = Math.min.apply(null, doorCells.map((c) => c.x));
        const maxX = Math.max.apply(null, doorCells.map((c) => c.x));
        const minY = Math.min.apply(null, doorCells.map((c) => c.y));
        const maxY = Math.max.apply(null, doorCells.map((c) => c.y));
        entities.push({
            type: "door", name: "DOOR",
            x: minX * TILE, y: minY * TILE,
            w: (maxX - minX + 1) * TILE, h: (maxY - minY + 1) * TILE,
            passed: false
        });
    }

    // Locked doors: one entity per column of 'k' tiles, opened with a DOOR CODE.
    const lockdoors = [];
    lockedCells.sort((a, b) => a.x - b.x || a.y - b.y).forEach((cell) => {
        let group = lockdoors.find((d) => d.tx === cell.x);
        if (!group) {
            group = { type: "lockdoor", name: "LOCKED DOOR", tx: cell.x, cells: [], open: false, passed: false };
            lockdoors.push(group);
        }
        group.cells.push(cell);
    });
    lockdoors.forEach((door) => {
        const minY = Math.min.apply(null, door.cells.map((c) => c.y));
        const maxY = Math.max.apply(null, door.cells.map((c) => c.y));
        door.x = door.tx * TILE;
        door.y = minY * TILE;
        door.w = TILE;
        door.h = (maxY - minY + 1) * TILE;
        entities.push(door);
    });

    applyDoorFrames();

    function isSolid(tx, ty) {
        if (tx < 0 || tx >= MAP_W) return true;
        if (ty < 0) return false;
        if (ty >= MAP_H) return true;
        const t = tiles[ty][tx];
        if (t === "D") return !state.doorOpen;
        return t === "#" || t === "S" || t === "W" || t === "G" || t === "V" || t === "~" || t === "[" || t === "k" || t === "F";
    }

    function rectHitsSolid(x, y, w, h) {
        const left = Math.floor(x / TILE);
        const right = Math.floor((x + w - 0.01) / TILE);
        const top = Math.floor(y / TILE);
        const bottom = Math.floor((y + h - 0.01) / TILE);

        for (let ty = top; ty <= bottom; ty++) {
            for (let tx = left; tx <= right; tx++) {
                if (isSolid(tx, ty)) return true;
            }
        }
        return false;
    }


    /* -----------------------------------------------------
       STATE
    ----------------------------------------------------- */

    const state = {
        phase: "lesson",         // lesson, intro, dialogue, play, challenge, result, finale, complete
        doorOpen: doorCells.length === 0,   // levels without a door tile are open from the start
        solved: false,
        metByte: false,
        bossDefeated: enemies.every((e) => !BOSS_TYPES.includes(e.type)),
        inventory: new Array(SLOT_COUNT).fill(null),
        selectedSlot: 0,
        hintIndex: 0,
        revealedHints: [],       // hints bought with chips stay visible all level
        flash: 0,
        timerStart: null,
        finalElapsed: null,
        result: null,
        dialogue: null,
        time: 0,
        lastNoEffect: 0,
        cagesBroken: false,
        lightsOn: !LEVEL.dark,
        darkness: 0,
        decals: [],              // blood splats where bugs died
        drops: [],               // items dropped by enemies [{item, x, y, taken}]
        checkpoint: null,        // last door save (in memory; also on the server)
        finishing: false,
        finale: null,            // {t} once the brain is dead
        cutscene: null,          // {t, flashed, done} once the obelisk button is pressed
        kills: {},               // enemies defeated since the last report to the server
        lastSafe: null,          // last spot the player stood on solid ground
        codeProgress: 0          // lines of LEVEL.code_lines revealed on the monitor
    };

    const player = {
        x: spawn.x, y: spawn.y, w: 8, h: 15,
        vx: 0, vy: 0, onGround: false,
        facing: 1, frame: 0, walkTime: 0,
        hp: MAX_HP, invuln: 0, attackTimer: 0, attackCooldown: 0
    };

    const camera = { x: 0 };
    const particles = [];
    const projectiles = [];


    /* -----------------------------------------------------
       INPUT
    ----------------------------------------------------- */

    const keys = {};

    function typingInField() {
        const active = document.activeElement;
        return active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA");
    }

    document.addEventListener("keydown", function (event) {

        if (typingInField()) return;

        const key = event.key.toLowerCase();

        if (key === "m" && window.academyAudio) {
            academyAudio.toggle();
            return;
        }

        if (state.phase === "intro") {
            skipIntro = true;
            return;
        }

        if (state.phase === "dialogue" && (key === "e" || key === "enter" || key === " ")) {
            event.preventDefault();
            advanceDialogue();
            return;
        }

        if (state.phase !== "play") return;

        if (key === " " || key === "arrowup" || key === "arrowdown") {
            event.preventDefault();
        }

        if (key === "e") { interact(); return; }
        if (key === "f") { useItem(); return; }
        if (key === "q") { dropSelectedItem(); return; }

        if (key >= "1" && key <= String(SLOT_COUNT)) {
            state.selectedSlot = Number(key) - 1;
            renderInventory();
            return;
        }

        keys[key] = true;
    });

    document.addEventListener("keyup", function (event) {
        keys[event.key.toLowerCase()] = false;
    });

    gameWindow.addEventListener("mousedown", function () {
        if (!typingInField()) gameWindow.focus();
    });

    canvas.addEventListener("click", function () {
        if (state.phase === "intro") { skipIntro = true; return; }
        if (state.phase === "play") useItem();
    });


    /* -----------------------------------------------------
       BANTER
       Level lines come first; after that a shuffled pool for the
       level's theme, never repeating the line just heard.
    ----------------------------------------------------- */

    const banter = { order: {}, index: {}, last: {} };

    function shuffled(list) {
        const copy = list.slice();
        for (let i = copy.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [copy[i], copy[j]] = [copy[j], copy[i]];
        }
        return copy;
    }

    function nextBanter(pool, key) {
        if (!pool || !pool.length) return "...";
        if (!banter.order[key] || banter.order[key].length !== pool.length) {
            banter.order[key] = shuffled(pool);
            banter.index[key] = 0;
        }
        const order = banter.order[key];
        let line = order[banter.index[key] % order.length];
        banter.index[key] += 1;
        if (line === banter.last[key] && order.length > 1) {
            line = order[banter.index[key] % order.length];
            banter.index[key] += 1;
        }
        banter.last[key] = line;
        return line;
    }

    function doctorSpeech(doctor) {
        const own = LEVEL.npcs || [];
        doctor.said = (doctor.said || 0) + 1;

        // The first chat is the level's own line for this doctor.
        if (doctor.said === 1 && own.length) return own[doctor.line % own.length];

        const pool = (LEVEL.banter && LEVEL.banter.doctor) || [];
        if (!pool.length) return own.length ? own[(doctor.line + doctor.said - 1) % own.length] : "...";
        return nextBanter(pool, "doctor");
    }


    /* -----------------------------------------------------
       DIALOGUE
    ----------------------------------------------------- */

    function startDialogue(name, pages, done) {
        state.dialogue = { name: name, pages: pages, index: 0, done: done };
        state.phase = "dialogue";
        dialogueName.textContent = name;
        dialogueText.textContent = pages[0];
        overlayDialogue.classList.remove("hidden");
        keys.a = keys.d = keys.w = keys[" "] = false;
    }

    function advanceDialogue() {
        const d = state.dialogue;
        if (!d) return;

        d.index += 1;

        if (d.index < d.pages.length) {
            dialogueText.textContent = d.pages[d.index];
            return;
        }

        overlayDialogue.classList.add("hidden");
        state.dialogue = null;
        state.phase = "play";

        if (d.done) d.done();
    }

    overlayDialogue.addEventListener("click", advanceDialogue);


    /* -----------------------------------------------------
       INVENTORY + ITEMS
    ----------------------------------------------------- */

    function addItem(name) {
        const free = state.inventory.indexOf(null);
        if (free === -1) return false;
        state.inventory[free] = name;
        renderInventory();
        return true;
    }

    function takeItem(name) {
        const index = state.inventory.indexOf(name);
        if (index === -1) return false;
        state.inventory[index] = null;
        renderInventory();
        return true;
    }

    function countItem(name) {
        return state.inventory.filter((item) => item === name).length;
    }

    function renderInventory() {
        const slots = inventoryElement.querySelectorAll(".inv-slot");
        slots.forEach((slot, index) => {
            slot.classList.toggle("inv-selected", index === state.selectedSlot);
            const label = slot.querySelector(".inv-item");
            label.textContent = state.inventory[index] || "";
            slot.classList.toggle("inv-filled", !!state.inventory[index]);
        });
    }

    function renderHearts() {
        clear(hudHearts);
        for (let i = 0; i < MAX_HP; i++) {
            hudHearts.appendChild(element("span", i < player.hp ? "heart-full" : "heart-empty", i < player.hp ? "♥" : "♡"));
        }
    }

    function eatCandy() {
        if (countItem(ITEM_CANDY) === 0) return false;
        if (player.hp >= MAX_HP) {
            toast("You're at full health. Save the candy.");
            return true;
        }
        takeItem(ITEM_CANDY);
        player.hp = Math.min(MAX_HP, player.hp + CANDY_HEAL);
        renderHearts();
        burst(player.x + 4, player.y + 4, "#ff4fa3", 12);
        toast("Candy eaten. +" + CANDY_HEAL + " health");
        return true;
    }

    function useItem() {
        if (state.phase !== "play") return;

        const item = state.inventory[state.selectedSlot];

        if (item === ITEM_DAGGER || item === ITEM_SWORD) {
            swingWeapon(item);
        } else if (item === ITEM_CANDY) {
            eatCandy();
        } else if (item === ITEM_CHIP) {
            toast("Hint chips are used at a terminal.");
        } else if (item === ITEM_CODE) {
            toast("Door codes are used with E at a locked door.");
        } else if (item === ITEM_KEY) {
            toast("The vent key is used with E at the vent.");
        } else if (item === null && (countItem(ITEM_SWORD) || countItem(ITEM_DAGGER))) {
            // Swinging from an empty slot still attacks - nobody wants to die fumbling for slot 1.
            swingWeapon(countItem(ITEM_SWORD) ? ITEM_SWORD : ITEM_DAGGER);
        } else {
            toast("Slot " + (state.selectedSlot + 1) + " is empty. Press 1-" + SLOT_COUNT + " to pick a slot.");
        }
    }


    // Q: put the selected item on the ground in front of the player. It is
    // a normal pickup again once the player has stepped off it.
    // (dropItem(item, x, y) below is the enemy-loot version.)
    function dropSelectedItem() {
        if (state.phase !== "play") return;

        const item = state.inventory[state.selectedSlot];

        if (!item) {
            toast("Slot " + (state.selectedSlot + 1) + " is empty - nothing to drop.");
            return;
        }

        state.inventory[state.selectedSlot] = null;
        renderInventory();

        if (item === ITEM_SWORD || item === ITEM_DAGGER) {
            player.weapon = state.inventory.includes(ITEM_SWORD) ? ITEM_SWORD : ITEM_DAGGER;
        }

        const entity = {
            type: "item", item: item, w: 10, h: 8, taken: false, dropped: true,
            x: Math.round(player.facing > 0 ? player.x + player.w + 3 : player.x - 13),
            y: Math.round(player.y + player.h - 8),
            cooldown: 45
        };
        entity.x = Math.max(0, Math.min(MAP_W * TILE - entity.w, entity.x));
        if (rectHitsSolid(entity.x, entity.y, entity.w, entity.h)) entity.x = Math.round(player.x);
        settle(entity);

        entities.push(entity);
        state.drops.push(entity);
        burst(entity.x + 5, entity.y + 4, theme.accent, 6);
        toast(item + " dropped. Walk over it to pick it back up.");
    }


    /* -----------------------------------------------------
       COMBAT
    ----------------------------------------------------- */

    function currentWeapon() {
        return WEAPONS[player.weapon] || WEAPONS[ITEM_DAGGER];
    }

    function attackBox() {
        const reach = currentWeapon().reach;
        return {
            x: player.facing > 0 ? player.x + player.w : player.x - reach,
            y: player.y + 2, w: reach, h: 12
        };
    }

    function swingWeapon(item) {
        if (player.attackCooldown > 0) return;

        player.weapon = item;
        const weapon = currentWeapon();
        player.attackTimer = 8;
        player.attackCooldown = weapon.cooldown;
        if (window.academyAudio) academyAudio.sfx("slash");

        const box = attackBox();

        // Vines
        const left = Math.floor(box.x / TILE), right = Math.floor((box.x + box.w - 1) / TILE);
        const top = Math.floor(box.y / TILE), bottom = Math.floor((box.y + box.h - 1) / TILE);
        let cut = false;
        for (let ty = top; ty <= bottom; ty++) {
            for (let tx = left; tx <= right; tx++) {
                if (tiles[ty] && tiles[ty][tx] === "V") {
                    setTile(tx, ty, ".");
                    cut = true;
                    burst(tx * TILE + 8, ty * TILE + 8, "#5fbf4a", 10);
                }
            }
        }
        if (cut) toast("Vines cut.");

        enemies.forEach((enemy) => {
            if (enemy.alive && overlaps(box, enemy)) hitEnemy(enemy, weapon.damage);
        });
    }

    function hitEnemy(enemy, damage) {
        damage = damage || 1;

        if ((enemy.type === "boss" || enemy.type === "vex") && enemy.state !== "rest") {
            if (state.time - state.lastNoEffect > 0.8) {
                toast(enemy.type === "vex" ? "No effect. Hit him while he is STAGGERED." : "No effect. Strike while it rests.");
                state.lastNoEffect = state.time;
            }
            burst(enemy.x + enemy.w / 2, enemy.y + 8, "#ffffff", 4);
            return;
        }

        if (enemy.type === "brain") {
            if (state.time - state.lastNoEffect > 0.8) {
                toast("Blades do nothing. Get on top of it.");
                state.lastNoEffect = state.time;
            }
            return;
        }

        enemy.hp -= damage;
        enemy.hitFlash = 10;
        enemy.stun = STUN_FRAMES;
        burst(enemy.x + enemy.w / 2, enemy.y + enemy.h / 2, "#ffffff", 8);

        if (!BOSS_TYPES.includes(enemy.type)) {
            enemy.x += player.facing * 8;
        }

        if (enemy.hp <= 0) killEnemy(enemy);
    }

    function dropItem(item, x, y) {
        const entity = { type: "item", item: item, x: x, y: y, w: 10, h: 8, taken: false, dropped: true };
        settle(entity);
        entities.push(entity);
        state.drops.push(entity);
        burst(x + 5, y + 4, "#ffd700", 14);
    }

    function killEnemy(enemy) {
        enemy.alive = false;
        state.kills[enemy.type] = (state.kills[enemy.type] || 0) + 1;
        if (BOSS_TYPES.includes(enemy.type) && window.academyAudio) academyAudio.bossEnd();
        burst(enemy.x + enemy.w / 2, enemy.y + enemy.h / 2, enemy.type === "bug" ? "#7a1f1f" : theme.accent, 24);

        if (enemy.type === "boss") {
            state.bossDefeated = true;
            projectiles.length = 0;
            toast("The specimen is down. The console flickers on.");
            setObjective(LEVEL.goal);
        }

        else if (enemy.type === "vex") {
            state.bossDefeated = true;
            projectiles.length = 0;
            dropItem(ITEM_KEY, enemy.x + 2, enemy.y + 6);
            toast("Dr. Vex is down. He dropped something.");
            setObjective("Take the VENT KEY and reach the vent (E)");
        }

        else if (enemy.type === "brain") {
            state.bossDefeated = true;
            projectiles.length = 0;
            state.finale = { t: 0, submitted: false };
            state.phase = "finale";
            overlayDialogue.classList.add("hidden");
        }

        else if (enemy.type === "bug") {
            const floorY = enemy.y + enemy.h;
            state.decals.push({ x: enemy.x + enemy.w / 2, y: floorY, seed: Math.floor(Math.random() * 100) });
            if (enemy.label && enemy.label.name) {
                toast(enemy.label.name + " squashed" + (enemy.label.fact ? " - " + enemy.label.fact : ""));
            }
            checkBugsCleared();
        }

        if (enemy.carries) {
            dropItem(enemy.carries, enemy.x + 1, enemy.y + 8);
            enemy.carries = null;
        }
    }

    function bugsRemaining() {
        return enemies.filter((e) => e.type === "bug" && e.alive).length;
    }

    function checkBugsCleared() {
        if (bugsRemaining() > 0) {
            if (LEVEL.dark || LEVEL.door_by_bugs) setObjective(bugsRemaining() + " bug" + (bugsRemaining() === 1 ? "" : "s") + " left");
            return;
        }

        if (LEVEL.dark && !state.lightsOn) {
            state.lightsOn = true;
            state.flash = 8;
            toast("The lights come back on.");
        }

        if (LEVEL.door_by_bugs && !state.doorOpen && state.cagesBroken) {
            openDoor();
            state.solved = true;
            toast("The lock releases.");
        }

        if (LEVEL.dark || LEVEL.door_by_bugs) setObjective(LEVEL.goal);
    }

    function breakCages(quiet) {
        if (state.cagesBroken) return;
        state.cagesBroken = true;

        entities.forEach((cage) => {
            if (cage.type !== "cage") return;
            cage.broken = true;
            setTile(cage.tx, cage.ty, "]");
            if (!quiet) burst(cage.x + 8, cage.y + 8, "#c0c8cd", 14);
            // Each cage owns one bug; a checkpoint restore reuses it so
            // enemy indices stay stable.
            if (!cage.bug) {
                cage.bug = makeEnemy("bug", cage.x + 3, cage.y + 10, 10, 6);
                cage.bug.label = cage.label;
                enemies.push(cage.bug);
            }
            const bug = cage.bug;
            bug.alive = true;
            bug.hp = bug.maxHp;
            bug.x = bug.spawnX;
            bug.y = bug.spawnY;
            bug.dir = player.x < bug.x ? -1 : 1;
        });

        if (quiet) return;
        state.flash = 6;
        toast("The cages burst open!");
        setObjective(bugsRemaining() + " bugs loose - kill them all");
    }

    function damagePlayer(amount, source) {
        if (player.invuln > 0 || state.phase !== "play") return;

        player.hp -= amount;
        player.invuln = 60;

        const sourceCenter = source ? source.x + source.w / 2 : player.x + player.facing * 10;
        const dir = player.x + player.w / 2 < sourceCenter ? -1 : 1;
        player.vx = dir * 2.6;
        player.vy = -2.8;
        player.onGround = false;

        burst(player.x + 4, player.y + 6, "#ff4d5e", 10);
        renderHearts();

        if (player.hp <= 0) respawn();
    }

    function resetEnemies() {
        enemies.forEach((enemy) => {
            enemy.alive = true;
            enemy.hp = enemy.maxHp;
            enemy.x = enemy.spawnX;
            enemy.y = enemy.spawnY;
            enemy.vx = 0;
            enemy.vy = 0;
            enemy.state = enemy.type === "vex" ? "chase" : "charge";
            enemy.timer = 0;
            enemy.shots = 0;
            enemy.stun = 0;
        });
        projectiles.length = 0;
        if (enemies.some((e) => BOSS_TYPES.includes(e.type))) state.bossDefeated = false;
    }

    function respawn() {
        projectiles.length = 0;

        if (state.checkpoint) {
            restoreCheckpoint(state.checkpoint);
            player.hp = MAX_HP;
            player.invuln = 90;
            renderHearts();
            startDialogue("—", ["You were knocked out. Reloaded at the last door you passed."], null);
            return;
        }

        player.x = spawn.x;
        player.y = spawn.y;
        player.vx = 0;
        player.vy = 0;
        player.hp = MAX_HP;
        player.invuln = 90;

        resetEnemies();

        renderHearts();
        startDialogue("—", ["You were knocked out. The sim reloads you at the entrance."], null);
    }


    /* -----------------------------------------------------
       CHECKPOINTS (saved when the player passes a door)
    ----------------------------------------------------- */

    function snapshot() {
        return {
            x: Math.round(player.x), y: Math.round(player.y), facing: player.facing,
            hp: player.hp,
            inventory: state.inventory.slice(),
            selectedSlot: state.selectedSlot,
            doorOpen: state.doorOpen,
            solved: state.solved,
            metByte: state.metByte,
            cagesBroken: state.cagesBroken,
            lightsOn: state.lightsOn,
            bossDefeated: state.bossDefeated,
            hintIndex: state.hintIndex,
            revealedHints: state.revealedHints.slice(),
            lockdoors: lockdoors.map((d) => d.open),
            passed: entities.filter((e) => e.type === "door" || e.type === "lockdoor").map((e) => !!e.passed),
            dead: enemies.map((e) => !e.alive),
            taken: entities.filter((e) => e.type === "item" && !e.dropped).map((e) => !!e.taken),
            drops: state.drops.map((d) => ({ item: d.item, x: Math.round(d.x), y: Math.round(d.y), taken: !!d.taken })),
            decals: state.decals.slice(0, 40),
            tiles: tileChanges.slice(0, 400)
        };
    }

    function restoreCheckpoint(data) {
        if (!data) return;

        // Rebuild the world from the level's initial state first.
        resetEnemies();
        entities.forEach((e) => { if (e.type === "item" && !e.dropped) e.taken = false; });
        state.drops.forEach((d) => { const i = entities.indexOf(d); if (i >= 0) entities.splice(i, 1); });
        state.drops = [];
        for (let y = 0; y < MAP_H; y++) for (let x = 0; x < MAP_W; x++) {
            const original = rows[y][x];
            tiles[y][x] = "#SWTLGVUA~D[k".includes(original) ? original : ".";
        }
        applyDoorFrames();
        tileChanges.length = 0;
        entities.forEach((cage) => { if (cage.type === "cage") cage.broken = false; });
        state.cagesBroken = false;

        if (data.cagesBroken) breakCages(true);

        (data.tiles || []).forEach(([tx, ty, ch]) => {
            if (tiles[ty] && tiles[ty][tx] !== undefined) setTile(tx, ty, ch);
        });

        lockdoors.forEach((d, i) => { d.open = !!(data.lockdoors && data.lockdoors[i]); });
        entities.filter((e) => e.type === "door" || e.type === "lockdoor").forEach((e, i) => { e.passed = !!(data.passed && data.passed[i]); });
        enemies.forEach((e, i) => { if (data.dead && data.dead[i]) e.alive = false; });
        entities.filter((e) => e.type === "item" && !e.dropped).forEach((e, i) => { e.taken = !!(data.taken && data.taken[i]); });
        (data.drops || []).forEach((d) => {
            const entity = { type: "item", item: d.item, x: d.x, y: d.y, w: 10, h: 8, taken: !!d.taken, dropped: true };
            entities.push(entity);
            state.drops.push(entity);
        });

        state.inventory = new Array(SLOT_COUNT).fill(null);
        (data.inventory || []).slice(0, SLOT_COUNT).forEach((item, i) => { state.inventory[i] = item || null; });
        state.selectedSlot = Math.min(SLOT_COUNT - 1, Math.max(0, data.selectedSlot | 0));
        state.doorOpen = !!data.doorOpen || doorCells.length === 0;
        state.solved = !!data.solved;
        state.metByte = !!data.metByte;
        state.lightsOn = !!data.lightsOn || !LEVEL.dark;
        state.bossDefeated = !!data.bossDefeated || enemies.every((e) => !BOSS_TYPES.includes(e.type) || !e.alive);
        state.hintIndex = data.hintIndex | 0;
        state.revealedHints = (data.revealedHints || []).slice();
        state.decals = (data.decals || []).slice();

        player.x = data.x;
        player.y = data.y;
        player.facing = data.facing === -1 ? -1 : 1;
        player.vx = 0;
        player.vy = 0;
        player.hp = Math.max(1, Math.min(MAX_HP, data.hp | 0));
        player.weapon = state.inventory.includes(ITEM_SWORD) ? ITEM_SWORD : ITEM_DAGGER;

        renderInventory();
        renderHearts();
        setObjective(state.doorOpen && state.solved ? "Go through the open door" : (state.metByte ? LEVEL.goal : "Find " + GUIDE + " and press E"));
    }

    let savingCheckpoint = false;

    async function saveCheckpoint() {
        const data = snapshot();
        state.checkpoint = data;
        if (savingCheckpoint) return;
        savingCheckpoint = true;
        try {
            await fetch("/api/level/checkpoint", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ course: LEVEL.course, level: LEVEL.number, state: data })
            });
            toast("Checkpoint saved.");
        } catch (error) {
            // The in-memory checkpoint still works for this session.
        } finally {
            savingCheckpoint = false;
        }
    }

    function checkDoorPasses() {
        entities.forEach((entity) => {
            if (entity.type !== "door" && entity.type !== "lockdoor") return;
            const open = entity.type === "door" ? state.doorOpen : entity.open;
            if (!open || entity.passed) return;
            // The exit door leads straight to the exit - nothing to save there.
            if (entity.type === "door" && entities.some((e) => e.type === "exit" && Math.abs(e.x - entity.x) < 64)) return;
            if (player.x > entity.x + entity.w + 2 && Math.abs(player.y - entity.y) < 40) {
                entity.passed = true;
                saveCheckpoint();
            }
        });
    }

    function burst(x, y, color, count) {
        for (let i = 0; i < count; i++) {
            particles.push({
                x: x, y: y,
                vx: (Math.random() - 0.5) * 2.4, vy: (Math.random() - 0.9) * 2.4,
                life: 20 + Math.random() * 25, color: color
            });
        }
    }


    /* -----------------------------------------------------
       INTERACTION
    ----------------------------------------------------- */

    // When two things are equally close, the one that advances the level wins.
    const INTERACT_PRIORITY = { terminal: 0, vent: 0, button: 0, npc: 1, mentorbot: 1, doctor: 2, sign: 3, obelisk: 4 };

    function nearestInteractable() {
        let best = null;
        let bestScore = Infinity;
        let door = null;

        entities.forEach((entity) => {
            if (entity.type === "item" || entity.type === "exit" || entity.type === "cage" || entity.type === "wire") return;

            const ex = entity.x + entity.w / 2;
            const px = player.x + player.w / 2;
            const dx = Math.abs(ex - px);

            const verticalOverlap =
                player.y < entity.y + entity.h + 8 &&
                player.y + player.h > entity.y - 8;

            if (entity.type === "door" || entity.type === "lockdoor") {
                // Doors only respond when nothing else is in reach.
                if (dx < INTERACT_RANGE + entity.w / 2 && verticalOverlap && (!door || dx < Math.abs(door.x + door.w / 2 - px))) door = entity;
                return;
            }

            const score = dx + (INTERACT_PRIORITY[entity.type] || 0) * 0.1;

            if (dx < INTERACT_RANGE && verticalOverlap && score < bestScore) {
                best = entity;
                bestScore = score;
            }
        });

        // An open exit door is the way out - it beats the terminal next to it.
        if (door && door.type === "door" && state.doorOpen) return door;
        // A locked door you can open beats a sign next to it.
        if (door && door.type === "lockdoor" && !door.open) return door;

        return best || door;
    }

    function interact() {
        const target = nearestInteractable();

        if (!target) {
            toast(countItem(ITEM_CANDY)
                ? "Nothing here. To eat candy, select its slot and press F."
                : "Nothing here.");
            return;
        }

        if (target.type === "npc") {
            const quips = (LEVEL.banter && LEVEL.banter.guide) || [];
            if (state.metByte && quips.length) {
                // The briefing was heard already: a quip instead of the same speech.
                startDialogue(GUIDE, [nextBanter(quips, "guide")], null);
                return;
            }
            startDialogue(GUIDE, LEVEL.dialogue.length ? LEVEL.dialogue : ["..."], function () {
                state.metByte = true;
                setObjective(LEVEL.boss && !state.bossDefeated ? (LEVEL.finale ? "Stomp the brain" : "Defeat the boss") : LEVEL.goal);
            });
        }

        else if (target.type === "doctor") {
            startDialogue("DOCTOR", [doctorSpeech(target)], null);
        }

        else if (target.type === "mentorbot") {
            // An in-world SecureMentor: a tip, then the real panel opens.
            const tips = LEVEL.npcs && LEVEL.npcs.length ? LEVEL.npcs : ["Ask me anything about the code you're looking at."];
            const tip = tips[target.tip % tips.length];
            target.tip += 1;
            startDialogue("MENTOR BOT", [tip, "Opening SecureMentor - ask it anything, it won't hand you answers."], function () {
                const panel = document.getElementById("mentor-panel");
                const button = document.getElementById("mentor-button");
                if (panel && button && panel.classList.contains("hidden")) button.click();
            });
        }

        else if (target.type === "button") {
            if (target.pressed) return;
            if (!LEVEL.obelisk) { toast("Nothing happens."); return; }
            target.pressed = true;
            startCutscene();
        }

        else if (target.type === "obelisk") {
            startDialogue("OBELISK", ["Smooth, white, warm to the touch. The button is at its base."], null);
        }

        else if (target.type === "sign") {
            startDialogue("SIGN", [LEVEL.sign || "The sign is blank."], null);
        }

        else if (target.type === "lockdoor") {
            if (target.open) return;
            if (takeItem(ITEM_CODE)) {
                target.open = true;
                target.cells.forEach((cell) => setTile(cell.x, cell.y, "o"));
                burst(target.x + 8, target.y + target.h / 2, "#4bd0e0", 16);
                toast("Door code accepted. The door slides open.");
            } else {
                startDialogue("LOCKED DOOR", ["A card reader blinks red. It wants a DOOR CODE - the doctors carry them."], null);
            }
        }

        else if (target.type === "vent") {
            if (countItem(ITEM_KEY)) {
                takeItem(ITEM_KEY);
                burst(target.x + 8, target.y + 8, theme.accent, 20);
                finishLevel();
            } else {
                startDialogue("VENT", ["A steel grille, bolted. It needs a key. Dr. Vex has it."], null);
            }
        }

        else if (target.type === "door") {
            if (state.doorOpen) {
                finishLevel();
                return;
            }
            if (LEVEL.door_by_bugs) {
                if (!state.cagesBroken) {
                    breakCages();
                } else {
                    startDialogue("DOOR", ["Sensor lock. " + bugsRemaining() + " specimen" + (bugsRemaining() === 1 ? "" : "s") + " still loose in the room."], null);
                }
                return;
            }
            startDialogue("DOOR", [LEVEL.gate ? "A firewall gate. The rulebook terminal beside it decides what passes." : "Sealed. The terminal beside it controls the lock."], null);
        }

        else if (target.type === "terminal") {
            if (state.solved) {
                startDialogue("TERMINAL", ["ACCESS GRANTED. The door is open - go through."], null);
            } else if (LEVEL.boss && !state.bossDefeated) {
                startDialogue("TERMINAL", ["OFFLINE while the specimen is loose."], null);
            } else {
                openChallenge();
            }
        }
    }


    /* -----------------------------------------------------
       CHALLENGE OVERLAY
    ----------------------------------------------------- */

    let challengeInput = null;
    let reviewSelection = { line: null, why: null };

    function openChallenge() {
        const challenge = LEVEL.challenge;

        state.phase = "challenge";
        keys.a = keys.d = keys.w = keys[" "] = false;

        challengeLabel.textContent = (challenge.label || "TERMINAL") + " · " + LEVEL.title.toUpperCase();
        challengePrompt.textContent = challenge.prompt;
        challengeFeedback.textContent = "";
        challengeFeedback.classList.remove("feedback-bad");
        clear(challengeBody);
        clear(challengeHints);
        state.revealedHints.forEach((text) => challengeHints.appendChild(element("p", "hint-line", "HINT: " + text)));
        reviewSelection = { line: null, why: null };

        buttonSubmit.classList.remove("hidden");

        if (challenge.type === "python_lines") buildPythonLines(challenge);
        else if (challenge.type === "text_answer") buildTextAnswer(challenge);
        else if (challenge.type === "mcq") buildChoices(challenge);
        else if (challenge.type === "code_review") buildCodeReview(challenge);
        else if (challenge.type === "fill_blank") buildFillBlank(challenge);
        else if (challenge.type === "order_code") buildOrderCode(challenge);
        else if (challenge.type === "swipe") buildSwipe(challenge);
        else if (challenge.type === "wires") buildWires(challenge);
        else if (challenge.type === "route_packets") buildRoute(challenge);
        else if (challenge.type === "ip_assign") buildIp(challenge);
        else if (challenge.type === "idea") buildIdea(challenge);
        else if (challenge.type === "language") buildLanguage(challenge);

        updateHintButton();
        overlayChallenge.classList.remove("hidden");
    }

    // Rearrange wires: click a device then a port (or drag the device onto
    // the port). Connections are drawn as lines between the two columns.
    function buildWires(challenge) {
        const board = element("div", "wire-board");
        const left = element("div", "wire-column");
        const right = element("div", "wire-column");
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("class", "wire-lines");
        const mapping = new Array(challenge.devices.length).fill(-1);
        let selected = null;
        const deviceButtons = [];
        const portButtons = [];

        function redraw() {
            while (svg.firstChild) svg.removeChild(svg.firstChild);
            const rect = board.getBoundingClientRect();
            svg.setAttribute("viewBox", "0 0 " + rect.width + " " + rect.height);
            svg.setAttribute("width", rect.width);
            svg.setAttribute("height", rect.height);
            mapping.forEach((port, i) => {
                deviceButtons[i].classList.toggle("wired", port >= 0);
                deviceButtons[i].classList.toggle("wire-selected", selected === i);
                if (port < 0) return;
                const a = deviceButtons[i].getBoundingClientRect();
                const b = portButtons[port].getBoundingClientRect();
                const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
                const x1 = a.right - rect.left, y1 = a.top + a.height / 2 - rect.top;
                const x2 = b.left - rect.left, y2 = b.top + b.height / 2 - rect.top;
                const mid = (x1 + x2) / 2;
                line.setAttribute("d", "M" + x1 + " " + y1 + " C" + mid + " " + y1 + " " + mid + " " + y2 + " " + x2 + " " + y2);
                line.setAttribute("class", "wire-line wire-" + (i % 4));
                svg.appendChild(line);
            });
            portButtons.forEach((b, p) => b.classList.toggle("wired", mapping.includes(p)));
        }

        function connect(device, port) {
            const other = mapping.indexOf(port);
            if (other >= 0 && other !== device) mapping[other] = -1;
            mapping[device] = port;
            selected = null;
            redraw();
        }

        challenge.devices.forEach((name, i) => {
            const button = element("button", "wire-node wire-device", name);
            button.type = "button";
            button.draggable = true;
            button.addEventListener("click", () => { selected = selected === i ? null : i; redraw(); });
            button.addEventListener("dragstart", (e) => { selected = i; e.dataTransfer.setData("text/plain", String(i)); redraw(); });
            deviceButtons.push(button);
            left.appendChild(button);
        });

        challenge.ports.forEach((name, p) => {
            const button = element("button", "wire-node wire-port", name);
            button.type = "button";
            button.addEventListener("click", () => { if (selected !== null) connect(selected, p); else toast("Pick a device first."); });
            button.addEventListener("dragover", (e) => e.preventDefault());
            button.addEventListener("drop", (e) => { e.preventDefault(); const i = Number(e.dataTransfer.getData("text/plain")); if (!isNaN(i)) connect(i, p); });
            portButtons.push(button);
            right.appendChild(button);
        });

        board.appendChild(left);
        board.appendChild(svg);
        board.appendChild(right);
        challengeBody.appendChild(element("p", "section-label", "DEVICES - click one, then click its port (or drag it there)"));
        challengeBody.appendChild(board);
        setTimeout(redraw, 30);
        window.addEventListener("resize", redraw);

        challengeInput = () => ({ map: mapping.slice() });
        buttonSubmit.textContent = "CONNECT";
    }

    // Packet delivery: drag packets from the tray onto machines (or click a
    // packet, then a machine).
    function buildRoute(challenge) {
        const mapping = new Array(challenge.packets.length).fill(-1);
        let selected = null;

        if (challenge.dns && Object.keys(challenge.dns).length) {
            const table = element("div", "dns-table");
            table.appendChild(element("p", "section-label", "DNS TABLE"));
            Object.keys(challenge.dns).forEach((name) => {
                table.appendChild(element("span", "dns-row", name + " = " + challenge.dns[name]));
            });
            challengeBody.appendChild(table);
        }

        const tray = element("div", "packet-tray");
        const machines = element("div", "machine-row");
        const packetChips = [];

        function render() {
            packetChips.forEach((chip, i) => {
                chip.classList.toggle("packet-selected", selected === i);
                const target = mapping[i] >= 0 ? machineBoxes[mapping[i]].querySelector(".machine-packets") : tray;
                if (chip.parentNode !== target) target.appendChild(chip);
            });
        }

        challenge.packets.forEach((packet, i) => {
            const chip = element("button", "packet-chip");
            chip.type = "button";
            chip.draggable = true;
            chip.appendChild(element("span", "packet-label", packet.label));
            chip.appendChild(element("span", "packet-to", "to: " + packet.to));
            chip.addEventListener("click", () => { selected = selected === i ? null : i; render(); });
            chip.addEventListener("dragstart", (e) => { selected = i; e.dataTransfer.setData("text/plain", String(i)); });
            packetChips.push(chip);
            tray.appendChild(chip);
        });

        const machineBoxes = challenge.machines.map((machine, m) => {
            const box = element("div", "machine-box");
            box.appendChild(element("strong", "machine-name", machine.name));
            box.appendChild(element("span", "machine-ip", machine.ip));
            box.appendChild(element("div", "machine-packets"));
            box.addEventListener("click", () => { if (selected !== null) { mapping[selected] = m; selected = null; render(); } });
            box.addEventListener("dragover", (e) => { e.preventDefault(); box.classList.add("drop-target"); });
            box.addEventListener("dragleave", () => box.classList.remove("drop-target"));
            box.addEventListener("drop", (e) => {
                e.preventDefault();
                box.classList.remove("drop-target");
                const i = Number(e.dataTransfer.getData("text/plain"));
                if (!isNaN(i)) { mapping[i] = m; selected = null; render(); }
            });
            machines.appendChild(box);
            return box;
        });

        tray.addEventListener("dragover", (e) => e.preventDefault());
        tray.addEventListener("drop", (e) => { e.preventDefault(); const i = Number(e.dataTransfer.getData("text/plain")); if (!isNaN(i)) { mapping[i] = -1; render(); } });

        challengeBody.appendChild(element("p", "section-label", "PACKETS - drag onto a machine (or click a packet, then a machine)"));
        challengeBody.appendChild(tray);
        challengeBody.appendChild(machines);

        challengeInput = () => ({ map: mapping.slice() });
        buttonSubmit.textContent = "DELIVER";
    }

    function buildIp(challenge) {
        const info = element("div", "ip-info");
        info.appendChild(element("span", "dns-row", "network: " + challenge.network + "x"));
        info.appendChild(element("span", "dns-row", "in use: " + challenge.taken.join("  ")));
        challengeBody.appendChild(info);

        const input = element("input", "challenge-text ip-input");
        input.type = "text";
        input.placeholder = challenge.placeholder || challenge.network + "?";
        input.autocomplete = "off";
        input.spellcheck = false;
        input.addEventListener("keydown", (e) => { if (e.key === "Enter") submitChallenge(); });
        challengeBody.appendChild(input);
        challengeInput = () => input.value;
        buttonSubmit.textContent = "ASSIGN";
        setTimeout(() => input.focus(), 50);
    }

    function buildIdea(challenge) {
        const form = element("div", "idea-form");
        const name = element("input", "challenge-text");
        name.placeholder = "Site name (e.g. Chess Club Hub)";
        name.maxLength = 60;
        const pitch = element("textarea", "challenge-code idea-pitch");
        pitch.placeholder = "One sentence: who is it for and what does it do?";
        pitch.maxLength = 300;
        pitch.rows = 2;
        const pages = [1, 2, 3].map((n) => {
            const input = element("input", "challenge-text");
            input.placeholder = "Page " + n + (n === 1 ? " (e.g. Home)" : "");
            input.maxLength = 40;
            return input;
        });
        form.appendChild(element("p", "section-label", "NAME"));
        form.appendChild(name);
        form.appendChild(element("p", "section-label", "WHAT IT DOES"));
        form.appendChild(pitch);
        form.appendChild(element("p", "section-label", "THREE PAGES"));
        const row = element("div", "idea-pages");
        pages.forEach((p) => row.appendChild(p));
        form.appendChild(row);
        challengeBody.appendChild(form);
        challengeInput = () => ({ name: name.value, pitch: pitch.value, pages: pages.map((p) => p.value) });
        buttonSubmit.textContent = "SAVE MY IDEA";
        setTimeout(() => name.focus(), 50);
    }

    function buildLanguage(challenge) {
        let chosen = null;
        const labels = { python: "PYTHON - the Academy's own language", javascript: "JAVASCRIPT - web pages and Node servers" };
        challenge.options.forEach((option) => {
            const button = element("button", "choice-button", labels[option] || option.toUpperCase());
            button.type = "button";
            button.addEventListener("click", () => {
                chosen = option;
                challengeBody.querySelectorAll(".choice-button").forEach((b) => b.classList.remove("choice-selected"));
                button.classList.add("choice-selected");
            });
            challengeBody.appendChild(button);
        });
        challengeInput = () => chosen;
        buttonSubmit.textContent = "CHOOSE";
    }

    // Tinder-style scam deck: one message at a time, SCAM or LEGIT, the
    // server judges each card and explains it; wrong cards come back
    // until the whole deck is clean.
    let swipeSession = 0;

    function buildSwipe(challenge) {
        const cards = challenge.cards;
        const answers = new Array(cards.length).fill(null);
        const results = new Array(cards.length).fill(null);
        const mySession = ++swipeSession;
        let order = cards.map((_, i) => i);
        let pos = 0;
        let busy = false;

        buttonSubmit.classList.add("hidden");

        const labels = challenge.labels || ["SCAM", "LEGIT"];
        const stage = element("div", "swipe-stage");
        const progress = element("p", "section-label swipe-progress", "");
        const card = element("div", "swipe-card");
        const verdict = element("div", "swipe-verdict hidden");
        const controls = element("div", "swipe-controls");
        const buttonScam = element("button", "swipe-button swipe-scam", labels[0]);
        const buttonLegit = element("button", "swipe-button swipe-legit", labels[1]);
        const buttonNext = element("button", "large-button swipe-next hidden", "NEXT MESSAGE");
        buttonScam.type = buttonLegit.type = buttonNext.type = "button";
        buttonScam.title = "Left arrow";
        buttonLegit.title = "Right arrow";
        controls.appendChild(buttonScam);
        controls.appendChild(buttonLegit);
        stage.appendChild(progress);
        stage.appendChild(card);
        stage.appendChild(verdict);
        stage.appendChild(controls);
        stage.appendChild(buttonNext);
        challengeBody.appendChild(stage);

        function showCard() {
            const i = order[pos];
            const data = cards[i];
            clear(card);
            clear(verdict);
            verdict.classList.add("hidden");
            card.className = "swipe-card swipe-deal" + (data.kind === "code" ? " swipe-codecard" : "");
            const kinds = { email: "EMAIL", sms: "TEXT MESSAGE", call: "PHONE CALL", code: "CODE REVIEW" };
            card.appendChild(element("span", "swipe-kind", kinds[data.kind] || data.kind.toUpperCase()));
            card.appendChild(element("p", "swipe-from", (data.kind === "call" ? "Caller: " : (data.kind === "code" ? "File: " : "From: ")) + data.from));
            if (data.subject) card.appendChild(element("p", "swipe-subject", data.subject));
            card.appendChild(element(data.kind === "code" ? "pre" : "p", data.kind === "code" ? "swipe-code" : "swipe-body", data.body));
            progress.textContent = "MESSAGE " + (pos + 1) + " OF " + order.length + (order.length < cards.length ? " · REDO" : "");
            buttonScam.disabled = buttonLegit.disabled = false;
            controls.classList.remove("hidden");
            buttonNext.classList.add("hidden");
        }

        async function choose(saidScam) {
            if (busy) return;
            busy = true;
            buttonScam.disabled = buttonLegit.disabled = true;
            const i = order[pos];

            const data = await postAnswer({ card: i, scam: saidScam });
            busy = false;

            if (!data || !data.success) {
                showFeedback((data && data.error) || "The terminal did not respond.");
                buttonScam.disabled = buttonLegit.disabled = false;
                return;
            }

            answers[i] = saidScam;
            results[i] = data.correct;
            card.classList.add(saidScam ? "swipe-left" : "swipe-right");
            card.classList.add(data.correct ? "swipe-right-answer" : "swipe-wrong-answer");

            clear(verdict);
            verdict.appendChild(element("strong", "", (data.correct ? "CORRECT - " : "WRONG - ") + "this was " + (data.verdict === "scam" ? labels[0] : labels[1])));
            verdict.appendChild(element("p", "", data.why || ""));
            verdict.classList.remove("hidden");
            controls.classList.add("hidden");
            buttonNext.classList.remove("hidden");
            buttonNext.focus();
        }

        function finishRound() {
            const wrong = cards.map((_, i) => i).filter((i) => results[i] === false);
            if (wrong.length === 0) {
                submitChallenge();
                return;
            }
            clear(card);
            clear(verdict);
            verdict.classList.add("hidden");
            card.className = "swipe-card swipe-summary";
            card.appendChild(element("strong", "", (cards.length - wrong.length) + " of " + cards.length + " right."));
            card.appendChild(element("p", "", "The " + wrong.length + " you missed come back now. Read the explanation you saw and try again."));
            progress.textContent = "ROUND OVER";
            controls.classList.add("hidden");
            buttonNext.textContent = "REDO THE " + wrong.length;
            buttonNext.classList.remove("hidden");
            buttonNext.onclick = function () {
                order = wrong;
                pos = 0;
                buttonNext.textContent = "NEXT MESSAGE";
                buttonNext.onclick = advance;
                showCard();
            };
        }

        function advance() {
            pos += 1;
            if (pos < order.length) showCard();
            else finishRound();
        }

        buttonNext.onclick = advance;
        buttonScam.addEventListener("click", () => choose(true));
        buttonLegit.addEventListener("click", () => choose(false));

        document.addEventListener("keydown", function (event) {
            if (mySession !== swipeSession) return;
            if (state.phase !== "challenge" || overlayChallenge.classList.contains("hidden")) return;
            if (LEVEL.challenge.type !== "swipe") return;
            if (event.key === "ArrowLeft" && !buttonScam.disabled && !controls.classList.contains("hidden")) { event.preventDefault(); choose(true); }
            else if (event.key === "ArrowRight" && !buttonLegit.disabled && !controls.classList.contains("hidden")) { event.preventDefault(); choose(false); }
            else if (event.key === "Enter" && !buttonNext.classList.contains("hidden")) { event.preventDefault(); buttonNext.onclick(); }
        });

        challengeInput = () => ({ answers: answers.map((a) => a === null ? false : a) });
        showCard();
    }

    // Tab inserts four spaces and Enter keeps the current indentation,
    // so Python blocks can be typed without the browser stealing Tab.
    function codeEditorKeys(area) {
        area.addEventListener("keydown", function (event) {
            const start = area.selectionStart;
            const end = area.selectionEnd;
            const value = area.value;

            if (event.key === "Tab") {
                event.preventDefault();
                const lineStart = value.lastIndexOf("\n", start - 1) + 1;
                if (event.shiftKey) {
                    const line = value.slice(lineStart, start);
                    const remove = Math.min(4, line.length - line.trimStart().length);
                    area.value = value.slice(0, lineStart) + value.slice(lineStart + remove);
                    area.selectionStart = area.selectionEnd = Math.max(lineStart, start - remove);
                } else {
                    area.value = value.slice(0, start) + "    " + value.slice(end);
                    area.selectionStart = area.selectionEnd = start + 4;
                }
                return;
            }

            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                const lineStart = value.lastIndexOf("\n", start - 1) + 1;
                const line = value.slice(lineStart, start);
                let indent = line.match(/^\s*/)[0];
                if (line.trimEnd().endsWith(":")) indent += "    ";
                area.value = value.slice(0, start) + "\n" + indent + value.slice(end);
                area.selectionStart = area.selectionEnd = start + 1 + indent.length;
            }
        });
    }

    function buildPythonLines(challenge) {
        const area = element("textarea", "challenge-code");
        area.rows = Math.max(2, (challenge.line_count || 1) + 1);
        area.placeholder = challenge.placeholder || "";
        area.spellcheck = false;
        codeEditorKeys(area);
        challengeBody.appendChild(area);
        challengeInput = () => area.value;
        buttonSubmit.textContent = "RUN";
        setTimeout(() => area.focus(), 50);
    }

    function buildTextAnswer(challenge) {
        const input = element("input", "challenge-text");
        input.type = "text";
        input.placeholder = challenge.placeholder || "";
        input.autocomplete = "off";
        input.addEventListener("keydown", (e) => { if (e.key === "Enter") submitChallenge(); });
        challengeBody.appendChild(input);
        challengeInput = () => input.value;
        buttonSubmit.textContent = "ANSWER";
        setTimeout(() => input.focus(), 50);
    }

    function buildChoices(challenge) {
        let chosen = null;
        challenge.options.forEach((option, index) => {
            const button = element("button", "choice-button", option);
            button.type = "button";
            button.addEventListener("click", () => {
                chosen = index;
                challengeBody.querySelectorAll(".choice-button").forEach((b) => b.classList.remove("choice-selected"));
                button.classList.add("choice-selected");
            });
            challengeBody.appendChild(button);
        });
        challengeInput = () => chosen;
        buttonSubmit.textContent = "ANSWER";
    }

    function buildCodeReview(challenge) {
        const list = element("div", "review-code");
        const whyBlock = element("div", "review-why hidden");

        challenge.code.forEach((line, index) => {
            const row = element("button", "review-line");
            row.type = "button";
            row.appendChild(element("span", "review-number", String(index + 1)));
            row.appendChild(element("span", "review-text", line));
            row.addEventListener("click", () => {
                reviewSelection.line = index + 1;
                list.querySelectorAll(".review-line").forEach((r) => r.classList.remove("review-selected"));
                row.classList.add("review-selected");
                whyBlock.classList.remove("hidden");
            });
            list.appendChild(row);
        });
        challengeBody.appendChild(list);

        whyBlock.appendChild(element("p", "section-label", "WHY IS IT A PROBLEM?"));
        challenge.why_options.forEach((option, index) => {
            const button = element("button", "choice-button", option);
            button.type = "button";
            button.addEventListener("click", () => {
                reviewSelection.why = index;
                whyBlock.querySelectorAll(".choice-button").forEach((b) => b.classList.remove("choice-selected"));
                button.classList.add("choice-selected");
            });
            whyBlock.appendChild(button);
        });
        challengeBody.appendChild(whyBlock);

        challengeInput = () => ({ line: reviewSelection.line, why: reviewSelection.why });
        buttonSubmit.textContent = "REPORT";
    }

    function buildFillBlank(challenge) {
        const wrap = element("div", "blank-code");
        const inputs = [];
        let activeBlank = null;

        challenge.code.forEach((line) => {
            const row = element("div", "blank-line");
            const parts = line.split("___");
            parts.forEach((part, i) => {
                row.appendChild(element("span", "blank-text", part));
                if (i < parts.length - 1) {
                    const input = element("input", "blank-input");
                    input.type = "text";
                    input.autocomplete = "off";
                    input.spellcheck = false;
                    input.addEventListener("focus", () => { activeBlank = input; });
                    input.addEventListener("keydown", (e) => { if (e.key === "Enter") submitChallenge(); });
                    inputs.push(input);
                    row.appendChild(input);
                }
            });
            wrap.appendChild(row);
        });
        challengeBody.appendChild(wrap);

        if (challenge.bank && challenge.bank.length) {
            const bank = element("div", "word-bank");
            bank.appendChild(element("p", "section-label word-bank-label", "PIECES - click one to drop it into the selected blank"));
            challenge.bank.forEach((token) => {
                const button = element("button", "bank-token", token);
                button.type = "button";
                button.addEventListener("click", () => {
                    const target = activeBlank || inputs.find((i) => !i.value) || inputs[0];
                    target.value = token;
                    target.focus();
                });
                bank.appendChild(button);
            });
            challengeBody.appendChild(bank);
        }

        challengeInput = () => ({ blanks: inputs.map((i) => i.value) });
        buttonSubmit.textContent = "RUN";
        setTimeout(() => inputs[0] && inputs[0].focus(), 50);
    }

    function buildOrderCode(challenge) {
        const list = element("div", "order-list");
        let dragged = null;

        function clearDropMarks() {
            list.querySelectorAll(".order-piece").forEach((r) => r.classList.remove("drop-before", "drop-after"));
        }

        challenge.pieces.forEach((text, index) => {
            const row = element("div", "order-piece");
            row.draggable = true;
            row.dataset.index = String(index);
            row.appendChild(element("span", "order-grip", "⋮⋮"));
            row.appendChild(element("code", "order-text", text));

            const buttons = element("div", "order-buttons");
            const up = element("button", "", "▲");
            const down = element("button", "", "▼");
            up.type = down.type = "button";
            up.title = "Move up";
            down.title = "Move down";
            up.addEventListener("click", () => { if (row.previousElementSibling) list.insertBefore(row, row.previousElementSibling); });
            down.addEventListener("click", () => { if (row.nextElementSibling) list.insertBefore(row.nextElementSibling, row); });
            buttons.appendChild(up);
            buttons.appendChild(down);
            row.appendChild(buttons);

            row.addEventListener("dragstart", (e) => {
                dragged = row;
                row.classList.add("dragging");
                e.dataTransfer.effectAllowed = "move";
                e.dataTransfer.setData("text/plain", row.dataset.index);
            });
            row.addEventListener("dragend", () => {
                row.classList.remove("dragging");
                clearDropMarks();
                dragged = null;
            });
            row.addEventListener("dragover", (e) => {
                if (!dragged || dragged === row) return;
                e.preventDefault();
                const rect = row.getBoundingClientRect();
                const before = e.clientY < rect.top + rect.height / 2;
                clearDropMarks();
                row.classList.add(before ? "drop-before" : "drop-after");
            });
            row.addEventListener("drop", (e) => {
                if (!dragged || dragged === row) return;
                e.preventDefault();
                const rect = row.getBoundingClientRect();
                const before = e.clientY < rect.top + rect.height / 2;
                list.insertBefore(dragged, before ? row : row.nextElementSibling);
                clearDropMarks();
            });

            list.appendChild(row);
        });

        challengeBody.appendChild(list);
        challengeInput = () => ({ order: Array.from(list.children).map((r) => Number(r.dataset.index)) });
        buttonSubmit.textContent = "RUN";
    }

    function closeChallenge() {
        overlayChallenge.classList.add("hidden");
        if (state.phase === "challenge") state.phase = "play";
        gameWindow.focus();
    }

    function hintsLeft() {
        return (LEVEL.hints || []).length - state.hintIndex;
    }

    function updateHintButton() {
        const chips = countItem(ITEM_CHIP);
        const left = hintsLeft();

        if (left <= 0) {
            // Never burn a chip on nothing: the button locks once every hint is shown.
            buttonHint.textContent = state.hintIndex ? "NO MORE HINTS HERE" : "NO HINTS ON THIS LEVEL";
            buttonHint.disabled = true;
            buttonHint.title = "Your hint chips are kept. Re-read the lesson notes or ask SecureMentor.";
            return;
        }

        buttonHint.textContent = "USE HINT CHIP (" + chips + ")";
        buttonHint.disabled = chips === 0;
        buttonHint.title = chips === 0
            ? "Find hint chips in the world - or ask SecureMentor."
            : left + " hint" + (left === 1 ? "" : "s") + " left on this level.";
    }

    function useHint() {
        if (hintsLeft() <= 0) {
            updateHintButton();
            return;
        }

        if (!takeItem(ITEM_CHIP)) return;

        const text = LEVEL.hints[state.hintIndex];
        state.hintIndex += 1;

        state.revealedHints.push(text);
        challengeHints.appendChild(element("p", "hint-line", "HINT: " + text));
        updateHintButton();
    }

    let submitting = false;

    async function postAnswer(answer) {
        const kills = state.kills;
        try {
            const response = await fetch("/api/level/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    course: LEVEL.course, level: LEVEL.number, answer: answer,
                    inventory: state.inventory, kills: kills
                })
            });
            const data = await response.json();
            if (data && data.success && state.kills === kills) state.kills = {};
            return data;
        } catch (error) {
            return null;
        }
    }

    async function submitChallenge() {
        if (submitting || state.phase !== "challenge") return;

        const answer = challengeInput ? challengeInput() : null;

        const empty =
            answer === null || answer === undefined || answer === "" ||
            (typeof answer === "object" && answer.line === null) ||
            (typeof answer === "object" && Array.isArray(answer.blanks) && answer.blanks.some((b) => !b.trim())) ||
            (typeof answer === "object" && Array.isArray(answer.map) && answer.map.some((m) => m < 0));

        if (empty) {
            showFeedback(typeof answer === "object" && answer && Array.isArray(answer.map) ? "Every item needs a place before you can run it." : "Fill everything in before you run it.");
            return;
        }

        submitting = true;
        buttonSubmit.disabled = true;

        try {
            const data = await postAnswer(answer);

            if (!data) {
                showFeedback("Connection lost. Try again.");
                return;
            }

            if (!data.success) {
                showFeedback(data.error || "The terminal did not respond.");
                return;
            }

            if (!data.correct) {
                showFeedback(data.feedback || "Not quite.");
                return;
            }

            state.solved = true;
            state.result = data;
            state.finalElapsed = data.elapsed;
            overlayChallenge.classList.add("hidden");
            celebrate(false);
            showSolved(data);

        } finally {
            submitting = false;
            buttonSubmit.disabled = false;
        }
    }

    // Story levels have no terminal: reaching the exit (or the vent, or
    // killing the brain) records the completion and shows the card.
    function finishLevel() {
        if (state.phase === "complete" || state.finishing) return;

        if (LEVEL.challenge.type === "walk" && !state.result) {
            state.finishing = true;
            postAnswer({ reached: true }).then((data) => {
                state.finishing = false;
                if (data && data.success && data.correct) {
                    state.solved = true;
                    state.result = data;
                    state.finalElapsed = data.elapsed;
                    showComplete();
                } else {
                    toast((data && data.error) || "Connection lost - try the exit again.");
                }
            });
            return;
        }

        showComplete();
    }

    function showFeedback(text) {
        challengeFeedback.textContent = text;
        challengeFeedback.classList.add("feedback-bad");
        challengeFeedback.classList.remove("shake");
        void challengeFeedback.offsetWidth;
        challengeFeedback.classList.add("shake");
    }

    buttonSubmit.addEventListener("click", submitChallenge);
    buttonHint.addEventListener("click", useHint);
    buttonChallengeClose.addEventListener("click", closeChallenge);


    /* -----------------------------------------------------
       RESULT SCREENS
    ----------------------------------------------------- */

    function stat(label, value) {
        const box = element("div", "result-stat");
        box.appendChild(element("span", "stat-label", label));
        box.appendChild(element("strong", "stat-value", value));
        return box;
    }

    function celebrate(big) {
        state.flash = big ? 18 : 10;
        const colors = [theme.accent, "#ffffff", "#ffd700", "#ff4fa3", "#4bd0e0"];
        const count = big ? 110 : 50;
        for (let i = 0; i < count; i++) {
            particles.push({
                x: camera.x + Math.random() * VIEW_W,
                y: -6 - Math.random() * 60,
                vx: (Math.random() - 0.5) * 1.2,
                vy: 0.4 + Math.random() * 1.4,
                life: 100 + Math.random() * 80,
                color: colors[i % colors.length],
                confetti: true
            });
        }
        if (player.onGround) {
            player.vy = -3.4;
            player.onGround = false;
        }
    }

    function showSolved(data) {
        state.phase = "result";
        const box = overlayResult.querySelector(".overlay-box");
        box.classList.remove("celebrate", "ready");
        box.classList.add("pop-in");

        resultLabel.textContent = data.new_record ? "ACCESS GRANTED · NEW LEVEL RECORD" : "ACCESS GRANTED";
        resultTitle.textContent = "The terminal accepts your answer";
        resultText.textContent = data.explanation || "";

        if (data.fixed && data.fixed.length) {
            resultCode.textContent = "SAFER APPROACH:\n" + data.fixed.join("\n");
            resultCode.classList.remove("hidden");
        } else {
            resultCode.classList.add("hidden");
        }

        clear(resultStats);
        resultStats.appendChild(stat("TIME", data.elapsed === null ? "--:--" : formatTime(data.elapsed)));
        resultStats.appendChild(stat("REWARD", data.reward || ""));

        clear(resultActions);
        const go = element("button", "large-button", "OPEN THE DOOR");
        go.type = "button";
        go.addEventListener("click", function () {
            overlayResult.classList.add("hidden");
            openDoor();
            state.phase = "play";
            setObjective("Go through the open door (walk in, or press E at it)");
            gameWindow.focus();
        });
        resultActions.appendChild(go);

        overlayResult.classList.remove("hidden");
    }

    // Counts a stat up from 0 to its final value so the card feels earned.
    function animateStat(box, seconds) {
        const value = box.querySelector(".stat-value");
        const total = Math.max(0, seconds);
        const steps = 18;
        let step = 0;
        const tick = setInterval(() => {
            step += 1;
            value.textContent = formatTime(Math.round(total * Math.min(1, step / steps)));
            if (step >= steps) clearInterval(tick);
        }, 40);
    }

    function showComplete() {
        if (state.phase === "complete") return;
        state.phase = "complete";

        celebrate(true);
        setObjective("LEVEL COMPLETE!");
        overlayDialogue.classList.add("hidden");

        // The obelisk keeps its music; everywhere else the track fades with the level.
        if (window.academyAudio && !LEVEL.obelisk) academyAudio.fadeOut(1800);

        // Let the confetti and the little hop play before the card slides in.
        setTimeout(renderCompleteCard, 900);
    }

    function renderCompleteCard() {
        const data = state.result || {};
        const box = overlayResult.querySelector(".overlay-box");
        box.classList.add("celebrate", "pop-in");
        box.classList.remove("ready");

        resultLabel.textContent = data.course_finished
            ? "COURSE COMPLETE"
            : (data.new_record ? "LEVEL COMPLETE · NEW LEVEL RECORD" : "LEVEL COMPLETE");
        resultTitle.textContent = LEVEL.title;

        const quips = GUIDE === "BYTE" ? BYTE_QUIPS : STATIC_QUIPS;
        const quip = quips[(LEVEL.number + (data.elapsed || 0)) % quips.length];
        const beamCount = (data.beams || LEVEL.beams || []).length;
        resultText.textContent = data.course_finished
            ? (LEVEL.obelisk
                ? "Your beam is lit, and it stays lit. " + beamCount + " of 4 beams now stand in the sky."
                    + (beamCount === 4 ? " Every course complete." : " Finish another course and come back to see it join them.")
                : (LEVEL.finale
                    ? "Everything you just did - stolen codes, an open gate, loose malware, sorted scams, a beaten response - is what cybersecurity exists to stop. The next courses teach the other side."
                    : "You have cleared every level of " + LEVEL.zone + ". The whole Academy heard about it."))
            : GUIDE + ": \"" + quip + "\"  ·  Reward earned: " + (data.reward || LEVEL.reward) + ".";
        resultCode.classList.add("hidden");

        // Secret achievements unlocked by this completion
        const old = box.querySelector(".result-achievements");
        if (old) old.remove();
        if (data.new_achievements && data.new_achievements.length) {
            const list = element("div", "result-achievements");
            data.new_achievements.forEach((a) => {
                const row = element("div", "achievement-unlock");
                row.appendChild(element("span", "achievement-tag", "SECRET ACHIEVEMENT UNLOCKED"));
                row.appendChild(element("strong", "", a.title));
                row.appendChild(element("span", "achievement-desc", a.desc));
                list.appendChild(row);
            });
            resultActions.parentNode.insertBefore(list, resultActions);
        }

        clear(resultStats);
        const timeBox = stat("TIME", "00:00");
        resultStats.appendChild(timeBox);
        resultStats.appendChild(stat("YOUR BEST", data.best === null || data.best === undefined ? "--:--" : formatTime(data.best)));
        const record = data.record;
        resultStats.appendChild(stat(
            data.new_record ? "RECORD · YOU" : "LEVEL RECORD",
            record ? formatTime(record.seconds) + " · " + record.username : "--:--"
        ));
        resultStats.appendChild(stat("ZONE", (data.levels_done || 0) + " / " + (data.level_count || LEVEL.level_count)));

        // The server's time is the one that counts; if it is missing
        // (start request lost), show the client clock instead of a blank.
        const shown = (data.elapsed !== null && data.elapsed !== undefined)
            ? data.elapsed
            : (state.timerStart !== null ? Math.floor((performance.now() - state.timerStart) / 1000) : null);
        if (shown !== null) {
            animateStat(timeBox, shown);
        } else {
            timeBox.querySelector(".stat-value").textContent = "--:--";
        }

        clear(resultActions);

        if (data.next_level) {
            const next = element("a", "large-button", "NEXT: " + data.next_level.title.toUpperCase());
            next.href = data.next_level.url;
            resultActions.appendChild(next);
        } else {
            const back = element("a", "large-button", "BACK TO COURSE");
            back.href = "/curriculum/" + LEVEL.course;
            resultActions.appendChild(back);
        }

        const again = element("a", "outline-button", "PLAY AGAIN");
        again.href = window.location.pathname;
        resultActions.appendChild(again);

        const board = element("a", "outline-button", "LEADERBOARD");
        board.href = "/leaderboard";
        resultActions.appendChild(board);

        overlayResult.classList.remove("hidden");
        setTimeout(() => box.classList.add("ready"), 1100);
    }

    function openDoor() {
        state.doorOpen = true;
        const door = entities.find((e) => e.type === "door");
        if (door) {
            for (let i = 0; i < 24; i++) {
                particles.push({
                    x: door.x + Math.random() * door.w, y: door.y + Math.random() * door.h,
                    vx: (Math.random() - 0.5) * 1.5, vy: -Math.random() * 1.5,
                    life: 40 + Math.random() * 30, color: theme.accent
                });
            }
        }
    }


    /* -----------------------------------------------------
       TIMER (display only - the server keeps the real one)
    ----------------------------------------------------- */

    async function startTimer(resume) {
        let offset = 0;
        try {
            const response = await fetch("/api/level/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ course: LEVEL.course, level: LEVEL.number, resume: !!resume })
            });
            const data = await response.json();
            if (data && data.elapsed) offset = data.elapsed;
        } catch (error) {
            // The level still plays; only the time may be missing.
        }
        state.timerStart = performance.now() - offset * 1000;
    }

    function updateTimer() {
        if (state.finalElapsed !== null && state.finalElapsed !== undefined) {
            hudTimer.textContent = formatTime(state.finalElapsed);
            return;
        }
        if (state.timerStart === null) {
            hudTimer.textContent = "00:00";
            return;
        }
        hudTimer.textContent = formatTime(Math.floor((performance.now() - state.timerStart) / 1000));
    }


    /* -----------------------------------------------------
       PHYSICS
    ----------------------------------------------------- */

    function moveBody(body) {
        // Horizontal
        let nx = body.x + body.vx;
        if (rectHitsSolid(nx, body.y, body.w, body.h)) {
            const step = body.vx > 0 ? 1 : -1;
            let guard = 0;
            while (!rectHitsSolid(body.x + step, body.y, body.w, body.h) && guard < 8) {
                body.x += step;
                guard += 1;
            }
            body.vx = 0;
            body.blocked = true;
        } else {
            body.x = nx;
            body.blocked = false;
        }

        // Vertical
        let ny = body.y + body.vy;
        if (rectHitsSolid(body.x, ny, body.w, body.h)) {
            const step = body.vy > 0 ? 1 : -1;
            let guard = 0;
            while (!rectHitsSolid(body.x, body.y + step, body.w, body.h) && guard < 8) {
                body.y += step;
                guard += 1;
            }
            if (body.vy > 0) body.onGround = true;
            body.vy = 0;
        } else {
            body.y = ny;
            body.onGround = false;
        }
    }

    function stepPlayer() {

        const left = keys.a || keys.arrowleft;
        const right = keys.d || keys.arrowright;
        const jump = keys.w || keys[" "] || keys.arrowup;

        if (player.invuln > 0) player.invuln -= 1;
        if (player.attackTimer > 0) player.attackTimer -= 1;
        if (player.attackCooldown > 0) player.attackCooldown -= 1;

        const stunned = player.invuln > 45;   // brief loss of control after a hit

        if (!stunned) {
            if (left && !right) {
                player.vx = Math.max(player.vx - RUN_ACCEL, -RUN_MAX);
                player.facing = -1;
            } else if (right && !left) {
                player.vx = Math.min(player.vx + RUN_ACCEL, RUN_MAX);
                player.facing = 1;
            } else {
                player.vx *= player.onGround ? 0.6 : 0.92;
                if (Math.abs(player.vx) < 0.05) player.vx = 0;
            }

            if (jump && player.onGround) {
                player.vy = JUMP_SPEED;
                player.onGround = false;
            }
        }

        player.vy = Math.min(player.vy + GRAVITY, MAX_FALL);
        moveBody(player);

        player.x = Math.max(0, Math.min(player.x, MAP_W * TILE - player.w));
        if (player.y > MAP_H * TILE) {
            player.x = spawn.x; player.y = spawn.y; player.vy = 0;
        }

        // The live data stream: one heart, and back to the last safe ledge.
        if (player.onGround && !touchingHazard()) {
            state.lastSafe = { x: player.x, y: player.y };
        } else if (touchingHazard() && player.invuln === 0) {
            player.hp -= 1;
            player.invuln = 70;
            renderHearts();
            burst(player.x + 4, player.y + 10, "#4bd0e0", 16);
            state.flash = 4;
            const safe = state.lastSafe || (state.checkpoint ? { x: state.checkpoint.x, y: state.checkpoint.y } : spawn);
            player.x = safe.x;
            player.y = safe.y;
            player.vx = 0;
            player.vy = 0;
            toast(player.hp > 0 ? "The stream bit you. Back to the last ledge." : "The stream bit you.");
            if (player.hp <= 0) { respawn(); return; }
        }

        // Code appears on the monitor as the player runs across the keys.
        if (LEVEL.code_lines && LEVEL.code_lines.length) {
            const revealed = Math.max(0, Math.min(LEVEL.code_lines.length, Math.floor((player.x - spawn.x) / 36)));
            if (revealed > state.codeProgress) state.codeProgress = revealed;
        }

        if (Math.abs(player.vx) > 0.2 && player.onGround) {
            player.walkTime += 1;
            player.frame = Math.floor(player.walkTime / 8) % 2;
        } else {
            player.frame = player.onGround ? 0 : 1;
        }

        // Stomping the brain: land on it from above to hurt it, touch its side and it hurts you.
        enemies.forEach((brain) => {
            if (brain.type !== "brain" || !brain.alive) return;
            const feet = player.y + player.h;
            const horizontal = player.x + player.w > brain.x + 2 && player.x < brain.x + brain.w - 2;
            if (horizontal && player.vy >= 0 && feet >= brain.y - 2 && feet <= brain.y + 10) {
                player.y = brain.y - player.h;
                player.vy = -4.6;
                player.onGround = false;
                brain.hp -= 1;
                brain.hitFlash = 12;
                burst(player.x + 4, brain.y, "#ff9ad0", 14);
                state.flash = 4;
                toast(brain.hp > 0 ? brain.hp + " more stomp" + (brain.hp === 1 ? "" : "s") : "The brain goes dark.");
                if (brain.hp <= 0) killEnemy(brain);
            } else if (overlaps(player, brain)) {
                damagePlayer(1, brain);
            }
        });

        // Pickups + exit
        entities.forEach((entity) => {
            if (entity.type === "item" && entity.cooldown > 0) {
                entity.cooldown -= 1;
                if (entity.cooldown === 0 && overlaps(player, entity)) entity.cooldown = 1;
                return;
            }
            if (entity.type === "item" && !entity.taken && overlaps(player, entity)) {
                if (addItem(entity.item)) {
                    entity.taken = true;
                    burst(entity.x + 4, entity.y + 4, theme.accent, 10);
                    const notes = {
                        "DAGGER": "DAGGER picked up. Select its slot and press F to swing.",
                        "SWORD": "SWORD picked up. Press F or click to swing.",
                        "CANDY": "CANDY picked up. Select its slot (1-5) and press F to eat it.",
                        "HINT CHIP": "HINT CHIP picked up. Spend it at a terminal.",
                        "DOOR CODE": "DOOR CODE taken. Press E at a locked door.",
                        "VENT KEY": "VENT KEY taken. Press E at the vent."
                    };
                    toast(notes[entity.item] || entity.item + " picked up.");
                } else {
                    toast("Inventory full.");
                }
            }
            if (entity.type === "exit" && state.doorOpen && overlaps(player, entity)) {
                finishLevel();
            }
        });

        checkDoorPasses();

        camera.x = Math.max(0, Math.min(player.x + player.w / 2 - VIEW_W / 2, MAP_W * TILE - VIEW_W));
    }

    function groundAhead(body, dir) {
        const probeX = dir > 0 ? body.x + body.w + 1 : body.x - 2;
        return rectHitsSolid(probeX, body.y + body.h + 1, 1, 1);
    }

    function touchingHazard() {
        const left = Math.floor(player.x / TILE), right = Math.floor((player.x + player.w - 1) / TILE);
        const top = Math.floor(player.y / TILE), bottom = Math.floor((player.y + player.h - 1) / TILE);
        for (let ty = top; ty <= bottom; ty++) {
            for (let tx = left; tx <= right; tx++) {
                if (tiles[ty] && tiles[ty][tx] === "%") return true;
            }
        }
        return false;
    }

    function stepEnemies() {
        enemies.forEach((enemy) => {
            if (!enemy.alive) return;
            if (enemy.hitFlash > 0) enemy.hitFlash -= 1;

            // The first time a boss is on screen its music takes over.
            if (!state.bossMusic && BOSS_TYPES.includes(enemy.type)
                && enemy.x + enemy.w > camera.x - 8 && enemy.x < camera.x + VIEW_W + 8) {
                state.bossMusic = true;
                if (window.academyAudio) academyAudio.bossStart(LEVEL.boss_music);
            }

            // Stunned enemies just stand there (gravity still applies) and
            // cannot hurt the player - the window for a follow-up strike.
            if (enemy.stun > 0) {
                enemy.stun -= 1;
                if (enemy.type !== "boss") {
                    enemy.vy = Math.min(enemy.vy + GRAVITY, MAX_FALL);
                    enemy.vx = 0;
                    moveBody(enemy);
                }
                return;
            }

            if (enemy.type === "snake" || enemy.type === "sniffer") {
                enemy.vy = Math.min(enemy.vy + GRAVITY, MAX_FALL);
                enemy.vx = enemy.dir * (enemy.type === "sniffer" ? 0.5 : SNAKE_SPEED);
                moveBody(enemy);
                if (enemy.blocked || (enemy.onGround && !groundAhead(enemy, enemy.dir))) enemy.dir *= -1;
                if (overlaps(player, enemy)) damagePlayer(1, enemy);
            }

            else if (enemy.type === "hostile") {
                enemy.vy = Math.min(enemy.vy + GRAVITY, MAX_FALL);
                const dx = (player.x + player.w / 2) - (enemy.x + enemy.w / 2);
                const chasing = Math.abs(dx) < 110 && Math.abs(player.y - enemy.y) < 40;
                if (chasing) {
                    enemy.dir = dx < 0 ? -1 : 1;
                    enemy.vx = (enemy.onGround && !groundAhead(enemy, enemy.dir)) ? 0 : enemy.dir * DOCTOR_SPEED;
                } else {
                    enemy.vx = 0;
                }
                moveBody(enemy);
                if (overlaps(player, enemy)) damagePlayer(1, enemy);
            }

            else if (enemy.type === "bug") {
                enemy.vy = Math.min(enemy.vy + GRAVITY, MAX_FALL);
                const dx = (player.x + player.w / 2) - (enemy.x + enemy.w / 2);
                const near = Math.abs(dx) < 64 && Math.abs(player.y - enemy.y) < 30;
                if (near) enemy.dir = dx < 0 ? -1 : 1;
                enemy.vx = enemy.dir * (near ? BUG_RUSH : BUG_SPEED);
                moveBody(enemy);
                if (enemy.blocked || (enemy.onGround && !near && !groundAhead(enemy, enemy.dir))) enemy.dir *= -1;
                if (overlaps(player, enemy)) damagePlayer(1, enemy);
            }

            else if (enemy.type === "boss") {
                stepBoss(enemy);
            }

            else if (enemy.type === "vex") {
                stepVex(enemy);
            }

            else if (enemy.type === "brain") {
                stepBrain(enemy);
            }
        });

        for (let i = projectiles.length - 1; i >= 0; i--) {
            const p = projectiles[i];
            if (p.kind === "thought") {
                // Slow homing: drifts toward the player, easy to outrun.
                const dx = (player.x + 4) - p.x, dy = (player.y + 6) - p.y;
                p.vx = Math.max(-1.1, Math.min(1.1, p.vx + Math.sign(dx) * 0.04));
                p.vy = Math.max(-0.9, Math.min(0.9, p.vy + Math.sign(dy) * 0.04));
                p.y += p.vy;
            }
            p.x += p.vx;
            p.life -= 1;
            if (Math.random() < 0.6) {
                const color = p.kind === "syringe" ? "#cfe8ff" : (p.kind === "thought" ? "#ff9ad0" : "#ffb347");
                particles.push({ x: p.x + 3, y: p.y + 3, vx: -p.vx * 0.2, vy: (Math.random() - 0.5), life: 10, color: color });
            }
            if (p.life <= 0 || rectHitsSolid(p.x, p.y, p.w, p.h)) {
                projectiles.splice(i, 1);
                continue;
            }
            if (overlaps(player, p)) {
                damagePlayer(p.damage || 2, p);
                projectiles.splice(i, 1);
            }
        }
    }

    // Dr. Vex: walks at you, stops to throw three syringes, then staggers.
    function stepVex(vex) {
        vex.timer += 1;
        vex.vy = Math.min(vex.vy + GRAVITY, MAX_FALL);
        const dx = (player.x + player.w / 2) - (vex.x + vex.w / 2);
        vex.dir = dx < 0 ? -1 : 1;

        if (vex.state === "chase") {
            vex.vx = (vex.onGround && !groundAhead(vex, vex.dir)) ? 0 : vex.dir * VEX_SPEED;
            if (vex.timer > 110 || (Math.abs(dx) < 70 && vex.timer > 40)) { vex.state = "throw"; vex.timer = 0; vex.shots = 0; }
        }

        else if (vex.state === "throw") {
            vex.vx = 0;
            if (vex.timer % 24 === 1 && vex.shots < 3) {
                projectiles.push({
                    kind: "syringe", damage: 1,
                    x: vex.dir > 0 ? vex.x + vex.w : vex.x - 6,
                    y: vex.y + 7, w: 7, h: 3,
                    vx: vex.dir * 2.4, life: 160
                });
                vex.shots += 1;
            }
            if (vex.shots >= 3 && vex.timer > 3 * 24 + 16) { vex.state = "rest"; vex.timer = 0; }
        }

        else if (vex.state === "rest") {
            vex.vx = 0;
            if (vex.timer > 150) { vex.state = "chase"; vex.timer = 0; }
        }

        moveBody(vex);
        if (vex.state !== "rest" && overlaps(player, vex)) damagePlayer(1, vex);
    }

    // The brain never moves. Every few seconds it lets two thoughts loose.
    function stepBrain(brain) {
        brain.timer += 1;
        if (brain.timer % 170 === 60) {
            for (let i = 0; i < 2; i++) {
                projectiles.push({
                    kind: "thought", damage: 1,
                    x: brain.x + brain.w / 2 - 3 + (i ? 8 : -8), y: brain.y - 4,
                    w: 6, h: 6, vx: i ? 0.6 : -0.6, vy: -0.8, life: 260
                });
            }
        }
    }

    function stepBoss(boss) {
        boss.timer += 1;
        boss.dir = (player.x + player.w / 2) < (boss.x + boss.w / 2) ? -1 : 1;

        if (boss.state === "charge") {
            if (boss.timer > 90) { boss.state = "volley"; boss.timer = 0; boss.shots = 0; }
        }

        else if (boss.state === "volley") {
            if (boss.timer % 27 === 1 && boss.shots < 4) {
                const floorY = boss.y + boss.h;
                const high = boss.shots % 2 === 1;
                projectiles.push({
                    x: boss.dir > 0 ? boss.x + boss.w : boss.x - 6,
                    y: high ? floorY - 27 : floorY - 8,
                    w: 6, h: 6, vx: boss.dir * 2.1, life: 200
                });
                boss.shots += 1;
            }
            if (boss.shots >= 4 && boss.timer > 4 * 27 + 20) { boss.state = "rest"; boss.timer = 0; }
        }

        else if (boss.state === "rest") {
            if (boss.timer > 180) { boss.state = "charge"; boss.timer = 0; }
        }

        if (overlaps(player, boss)) damagePlayer(1, boss);
    }


    /* -----------------------------------------------------
       RENDERING
    ----------------------------------------------------- */

    function render() {
        const camX = Math.floor(camera.x);

        const sky = ctx.createLinearGradient(0, 0, 0, VIEW_H);
        sky.addColorStop(0, theme.skyTop);
        sky.addColorStop(1, theme.skyBottom);
        ctx.fillStyle = sky;
        ctx.fillRect(0, 0, VIEW_W, VIEW_H);

        ctx.fillStyle = theme.far;
        for (let i = 0; i < 14; i++) {
            const bx = ((i * 97) - camX * 0.35) % (VIEW_W + 120) - 60;
            const bh = 50 + ((i * 37) % 60);
            drawSilhouette(bx, VIEW_H - 48 - bh, bh, i);
        }

        if (theme.glow) {
            ctx.fillStyle = theme.accent;
            for (let i = 0; i < 10; i++) {
                const fx = ((i * 131) + Math.sin(state.time * 0.7 + i) * 12 - camX * 0.6) % VIEW_W;
                const fy = 40 + ((i * 53) % 90) + Math.cos(state.time * 0.9 + i * 2) * 6;
                ctx.globalAlpha = 0.35 + 0.35 * Math.sin(state.time * 3 + i);
                ctx.fillRect((fx + VIEW_W) % VIEW_W, fy, 1, 1);
            }
            ctx.globalAlpha = 1;
        }

        if (theme === THEMES.desk) drawMonitor();
        if (LEVEL.obelisk) drawBeams(camX);

        const firstCol = Math.floor(camX / TILE);
        const lastCol = Math.min(MAP_W - 1, firstCol + Math.ceil(VIEW_W / TILE) + 1);

        for (let ty = 0; ty < MAP_H; ty++) {
            for (let tx = firstCol; tx <= lastCol; tx++) {
                drawTile(tiles[ty][tx], tx, ty, tx * TILE - camX, ty * TILE);
            }
        }

        // Blood where bugs died
        state.decals.forEach((d) => {
            const dx = Math.floor(d.x - camX);
            if (dx < -12 || dx > VIEW_W + 12) return;
            ctx.fillStyle = "#6e1a1a";
            ctx.fillRect(dx - 4, d.y - 1, 8, 1);
            ctx.fillRect(dx - 2 + (d.seed % 3), d.y - 2, 3, 1);
            ctx.fillStyle = "#8a2222";
            ctx.fillRect(dx - 6 + (d.seed % 5), d.y - 1, 2, 1);
            ctx.fillRect(dx + 3 - (d.seed % 4), d.y - 1, 2, 1);
        });

        entities.forEach((entity) => drawEntity(entity, entity.x - camX, entity.y));
        enemies.forEach((enemy) => drawEnemy(enemy, enemy.x - camX, enemy.y));

        projectiles.forEach((p) => {
            const px = Math.floor(p.x - camX), py = Math.floor(p.y);
            if (p.kind === "syringe") {
                ctx.fillStyle = "#e8f2ff";
                ctx.fillRect(px, py, p.w, p.h);
                ctx.fillStyle = "#4bd0e0";
                ctx.fillRect(px + (p.vx > 0 ? 1 : 3), py + 1, 3, 1);
                ctx.fillStyle = "#8a949a";
                ctx.fillRect(p.vx > 0 ? px + p.w : px - 2, py + 1, 2, 1);
            } else if (p.kind === "thought") {
                ctx.fillStyle = "#ff9ad0";
                ctx.fillRect(px, py, p.w, p.h);
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(px + 2, py + 2, 2, 2);
            } else {
                ctx.fillStyle = "#ff7a1f";
                ctx.fillRect(px, py, p.w, p.h);
                ctx.fillStyle = "#ffe066";
                ctx.fillRect(px + 2, py + 2, 2, 2);
            }
        });

        // Player (blinks while invulnerable)
        if (player.invuln === 0 || Math.floor(state.time * 20) % 2 === 0) {
            CyberSprite.drawCharacter(ctx, CHARACTER, Math.floor(player.x - 2 - camX), Math.floor(player.y - 1), 1, player.facing, player.frame);
        }

        if (player.attackTimer > 0) {
            const box = attackBox();
            ctx.fillStyle = "#e8eef2";
            ctx.fillRect(Math.floor(box.x - camX) + (player.facing > 0 ? 0 : 2), Math.floor(player.y) + 7, 12, 2);
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(Math.floor(box.x - camX) + (player.facing > 0 ? 8 : 2), Math.floor(player.y) + 5, 3, 1);
        }

        if (state.phase === "play") {
            const target = nearestInteractable();
            if (target) {
                drawPrompt(target.x - camX + target.w / 2, target.y - 10);
            }
        }

        // Stun stars over frozen enemies
        enemies.forEach((enemy) => {
            if (!enemy.alive || enemy.stun <= 0) return;
            ctx.fillStyle = "#ffffff";
            for (let i = 0; i < 3; i++) {
                const angle = state.time * 6 + i * 2.1;
                ctx.fillRect(Math.floor(enemy.x - camX + enemy.w / 2 + Math.cos(angle) * 6), Math.floor(enemy.y - 5 + Math.sin(angle) * 2), 1, 1);
            }
        });

        particles.forEach((p) => {
            ctx.globalAlpha = Math.max(0, Math.min(1, p.life / 40));
            ctx.fillStyle = p.color;
            const size = p.confetti ? 2 : 1;
            ctx.fillRect(Math.floor(p.x - camX), Math.floor(p.y), size, size);
        });
        ctx.globalAlpha = 1;

        // The long dark: the corridor loses its lights the deeper you go,
        // leaving a small circle around the player until every bug is dead.
        if (LEVEL.dark) {
            const span = Math.max(1, MAP_W * TILE - 96 - 220);
            const target = state.lightsOn ? 0 : Math.max(0, Math.min(1, (player.x - 96) / span)) * 0.94;
            state.darkness += (target - state.darkness) * (state.lightsOn ? 0.06 : 0.05);
            if (state.darkness > 0.01) {
                ctx.fillStyle = "rgba(0,0,0," + state.darkness.toFixed(3) + ")";
                ctx.fillRect(0, 0, VIEW_W, VIEW_H);

                const lx = Math.floor(player.x + 4 - camX), ly = Math.floor(player.y + 8);
                const glow = ctx.createRadialGradient(lx, ly, 4, lx, ly, 44 + Math.sin(state.time * 5) * 2);
                glow.addColorStop(0, "rgba(0,0,0," + state.darkness.toFixed(3) + ")");
                glow.addColorStop(0.6, "rgba(0,0,0," + (state.darkness * 0.5).toFixed(3) + ")");
                glow.addColorStop(1, "rgba(0,0,0,0)");
                ctx.globalCompositeOperation = "destination-out";
                ctx.fillStyle = glow;
                ctx.fillRect(lx - 50, ly - 50, 100, 100);
                ctx.globalCompositeOperation = "source-over";

                // Eyes in the dark
                enemies.forEach((bug) => {
                    if (bug.type !== "bug" || !bug.alive) return;
                    const bx = Math.floor(bug.x - camX);
                    if (bx < -10 || bx > VIEW_W) return;
                    ctx.fillStyle = Math.floor(state.time * 3 + bug.x) % 5 === 0 ? "#400000" : "#ff2a2a";
                    ctx.fillRect(bx + (bug.dir > 0 ? 7 : 1), Math.floor(bug.y) + 1, 1, 1);
                    ctx.fillRect(bx + (bug.dir > 0 ? 9 : 3), Math.floor(bug.y) + 1, 1, 1);
                });
            }
        }

        if (state.flash > 0) {
            ctx.fillStyle = "rgba(255,255,255," + (state.flash / 45) + ")";
            ctx.fillRect(0, 0, VIEW_W, VIEW_H);
            state.flash -= 1;
        }

        // Finale: two seconds after the brain dies the lights go out, then the line.
        if (state.finale) {
            const t = state.finale.t;
            const black = Math.max(0, Math.min(1, (t - 2.0) / 1.2));
            if (black > 0) {
                ctx.fillStyle = "rgba(0,0,0," + black.toFixed(3) + ")";
                ctx.fillRect(0, 0, VIEW_W, VIEW_H);
            }
            if (t > 3.6) {
                const line = "THIS IS CYBERSECURITY";
                const shown = line.slice(0, Math.min(line.length, Math.floor((t - 3.6) * 14)));
                ctx.font = "bold 14px monospace";
                ctx.fillStyle = "#ffffff";
                const width = ctx.measureText(line).width;
                ctx.fillText(shown, Math.floor((VIEW_W - width) / 2), Math.floor(VIEW_H / 2) + 5);
                if (t > 4.2 && Math.floor(t * 2) % 2 === 0 && shown.length < line.length) {
                    ctx.fillRect(Math.floor((VIEW_W - width) / 2) + ctx.measureText(shown).width + 1, Math.floor(VIEW_H / 2) - 6, 7, 13);
                }
            }
            if (t > 8 && !state.finale.submitted) {
                state.finale.submitted = true;
                finishLevel();
            }
        }

        ctx.fillStyle = "rgba(0,0,0,0.35)";
        ctx.fillRect(0, 0, VIEW_W, 2);
        ctx.fillRect(0, VIEW_H - 2, VIEW_W, 2);
    }

    // The desk levels: a monitor in the background that mirrors the player
    // (and, on the coding levels, shows the lines they have "typed").
    function drawMonitor() {
        const mx = 196, my = 6, mw = 118, mh = 72;
        ctx.fillStyle = "#1a1a1e";
        ctx.fillRect(mx, my, mw, mh);
        ctx.fillStyle = "#0b0f14";
        ctx.fillRect(mx + 4, my + 4, mw - 8, mh - 14);
        ctx.fillStyle = "#2a2a30";
        ctx.fillRect(mx + mw / 2 - 10, my + mh, 20, 6);
        ctx.fillRect(mx + mw / 2 - 20, my + mh + 6, 40, 3);

        const sx = mx + 4, sy = my + 4, sw = mw - 8, sh = mh - 14;

        if (LEVEL.code_lines && LEVEL.code_lines.length) {
            ctx.font = "6px monospace";
            const lines = LEVEL.code_lines.slice(0, state.codeProgress);
            const visible = lines.slice(-8);
            visible.forEach((line, i) => {
                ctx.fillStyle = line.trim().startsWith("<") ? "#4ec9b0" : (line.trim().startsWith("//") ? "#6a9955" : "#d4d4d4");
                ctx.fillText(line.slice(0, 26), sx + 3, sy + 8 + i * 7);
            });
            if (Math.floor(state.time * 2) % 2 === 0) {
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(sx + 3 + Math.min(26, (visible[visible.length - 1] || "").length) * 3.6, sy + 3 + visible.length * 7, 3, 6);
            }
            if (!lines.length) {
                ctx.fillStyle = "#4a5560";
                ctx.fillText("run across the keys...", sx + 3, sy + 8);
            }
            return;
        }

        if (LEVEL.mimic) {
            // A tiny copy of the scene: keys as a bar, the player as a dot that follows you
            ctx.fillStyle = "#1f2a30";
            ctx.fillRect(sx + 6, sy + sh - 12, sw - 12, 6);
            const fx = sx + 6 + Math.floor((player.x / (MAP_W * TILE)) * (sw - 16));
            const fy = sy + sh - 14 - Math.max(0, Math.floor((MAP_H * TILE - player.y - 60) / 8));
            ctx.fillStyle = "#4bd0e0";
            ctx.fillRect(fx, fy - 5, 3, 5);
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(fx + 1, fy - 5, 1, 1);
            ctx.font = "6px monospace";
            ctx.fillStyle = "#6a9955";
            ctx.fillText("mirror: on", sx + 3, sy + 8);
        }
    }

    // Beams of light above the obelisk: one per finished course, plus the
    // one being lit right now.
    function drawBeams(camX) {
        const obelisk = entities.find((e) => e.type === "obelisk");
        if (!obelisk) return;
        BEAM_SLOTS.forEach((slug, i) => {
            let strength = (LEVEL.beams || []).includes(slug) ? 1 : 0;
            if (slug === LEVEL.course && state.cutscene) strength = Math.max(strength, Math.min(1, state.cutscene.t / 2.6));
            if (strength <= 0) return;
            const x = Math.floor(obelisk.x - camX + 5 + i * 6);
            const top = obelisk.y - strength * (obelisk.y + 60);
            const height = obelisk.y - top;
            ctx.globalAlpha = 0.35 + 0.15 * Math.sin(state.time * 3 + i);
            ctx.fillStyle = BEAM_COLORS[slug];
            ctx.fillRect(x - 2, top, 8, height);
            ctx.globalAlpha = 0.8;
            ctx.fillRect(x, top, 4, height);
            ctx.globalAlpha = 1;
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(x + 1, top, 2, height);
            if (strength < 1) {
                for (let k = 0; k < 3; k++) {
                    particles.push({ x: obelisk.x + 8 + Math.random() * 16, y: obelisk.y + Math.random() * 20, vx: (Math.random() - 0.5) * 0.6, vy: -1.5 - Math.random() * 2, life: 30 + Math.random() * 30, color: BEAM_COLORS[slug] });
                }
            }
        });
    }

    function startCutscene() {
        state.phase = "cutscene";
        // Wall-clock timed so a throttled tab still finishes the scene.
        state.cutscene = { t: 0, start: performance.now(), flashed: false, done: false };
        overlayDialogue.classList.add("hidden");
        setObjective("...");
        keys.a = keys.d = keys.w = keys[" "] = false;
        player.vx = 0;
    }

    function stepCutscene(delta) {
        const scene = state.cutscene;
        scene.t = (performance.now() - scene.start) / 1000;
        if (!scene.flashed && scene.t > 0.4) {
            scene.flashed = true;
            state.flash = 14;
        }
        if (scene.t > 2.8 && !scene.lit) {
            scene.lit = true;
            celebrate(true);
            setObjective("Your beam is lit.");
        }
        if (scene.t > 5.2 && !scene.done) {
            scene.done = true;
            finishLevel();
        }
    }

    function drawSilhouette(x, y, h, seed) {
        if (theme === THEMES.cable) {
            // Loose strands of cable in the far wall
            ctx.fillRect(x + 4, y + 10, 3, h - 10);
            ctx.fillRect(x + 14, y + 18, 3, h - 18);
            ctx.fillRect(x + 22, y + 4, 3, h - 4);
            return;
        }
        if (theme === THEMES.desk) {
            // Things at the back of the desk: mugs, a lamp, a stack of books
            if (seed % 3 === 0) { ctx.fillRect(x + 4, y + h - 20, 14, 20); ctx.fillRect(x + 18, y + h - 16, 4, 8); }
            else if (seed % 3 === 1) { ctx.fillRect(x + 8, y + h - 40, 4, 40); ctx.fillRect(x, y + h - 46, 20, 8); }
            else { ctx.fillRect(x, y + h - 10, 24, 10); ctx.fillRect(x + 2, y + h - 18, 20, 8); }
            return;
        }
        if (theme === THEMES.editor) {
            // Lines of code on the far panel
            for (let i = 0; i < 4; i++) ctx.fillRect(x + (i % 2) * 6, y + 10 + i * 9, 16 - (i * 3) % 9, 3);
            return;
        }
        if (theme === THEMES.obelisk) {
            ctx.beginPath();
            ctx.moveTo(x - 10, y + h);
            ctx.lineTo(x + 14, y + h - 18 - (seed % 3) * 6);
            ctx.lineTo(x + 40, y + h);
            ctx.closePath();
            ctx.fill();
            return;
        }
        if (theme === THEMES.jungle) {
            // Fern fronds fanning out of one stem
            ctx.fillRect(x + 12, y + 14, 3, h - 14);
            for (let i = 0; i < 4; i++) {
                const fy = y + 16 + i * 9;
                const len = 14 - i * 2;
                ctx.fillRect(x + 12 - len, fy, len, 2);
                ctx.fillRect(x + 15, fy - 3, len, 2);
            }
            if (seed % 2) ctx.fillRect(x + 8, y + 6, 10, 10);
            return;
        }
        if (theme === THEMES.forest) {
            ctx.beginPath();
            ctx.moveTo(x, y + h);
            ctx.lineTo(x + 14, y);
            ctx.lineTo(x + 28, y + h);
            ctx.closePath();
            ctx.fill();
        } else if (theme === THEMES.relay) {
            ctx.fillRect(x + 12, y, 4, h);
            ctx.fillRect(x + 6, y + 10, 16, 2);
            ctx.fillRect(x + 8, y + 22, 12, 2);
        } else if (theme === THEMES.sewer) {
            ctx.fillRect(x, y + h - 30, 30, 30);
            ctx.fillRect(x + 4, y + h - 44, 22, 14);
        } else if (theme === THEMES.lab) {
            ctx.fillRect(x, y + 20, 24, h - 20);
            ctx.fillRect(x + 3, y + 26, 18, 2);
            ctx.fillRect(x + 3, y + 34, 18, 2);
        } else {
            ctx.fillRect(x, y + 10, 26, h - 10);
            if (seed % 2) ctx.fillRect(x + 4, y, 6, 12);
            if (seed % 3) ctx.fillRect(x + 16, y + 4, 6, 8);
        }
    }

    function drawThemedTile(tile, tx, ty, sx, sy) {
        if (theme === THEMES.cable) {
            if (tile === "W") {
                ctx.fillStyle = theme.wall;
                ctx.fillRect(sx, sy, TILE, TILE);
                ctx.fillStyle = "#d7e1ea";
                ctx.fillRect(sx, sy + 7, TILE, 1);
                ctx.fillRect(sx + ((ty % 2) ? 8 : 0), sy, 1, 7);
                ctx.fillRect(sx + ((ty % 2) ? 0 : 8), sy + 8, 1, 8);
                // a blue pulse travelling along the sheath
                if ((tx + Math.floor(state.time * 6)) % 9 === 0) {
                    ctx.fillStyle = "#8fd0ff";
                    ctx.fillRect(sx + 2, sy + 7, 12, 1);
                }
                return true;
            }
            if (tile === "G") {
                // a cable strand: white sheath, blue core
                ctx.fillStyle = "#eef2f6";
                ctx.fillRect(sx, sy + 3, TILE, 10);
                ctx.fillStyle = "#2f9be8";
                ctx.fillRect(sx, sy + 7, TILE, 2);
                ctx.fillStyle = "#b8c6d4";
                ctx.fillRect(sx, sy + 3, TILE, 1);
                ctx.fillRect(sx, sy + 12, TILE, 1);
                return true;
            }
            if (tile === "%") {
                ctx.fillStyle = "#1c6fb8";
                ctx.fillRect(sx, sy, TILE, TILE);
                ctx.fillStyle = "#8fd0ff";
                const dash = (Math.floor(state.time * 30) + tx * 5 + ty * 3) % 16;
                ctx.fillRect(sx + dash, sy + 4 + (ty % 2) * 6, 5, 1);
                ctx.fillRect(sx + (dash + 8) % 16, sy + 9, 3, 1);
                if (ty > 0 && tiles[ty - 1][tx] !== "%") {
                    ctx.fillStyle = "#c5e6ff";
                    ctx.globalAlpha = 0.5 + 0.3 * Math.sin(state.time * 5 + tx);
                    ctx.fillRect(sx, sy, TILE, 2);
                    ctx.globalAlpha = 1;
                }
                return true;
            }
            if (tile === "U") {
                ctx.fillStyle = "#2f9be8";
                ctx.fillRect(sx, sy + 4, TILE, 3);
                ctx.fillStyle = "#e0c04b";
                ctx.fillRect(sx, sy + 8, TILE, 2);
                ctx.fillStyle = "#4be07a";
                ctx.fillRect(sx, sy + 11, TILE, 2);
                return true;
            }
        }

        if (theme === THEMES.desk) {
            if (tile === "#") {
                ctx.fillStyle = theme.ground;
                ctx.fillRect(sx, sy, TILE, TILE);
                ctx.fillStyle = "#74492a";
                ctx.fillRect(sx, sy + 5 + (tx % 3), TILE, 1);
                ctx.fillRect(sx + (tx * 5) % 12, sy + 11, 6, 1);
                if (ty > 0 && tiles[ty - 1][tx] === ".") {
                    ctx.fillStyle = "#a56d3c";
                    ctx.fillRect(sx, sy, TILE, 2);
                }
                return true;
            }
            if (tile === "S") {
                // a keycap with its letter
                ctx.fillStyle = "#cfd0d4";
                ctx.fillRect(sx, sy + 2, TILE, TILE - 2);
                ctx.fillStyle = "#eeeef0";
                ctx.fillRect(sx + 1, sy + 1, TILE - 2, 10);
                ctx.fillStyle = "#9a9ba0";
                ctx.fillRect(sx + 1, sy + 11, TILE - 2, 1);
                ctx.fillStyle = "#2a2a30";
                ctx.font = "7px monospace";
                ctx.fillText(KEYCAPS[(tx * 7) % KEYCAPS.length], sx + 5, sy + 9);
                return true;
            }
            if (tile === "G") {
                // a stack of paper
                ctx.fillStyle = "#f4f4f4";
                ctx.fillRect(sx, sy + 4, TILE, 12);
                ctx.fillStyle = "#d8d8d8";
                ctx.fillRect(sx, sy + 8, TILE, 1);
                ctx.fillRect(sx, sy + 12, TILE, 1);
                return true;
            }
        }

        if (theme === THEMES.editor) {
            if (tile === "G") {
                ctx.fillStyle = theme.panel;
                ctx.fillRect(sx, sy, TILE, TILE);
                ctx.fillStyle = "#3c3c41";
                ctx.fillRect(sx, sy, TILE, 1);
                ctx.fillRect(sx, sy, 1, TILE);
                if (tx % 4 === 0 && ty > 0 && ty < MAP_H - 3) {
                    ctx.fillStyle = "#858585";
                    ctx.font = "6px monospace";
                    ctx.fillText(String(ty * 10 + (tx % 10)), sx + 3, sy + 10);
                }
                return true;
            }
            if (tile === "A") {
                // a database cylinder
                ctx.fillStyle = "#3a6ea0";
                ctx.fillRect(sx + 2, sy + 2, 12, 13);
                ctx.fillStyle = "#4ec9b0";
                ctx.fillRect(sx + 2, sy + 1, 12, 2);
                ctx.fillRect(sx + 2, sy + 6, 12, 1);
                ctx.fillRect(sx + 2, sy + 11, 12, 1);
                return true;
            }
        }

        if (theme === THEMES.obelisk && tile === "#") {
            ctx.fillStyle = theme.ground;
            ctx.fillRect(sx, sy, TILE, TILE);
            ctx.fillStyle = "#d3d9de";
            ctx.fillRect(sx + (tx * 5) % 11, sy + 6 + (ty % 3), 3, 1);
            if (ty > 0 && tiles[ty - 1][tx] === ".") {
                ctx.fillStyle = "#f4f6f7";
                ctx.fillRect(sx, sy, TILE, 2);
            }
            return true;
        }

        return false;
    }

    function drawTile(tile, tx, ty, sx, sy) {
        if (tile === ".") return;

        if (drawThemedTile(tile, tx, ty, sx, sy)) return;

        if (tile === "%") {
            ctx.fillStyle = theme.water;
            ctx.fillRect(sx, sy, TILE, TILE);
            return;
        }

        if (tile === "#") {
            ctx.fillStyle = theme.ground;
            ctx.fillRect(sx, sy, TILE, TILE);
            if (!isSolid(tx, ty - 1) && tiles[ty - 1] && tiles[ty - 1][tx] !== "D") {
                ctx.fillStyle = theme.grass;
                ctx.fillRect(sx, sy, TILE, 3);
                ctx.fillStyle = theme.leavesLight;
                ctx.fillRect(sx + (tx * 5) % 12, sy - 1, 2, 1);
            }
            ctx.fillStyle = "rgba(0,0,0,0.25)";
            ctx.fillRect(sx + (tx * 7 + ty * 3) % 12, sy + 6 + (tx * 3) % 8, 2, 2);
            return;
        }

        if (tile === "S") {
            ctx.fillStyle = theme.stone;
            ctx.fillRect(sx, sy, TILE, TILE);
            ctx.fillStyle = "rgba(255,255,255,0.08)";
            ctx.fillRect(sx, sy, TILE, 2);
            ctx.fillStyle = "rgba(0,0,0,0.3)";
            ctx.fillRect(sx + 3, sy + 9, 6, 2);
            return;
        }

        if (tile === "W") {
            ctx.fillStyle = theme.wall;
            ctx.fillRect(sx, sy, TILE, TILE);
            ctx.fillStyle = "rgba(0,0,0,0.35)";
            ctx.fillRect(sx, sy + 7, TILE, 1);
            ctx.fillRect(sx + ((ty % 2) ? 8 : 0), sy, 1, 7);
            ctx.fillRect(sx + ((ty % 2) ? 0 : 8), sy + 8, 1, 8);
            if (theme === THEMES.sewer && (tx * 3 + ty * 5) % 7 === 0) {
                ctx.fillStyle = "#3f6a3a";
                ctx.fillRect(sx + 2, sy + 2, 4, 3);
            }
            return;
        }

        if (tile === "G") {
            ctx.fillStyle = theme.panel;
            ctx.fillRect(sx, sy, TILE, TILE);
            ctx.fillStyle = "rgba(0,0,0,0.12)";
            ctx.fillRect(sx, sy + TILE - 1, TILE, 1);
            ctx.fillRect(sx + TILE - 1, sy, 1, TILE);
            ctx.fillStyle = "rgba(255,255,255,0.7)";
            ctx.fillRect(sx, sy, TILE, 1);
            return;
        }

        if (tile === "F") {
            // Door frame: a pillar that rises from the door to the ceiling
            ctx.fillStyle = theme === THEMES.lab || theme === THEMES.jungle ? "#c9d1d6" : theme.wall;
            ctx.fillRect(sx + 2, sy, 12, TILE);
            ctx.fillStyle = "rgba(0,0,0,0.25)";
            ctx.fillRect(sx + 2, sy, 1, TILE);
            ctx.fillRect(sx + 13, sy, 1, TILE);
            ctx.fillRect(sx + 4, sy + 7, 8, 1);
            return;
        }

        if (tile === "T") {
            ctx.fillStyle = theme.trunk;
            ctx.fillRect(sx + 5, sy, 6, TILE);
            ctx.fillStyle = "rgba(0,0,0,0.3)";
            ctx.fillRect(sx + 9, sy, 2, TILE);
            return;
        }

        if (tile === "L") {
            ctx.fillStyle = theme.leaves;
            ctx.fillRect(sx, sy, TILE, TILE);
            ctx.fillStyle = theme.leavesLight;
            ctx.fillRect(sx + 2 + (tx % 3) * 2, sy + 2 + (ty % 2) * 3, 5, 4);
            return;
        }

        if (tile === "V") {
            ctx.fillStyle = "#2f6a2a";
            ctx.fillRect(sx + 3, sy, 2, TILE);
            ctx.fillRect(sx + 9, sy, 2, TILE);
            ctx.fillRect(sx + 6 + Math.floor(Math.sin(ty + state.time) * 1.5), sy, 2, TILE);
            ctx.fillStyle = "#4fa542";
            ctx.fillRect(sx + 1, sy + 3 + (ty % 3) * 2, 4, 2);
            ctx.fillRect(sx + 10, sy + 8 + (ty % 2) * 3, 4, 2);
            ctx.fillRect(sx + 5, sy + 12, 3, 2);
            return;
        }

        if (tile === "~") {
            ctx.fillStyle = theme.water;
            ctx.fillRect(sx, sy, TILE, TILE);
            ctx.fillStyle = "rgba(255,255,255,0.18)";
            ctx.fillRect(sx + Math.floor((Math.sin(state.time * 2 + tx) + 1) * 4), sy + 2, 6, 1);
            return;
        }

        if (tile === "U") {
            ctx.fillStyle = "#3b4048";
            ctx.fillRect(sx, sy + 5, TILE, 7);
            ctx.fillStyle = "#5a6068";
            ctx.fillRect(sx, sy + 6, TILE, 1);
            ctx.fillStyle = "#23272c";
            ctx.fillRect(sx + 6, sy + 4, 3, 9);
            return;
        }

        if (tile === "A") {
            ctx.fillStyle = "#9fd6e0";
            ctx.fillRect(sx + 2, sy + 1, 12, 15);
            ctx.fillStyle = "#d9f2f7";
            ctx.fillRect(sx + 3, sy + 2, 2, 12);
            ctx.fillStyle = "#3d8f3a";
            const wob = Math.floor(Math.sin(state.time * 2 + tx) * 1.5);
            ctx.fillRect(sx + 5, sy + 9 + wob, 6, 2);
            ctx.fillRect(sx + 9, sy + 6 + wob, 3, 3);
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(sx + 6 + (Math.floor(state.time * 3 + tx) % 5), sy + 3 + (Math.floor(state.time * 4) % 6), 1, 1);
            ctx.fillStyle = "#6b7378";
            ctx.fillRect(sx + 1, sy, 14, 1);
            ctx.fillRect(sx + 1, sy + 15, 14, 1);
            return;
        }

        if (tile === "[" || tile === "]") {
            // Specimen cage: bars over a dark box; a broken cage hangs open
            ctx.fillStyle = tile === "[" ? "#1c1c22" : "#2a2a30";
            ctx.fillRect(sx + 1, sy + 1, 14, 15);
            ctx.fillStyle = "#c0c8cd";
            for (let i = 2; i < 15; i += 4) {
                if (tile === "]" && i > 6) { ctx.fillRect(sx + i + 3, sy + 4, 1, 12); continue; }
                ctx.fillRect(sx + i, sy + 1, 1, 15);
            }
            ctx.fillRect(sx + 1, sy + 1, 14, 1);
            ctx.fillRect(sx + 1, sy + 15, 14, 1);
            if (tile === "]") {
                ctx.fillStyle = "#6e1a1a";
                ctx.fillRect(sx + 3, sy + 13, 6, 2);
            }
            return;
        }

        if (tile === "k") {
            ctx.fillStyle = "#b9c2c8";
            ctx.fillRect(sx, sy, TILE, TILE);
            ctx.fillStyle = "#8a949a";
            ctx.fillRect(sx + 2, sy + 1, 5, TILE - 2);
            ctx.fillRect(sx + 9, sy + 1, 5, TILE - 2);
            ctx.fillStyle = "#1c1c22";
            ctx.fillRect(sx + 6, sy + 5, 4, 6);
            ctx.fillStyle = Math.floor(state.time * 2) % 2 ? "#ff3b3b" : "#7a1f1f";
            ctx.fillRect(sx + 7, sy + 6, 2, 2);
            return;
        }

        if (tile === "o") {
            ctx.fillStyle = theme === THEMES.lab || theme === THEMES.jungle ? "#7a8a92" : "#050505";
            ctx.fillRect(sx, sy, TILE, TILE);
            ctx.fillStyle = "#4bd0e0";
            ctx.globalAlpha = 0.5 + 0.3 * Math.sin(state.time * 4);
            ctx.fillRect(sx, sy, 1, TILE);
            ctx.fillRect(sx + TILE - 1, sy, 1, TILE);
            ctx.globalAlpha = 1;
            return;
        }

        if (tile === "D") {
            if (state.doorOpen) {
                ctx.fillStyle = theme === THEMES.lab ? "#7a8a92" : "#050505";
                ctx.fillRect(sx, sy, TILE, TILE);
                ctx.fillStyle = theme.accent;
                ctx.globalAlpha = 0.5 + 0.3 * Math.sin(state.time * 4);
                ctx.fillRect(sx, sy, 1, TILE);
                ctx.fillRect(sx + TILE - 1, sy, 1, TILE);
                ctx.globalAlpha = 1;
            } else if (LEVEL.gate) {
                // Firewall gate: humming orange bars
                ctx.fillStyle = "#2a1a10";
                ctx.fillRect(sx, sy, TILE, TILE);
                ctx.fillStyle = Math.floor(state.time * 8) % 2 ? "#ff8a2a" : "#ffb347";
                for (let i = 2; i < TILE; i += 4) ctx.fillRect(sx + i, sy, 2, TILE);
                ctx.fillStyle = "#ffffff";
                ctx.globalAlpha = 0.5;
                ctx.fillRect(sx + 2 + (Math.floor(state.time * 20) % 12), sy + (Math.floor(state.time * 9) % TILE), 2, 1);
                ctx.globalAlpha = 1;
            } else {
                ctx.fillStyle = theme.door;
                ctx.fillRect(sx, sy, TILE, TILE);
                ctx.fillStyle = "rgba(255,255,255,0.12)";
                ctx.fillRect(sx + 2, sy + 1, 5, TILE - 2);
                ctx.fillRect(sx + 9, sy + 1, 5, TILE - 2);
                ctx.fillStyle = "#c0302f";
                ctx.fillRect(sx + 7, sy + 7, 2, 2);
            }
        }
    }

    function drawEntity(entity, sx, sy) {
        const bob = Math.sin(state.time * 3) * 2;

        if (entity.type === "npc") {
            const y = sy + bob;
            ctx.fillStyle = "#8d8d94";
            ctx.fillRect(sx + 3, y + 5, 10, 7);
            ctx.fillStyle = "#c8c8d0";
            ctx.fillRect(sx + 4, y + 6, 8, 2);
            ctx.fillStyle = theme.accent;
            ctx.fillRect(sx + 6, y + 8, 4, 2);
            ctx.fillStyle = "#5a5a62";
            ctx.fillRect(sx + 7, y + 3, 2, 2);
            ctx.fillRect(sx + 2 + (Math.floor(state.time * 20) % 2) * 6, y + 2, 6, 1);
            ctx.fillStyle = "#3a3a40";
            ctx.fillRect(sx + 4, y + 12, 2, 2);
            ctx.fillRect(sx + 10, y + 12, 2, 2);
            return;
        }

        if (entity.type === "doctor") {
            drawDoctor(sx, sy, false, 0, 1);
            return;
        }

        if (entity.type === "sign") {
            ctx.fillStyle = theme === THEMES.lab ? "#8a949a" : "#5a4a3a";
            ctx.fillRect(sx + 7, sy + 6, 2, 10);
            ctx.fillStyle = theme === THEMES.lab ? "#f7f9fa" : "#6a5030";
            ctx.fillRect(sx + 1, sy + 2, 14, 7);
            ctx.fillStyle = theme === THEMES.lab ? "#4a5560" : "#e0d0a0";
            ctx.fillRect(sx + 3, sy + 4, 6, 1);
            ctx.fillRect(sx + 3, sy + 6, 9, 1);
            return;
        }

        if (entity.type === "terminal") {
            const offline = LEVEL.boss && !state.bossDefeated;
            ctx.fillStyle = "#1a1a1f";
            ctx.fillRect(sx + 1, sy + 2, 14, 14);
            ctx.fillStyle = state.solved ? theme.accent : (offline ? "#2a2a2f" : "#0f2a18");
            ctx.fillRect(sx + 3, sy + 4, 10, 7);
            if (!state.solved && !offline) {
                ctx.fillStyle = theme.accent;
                ctx.fillRect(sx + 4, sy + 5, 5, 1);
                ctx.fillRect(sx + 4, sy + 7, 3, 1);
                if (Math.floor(state.time * 2) % 2) ctx.fillRect(sx + 8, sy + 9, 2, 1);
            }
            ctx.fillStyle = "#3a3a44";
            ctx.fillRect(sx + 3, sy + 12, 10, 2);
            return;
        }

        if (entity.type === "mentorbot") {
            const y = sy + Math.floor(Math.sin(state.time * 2) * 1);
            ctx.fillStyle = "#3c3c41";
            ctx.fillRect(sx + 1, y + 4, 10, 9);
            ctx.fillStyle = "#4ec9b0";
            ctx.fillRect(sx + 2, y + 5, 8, 5);
            ctx.fillStyle = "#1e1e1e";
            ctx.fillRect(sx + 3, y + 6, 2, 1);
            ctx.fillRect(sx + 7, y + 6, 2, 1);
            ctx.fillRect(sx + 4, y + 8, 4, 1);
            ctx.fillStyle = "#858585";
            ctx.fillRect(sx + 5, y + 1, 2, 3);
            ctx.fillRect(sx + 3, y + 13, 2, 3);
            ctx.fillRect(sx + 7, y + 13, 2, 3);
            ctx.fillStyle = Math.floor(state.time * 3) % 2 ? "#4ec9b0" : "#1e1e1e";
            ctx.fillRect(sx + 5, y, 2, 1);
            return;
        }

        if (entity.type === "obelisk") {
            const lit = (LEVEL.beams || []).includes(LEVEL.course) || (state.cutscene && state.cutscene.t > 0.4);
            ctx.fillStyle = "#f7f9fb";
            ctx.fillRect(sx + 6, sy, 20, entity.h);
            ctx.fillStyle = "#dfe4e8";
            ctx.fillRect(sx + 22, sy, 4, entity.h);
            ctx.fillRect(sx + 6, sy, 20, 2);
            ctx.fillStyle = "#c9d1d6";
            ctx.fillRect(sx + 4, sy + entity.h - 6, 24, 6);
            // the four beam slots on its face
            BEAM_SLOTS.forEach((slug, i) => {
                const on = (LEVEL.beams || []).includes(slug) || (slug === LEVEL.course && lit);
                ctx.fillStyle = on ? BEAM_COLORS[slug] : "#e6e9ec";
                ctx.fillRect(sx + 9 + i * 4, sy + 10, 2, entity.h - 24);
            });
            return;
        }

        if (entity.type === "button") {
            ctx.fillStyle = "#c9d1d6";
            ctx.fillRect(sx + 3, sy + 8, 10, 8);
            ctx.fillStyle = entity.pressed ? "#4be07a" : (Math.floor(state.time * 2) % 2 ? "#ff3b3b" : "#c0302f");
            ctx.fillRect(sx + 5, sy + (entity.pressed ? 7 : 5), 6, 3);
            ctx.fillStyle = "#f7f9fb";
            ctx.fillRect(sx + 6, sy + (entity.pressed ? 7 : 5), 1, 1);
            return;
        }

        if (entity.type === "wire" && theme === THEMES.desk) {
            // The HDMI port you came out of
            ctx.fillStyle = "#1c1c22";
            ctx.fillRect(sx - 2, sy + 4, 20, 10);
            ctx.fillStyle = "#101014";
            ctx.fillRect(sx, sy + 6, 16, 6);
            ctx.fillStyle = "#e0c04b";
            for (let i = 0; i < 6; i++) ctx.fillRect(sx + 2 + i * 2, sy + 8, 1, 3);
            if (Math.random() < 0.15) {
                particles.push({ x: entity.x + 8, y: entity.y + 9, vx: 1 + Math.random(), vy: (Math.random() - 0.5), life: 8, color: "#4bd0e0" });
            }
            return;
        }

        if (entity.type === "wire") {
            // A thick cable out of the hillside, mouth crackling with sparks
            ctx.fillStyle = "#1c1c22";
            ctx.fillRect(sx - 20, sy + 4, 30, 8);
            ctx.fillStyle = "#3a3a44";
            ctx.fillRect(sx - 20, sy + 5, 30, 1);
            ctx.fillStyle = "#101014";
            ctx.fillRect(sx + 8, sy + 2, 4, 12);
            ctx.fillStyle = "#050505";
            ctx.fillRect(sx + 10, sy + 5, 3, 6);
            if (Math.random() < 0.35) {
                particles.push({ x: entity.x + 12, y: entity.y + 8, vx: 1 + Math.random() * 2.2, vy: (Math.random() - 0.6) * 2, life: 8 + Math.random() * 10, color: Math.random() < 0.5 ? "#9dffb0" : "#ffffff" });
            }
            ctx.fillStyle = Math.floor(state.time * 30) % 3 === 0 ? "#d8ffe0" : "#7bff8a";
            ctx.fillRect(sx + 12, sy + 6 + (Math.floor(state.time * 40) % 4), 2, 1);
            return;
        }

        if (entity.type === "vent") {
            ctx.fillStyle = "#8a949a";
            ctx.fillRect(sx + 1, sy + 1, 14, 14);
            ctx.fillStyle = "#3a4048";
            for (let i = 3; i < 14; i += 3) ctx.fillRect(sx + 2, sy + i, 12, 1);
            ctx.fillStyle = countItem(ITEM_KEY) ? "#4be07a" : "#ff3b3b";
            ctx.fillRect(sx + 12, sy + 2, 2, 2);
            ctx.globalAlpha = 0.5 + 0.3 * Math.sin(state.time * 3);
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(sx + 6, sy - 6 + Math.floor(Math.sin(state.time * 4) * 2), 4, 1);
            ctx.globalAlpha = 1;
            return;
        }

        if (entity.type === "cage") {
            // Label above the cage so the malware type is readable
            ctx.font = "7px monospace";
            ctx.fillStyle = theme === THEMES.lab ? "#1f2a30" : "#ffffff";
            ctx.fillText(entity.label.name, sx - 2, sy - 3);
            if (!entity.broken) {
                const wig = Math.floor(Math.sin(state.time * 6 + entity.x) * 1);
                ctx.fillStyle = "#111";
                ctx.fillRect(sx + 4 + wig, sy + 9, 8, 4);
                ctx.fillStyle = "#ff2a2a";
                ctx.fillRect(sx + 5 + wig, sy + 10, 1, 1);
                ctx.fillRect(sx + 7 + wig, sy + 10, 1, 1);
            }
            return;
        }

        if (entity.type === "item") {
            if (entity.taken) return;
            const y = sy + bob;
            if (entity.item === ITEM_SWORD) {
                ctx.fillStyle = "#dfe6ea";
                ctx.fillRect(sx, y + 3, 9, 2);
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(sx, y + 3, 6, 1);
                ctx.fillStyle = "#ffd700";
                ctx.fillRect(sx + 8, y + 1, 1, 6);
                ctx.fillStyle = "#6b4a2b";
                ctx.fillRect(sx + 9, y + 3, 2, 2);
            } else if (entity.item === ITEM_CODE) {
                ctx.fillStyle = "#f4f6f7";
                ctx.fillRect(sx, y + 1, 10, 7);
                ctx.fillStyle = "#4bd0e0";
                ctx.fillRect(sx + 1, y + 2, 3, 3);
                ctx.fillStyle = "#1c1c22";
                ctx.fillRect(sx + 5, y + 3, 4, 1);
                ctx.fillRect(sx + 5, y + 5, 3, 1);
            } else if (entity.item === ITEM_KEY) {
                ctx.fillStyle = "#ffd700";
                ctx.fillRect(sx + 1, y + 2, 4, 4);
                ctx.fillRect(sx + 5, y + 3, 5, 2);
                ctx.fillRect(sx + 8, y + 5, 1, 2);
                ctx.fillStyle = "#1c1c22";
                ctx.fillRect(sx + 2, y + 3, 2, 2);
            } else if (entity.item === ITEM_CHIP) {
                ctx.fillStyle = "#0e2d1a";
                ctx.fillRect(sx, y, 8, 8);
                ctx.fillStyle = theme.accent;
                ctx.fillRect(sx + 2, y + 2, 4, 4);
                ctx.fillStyle = "#cfe";
                ctx.fillRect(sx + 3, y + 3, 1, 1);
            } else if (entity.item === ITEM_DAGGER) {
                ctx.fillStyle = "#dfe6ea";
                ctx.fillRect(sx + 1, y + 3, 7, 2);
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(sx + 1, y + 3, 4, 1);
                ctx.fillStyle = "#6b4a2b";
                ctx.fillRect(sx + 8, y + 2, 2, 4);
                ctx.fillStyle = "#3a2a1a";
                ctx.fillRect(sx + 7, y + 1, 1, 6);
            } else {
                ctx.fillStyle = "#ff4fa3";
                ctx.fillRect(sx + 2, y + 2, 4, 4);
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(sx + 3, y + 2, 1, 1);
                ctx.fillStyle = "#ffd1e8";
                ctx.fillRect(sx, y + 3, 2, 2);
                ctx.fillRect(sx + 6, y + 3, 2, 2);
            }
            return;
        }

        if (entity.type === "exit") {
            ctx.globalAlpha = state.doorOpen ? 0.6 + 0.3 * Math.sin(state.time * 5) : 0.15;
            ctx.fillStyle = theme.accent;
            const ay = sy + 14 + Math.sin(state.time * 4) * 2;
            ctx.fillRect(sx + 7, ay, 2, 8);
            ctx.fillRect(sx + 5, ay + 2, 6, 1);
            ctx.fillRect(sx + 6, ay + 1, 4, 1);
            ctx.globalAlpha = 1;
        }
    }

    function drawDoctor(sx, sy, hostile, flash, dir) {
        const coat = flash ? "#ffffff" : "#f4f4f4";
        ctx.fillStyle = "#e8b990";
        ctx.fillRect(sx + 3, sy + 1, 6, 5);
        ctx.fillStyle = hostile ? "#3a2a1a" : "#8a8a8a";
        ctx.fillRect(sx + 3, sy, 6, 2);
        ctx.fillStyle = "#101010";
        ctx.fillRect(sx + (dir > 0 ? 6 : 4), sy + 3, 2, 1);
        ctx.fillStyle = "#222";
        ctx.fillRect(sx + 3, sy + 3, 6, 1);
        ctx.fillStyle = coat;
        ctx.fillRect(sx + 2, sy + 6, 8, 7);
        ctx.fillStyle = hostile ? "#d0302f" : "#7fb3c9";
        ctx.fillRect(sx + 5, sy + 7, 2, 4);
        if (!hostile) {
            ctx.fillStyle = "#b9c2c8";
            ctx.fillRect(sx + (dir > 0 ? 9 : 0), sy + 8, 3, 4);
        }
        ctx.fillStyle = "#2a2f36";
        ctx.fillRect(sx + 3, sy + 13, 2, 3);
        ctx.fillRect(sx + 7, sy + 13, 2, 3);
    }

    function drawEnemy(enemy, sx, sy) {
        if (!enemy.alive) return;
        const flash = enemy.hitFlash > 0;

        if (enemy.type === "snake") {
            const wig = Math.floor(Math.sin(state.time * 8 + enemy.x) * 1);
            ctx.fillStyle = flash ? "#ffffff" : "#3d8f3a";
            ctx.fillRect(sx, sy + 2 + wig, enemy.w, 6);
            ctx.fillStyle = flash ? "#ffffff" : "#2a6a28";
            for (let i = 2; i < enemy.w - 2; i += 4) ctx.fillRect(sx + i, sy + 3 + wig, 2, 4);
            const headX = enemy.dir > 0 ? sx + enemy.w - 5 : sx;
            ctx.fillStyle = flash ? "#ffffff" : "#4aa845";
            ctx.fillRect(headX, sy + wig, 5, 6);
            ctx.fillStyle = "#f2e33a";
            ctx.fillRect(headX + (enemy.dir > 0 ? 3 : 1), sy + 1 + wig, 1, 1);
            if (Math.floor(state.time * 4) % 3 === 0) {
                ctx.fillStyle = "#e04040";
                ctx.fillRect(enemy.dir > 0 ? headX + 5 : headX - 2, sy + 3 + wig, 2, 1);
            }
            return;
        }

        if (enemy.type === "sniffer") {
            // A hooded figure crouched over the cable with a tap clip
            ctx.fillStyle = flash ? "#ffffff" : "#1a1a22";
            ctx.fillRect(sx + 2, sy + 2, 8, 6);
            ctx.fillRect(sx + 1, sy + 7, 10, 8);
            ctx.fillStyle = flash ? "#ffffff" : "#2c2c36";
            ctx.fillRect(sx + 3, sy + 1, 6, 2);
            ctx.fillStyle = "#ff3b3b";
            ctx.fillRect(sx + (enemy.dir > 0 ? 7 : 3), sy + 4, 2, 1);
            ctx.fillStyle = "#2f9be8";
            ctx.fillRect(enemy.dir > 0 ? sx + 11 : sx - 3, sy + 12, 4, 2);
            ctx.fillStyle = "#3a3a44";
            ctx.fillRect(sx + 3, sy + 15, 2, 1);
            ctx.fillRect(sx + 7, sy + 15, 2, 1);
            return;
        }

        if (enemy.type === "hostile") {
            drawDoctor(sx, sy, true, flash, enemy.dir);
            if (enemy.carries) {
                // A lanyard with the door code
                ctx.fillStyle = "#4bd0e0";
                ctx.fillRect(sx + 5, sy + 9, 3, 2);
            }
            return;
        }

        if (enemy.type === "bug") {
            const leg = Math.floor(state.time * 14 + enemy.x) % 2;
            ctx.fillStyle = flash ? "#ffffff" : "#111111";
            ctx.fillRect(sx + 1, sy + 1, 8, 4);
            ctx.fillRect(sx + (enemy.dir > 0 ? 8 : 0), sy + 2, 2, 3);
            ctx.fillStyle = flash ? "#ffffff" : "#2a2a2a";
            for (let i = 0; i < 3; i++) ctx.fillRect(sx + 1 + i * 3 + leg, sy + 5, 1, 1);
            ctx.fillStyle = "#ff2a2a";
            ctx.fillRect(sx + (enemy.dir > 0 ? 8 : 1), sy + 2, 1, 1);
            if (enemy.label && Math.abs((player.x) - enemy.x) < 70) {
                ctx.font = "7px monospace";
                ctx.fillStyle = theme === THEMES.lab && state.lightsOn ? "#1f2a30" : "#ffffff";
                ctx.fillText(enemy.label.name, sx - 6, sy - 3);
            }
            return;
        }

        if (enemy.type === "vex") {
            const stagger = enemy.state === "rest";
            const lean = stagger ? Math.floor(Math.sin(state.time * 10) * 1.5) : 0;
            drawDoctor(sx + 1 + lean, sy + 2, true, flash, enemy.dir);
            // Bigger coat, glasses, a syringe in hand
            ctx.fillStyle = flash ? "#ffffff" : "#f4f4f4";
            ctx.fillRect(sx + lean, sy + 8, 14, 8);
            ctx.fillStyle = "#101010";
            ctx.fillRect(sx + 4 + lean, sy + 5, 6, 1);
            ctx.fillStyle = "#e8f2ff";
            ctx.fillRect(enemy.dir > 0 ? sx + 13 : sx - 3, sy + 10, 5, 2);
            // status + health
            ctx.fillStyle = "rgba(0,0,0,0.6)";
            ctx.fillRect(sx - 6, sy - 12, 26, 4);
            ctx.fillStyle = stagger ? theme.accent : "#d0302f";
            ctx.fillRect(sx - 6, sy - 12, Math.round(26 * enemy.hp / enemy.maxHp), 4);
            ctx.font = "7px monospace";
            ctx.fillStyle = stagger ? theme.accent : (theme === THEMES.lab ? "#1f2a30" : "#ffffff");
            ctx.fillText(stagger ? "STAGGERED" : (enemy.state === "throw" ? "!!!" : "DR. VEX"), sx - 8, sy - 15);
            return;
        }

        if (enemy.type === "brain") {
            const pulse = Math.floor(Math.sin(state.time * 2.5) * 1.5);
            const pink = flash ? "#ffffff" : "#ff9ad0";
            const dark = flash ? "#ffffff" : "#d0608f";
            ctx.fillStyle = dark;
            ctx.fillRect(sx + 2, sy + 6 - pulse, enemy.w - 4, enemy.h - 6 + pulse);
            ctx.fillStyle = pink;
            ctx.fillRect(sx + 6, sy + 2 - pulse, enemy.w - 12, enemy.h - 6 + pulse);
            ctx.fillRect(sx + 2, sy + 10 - pulse, enemy.w - 4, 6);
            ctx.fillStyle = dark;
            for (let i = 4; i < enemy.w - 4; i += 7) ctx.fillRect(sx + i, sy + 4 - pulse + (i % 3), 2, 8);
            ctx.fillRect(sx + enemy.w / 2 - 1, sy + 2 - pulse, 2, enemy.h - 4);
            // Wires into the walls
            ctx.fillStyle = "#3a4048";
            ctx.fillRect(sx - 40, sy + 12, 42, 2);
            ctx.fillRect(sx + enemy.w - 2, sy + 12, 42, 2);
            ctx.fillStyle = Math.floor(state.time * 6) % 2 ? "#4bd0e0" : "#1c1c22";
            ctx.fillRect(sx - 30 + (Math.floor(state.time * 30) % 28), sy + 12, 3, 2);
            ctx.fillRect(sx + enemy.w + 30 - (Math.floor(state.time * 30) % 28), sy + 12, 3, 2);
            // health
            ctx.fillStyle = "rgba(0,0,0,0.6)";
            ctx.fillRect(sx, sy - 12, enemy.w, 4);
            ctx.fillStyle = "#ff9ad0";
            ctx.fillRect(sx, sy - 12, Math.round(enemy.w * enemy.hp / enemy.maxHp), 4);
            ctx.font = "7px monospace";
            ctx.fillStyle = theme === THEMES.lab ? "#1f2a30" : "#ffffff";
            ctx.fillText("THE BRAIN - STOMP IT", sx - 8, sy - 15);
            return;
        }

        if (enemy.type === "boss") {
            const body = flash ? "#ffffff" : "#2f7d2c";
            const dark = flash ? "#ffffff" : "#1e5a1c";
            const breathe = Math.floor(Math.sin(state.time * 3) * 1.5);

            // coils
            ctx.fillStyle = body;
            ctx.fillRect(sx + 4, sy + 10 + breathe, 32, 12);
            ctx.fillRect(sx + 10, sy + 4 + breathe, 22, 8);
            ctx.fillStyle = dark;
            for (let i = 6; i < 34; i += 6) ctx.fillRect(sx + i, sy + 12 + breathe, 3, 8);

            // head
            const headX = enemy.dir > 0 ? sx + 26 : sx + 2;
            ctx.fillStyle = body;
            ctx.fillRect(headX, sy + 2, 12, 9);
            ctx.fillStyle = "#f2e33a";
            ctx.fillRect(headX + (enemy.dir > 0 ? 8 : 2), sy + 4, 2, 2);
            ctx.fillRect(headX + (enemy.dir > 0 ? 8 : 2), sy + 7, 2, 1);

            if (enemy.state === "volley" || (enemy.state === "charge" && enemy.timer > 60)) {
                ctx.fillStyle = "#ff7a1f";
                ctx.fillRect(headX + (enemy.dir > 0 ? 10 : -2), sy + 8, 4, 2);
            }

            // status + health
            ctx.fillStyle = "rgba(0,0,0,0.6)";
            ctx.fillRect(sx, sy - 12, 40, 4);
            ctx.fillStyle = enemy.state === "rest" ? theme.accent : "#d0302f";
            ctx.fillRect(sx, sy - 12, Math.round(40 * enemy.hp / enemy.maxHp), 4);
            ctx.font = "7px monospace";
            ctx.fillStyle = enemy.state === "rest" ? theme.accent : (theme === THEMES.lab ? "#1f2a30" : "#ffffff");
            ctx.fillText(enemy.state === "rest" ? "VULNERABLE" : (enemy.state === "volley" ? "!!!" : "..."), sx + 2, sy - 15);
        }
    }

    function drawPrompt(cx, cy) {
        const y = cy + Math.sin(state.time * 6) * 1.5;
        ctx.fillStyle = "#101010";
        ctx.fillRect(cx - 4, y - 4, 9, 9);
        ctx.fillStyle = "#f0f0f0";
        ctx.fillRect(cx - 3, y - 3, 7, 7);
        ctx.fillStyle = "#101010";
        ctx.fillRect(cx - 1, y - 2, 4, 1);
        ctx.fillRect(cx - 1, y, 3, 1);
        ctx.fillRect(cx - 1, y + 2, 4, 1);
        ctx.fillRect(cx - 1, y - 2, 1, 5);
    }


    /* -----------------------------------------------------
       MATRIX INTRO ("loading into the sim")
    ----------------------------------------------------- */

    let skipIntro = false;

    function playIntro() {
        return new Promise(function (resolve) {

            state.phase = "intro";
            skipIntro = false;

            const W = 640, H = 384, CELL = 8;
            canvas.width = W;
            canvas.height = H;
            ctx.imageSmoothingEnabled = false;

            const columns = Math.floor(W / CELL);
            const cycle = H + 120;
            const drops = [];
            for (let i = 0; i < columns; i++) {
                drops.push({ offset: Math.random() * cycle, speed: 0.12 + Math.random() * 0.24 });
            }

            const mask = CyberSprite.characterMask(CHARACTER);
            const maskW = mask[0].length, maskH = mask.length;
            const scale = 8;
            const originX = Math.floor((W - maskW * scale) / 2);
            const originY = Math.floor((H - maskH * scale) / 2);

            const RAIN = 2400, ASSEMBLE = 1700, REVEAL = 1100, HOLD = 500;
            const total = RAIN + ASSEMBLE + REVEAL + HOLD;
            const start = performance.now();

            ctx.font = "8px monospace";

            function frame(now) {
                const t = now - start;

                if (skipIntro || t > total) {
                    canvas.width = VIEW_W;
                    canvas.height = VIEW_H;
                    ctx.imageSmoothingEnabled = false;
                    resolve();
                    return;
                }

                ctx.fillStyle = "rgba(0,0,0,0.22)";
                ctx.fillRect(0, 0, W, H);

                const assembleProgress = Math.max(0, Math.min(1, (t - RAIN) / ASSEMBLE));
                const revealProgress = Math.max(0, Math.min(1, (t - RAIN - ASSEMBLE) / REVEAL));
                const rainAlpha = 1 - revealProgress;

                drops.forEach((drop, i) => {
                    const x = i * CELL;
                    const headY = ((drop.offset + t * drop.speed * (1 - assembleProgress * 0.6)) % cycle) - 100;
                    for (let k = 0; k < 9; k++) {
                        const gy = headY - k * CELL;
                        if (gy < -CELL || gy > H + CELL) continue;
                        ctx.globalAlpha = rainAlpha * (k === 0 ? 1 : 0.85 - k * 0.09);
                        ctx.fillStyle = k === 0 ? "#d8ffe0" : "#22b850";
                        ctx.fillText(((i * 13 + k * 7 + Math.floor(t / 80)) % 2) ? "1" : "0", x, gy);
                    }
                });
                ctx.globalAlpha = 1;

                if (assembleProgress > 0) {
                    const rowsLit = Math.floor(assembleProgress * (maskH + 2));
                    for (let my = 0; my < maskH; my++) {
                        for (let mx = 0; mx < maskW; mx++) {
                            if (!mask[my][mx] || my > rowsLit) continue;
                            const px = originX + mx * scale;
                            const py = originY + my * scale;
                            ctx.fillStyle = "#031a0a";
                            ctx.fillRect(px, py, scale, scale);
                            ctx.fillStyle = (mx + my + Math.floor(t / 90)) % 3 === 0 ? "#d8ffe0" : "#2fd45e";
                            ctx.globalAlpha = 1 - revealProgress;
                            ctx.fillText(((mx * 7 + my * 3 + Math.floor(t / 120)) % 2) ? "1" : "0", px, py + 7);
                            ctx.globalAlpha = 1;
                        }
                    }
                }

                if (revealProgress > 0) {
                    ctx.globalAlpha = revealProgress;
                    CyberSprite.drawCharacter(ctx, CHARACTER, originX, originY, scale, 1, 0);
                    ctx.globalAlpha = 1;
                }

                if (t > RAIN + ASSEMBLE * 0.5) {
                    ctx.globalAlpha = Math.min(1, (t - RAIN - ASSEMBLE * 0.5) / 600);
                    ctx.fillStyle = "#8fffb0";
                    ctx.font = "10px monospace";
                    ctx.fillText("LOADING RECRUIT INTO " + LEVEL.zone.toUpperCase() + "...", 16, H - 16);
                    ctx.font = "8px monospace";
                    ctx.globalAlpha = 1;
                }

                requestAnimationFrame(frame);
            }

            requestAnimationFrame(frame);
        });
    }


    /* -----------------------------------------------------
       GAME FLOW
    ----------------------------------------------------- */

    function afterStory() {
        startTimer(false);
        const wire = entities.find((e) => e.type === "wire");
        if (wire) {
            // Spat out of the wire: a short launch with a burst of sparks
            player.x = wire.x + 12;
            player.y = wire.y;
            player.vx = 3.2;
            player.vy = -3.4;
            player.onGround = false;
            player.facing = 1;
            state.flash = 6;
            for (let i = 0; i < 26; i++) {
                particles.push({ x: wire.x + 12, y: wire.y + 8, vx: 1 + Math.random() * 3, vy: (Math.random() - 0.7) * 3, life: 15 + Math.random() * 20, color: Math.random() < 0.5 ? "#9dffb0" : "#ffffff" });
            }
        }
        const hasGuide = entities.some((e) => e.type === "npc");
        setObjective(hasGuide ? "Find " + GUIDE + " and press E" : LEVEL.goal);
        if (!hasGuide) state.metByte = true;
    }

    function beginLevel() {
        state.phase = "play";
        if (LEVEL.story) {
            startDialogue("—", [LEVEL.story], afterStory);
        } else {
            afterStory();
        }
    }

    function resumeLevel() {
        state.phase = "play";
        restoreCheckpoint(SAVED_CHECKPOINT.data);
        state.checkpoint = SAVED_CHECKPOINT.data;
        startTimer(true);
        startDialogue("—", ["Resumed at the last door you passed. Everything from there is as you left it."], null);
    }

    buttonStart.addEventListener("click", function () {
        overlayLesson.classList.add("hidden");
        gameWindow.focus();
        if (window.academyAudio) {
            academyAudio.loadSfx(LEVEL.sfx);
            academyAudio.play(LEVEL.music);
        }

        if (SAVED_CHECKPOINT) {
            // Starting over throws the old save away.
            fetch("/api/level/checkpoint", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ course: LEVEL.course, level: LEVEL.number, clear: true })
            }).catch(() => {});
        }

        if (LEVEL.intro) {
            playIntro().then(beginLevel);
        } else {
            beginLevel();
        }
    });

    const buttonResume = document.getElementById("btn-resume");
    if (buttonResume) {
        buttonResume.addEventListener("click", function () {
            overlayLesson.classList.add("hidden");
            gameWindow.focus();
            if (window.academyAudio) {
                academyAudio.loadSfx(LEVEL.sfx);
                academyAudio.play(LEVEL.music);
            }
            resumeLevel();
        });
    }

    buttonFullscreen.addEventListener("click", function () {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else if (gameWindow.requestFullscreen) {
            gameWindow.requestFullscreen();
        }
        gameWindow.focus();
    });


    /* -----------------------------------------------------
       MAIN LOOP (fixed 60 Hz physics)
    ----------------------------------------------------- */

    let last = performance.now();
    let accumulator = 0;
    const STEP = 1000 / 60;

    function loop(now) {
        const delta = Math.min(now - last, 100);
        last = now;
        accumulator += delta;
        state.time += delta / 1000;

        if (state.finale) state.finale.t += delta / 1000;
        if (state.cutscene && state.phase === "cutscene") stepCutscene(delta / 1000);

        if (state.phase !== "intro") {
            let steps = 0;
            while (accumulator >= STEP && steps < 4) {
                if (state.phase === "play") {
                    stepPlayer();
                    stepEnemies();
                }
                particles.forEach((p) => {
                    p.x += p.vx;
                    p.y += p.vy;
                    p.vy += p.confetti ? 0.015 : 0.05;
                    if (p.confetti) p.x += Math.sin(p.life / 7) * 0.4;
                    p.life -= 1;
                });
                for (let i = particles.length - 1; i >= 0; i--) if (particles[i].life <= 0) particles.splice(i, 1);
                accumulator -= STEP;
                steps += 1;
            }
            if (steps === 4) accumulator = 0;

            render();
            updateTimer();
        }

        requestAnimationFrame(loop);
    }

    // Inventory travels between levels: what was saved last, plus any
    // item this level guarantees (the dagger) if it is somehow missing.
    if (Array.isArray(SAVED_INVENTORY)) {
        SAVED_INVENTORY.slice(0, SLOT_COUNT).forEach((item, index) => { state.inventory[index] = item || null; });
    }
    (LEVEL.start_items || []).forEach((item) => {
        if (!state.inventory.includes(item)) addItem(item);
    });
    player.weapon = state.inventory.includes(ITEM_SWORD) ? ITEM_SWORD : ITEM_DAGGER;
    renderInventory();
    renderHearts();
    setObjective(LEVEL.no_lesson ? "Press START" : "Read the lesson, then press START");
    requestAnimationFrame(loop);

    // What the player has typed/arranged in the open terminal, as text,
    // so SecureMentor's CHECK MY CODE button can review it.
    function currentInput() {
        if (state.phase !== "challenge" || !challengeInput) return "";
        const value = challengeInput();
        const kind = LEVEL.challenge.type;
        if (kind === "python_lines" || kind === "text_answer") return String(value || "");
        if (kind === "fill_blank") {
            let i = 0;
            return LEVEL.challenge.code.map((line) => line.replace(/___/g, () => value.blanks[i++] || "___")).join("\n");
        }
        if (kind === "order_code") {
            return (value.order || []).map((idx) => LEVEL.challenge.pieces[idx]).join("\n");
        }
        if (kind === "wires") {
            return (value.map || []).map((p, i) => LEVEL.challenge.devices[i] + " -> " + (p >= 0 ? LEVEL.challenge.ports[p] : "(not connected)")).join("\n");
        }
        if (kind === "route_packets") {
            return (value.map || []).map((m, i) => LEVEL.challenge.packets[i].label + " (to " + LEVEL.challenge.packets[i].to + ") -> " + (m >= 0 ? LEVEL.challenge.machines[m].name : "(undelivered)")).join("\n");
        }
        if (kind === "ip_assign") return String(value || "");
        if (kind === "idea") return "Name: " + value.name + "\nPitch: " + value.pitch + "\nPages: " + value.pages.join(", ");
        return "";
    }

    // Debug handle for the browser console. step(n) advances the physics
    // n frames without waiting for the screen, handy when testing enemies.
    window.cyberGame = {
        state: state, player: player, keys: keys, level: LEVEL,
        enemies: enemies, entities: entities, projectiles: projectiles, tiles: tiles,
        currentInput: currentInput, snapshot: snapshot, restoreCheckpoint: restoreCheckpoint,
        step: function (n) {
            for (let i = 0; i < (n || 1); i++) {
                if (state.phase === "play") { stepPlayer(); stepEnemies(); }
            }
        }
    };

})();
