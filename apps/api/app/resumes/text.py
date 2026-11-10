"""Text helpers: normalisation for grounding checks, privacy redaction before sending text to an AI provider,
and a heuristic that flags text which looks like instructions aimed at an AI."""

import re
import unicodedata

_EMAIL = re.compile(r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+")
_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_CNIC = re.compile(r"\b\d{5}-?\d{7}-?\d\b")
_PHONE = re.compile(r"(?<!\w)\+?\d[\d\s().\-]{8,}\d(?!\w)")

INJECTION_PATTERNS = [
    r"ignore (?:all |any |the )?(?:previous|prior|above|earlier) (?:instructions|prompts?|rules)",
    r"disregard (?:all |any |the )?(?:previous|prior|above|earlier|your) ",
    r"(?:reveal|show|print|repeat) (?:your |the )?(?:system )?(?:prompt|instructions)",
    r"you are (?:now )?(?:an? )?(?:ai|assistant|chatgpt|dan|jailbroken)",
    r"as an ai language model",
    r"new instructions?:",
    r"<\s*/?\s*(?:system|resume)\s*>",
]
_INJECTION = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).strip().casefold()


def grounded(snippet: str, haystack_normalized: str) -> bool:
    """A snippet counts as copied from the source if each fragment (split at ellipses) appears in it."""
    parts = [p for p in normalize(snippet.replace("…", "...")).split("...") if p.strip()]
    return bool(parts) and all(p.strip() in haystack_normalized for p in parts)


def redact(text: str) -> str:
    """Remove contact details and IDs before the text leaves our server."""
    text = _EMAIL.sub("[email]", text)
    text = _URL.sub("[link]", text)
    text = _CNIC.sub("[id]", text)
    return _PHONE.sub("[phone]", text)


def injection_signals(text: str) -> list[str]:
    return sorted({m.group(0).strip()[:60] for p in _INJECTION if (m := p.search(text))})


def wrap_resume(text: str) -> str:
    """Delimit untrusted text and stop it from closing the delimiter itself."""
    safe = re.sub(r"<\s*/\s*resume\s*>", "< /resume >", text, flags=re.IGNORECASE)
    return f"<resume>\n{safe}\n</resume>"
