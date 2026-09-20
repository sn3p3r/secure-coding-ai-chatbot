/* =========================================================
   TIME TRACKING
========================================================= */

const TIME_KEY = "cyberAcademyTime";

const timeElement =
    document.getElementById("time-spent");

// The server keeps the count that other players may see; the local
// counter only bridges the seconds between two pings.
const serverSeconds =
    timeElement ? Number(timeElement.dataset.seconds || 0) : 0;

let localSeconds = 0;

try {
    localSeconds = Number(localStorage.getItem(TIME_KEY)) || 0;
} catch (error) {
    localSeconds = 0;
}

let totalSeconds =
    Math.max(localSeconds, serverSeconds);


function formatTime(seconds) {

    const hours =
        Math.floor(seconds / 3600);

    const minutes =
        Math.floor((seconds % 3600) / 60);

    const secs =
        seconds % 60;

    return (
        String(hours).padStart(2, "0") +
        ":" +
        String(minutes).padStart(2, "0") +
        ":" +
        String(secs).padStart(2, "0")
    );
}


function updateTimeDisplays() {

    const elements =
        document.querySelectorAll("#time-spent");

    elements.forEach((element) => {

        element.textContent =
            formatTime(totalSeconds);

    });


    const profileTime =
        document.getElementById("profile-time");

    if (profileTime) {

        profileTime.textContent =
            formatTime(totalSeconds);
    }
}


setInterval(() => {

    totalSeconds++;

    try {
        localStorage.setItem(TIME_KEY, totalSeconds);
    } catch (error) {
        // private mode: the server count still grows through the pings
    }

    updateTimeDisplays();

}, 1000);


updateTimeDisplays();


/*
 * Every 30 s tell the server the page is still open. The server adds
 * the real gap since the last ping; nothing here can inflate it.
 */
if (timeElement && timeElement.dataset.seconds !== undefined) {

    const ping = function() {

        fetch("/api/time/ping", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ seconds: totalSeconds })
        }).catch(() => {});
    };

    ping();

    setInterval(ping, 30000);
}


/* =========================================================
   TABS (profile, friends)
========================================================= */

document.querySelectorAll("[data-tabs]").forEach((nav) => {

    const buttons =
        nav.querySelectorAll("[data-tab]");

    const panels =
        document.querySelectorAll("[data-panel]");

    function show(name) {

        buttons.forEach((button) => {
            button.classList.toggle("is-active", button.dataset.tab === name);
        });

        panels.forEach((panel) => {
            panel.hidden = panel.dataset.panel !== name;
        });
    }

    buttons.forEach((button) => {

        button.addEventListener("click", function() {
            show(button.dataset.tab);
            history.replaceState(null, "", "#" + button.dataset.tab);
        });
    });

    const fromHash =
        location.hash.slice(1);

    if (fromHash && Array.from(buttons).some((b) => b.dataset.tab === fromHash)) {
        show(fromHash);
    }
});


/* =========================================================
   LEADERBOARD: the level box follows the chosen course
========================================================= */

const boardCourse =
    document.getElementById("board-course");

const boardLevel =
    document.getElementById("board-level");

const levelsData =
    document.getElementById("levels-data");

if (boardCourse && boardLevel && levelsData) {

    let levelsByCourse = {};

    try {
        levelsByCourse = JSON.parse(levelsData.textContent);
    } catch (error) {
        levelsByCourse = {};
    }

    function fillLevels() {

        const levels =
            levelsByCourse[boardCourse.value] || [];

        const previous =
            boardLevel.value;

        boardLevel.innerHTML = "";

        if (!levels.length) {

            const option = document.createElement("option");
            option.value = "";
            option.textContent = "Choose a course first";
            boardLevel.appendChild(option);
            boardLevel.disabled = true;
            return;
        }

        levels.forEach((level) => {

            const option = document.createElement("option");
            option.value = String(level.number);
            option.textContent =
                String(level.number).padStart(2, "0") + " · " + level.title + (level.kind === "quiz" ? " (quiz)" : "");
            boardLevel.appendChild(option);
        });

        boardLevel.disabled = false;

        if (levels.some((level) => String(level.number) === previous)) {
            boardLevel.value = previous;
        }
    }

    boardCourse.addEventListener("change", fillLevels);
}


/* =========================================================
   QUIZ
========================================================= */

const quizForm =
    document.getElementById("quiz-form");


