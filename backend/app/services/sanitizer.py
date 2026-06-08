"""
Input sanitization — strip dangerous HTML/scripts from user inputs.
"""
import re

import bleach


ALLOWED_TAGS: list[str] = []
ALLOWED_ATTRIBUTES: dict[str, list[str]] = {}

MAX_PROMPT_LENGTH = 5000
MAX_TITLE_LENGTH = 200


def sanitize_text(text: str) -> str:
    """Strip all HTML tags and limit whitespace."""
    cleaned = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def sanitize_prompt(prompt: str) -> str:
    """Sanitize a film prompt — strip HTML, enforce max length."""
    cleaned = sanitize_text(prompt)
    if len(cleaned) > MAX_PROMPT_LENGTH:
        cleaned = cleaned[:MAX_PROMPT_LENGTH]
    return cleaned


def sanitize_title(title: str) -> str:
    """Sanitize a project title — strip HTML, enforce max length."""
    cleaned = sanitize_text(title)
    if len(cleaned) > MAX_TITLE_LENGTH:
        cleaned = cleaned[:MAX_TITLE_LENGTH]
    return cleaned
