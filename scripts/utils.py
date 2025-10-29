# scripts/utils.py
import re
import urllib.parse

# -------------------------
# ID helpers
# -------------------------
def int_to_letters(n: int) -> str:
    """1 -> A, 26 -> Z, 27 -> AA, etc."""
    s = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s

def make_log_id(seq: int) -> str:
    return f"1022{int_to_letters(seq)}"

def slugify_log_id(log_id: str) -> str:
    return f"log-{log_id.lower()}"

# -------------------------
# String / slug helpers
# -------------------------
def clean_title(title: str) -> str:
    """Normalize whitespace, tolerate None."""
    return re.sub(r"\s+", " ", (title or "")).strip()

def safe_filename(s: str) -> str:
    """
    Lowercase, keep a–z, 0–9, dot, underscore, dash.
    Collapse repeated dashes and trim edges.
    """
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")

# -------------------------
# URL → slug
# -------------------------
_IGNORE_LAST_SEGMENTS = {
    "", "p", "feed", "feeds", "archive", "about", "subscribe", "login",
    "signup", "comments", "notes", "video", "podcast"
}

def extract_slug_from_url(url: str) -> str:
    """
    Extract a post slug from any Finch/Substack-style URL by taking the
    last meaningful path segment (host-agnostic).

    Examples:
      https://hallowayfinch.com/p/the-voice-in-the-static       -> the-voice-in-the-static
      https://hallowayfinch.substack.com/p/the-orchard-transmission -> the-orchard-transmission
      https://substack.com/@hallowayfinch/p/the-orchard-transmission -> the-orchard-transmission
    """
    path = urllib.parse.urlparse(url or "").path
    parts = [p for p in (path or "").strip("/").split("/") if p]

    # Walk from end to start; pick the first non-ignored segment.
    for seg in reversed(parts):
        if seg.lower() not in _IGNORE_LAST_SEGMENTS:
            # Strip a rare trailing .html (some exports)
            seg = re.sub(r"\.html?$", "", seg, flags=re.I)
            return safe_filename(seg)

    # Fallback
    return "log"

# Backwards-compat alias (can remove later once all imports updated)
def extract_substack_slug(url: str) -> str:
    return extract_slug_from_url(url)

# -------------------------
# Slug de-duplication
# -------------------------
def dedupe_slug(base_slug: str, existing_slugs: set) -> str:
    """Ensure unique slug by suffixing -2, -3, ... if needed."""
    slug = base_slug or "log"
    if slug not in (existing_slugs or set()):
        return slug
    i = 2
    while f"{slug}-{i}" in existing_slugs:
        i += 1
    return f"{slug}-{i}"