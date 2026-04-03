"""
haven/services.py
─────────────────
Handles all communication with the local Ollama LLM.
Keeps AI logic completely separate from Django views.
"""

import json
import logging
import requests
from django.conf import settings

from .utils import (
    sanitise_input,
    is_crisis,
    get_history,
    update_history,
    CRISIS_RESPONSE,
    FALLBACK_RESPONSE,
)

logger = logging.getLogger(__name__)

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are BUDDY, a warm and supportive mental health companion for students. "
    "Your role is to listen carefully, respond with empathy, and offer gentle comfort. "
    "Keep your replies short (2–4 sentences), calm, and non-judgmental. "
    "Never diagnose, prescribe medication, or give medical advice. "
    "If someone seems to be in crisis, gently encourage them to seek professional help. "
    "Always respond in a caring, human tone."
)


def _build_prompt(history: list, user_message: str) -> str:
    """
    Build a single prompt string that includes:
      - System instructions
      - Last N conversation turns (from session history)
      - The current user message

    Mistral uses a simple text format; we embed history as labelled turns.
    """
    parts = [f"[SYSTEM]\n{SYSTEM_PROMPT}\n"]

    for turn in history:
        role  = "User" if turn["role"] == "user" else "BUDDY"
        parts.append(f"[{role}]\n{turn['content']}")

    parts.append(f"[User]\n{user_message}")
    parts.append("[BUDDY]")          # model continues from here

    return "\n\n".join(parts)


def ask_ollama(user_message: str, django_session) -> dict:
    """
    Main entry point called by the view.

    Returns a dict:
        {
            "response":     str,   # text to send back to the user
            "status":       str,   # "success" | "crisis_detected" | "error"
            "is_emergency": bool,
        }
    """
    # 1. Sanitise input
    clean_msg = sanitise_input(user_message)

    if not clean_msg:
        return {
            "response":     "Please type a message so I can help you.",
            "status":       "error",
            "is_emergency": False,
        }

    # 2. Crisis detection — never reaches the LLM
    if is_crisis(clean_msg):
        logger.info("Crisis keywords detected — returning emergency response.")
        return {
            "response":     CRISIS_RESPONSE,
            "status":       "crisis_detected",
            "is_emergency": True,
        }

    # 3. Build prompt with session history
    history = get_history(django_session)
    prompt  = _build_prompt(history, clean_msg)

    # 4. Call Ollama
    reply = _call_ollama(prompt)

    # 5. Persist history for next turn
    if reply:
        update_history(django_session, clean_msg, reply)

    return {
        "response":     reply or FALLBACK_RESPONSE,
        "status":       "success" if reply else "error",
        "is_emergency": False,
    }


def _call_ollama(prompt: str) -> str | None:
    """
    POST to the local Ollama API and return the model's reply text.
    Returns None on any failure so the caller can use the fallback.
    """
    url     = getattr(settings, "OLLAMA_URL",     "http://localhost:11434/api/generate")
    model   = getattr(settings, "OLLAMA_MODEL",   "mistral")
    timeout = getattr(settings, "OLLAMA_TIMEOUT", 60)   # seconds

    payload = {
        "model":  model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 300,   # cap response length
        },
    }

    try:
        logger.debug("Sending request to Ollama (%s) model=%s", url, model)
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()

        data  = resp.json()
        reply = data.get("response", "").strip()

        if not reply:
            logger.warning("Ollama returned an empty response.")
            return None

        logger.debug("Ollama reply received (%d chars).", len(reply))
        return reply

    except requests.exceptions.ConnectionError:
        logger.error("Ollama is not running or unreachable at %s.", url)
        return None

    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out after %ds.", timeout)
        return None

    except requests.exceptions.HTTPError as exc:
        logger.error("Ollama HTTP error: %s", exc)
        return None

    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("Unexpected Ollama response format: %s", exc)
        return None

    except Exception as exc:
        logger.exception("Unexpected error calling Ollama: %s", exc)
        return None
