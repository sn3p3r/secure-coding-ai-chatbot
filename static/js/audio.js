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
    let audio = null;           // the level's track
    let bossAudio = null;       // takes over while a boss is on screen
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
        audio.dataset.title = title;
        audio.loop = !!track.loop;
        audio.volume = VOLUME;
        audio.preload = "auto";
        audio.addEventListener("play", () => showNowPlaying(true));
        audio.addEventListener("pause", () => showNowPlaying(false));
        audio.addEventListener("ended", () => showNowPlaying(false));
    }

    function safePlay(element) {
        const attempt = element.play();
        if (attempt && attempt.catch) attempt.catch(() => {});
    }

    function resume() {
        if (!enabled || !requested) return;
        clearTimeout(fadeTimer);
        if (bossAudio) {
            bossAudio.volume = VOLUME;
            safePlay(bossAudio);
            return;
        }
        if (!audio) return;
        audio.volume = VOLUME;
        safePlay(audio);
    }

    function fade(element, ms, then) {
        const steps = 20;
        const drop = element.volume / steps;
        let done = 0;
        (function step() {
            done += 1;
            element.volume = Math.max(0, element.volume - drop);
            if (done < steps) {
                fadeTimer = setTimeout(step, (ms || 1500) / steps);
            } else {
                element.pause();
                if (then) then();
            }
        })();
    }

    // A boss appeared: hand over to its track (looped) until it is beaten.
    function bossStart(track) {
        if (!track || !track.file || bossAudio) return;
        title = track.title || title;
        bossAudio = new Audio(track.file);
        bossAudio.loop = true;
        bossAudio.volume = VOLUME;
        bossAudio.addEventListener("play", () => showNowPlaying(true));
        bossAudio.addEventListener("pause", () => showNowPlaying(false));
        if (audio && !audio.paused) fade(audio, 700);
        if (enabled && requested) safePlay(bossAudio);
        else showNowPlaying(false);
    }

    // The boss is gone: fade its track out and let the level track finish.
    function bossEnd() {
        if (!bossAudio) return;
        const finished = bossAudio;
        bossAudio = null;
        fade(finished, 1200, () => {
            if (audio && audio.currentTime > 0 && !audio.ended) {
                title = audio.dataset.title || title;
                resume();
            }
        });
    }

    // Called from the START / RESUME click: the first call on a page starts the track.
    function play(track) {
        load(track);
        if (requested) return;
        requested = true;
        resume();
    }

    function fadeOut(ms) {
        clearTimeout(fadeTimer);
        if (bossAudio && !bossAudio.paused) fade(bossAudio, ms || 1500);
        if (!audio || audio.paused) return;
        fade(audio, ms || 1500, () => {
            audio.currentTime = 0;
            requested = false;
        });
    }

    function toggle() {
        enabled = !enabled;
        remember();
        paint();
        if (enabled) {
            resume();
        } else {
            if (audio) audio.pause();
            if (bossAudio) bossAudio.pause();
        }
    }

    if (button) {
        button.addEventListener("click", function () {
            toggle();
            const gameWindow = document.getElementById("game-window");
            if (gameWindow) gameWindow.focus();
        });
    }

    paint();

    return { play, fadeOut, toggle, bossStart, bossEnd, isOn: () => enabled };

})();
