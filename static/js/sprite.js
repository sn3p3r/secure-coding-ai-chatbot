/* =========================================================
   CYBER ACADEMY - PIXEL CHARACTER
   Shared by the game (game.js) and the character page.
   Everything is drawn with fillRect, so there are no image
   files to load. The sprite is 12 x 16 pixels.
========================================================= */

(function () {

    const HAIR_COLORS = {
        black:  "#1c1c22",
        brown:  "#6b3e1e",
        blonde: "#e6c15a",
        red:    "#b8321f",
        blue:   "#2f6fdb",
        green:  "#35b64a"
    };

    const OUTFIT_COLORS = {
        dark:  "#2c2c34",
        grey:  "#8d8d94",
        green: "#2f7a3e",
        blue:  "#2c5fa8"
    };

    const PALETTE = {
        S: "#e8b990",   // skin
        E: "#101010",   // eyes
        P: "#23232a",   // trousers
        B: "#141416",   // boots
        M: "#f0f0f0"    // highlight
    };

    /*
     * Body templates. T = outfit, H = hair placeholder (filled by
     * hair style), S = skin. Two leg frames for walking.
     */
    const BODIES = {
        male: [
            "............",
            "...SSSSSS...",
            "...SSSSSS...",
            "...SESSES...",
            "...SSSSSS...",
            "....SSSS....",
            "..TTTTTTTT..",
            ".TTTTTTTTTT.",
            ".TTTTTTTTTT.",
            ".S.TTTTTT.S.",
            "...TTTTTT...",
            "...PPPPPP...",
            "...PPPPPP...",
            "...PP..PP...",
            "...BB..BB...",
            "..BBB..BBB.."
        ],
        female: [
            "............",
            "...SSSSSS...",
            "...SSSSSS...",
            "...SESSES...",
            "...SSSSSS...",
            "....SSSS....",
            "...TTTTTT...",
            "..TTTTTTTT..",
            "..TTTTTTTT..",
            "..S.TTTT.S..",
            "....TTTT....",
            "...TTTTTT...",
            "....PPPP....",
            "....P..P....",
            "....B..B....",
            "...BB..BB..."
        ],
        nonbinary: [
            "............",
            "...SSSSSS...",
            "...SSSSSS...",
            "...SESSES...",
            "...SSSSSS...",
            "....SSSS....",
            "...TTTTTT...",
            "..TTTTTTTT..",
            "..TTTTTTTT..",
            "..S.TTTT.S..",
            "....TTTT....",
            "....PPPP....",
            "....PPPP....",
            "....P..P....",
            "....B..B....",
            "...BB..BB..."
        ]
    };

    /* Walking frame: legs apart. Rows 13-15 are replaced. */
    const WALK_LEGS = {
        wide:   ["..PP....PP..", "..BB....BB..", ".BBB....BBB."],
        narrow: ["...P....P...", "...B....B...", "..BB....BB.."]
    };

    const HAIR = {
        short: [
            "....HHHH....",
            "...HHHHHH...",
            "...H....H..."
        ],
        long: [
            "....HHHH....",
            "...HHHHHH...",
            "..HH....HH..",
            "..H......H..",
            "..H......H..",
            "..H......H..",
            "..H......H..",
            "..H......H.."
        ],
        spiky: [
            "...H.H.H.H..",
            "...HHHHHH...",
            "...H....H..."
        ],
        buzz: [
            "............",
            "...HHHHHH..."
        ]
    };

    function buildGrid(character, frame) {

        const gender = BODIES[character.gender] ? character.gender : "nonbinary";
        const body = BODIES[gender].map((row) => row.split(""));

        if (frame === 1) {
            const legs = gender === "male" ? WALK_LEGS.wide : WALK_LEGS.narrow;
            for (let i = 0; i < 3; i++) {
                body[13 + i] = legs[i].split("");
            }
        }

        const hair = HAIR[character.hair] || HAIR.short;

        hair.forEach((row, y) => {
            row.split("").forEach((cell, x) => {
                if (cell === "H") {
                    body[y][x] = "H";
                }
            });
        });

        return body;
    }

    /*
     * Draw the character at (x, y) in canvas pixels.
     *   scale   - pixel size
     *   facing  - 1 (right) or -1 (left)
     *   frame   - 0 standing, 1 walking
     */
    function drawCharacter(ctx, character, x, y, scale, facing, frame) {

        const grid = buildGrid(character, frame);
        const hairColor = HAIR_COLORS[character.hair_color] || HAIR_COLORS.black;
        const outfitColor = OUTFIT_COLORS[character.outfit] || OUTFIT_COLORS.dark;

        ctx.save();

        if (facing === -1) {
            ctx.translate(x + 12 * scale, y);
            ctx.scale(-1, 1);
        } else {
            ctx.translate(x, y);
        }

        for (let row = 0; row < grid.length; row++) {
            for (let col = 0; col < grid[row].length; col++) {

                const cell = grid[row][col];

                if (cell === ".") continue;

                if (cell === "H") ctx.fillStyle = hairColor;
                else if (cell === "T") ctx.fillStyle = outfitColor;
                else ctx.fillStyle = PALETTE[cell] || "#ff00ff";

                ctx.fillRect(col * scale, row * scale, scale, scale);
            }
        }

        ctx.restore();
    }

    /* Mask used by the matrix intro: 1 where the sprite has a pixel. */
    function characterMask(character) {
        return buildGrid(character, 0).map((row) => row.map((c) => (c === "." ? 0 : 1)));
    }

    window.CyberSprite = {
        drawCharacter: drawCharacter,
        characterMask: characterMask,
        HAIR_COLORS: HAIR_COLORS,
        OUTFIT_COLORS: OUTFIT_COLORS,
        WIDTH: 12,
        HEIGHT: 16
    };

})();
