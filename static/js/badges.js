/* =========================================================
   CYBER ACADEMY - PIXEL BADGES (profile page)
   Each <canvas class="badge-icon"> is drawn from a 12x12
   pixel template chosen by course. Earned badges use the
   course colour; locked ones are drawn dark.
========================================================= */

(function () {

    const SHAPES = {
        // shield
        cybersecurity: [
            "............",
            ".XXXXXXXXXX.",
            ".XXXXXXXXXX.",
            ".XX..XX..XX.",
            ".XX..XX..XX.",
            ".XXXXXXXXXX.",
            ".XXXXXXXXXX.",
            "..XXXXXXXX..",
            "...XXXXXX...",
            "....XXXX....",
            ".....XX.....",
            "............"
        ],
        // leaf
        python: [
            "............",
            "........XXX.",
            "......XXXXX.",
            ".....XXXXXX.",
            "....XXXXXXX.",
            "...XXXX.XXX.",
            "..XXXX.XXX..",
            ".XXXX.XXX...",
            ".XXX.XXX....",
            ".XX.XXX.....",
            ".X.XX.......",
            "............"
        ],
        // signal tower
        internet: [
            "............",
            ".....XX.....",
            "...XXXXXX...",
            "..XX.XX.XX..",
            ".X..XXXX..X.",
            ".....XX.....",
            "....XXXX....",
            "....XXXX....",
            "...XXXXXX...",
            "...XX..XX...",
            "..XX....XX..",
            "............"
        ],
        // gear
        "secure-coding": [
            "............",
            "....X..X....",
            "..XXXXXXXX..",
            "..XX....XX..",
            ".XX..XX..XX.",
            ".X..XXXX..X.",
            ".X..XXXX..X.",
            ".XX..XX..XX.",
            "..XX....XX..",
            "..XXXXXXXX..",
            "....X..X....",
            "............"
        ],
        // checkpoint pin
        quiz: [
            "............",
            "....XXXX....",
            "...XXXXXX...",
            "..XXX..XXX..",
            "..XX....XX..",
            "..XXX..XXX..",
            "...XXXXXX...",
            "....XXXX....",
            ".....XX.....",
            ".....XX.....",
            ".....XX.....",
            "............"
        ]
    };

    const COLORS = {
        cybersecurity: "#e0c04b",
        python: "#4be07a",
        internet: "#4bd0e0",
        "secure-coding": "#ff8a4b"
    };

    function draw(canvas) {
        const ctx = canvas.getContext("2d");
        const course = canvas.dataset.course;
        const earned = canvas.dataset.earned === "1";
        const master = canvas.dataset.master === "1";
        const kind = canvas.dataset.kind;

        const shape = SHAPES[kind === "quiz" ? "quiz" : course] || SHAPES.python;
        const color = earned ? (COLORS[course] || "#dddddd") : "#2a2a2a";
        const outline = earned ? (master ? "#ffd700" : "#ffffff") : "#3c3c3c";

        ctx.clearRect(0, 0, 24, 24);

        // outline pass (draw shape offset in 4 directions)
        ctx.fillStyle = outline;
        shape.forEach((row, y) => {
            row.split("").forEach((cell, x) => {
                if (cell !== "X") return;
                [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => {
                    ctx.fillRect(x * 2 + dx, y * 2 + dy, 2, 2);
                });
            });
        });

        ctx.fillStyle = color;
        shape.forEach((row, y) => {
            row.split("").forEach((cell, x) => {
                if (cell === "X") ctx.fillRect(x * 2, y * 2, 2, 2);
            });
        });

        // a highlight pixel; a star for the course master badge
        if (earned) {
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(8, 6, 2, 2);
            if (master) {
                ctx.fillStyle = "#ffd700";
                ctx.fillRect(18, 2, 2, 2);
                ctx.fillRect(16, 4, 6, 2);
                ctx.fillRect(18, 6, 2, 2);
            }
        }
    }

    document.querySelectorAll("canvas.badge-icon").forEach(draw);

})();
