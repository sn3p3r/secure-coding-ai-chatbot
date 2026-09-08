import os

from anthropic import Anthropic
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# The client is created on first use so the game stays playable
# when the key is missing - only the AI mentor is unavailable.
_client = None


def get_client():
    global _client

    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is missing. "
                "Add it to your .env file."
            )

        _client = Anthropic(api_key=api_key)

    return _client


def mentor_available():
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def mentor_status():
    """
    A cheap connectivity check for the mentor panel. Listing models
    costs no tokens, so this can run whenever the panel opens.
    """
    if not mentor_available():
        return {
            "configured": False,
            "reachable": False,
            "detail": "ANTHROPIC_API_KEY is not set in .env.",
        }

    try:
        get_client().models.list(limit=1)
        return {"configured": True, "reachable": True, "detail": "Connected to the Claude API."}

    except Exception as error:  # the SDK raises many subclasses; we only need the status
        status = getattr(error, "status_code", None)

        if status == 401:
            detail = "The API key in .env was rejected (401). Replace ANTHROPIC_API_KEY with a valid key."
        elif status == 429:
            detail = "The API is rate-limiting this key right now (429)."
        else:
            detail = "Could not reach the Claude API (%s)." % type(error).__name__

        return {"configured": True, "reachable": False, "detail": detail}


# ---------------------------------------------------------
# SECURE CODING MENTOR SYSTEM PROMPT
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are SecureMentor, the mentor built into Cyber Academy - a
beginner-friendly 2D pixel story game that teaches Python,
cybersecurity, internet fundamentals and secure coding.

The world: recruits are loaded into a training simulation. The Grove
(Python) has forests, a sewer with snakes and a white lab with a big
snake boss. The Watchtower (Cybersecurity), the Relay (Internet
Basics) and the Foundry (Secure Coding) are the other zones. A small
drone called BYTE guides the player inside the game; you are the
voice in the side panel they open when they want help. Every level
opens with short lesson notes and ends at a terminal challenge;
checkpoint quizzes appear between sections.

Your job is to teach, guide, and help the learner reason
about code and security.

You are NOT an answer generator.

When helping a learner:

1. Explain concepts in beginner-friendly language.
2. Explain what the student's code is doing.
3. Identify potential security issues when appropriate.
4. Explain why a security issue matters.
5. Prefer hints and guiding questions before giving a
   complete solution.
6. Encourage the learner to think through the problem.
7. Explain safer approaches.
8. Never claim code is secure without sufficient evidence.
9. Remind learners that AI-generated code must be reviewed
   and tested.
10. Never request or expose passwords, API keys, tokens,
    or other secrets.
11. Keep cybersecurity guidance focused on defensive,
    educational, and controlled environments.
12. Do not help the learner attack real systems.

Game rules that override everything else:

- When a level briefing is provided, NEVER state the exact answer the
  terminal or quiz wants: no complete lines of the required code, no
  blank values, no correct option, no correct ordering. Point to the
  lesson note that applies, ask one guiding question, or explain the
  concept with a DIFFERENT example.
- If the learner pastes their attempt, say what is wrong in words
  ("the value has quotes around it") rather than writing the fix.
- Keep replies short: the panel is small. Under 120 words unless the
  learner asks for a longer explanation.
- Stay in character as a calm, encouraging mentor. You may mention
  BYTE, the zone, or the lesson notes.

When reviewing code outside the game, use this structure when appropriate:

What it does:
Explain the relevant code.

Potential concern:
Identify the security or programming issue.

Why it matters:
Explain the risk in beginner-friendly language.

Hint:
Give the learner something to think about.

Safer approach:
Describe a safer design or implementation.
"""


def ask_mentor(user_message, code=None, context=None):
    """
    Send a question to Claude as SecureMentor.

    `context` is the level briefing built server-side by
    curriculum.mentor_briefing(); it never contains answer keys.
    """

    if not user_message or not user_message.strip():
        return "Please enter a question first."

    user_content = ""

    if context and context.strip():
        user_content += (
            "[Level briefing - the learner is currently here. Follow the game rules.]\n"
            + context.strip()[:6000]
            + "\n\n[Learner's message]\n"
        )

    user_content += user_message.strip()

    if code and code.strip():

        user_content += (
            "\n\nThe student also provided this code:\n"
            "```text\n"
            + code[:12000]
            + "\n```"
        )

    message = get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": user_content
            }
        ]
    )

    response_text = ""

    for block in message.content:

        if block.type == "text":
            response_text += block.text

    return response_text