if (quizForm) {

    quizForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            const formData =
                new FormData(quizForm);


            const scores = {

                python: 0,

                cybersecurity: 0,

                internet: 0,

                secure: 0

            };


            for (
                const answer
                of formData.values()
            ) {

                if (
                    scores[answer] !== undefined
                ) {

                    scores[answer]++;
                }

            }


            let recommendedCourse =
                "python";


            for (
                const course in scores
            ) {

                if (
                    scores[course] >
                    scores[recommendedCourse]
                ) {

                    recommendedCourse =
                        course;
                }

            }


            const courseInfo = {

                python: {

                    title: "Python",

                    text:
                        "Your answers suggest that " +
                        "you may enjoy building programs " +
                        "and solving programming problems."

                },

                cybersecurity: {

                    title: "Cybersecurity",

                    text:
                        "Your answers suggest that " +
                        "you may enjoy defending systems " +
                        "and investigating threats."

                },

                internet: {

                    title: "Internet Basics",

                    text:
                        "Your answers suggest that " +
                        "you may enjoy understanding how " +
                        "computers and networks communicate."

                },

                secure: {

                    title: "Secure Coding",

                    text:
                        "Your answers suggest that " +
                        "you may enjoy investigating code " +
                        "and finding security weaknesses."

                }

            };


            document.getElementById(
                "result-title"
            ).textContent =
                courseInfo[
                    recommendedCourse
                ].title;


            document.getElementById(
                "result-text"
            ).textContent =
                courseInfo[
                    recommendedCourse
                ].text;


            document.getElementById(
                "quiz-result"
            ).classList.remove("hidden");


            quizForm.classList.add("hidden");


            /*
             * Save the recommendation locally as a backup.
             */
            localStorage.setItem(
                "recommendedCourse",
                recommendedCourse
            );


            /*
             * Save the recommendation to the
             * logged-in user's SQLite account.
             */
            try {

                const response =
                    await fetch(
                        "/save-quiz",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                recommended_course:
                                    recommendedCourse
                            })
                        }
                    );


                const data =
                    await response.json();


                if (!data.success) {

                    console.error(
                        "Quiz result was not saved:",
                        data.error
                    );
                }

            } catch (error) {

                console.error(
                    "Error saving quiz result:",
                    error
                );

            }

        }
    );
}


/* =========================================================
   SECUREMENTOR
========================================================= */

const mentorButton =
    document.getElementById(
        "mentor-button"
    );


const mentorPanel =
    document.getElementById(
        "mentor-panel"
    );


const mentorClose =
    document.getElementById(
        "mentor-close"
    );


const mentorSend =
    document.getElementById(
        "mentor-send"
    );


const mentorQuestion =
    document.getElementById(
        "mentor-question"
    );


const mentorCode =
    document.getElementById(
        "mentor-code"
    );


const mentorMessages =
    document.getElementById(
        "mentor-messages"
    );


const mentorStatus =
    document.getElementById(
        "mentor-status"
    );


const mentorActions =
    document.getElementById(
        "mentor-actions"
    );


/*
 * Connectivity check (token-free on the server) shown in the header.
 */

let mentorStatusChecked = false;

async function checkMentorStatus() {

    if (mentorStatusChecked || !mentorStatus) {
        return;
    }

    mentorStatusChecked = true;

    try {

        const response =
            await fetch("/api/mentor/status");

        const data =
            await response.json();

        mentorStatus.textContent =
            data.reachable ? "ONLINE" : "OFFLINE";

        mentorStatus.className =
            "mentor-status " +
            (data.reachable ? "mentor-online" : "mentor-offline");

        mentorStatus.title = data.detail || "";

        if (!data.reachable) {

            addMentorMessage(
                "SecureMentor",
                "I'm offline right now: " + (data.detail || "no connection.") +
                " The in-game lesson notes and hint chips still work."
            );
        }

    } catch (error) {

        mentorStatus.textContent = "OFFLINE";
        mentorStatus.className = "mentor-status mentor-offline";
    }
}


/*
 * Quick actions for the level or quiz the player is on.
 * window.mentorLevel is set by the course page.
 */

function buildMentorActions() {

    if (!mentorActions || !window.mentorLevel || mentorActions.childElementCount) {
        return;
    }

    const level = window.mentorLevel;

    const actions = level.kind === "quiz"
        ? [
            ["EXPLAIN THE TOPIC", "Explain the main idea behind this checkpoint's questions, without saying which options are correct."],
            ["NUDGE ME", "One of my quiz answers is wrong. Ask me a question that helps me spot which one, without telling me the answer."]
          ]
        : [
            ["EXPLAIN THIS LEVEL", "Explain what this level is asking me to do and which lesson note matters most. Don't give me the answer."],
            ["NUDGE ME", "I'm stuck at the terminal. Give me one small nudge, not the answer."],
            ["CHECK MY CODE", "Here is what I typed into the terminal. Tell me what's wrong with it in words, without writing the fix for me.", true]
          ];

    const label =
        document.createElement("span");

    label.className = "mentor-actions-label";

    label.textContent =
        "LEVEL " + String(level.level).padStart(2, "0") + " · " + level.title.toUpperCase();

    mentorActions.appendChild(label);

    actions.forEach(([text, question, useCode]) => {

        const button =
            document.createElement("button");

        button.type = "button";

        button.className = "mentor-action";

        button.textContent = text;

        button.addEventListener("click", function() {

            let code = "";

            if (useCode) {

                code =
                    (window.cyberGame && window.cyberGame.currentInput)
                        ? window.cyberGame.currentInput()
                        : "";

                if (!code && mentorCode) {
                    code = mentorCode.value.trim();
                }

                if (!code) {

                    addMentorMessage(
                        "SecureMentor",
                        "Type something into the terminal first (or paste it in the code box), then press CHECK MY CODE."
                    );

                    return;
                }
            }

            askSecureMentor(question, code);
        });

        mentorActions.appendChild(button);
    });

    mentorActions.classList.remove("hidden");
}


