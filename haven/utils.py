"""
haven/utils.py
──────────────
Helper utilities for the HAVEN chatbot:
  - Input sanitisation
  - Crisis keyword detection
  - Conversation history management
"""

import re
import logging

logger = logging.getLogger(__name__)

# ── Crisis keywords ────────────────────────────────────────────────────────────
CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "want to die",
    "die", "dying", "hopeless", "no reason to live", "self harm",
    "self-harm", "hurt myself", "cut myself", "overdose", "not worth living",
    "better off dead", "jump off", "hang myself", "shoot myself",
    "depressed", "depression", "can't go on", "give up on life",
]

# Predefined crisis response — never calls the LLM for these
CRISIS_RESPONSE = (
    "I'm really concerned about what you've shared. Your safety matters deeply. "
    "Please reach out for immediate support:\n\n"
    "🇮🇳 KIRAN Mental Health Helpline: 1800-599-0019 (24/7, free)\n"
    "🇮🇳 iCALL: 9152987821\n"
    "🇮🇳 Vandrevala Foundation: 1860-266-2345\n"
    "🌍 Emergency: 112\n\n"
    "You are not alone. Please talk to someone you trust right now. 💚"
)

# Safe fallback when the LLM is unavailable
FALLBACK_RESPONSE = (
    "I'm here for you, though I'm having a little trouble connecting right now. "
    "Please try again in a moment. If you need immediate support, "
    "call KIRAN at 1800-599-0019 (free, 24/7)."
)

# Session key used to store conversation history in Django's session
SESSION_HISTORY_KEY = "buddy_history"
MAX_HISTORY_TURNS   = 3   # keep last N user+assistant pairs


def sanitise_input(text: str) -> str:
    """
    Clean user input before sending to the model.
    - Strip leading/trailing whitespace
    - Collapse multiple spaces/newlines
    - Remove control characters
    - Truncate to a safe length
    """
    if not text:
        return ""

    # Remove control characters (except newline/tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Collapse excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    text = text.strip()

    # Hard cap — Mistral context is large but we keep prompts lean
    if len(text) > 1000:
        text = text[:1000]
        logger.debug("Input truncated to 1000 chars.")

    return text


def is_crisis(text: str) -> bool:
    """
    Return True if the message contains any crisis keyword.
    Uses word-boundary matching to avoid false positives
    (e.g. 'depressed' matches but 'undepressed' would not).
    """
    lower = text.lower()
    for kw in CRISIS_KEYWORDS:
        # Use word boundary for single words; phrase match for multi-word
        if " " in kw:
            if kw in lower:
                logger.warning("Crisis keyword detected (phrase): '%s'", kw)
                return True
        else:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, lower):
                logger.warning("Crisis keyword detected (word): '%s'", kw)
                return True
    return False


def get_history(session) -> list:
    """
    Retrieve conversation history from Django session.
    Returns a list of dicts: [{"role": "user"|"assistant", "content": "..."}]
    """
    return session.get(SESSION_HISTORY_KEY, [])


def update_history(session, user_msg: str, assistant_msg: str) -> None:
    """
    Append the latest exchange to session history and trim to MAX_HISTORY_TURNS.
    Each 'turn' = one user message + one assistant message.
    """
    history = get_history(session)
    history.append({"role": "user",      "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})

    # Keep only the last MAX_HISTORY_TURNS turns (2 messages per turn)
    max_messages = MAX_HISTORY_TURNS * 2
    if len(history) > max_messages:
        history = history[-max_messages:]

    session[SESSION_HISTORY_KEY] = history
    session.modified = True


def clear_history(session) -> None:
    """Clear conversation history (e.g. on logout or new session)."""
    session.pop(SESSION_HISTORY_KEY, None)
    session.modified = True
