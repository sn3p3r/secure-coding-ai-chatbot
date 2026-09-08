/* =========================================================
   CYBER ACADEMY - 2D PIXEL GAME ENGINE

   One engine for every course. The level (map, dialogue,
   challenge, hints) comes from the JSON the server puts in
   #level-data. Answers are never checked here - they go to
   /api/level/submit and the server decides.

   Controls:  A / D move    W / SPACE jump    E talk / read / use
              F or click = use the item in the selected slot
              1-5 select slot    ENTER continue dialogue
========================================================= */

(function () {

    const levelElement = document.getElementById("level-data");

    if (!levelElement) {
        return;
    }

    const LEVEL = JSON.parse(levelElement.textContent);
    const CHARACTER = JSON.parse(document.getElementById("character-data").textContent) || {};

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
            document.getElementById("result-label").textContent = data.course_finished ? "COURSE COMPLETE" : "CHECKPOINT PASSED";
            document.getElementById("result-title").textContent = LEVEL.title;
            document.getElementById("result-text").textContent = data.explanation || "";
            document.getElementById("result-code").classList.add("hidden");
            const stats = document.getElementById("result-stats");
            const actionsBox = document.getElementById("result-actions");
            stats.textContent = "";
            actionsBox.textContent = "";
            stats.appendChild(stat("TIME", data.elapsed === null ? "--:--" : fmt(data.elapsed)));
            stats.appendChild(stat("REWARD", data.reward || ""));
            stats.appendChild(stat("COURSE", (data.percent || 0) + "%"));
            if (data.next_level) {
                const next = el("a", "large-button", "NEXT: " + data.next_level.title.toUpperCase());
                next.href = data.next_level.url;
                actionsBox.appendChild(next);
            } else {
                const back = el("a", "large-button", "BACK TO COURSE");
                back.href = "/curriculum/" + LEVEL.course;
                actionsBox.appendChild(back);
            }
            resultOverlay.classList.remove("hidden");
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

    const ITEM_CHIP = "HINT CHIP";
    const ITEM_DAGGER = "DAGGER";
    const ITEM_CANDY = "CANDY";

    const THEMES = {
        forest:  { skyTop: "#070c18", skyBottom: "#0f2a2a", ground: "#3b2a1e", grass: "#3f7a2f", stone: "#4a4a52", wall: "#5a4630", panel: "#d9dde0", trunk: "#4a3220", leaves: "#1f5a2a", leavesLight: "#2c7a3a", far: "#0b1a1a", accent: "#4be07a", water: "#123f3a", door: "#2a2a30", glow: true },
        sewer:   { skyTop: "#05100b", skyBottom: "#0c2416", ground: "#2f3b2c", grass: "#3f5a34", stone: "#3a4638", wall: "#2c3a30", panel: "#dfe6ea", trunk: "#2c3a30", leaves: "#1f4a2a", leavesLight: "#2c6a3a", far: "#08170f", accent: "#7bd66b", water: "#0d3f3a", door: "#3a2f22", glow: true },
        lab:     { skyTop: "#e9eef1", skyBottom: "#cfd8dd", ground: "#f2f4f5", grass: "#bfc8ce", stone: "#c9d1d6", wall: "#eef1f3", panel: "#f4f6f7", trunk: "#c0c8cd", leaves: "#b9c2c8", leavesLight: "#cfd6da", far: "#b3bdc3", accent: "#12a9c0", water: "#9fc9d6", door: "#dbe2e6", glow: false },
        tower:   { skyTop: "#0b0912", skyBottom: "#221a33", ground: "#3a3a44", grass: "#5b5b6b", stone: "#4a4a52", wall: "#5a5a66", panel: "#d9dde0", trunk: "#3a3a44", leaves: "#2c2c3a", leavesLight: "#3b3b4d", far: "#151222", accent: "#e0c04b", water: "#1c2436", door: "#2a2a30", glow: true },
        relay:   { skyTop: "#050a16", skyBottom: "#0f1e3a", ground: "#2b3340", grass: "#3e7ea8", stone: "#3a4250", wall: "#4a5262", panel: "#d9dde0", trunk: "#2b3340", leaves: "#1f4a6a", leavesLight: "#2c6a90", far: "#0a1426", accent: "#4bd0e0", water: "#12304a", door: "#2a2a30", glow: true },
        foundry: { skyTop: "#120808", skyBottom: "#2a1010", ground: "#3a2020", grass: "#8a3a2a", stone: "#4a3a3a", wall: "#5a4444", panel: "#d9dde0", trunk: "#3a2020", leaves: "#4a2a1a", leavesLight: "#6a3a22", far: "#1c0c0c", accent: "#ff8a4b", water: "#3a1a1a", door: "#2a2a30", glow: true }
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
    let spawn = { x: 2 * TILE, y: 8 * TILE };
    let doctorLine = 0;

    for (let y = 0; y < MAP_H; y++) {
        tiles[y] = [];
        for (let x = 0; x < MAP_W; x++) {
            const cell = rows[y][x];
            let tile = ".";
            const px = x * TILE, py = y * TILE;

            switch (cell) {
                case "#": case "S": case "W": case "T": case "L": case "G": case "V": case "U": case "A": case "~":
                    tile = cell;
                    break;
                case "D":
                    tile = "D";
                    doorCells.push({ x: x, y: y });
                    break;
                case "P":
                    spawn = { x: px + 4, y: py + 1 };
                    break;
                case "N":
                    entities.push({ type: "npc", name: "BYTE", x: px, y: py, w: 16, h: 16 });
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
        const hp = type === "boss" ? 8 : (type === "hostile" ? 3 : 2);
        return {
            type: type, x: x, y: y, w: w, h: h, spawnX: x, spawnY: y,
            vx: 0, vy: 0, dir: -1, onGround: false,
            hp: hp, maxHp: hp, alive: true, hitFlash: 0,
            state: "charge", timer: 0, shots: 0
        };
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
        if (entity.type === "doctor" || entity.type === "sign" || entity.type === "terminal") settle(entity);
    });

    enemies.forEach((enemy) => {
        if (enemy.type === "boss") {
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
            w: (maxX - minX + 1) * TILE, h: (maxY - minY + 1) * TILE
        });
    }

    function isSolid(tx, ty) {
        if (tx < 0 || tx >= MAP_W) return true;
        if (ty < 0) return false;
        if (ty >= MAP_H) return true;
        const t = tiles[ty][tx];
        if (t === "D") return !state.doorOpen;
        return t === "#" || t === "S" || t === "W" || t === "G" || t === "V" || t === "~";
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
        phase: "lesson",         // lesson, intro, dialogue, play, challenge, result, complete
        doorOpen: false,
        solved: false,
        metByte: false,
        bossDefeated: enemies.every((e) => e.type !== "boss"),
        inventory: new Array(SLOT_COUNT).fill(null),
        selectedSlot: 0,
        hintIndex: 0,
        timerStart: null,
        finalElapsed: null,
        result: null,
        dialogue: null,
        time: 0,
        lastNoEffect: 0
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

    function useItem() {
        if (state.phase !== "play") return;

        const item = state.inventory[state.selectedSlot];

        if (item === ITEM_DAGGER) {
            swingDagger();
        } else if (item === ITEM_CANDY) {
            if (player.hp >= MAX_HP) {
                toast("You're at full health. Save the candy.");
                return;
            }
            takeItem(ITEM_CANDY);
            player.hp = Math.min(MAX_HP, player.hp + CANDY_HEAL);
            renderHearts();
            toast("Candy eaten. +" + CANDY_HEAL + " health");
        } else if (item === ITEM_CHIP) {
            toast("Hint chips are used at a terminal.");
        } else {
            toast("Slot " + (state.selectedSlot + 1) + " is empty. Press 1-" + SLOT_COUNT + " to pick a slot.");
        }
    }


    /* -----------------------------------------------------
       COMBAT
    ----------------------------------------------------- */

    function attackBox() {
        return {
            x: player.facing > 0 ? player.x + player.w : player.x - 14,
            y: player.y + 2, w: 14, h: 12
        };
    }

    function swingDagger() {
        if (player.attackCooldown > 0) return;

        player.attackTimer = 8;
        player.attackCooldown = 18;

        const box = attackBox();

        // Vines
        const left = Math.floor(box.x / TILE), right = Math.floor((box.x + box.w - 1) / TILE);
        const top = Math.floor(box.y / TILE), bottom = Math.floor((box.y + box.h - 1) / TILE);
        let cut = false;
        for (let ty = top; ty <= bottom; ty++) {
            for (let tx = left; tx <= right; tx++) {
                if (tiles[ty] && tiles[ty][tx] === "V") {
                    tiles[ty][tx] = ".";
                    cut = true;
                    burst(tx * TILE + 8, ty * TILE + 8, "#5fbf4a", 10);
                }
            }
        }
        if (cut) toast("Vines cut.");

        enemies.forEach((enemy) => {
            if (enemy.alive && overlaps(box, enemy)) hitEnemy(enemy);
        });
    }

    function hitEnemy(enemy) {
        if (enemy.type === "boss" && enemy.state !== "rest") {
            if (state.time - state.lastNoEffect > 0.8) {
                toast("No effect. Strike while it rests.");
                state.lastNoEffect = state.time;
            }
            burst(enemy.x + enemy.w / 2, enemy.y + 8, "#ffffff", 4);
            return;
        }

        enemy.hp -= 1;
        enemy.hitFlash = 10;
        burst(enemy.x + enemy.w / 2, enemy.y + enemy.h / 2, "#ffffff", 8);

        if (enemy.type !== "boss") {
            enemy.x += player.facing * 5;
        }

        if (enemy.hp <= 0) killEnemy(enemy);
    }

    function killEnemy(enemy) {
        enemy.alive = false;
        burst(enemy.x + enemy.w / 2, enemy.y + enemy.h / 2, theme.accent, 24);

        if (enemy.type === "boss") {
            state.bossDefeated = true;
            projectiles.length = 0;
            toast("The specimen is down. The console flickers on.");
            setObjective(LEVEL.goal);
        }
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

    function respawn() {
        player.x = spawn.x;
        player.y = spawn.y;
        player.vx = 0;
        player.vy = 0;
        player.hp = MAX_HP;
        player.invuln = 90;

        enemies.forEach((enemy) => {
            enemy.alive = true;
            enemy.hp = enemy.maxHp;
            enemy.x = enemy.spawnX;
            enemy.y = enemy.spawnY;
            enemy.vx = 0;
            enemy.vy = 0;
            enemy.state = "charge";
            enemy.timer = 0;
            enemy.shots = 0;
        });

        projectiles.length = 0;
        if (enemies.some((e) => e.type === "boss")) state.bossDefeated = false;

        renderHearts();
        startDialogue("—", ["You were knocked out. The sim reloads you at the entrance."], null);
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
    const INTERACT_PRIORITY = { terminal: 0, npc: 1, doctor: 2, sign: 3 };

    function nearestInteractable() {
        let best = null;
        let bestScore = Infinity;
        let door = null;

        entities.forEach((entity) => {
            if (entity.type === "item" || entity.type === "exit") return;

            const ex = entity.x + entity.w / 2;
            const px = player.x + player.w / 2;
            const dx = Math.abs(ex - px);

            const verticalOverlap =
                player.y < entity.y + entity.h + 8 &&
                player.y + player.h > entity.y - 8;

            if (entity.type === "door") {
                // Doors only respond when nothing else is in reach.
                if (dx < INTERACT_RANGE + entity.w / 2 && verticalOverlap) door = entity;
                return;
            }

            const score = dx + (INTERACT_PRIORITY[entity.type] || 0) * 0.1;

            if (dx < INTERACT_RANGE && verticalOverlap && score < bestScore) {
                best = entity;
                bestScore = score;
            }
        });

        return best || door;
    }

    function interact() {
        const target = nearestInteractable();
        if (!target) return;

        if (target.type === "npc") {
            startDialogue("BYTE", LEVEL.dialogue, function () {
                state.metByte = true;
                setObjective(LEVEL.boss && !state.bossDefeated ? "Defeat the big snake" : LEVEL.goal);
            });
        }

        else if (target.type === "doctor") {
            const lines = LEVEL.npcs && LEVEL.npcs.length ? LEVEL.npcs : ["..."];
            startDialogue("DOCTOR", [lines[target.line % lines.length]], null);
        }

        else if (target.type === "sign") {
            startDialogue("SIGN", [LEVEL.sign || "The sign is blank."], null);
        }

        else if (target.type === "door") {
            if (state.doorOpen) return;
            startDialogue("DOOR", ["Sealed. The terminal beside it controls the lock."], null);
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
        reviewSelection = { line: null, why: null };

        if (challenge.type === "python_lines") buildPythonLines(challenge);
        else if (challenge.type === "text_answer") buildTextAnswer(challenge);
        else if (challenge.type === "mcq") buildChoices(challenge);
        else if (challenge.type === "code_review") buildCodeReview(challenge);
        else if (challenge.type === "fill_blank") buildFillBlank(challenge);
        else if (challenge.type === "order_code") buildOrderCode(challenge);

        updateHintButton();
        overlayChallenge.classList.remove("hidden");
    }

    function buildPythonLines(challenge) {
        const area = element("textarea", "challenge-code");
        area.rows = Math.max(2, (challenge.line_count || 1) + 1);
        area.placeholder = challenge.placeholder || "";
        area.spellcheck = false;
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

    function updateHintButton() {
        const chips = countItem(ITEM_CHIP);
        buttonHint.textContent = "USE HINT CHIP (" + chips + ")";
        buttonHint.disabled = chips === 0;
        buttonHint.title = chips === 0 ? "Find hint chips in the world - or ask SecureMentor." : "";
    }

    function useHint() {
        if (!takeItem(ITEM_CHIP)) return;

        let text;
        if (state.hintIndex < LEVEL.hints.length) {
            text = LEVEL.hints[state.hintIndex];
            state.hintIndex += 1;
        } else {
            text = "No more hints here. Re-read the lesson notes, or ask SecureMentor to guide you.";
        }

        challengeHints.appendChild(element("p", "hint-line", "HINT: " + text));
        updateHintButton();
    }

    let submitting = false;

    async function submitChallenge() {
        if (submitting || state.phase !== "challenge") return;

        const answer = challengeInput ? challengeInput() : null;

        const empty =
            answer === null || answer === undefined || answer === "" ||
            (typeof answer === "object" && answer.line === null) ||
            (typeof answer === "object" && Array.isArray(answer.blanks) && answer.blanks.some((b) => !b.trim()));

        if (empty) {
            showFeedback("Fill everything in before you run it.");
            return;
        }

        submitting = true;
        buttonSubmit.disabled = true;

        try {
            const response = await fetch("/api/level/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ course: LEVEL.course, level: LEVEL.number, answer: answer })
            });

            const data = await response.json();

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
            showSolved(data);

        } catch (error) {
            showFeedback("Connection lost. Try again.");
        } finally {
            submitting = false;
            buttonSubmit.disabled = false;
        }
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

    function showSolved(data) {
        state.phase = "result";

        resultLabel.textContent = "ACCESS GRANTED";
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
            setObjective("Go through the open door");
            gameWindow.focus();
        });
        resultActions.appendChild(go);

        overlayResult.classList.remove("hidden");
    }

    function showComplete() {
        const data = state.result || {};
        state.phase = "complete";

        resultLabel.textContent = data.course_finished ? "COURSE COMPLETE" : "LEVEL COMPLETE";
        resultTitle.textContent = LEVEL.title;
        resultText.textContent = data.course_finished
            ? "You have cleared every level of " + LEVEL.zone + ". The whole Academy heard about it."
            : "Reward earned: " + (data.reward || LEVEL.reward) + ".";
        resultCode.classList.add("hidden");

        clear(resultStats);
        resultStats.appendChild(stat("TIME", data.elapsed === null || data.elapsed === undefined ? "--:--" : formatTime(data.elapsed)));
        resultStats.appendChild(stat("BEST", data.best === null || data.best === undefined ? "--:--" : formatTime(data.best)));
        resultStats.appendChild(stat("COURSE", (data.percent || 0) + "%"));

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

    async function startTimer() {
        try {
            await fetch("/api/level/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ course: LEVEL.course, level: LEVEL.number })
            });
        } catch (error) {
            // The level still plays; only the time may be missing.
        }
        state.timerStart = performance.now();
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

        if (Math.abs(player.vx) > 0.2 && player.onGround) {
            player.walkTime += 1;
            player.frame = Math.floor(player.walkTime / 8) % 2;
        } else {
            player.frame = player.onGround ? 0 : 1;
        }

        // Pickups + exit
        entities.forEach((entity) => {
            if (entity.type === "item" && !entity.taken && overlaps(player, entity)) {
                if (addItem(entity.item)) {
                    entity.taken = true;
                    burst(entity.x + 4, entity.y + 4, theme.accent, 10);
                    if (entity.item === ITEM_DAGGER) {
                        toast("DAGGER picked up. Select its slot and press F to swing.");
                    } else if (entity.item === ITEM_CANDY) {
                        toast("CANDY picked up. Select it and press F to heal.");
                    } else {
                        toast("HINT CHIP picked up. Spend it at a terminal.");
                    }
                } else {
                    toast("Inventory full.");
                }
            }
            if (entity.type === "exit" && state.doorOpen && overlaps(player, entity)) {
                showComplete();
            }
        });

        camera.x = Math.max(0, Math.min(player.x + player.w / 2 - VIEW_W / 2, MAP_W * TILE - VIEW_W));
    }

    function groundAhead(body, dir) {
        const probeX = dir > 0 ? body.x + body.w + 1 : body.x - 2;
        return rectHitsSolid(probeX, body.y + body.h + 1, 1, 1);
    }

    function stepEnemies() {
        enemies.forEach((enemy) => {
            if (!enemy.alive) return;
            if (enemy.hitFlash > 0) enemy.hitFlash -= 1;

            if (enemy.type === "snake") {
                enemy.vy = Math.min(enemy.vy + GRAVITY, MAX_FALL);
                enemy.vx = enemy.dir * 0.55;
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
                    enemy.vx = (enemy.onGround && !groundAhead(enemy, enemy.dir)) ? 0 : enemy.dir * 0.8;
                } else {
                    enemy.vx = 0;
                }
                moveBody(enemy);
                if (overlaps(player, enemy)) damagePlayer(1, enemy);
            }

            else if (enemy.type === "boss") {
                stepBoss(enemy);
            }
        });

        for (let i = projectiles.length - 1; i >= 0; i--) {
            const p = projectiles[i];
            p.x += p.vx;
            p.life -= 1;
            if (Math.random() < 0.6) particles.push({ x: p.x + 3, y: p.y + 3, vx: -p.vx * 0.2, vy: (Math.random() - 0.5), life: 10, color: "#ffb347" });
            if (p.life <= 0 || rectHitsSolid(p.x, p.y, p.w, p.h)) {
                projectiles.splice(i, 1);
                continue;
            }
            if (overlaps(player, p)) {
                damagePlayer(2, p);
                projectiles.splice(i, 1);
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

        const firstCol = Math.floor(camX / TILE);
        const lastCol = Math.min(MAP_W - 1, firstCol + Math.ceil(VIEW_W / TILE) + 1);

        for (let ty = 0; ty < MAP_H; ty++) {
            for (let tx = firstCol; tx <= lastCol; tx++) {
                drawTile(tiles[ty][tx], tx, ty, tx * TILE - camX, ty * TILE);
            }
        }

        entities.forEach((entity) => drawEntity(entity, entity.x - camX, entity.y));
        enemies.forEach((enemy) => drawEnemy(enemy, enemy.x - camX, enemy.y));

        projectiles.forEach((p) => {
            ctx.fillStyle = "#ff7a1f";
            ctx.fillRect(Math.floor(p.x - camX), Math.floor(p.y), p.w, p.h);
            ctx.fillStyle = "#ffe066";
            ctx.fillRect(Math.floor(p.x - camX) + 2, Math.floor(p.y) + 2, 2, 2);
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
            if (target && !(target.type === "door" && state.doorOpen)) {
                drawPrompt(target.x - camX + target.w / 2, target.y - 10);
            }
        }

        particles.forEach((p) => {
            ctx.globalAlpha = Math.max(0, Math.min(1, p.life / 40));
            ctx.fillStyle = p.color;
            ctx.fillRect(Math.floor(p.x - camX), Math.floor(p.y), 1, 1);
        });
        ctx.globalAlpha = 1;

        ctx.fillStyle = "rgba(0,0,0,0.35)";
        ctx.fillRect(0, 0, VIEW_W, 2);
        ctx.fillRect(0, VIEW_H - 2, VIEW_W, 2);
    }

    function drawSilhouette(x, y, h, seed) {
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

    function drawTile(tile, tx, ty, sx, sy) {
        if (tile === ".") return;

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

        if (tile === "D") {
            if (state.doorOpen) {
                ctx.fillStyle = theme === THEMES.lab ? "#7a8a92" : "#050505";
                ctx.fillRect(sx, sy, TILE, TILE);
                ctx.fillStyle = theme.accent;
                ctx.globalAlpha = 0.5 + 0.3 * Math.sin(state.time * 4);
                ctx.fillRect(sx, sy, 1, TILE);
                ctx.fillRect(sx + TILE - 1, sy, 1, TILE);
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

        if (entity.type === "item") {
            if (entity.taken) return;
            const y = sy + bob;
            if (entity.item === ITEM_CHIP) {
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

        if (enemy.type === "hostile") {
            drawDoctor(sx, sy, true, flash, enemy.dir);
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

    function beginLevel() {
        state.phase = "play";
        startDialogue("—", [LEVEL.story], function () {
            startTimer();
            setObjective("Find BYTE and press E");
        });
    }

    buttonStart.addEventListener("click", function () {
        overlayLesson.classList.add("hidden");
        gameWindow.focus();

        if (LEVEL.intro) {
            playIntro().then(beginLevel);
        } else {
            beginLevel();
        }
    });

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

        if (state.phase !== "intro") {
            let steps = 0;
            while (accumulator >= STEP && steps < 4) {
                if (state.phase === "play") {
                    stepPlayer();
                    stepEnemies();
                }
                particles.forEach((p) => { p.x += p.vx; p.y += p.vy; p.vy += 0.05; p.life -= 1; });
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

    (LEVEL.start_items || []).forEach(addItem);
    renderInventory();
    renderHearts();
    setObjective("Read the lesson, then press START");
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
        return "";
    }

    // Debug handle for the browser console. step(n) advances the physics
    // n frames without waiting for the screen, handy when testing enemies.
    window.cyberGame = {
        state: state, player: player, keys: keys, level: LEVEL,
        enemies: enemies, entities: entities, projectiles: projectiles,
        currentInput: currentInput,
        step: function (n) {
            for (let i = 0; i < (n || 1); i++) {
                if (state.phase === "play") { stepPlayer(); stepEnemies(); }
            }
        }
    };

})();