/*
 * On every page load the tab rises for a moment so new players learn
 * where SecureMentor lives, then settles back into the corner.
 */

const mentorDock =
    document.getElementById("mentor-dock");

if (mentorDock) {

    setTimeout(() => mentorDock.classList.add("peek"), 600);

    setTimeout(() => mentorDock.classList.remove("peek"), 3400);
}


/*
 * Open / close the mentor panel.
 */

if (
    mentorButton &&
    mentorPanel
) {

    mentorButton.addEventListener(
        "click",
        function() {

            mentorPanel.classList.toggle(
                "hidden"
            );


            const dock =
                document.getElementById("mentor-dock");

            const open =
                !mentorPanel.classList.contains("hidden");

            if (dock) {
                dock.classList.toggle("open", open);
            }


            if (open) {

                checkMentorStatus();

                buildMentorActions();

                if (mentorQuestion) {
                    mentorQuestion.focus();
                }

            }

        }
    );

}


if (
    mentorClose &&
    mentorPanel
) {

    mentorClose.addEventListener(
        "click",
        function() {

            mentorPanel.classList.add(
                "hidden"
            );

            const dock =
                document.getElementById("mentor-dock");

            if (dock) {
                dock.classList.remove("open");
            }

            // Hand the keyboard back to the game.
            const gameWindow =
                document.getElementById("game-window");

            if (gameWindow) {
                gameWindow.focus();
            }

        }
    );

}


/*
 * Add a message to the chat window.
 */

function addMentorMessage(
    sender,
    text,
    isUser = false
) {

    if (!mentorMessages) {
        return;
    }


    const message =
        document.createElement("div");


    message.className =
        isUser
            ? "mentor-message mentor-user-message"
            : "mentor-message";


    const senderElement =
        document.createElement("strong");

    senderElement.textContent =
        sender;


    const textElement =
        document.createElement("p");

    textElement.textContent =
        text;


    message.appendChild(
        senderElement
    );

    message.appendChild(
        textElement
    );


    mentorMessages.appendChild(
        message
    );


    mentorMessages.scrollTop =
        mentorMessages.scrollHeight;
}


/*
 * Send a question and optional code
 * to the Flask backend.
 */

async function askSecureMentor(presetQuestion, presetCode) {

    if (
        !mentorQuestion ||
        !mentorSend
    ) {

        return;
    }


    const question =
        presetQuestion || mentorQuestion.value.trim();


    const code =
        presetCode !== undefined
            ? presetCode
            : (mentorCode ? mentorCode.value.trim() : "");


    if (!question) {

        return;
    }


    addMentorMessage(
        "You",
        question + (presetCode ? "\n\n" + presetCode : ""),
        true
    );


    if (!presetQuestion) {
        mentorQuestion.value = "";
    }

    mentorSend.disabled = true;


    const level = window.mentorLevel || {};


    try {

        const response =
            await fetch(
                "/api/mentor",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question: question,
                        code: code,
                        course: level.course || null,
                        level: level.level || null
                    })
                }
            );


        const data =
            await response.json();


        if (!data.success) {

            addMentorMessage(
                "SecureMentor",
                data.error ||
                "Something went wrong."
            );

            return;
        }


        addMentorMessage(
            "SecureMentor",
            data.answer
        );


    } catch (error) {

        console.error(
            "SecureMentor error:",
            error
        );


        addMentorMessage(
            "SecureMentor",
            "I couldn't connect to the mentor right now."
        );


    } finally {

        mentorSend.disabled = false;

        if (mentorQuestion) {
            mentorQuestion.focus();
        }

    }

}


/*
 * ASK button
 */

if (mentorSend) {

    mentorSend.addEventListener(
        "click",
        function() {
            askSecureMentor();
        }
    );

}


/*
 * Enter = send
 * Shift + Enter = new line
 */

if (mentorQuestion) {

    mentorQuestion.addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                askSecureMentor();

            }

        }
    );

}