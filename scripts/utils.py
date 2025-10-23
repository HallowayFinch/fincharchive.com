import re, urllib.parse

def int_to_letters(n: int) -> str:
    # 1 -> A, 26 -> Z, 27 -> AA, etc.
    s = ""
    while n > 0:
        n, rem = divmod(n-1, 26)
        s = chr(65 + rem) + s
    return s

def make_log_id(seq: int) -> str:
    return f"1022{int_to_letters(seq)}"

def slugify_log_id(log_id: str) -> str:
    return f"log-{log_id.lower()}"

def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()

def safe_filename(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", s).strip("-").lower()

def extract_substack_slug(url: str) -> str:
    """
    Substack post URLs are like:
    https://hallowayfinch.substack.com/p/the-voice-in-the-static
    or with date segments:
    https://substack.com/@hallowayfinch/p/the-voice-in-the-static
    We take the last non-empty path segment.
    """
    path = urllib.parse.urlparse(url).path.strip("/")
    if not path:
        return ""
    parts = [p for p in path.split("/") if p]
    return safe_filename(parts[-1])

def dedupe_slug(base_slug: str, existing_slugs: set) -> str:
    """Ensure unique folder slug by suffixing -2, -3, ... if needed."""
    slug = base_slug or "log"
    if slug not in existing_slugs:
        return slug
    i = 2
    while f"{slug}-{i}" in existing_slugs:
        i += 1
    return f"{slug}-{i}"
