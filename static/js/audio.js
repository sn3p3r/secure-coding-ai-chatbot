/* =========================================================
   MUSIC
   One track per level (LEVEL.music from the server): it starts on the
   START / RESUME click (browsers only allow sound after a click),
   plays once, and loops on the obelisk levels. The ♪ button and the
   M key switch it off; the choice is kept in localStorage.
========================================================= */

window.academyAudio = (function () {

    const KEY = "academyMusic";
    const VOLUME = 0.45;

    const button = document.getElementById("music-btn");
    const nowPlaying = document.getElementById("hud-music");   // absent when switched off in settings

    let title = "";

    function showNowPlaying(on) {
        if (!nowPlaying) return;
        nowPlaying.textContent = on && title ? "\u266a " + title : "";
        nowPlaying.hidden = !(on && title);
    }

    let enabled = true;
    let audio = null;
    let requested = false;      // START was pressed on this page
    let fadeTimer = null;

    try {
        enabled = localStorage.getItem(KEY) !== "off";
    } catch (error) {
        enabled = true;
    }

    function remember() {
        try {
            localStorage.setItem(KEY, enabled ? "on" : "off");
        } catch (error) {
            // private mode: the choice lasts for this page only
        }
    }

    function paint() {
        if (!button) return;
        button.classList.toggle("is-off", !enabled);
        button.setAttribute("aria-pressed", enabled ? "true" : "false");
        button.title = enabled ? "Music on (M to mute)" : "Music off (M to unmute)";
    }

    function load(track) {
        if (audio || !track || !track.file) return;
        title = track.title || "";
        audio = new Audio(track.file);
        audio.loop = !!track.loop;
        audio.volume = VOLUME;
        audio.preload = "auto";
        audio.addEventListener("play", () => showNowPlaying(true));
        audio.addEventListener("pause", () => showNowPlaying(false));
        audio.addEventListener("ended", () => showNowPlaying(false));
    }

    function resume() {
        if (!audio || !enabled || !requested) return;
        clearTimeout(fadeTimer);
        audio.volume = VOLUME;
        const attempt = audio.play();
        if (attempt && attempt.catch) attempt.catch(() => {});
    }

    // Called from the START / RESUME click: the first call on a page starts the track.
    function play(track) {
        load(track);
        if (requested) return;
        requested = true;
        resume();
    }

    function fadeOut(ms) {
        if (!audio || audio.paused) return;
        const steps = 20;
        const drop = audio.volume / steps;
        let done = 0;
        clearTimeout(fadeTimer);
        (function step() {
            done += 1;
            audio.volume = Math.max(0, audio.volume - drop);
            if (done < steps) {
                fadeTimer = setTimeout(step, (ms || 1500) / steps);
            } else {
                audio.pause();
                audio.currentTime = 0;
                requested = false;
            }
        })();
    }

    function toggle() {
        enabled = !enabled;
        remember();
        paint();
        if (enabled) resume();
        else if (audio) audio.pause();
    }

    if (button) {
        button.addEventListener("click", function () {
            toggle();
            const gameWindow = document.getElementById("game-window");
            if (gameWindow) gameWindow.focus();
        });
    }

    paint();

    return { play, fadeOut, toggle, isOn: () => enabled };

})();
