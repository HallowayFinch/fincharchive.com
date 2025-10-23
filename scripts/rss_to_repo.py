# scripts/rss_to_repo.py
import os, sys, json, time, feedparser, datetime as dt
from pathlib import Path
import re, html, urllib.request, urllib.parse

# -----------------------------
# Logging helper
# -----------------------------
def log(*args):
    print("[rss-sync]", *args, flush=True)

# -----------------------------
# HTTP helpers (manual fetch with UA)
# -----------------------------
def fetch_url(url: str, timeout=30) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) FinchArchiveBot/1.0 (+https://fincharchive.com)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")

# -----------------------------
# Minimal readable-content + HTML→MD (no extra deps)
# -----------------------------
def readability_extract(html_text: str) -> str:
    # prefer <article>, else <body>, else everything
    m = re.search(r"(?is)<article[^>]*>(.*?)</article>", html_text)
    if m:
        return m.group(1)
    m = re.search(r"(?is)<body[^>]*>(.*?)</body>", html_text)
    return m.group(1) if m else html_text

def html_to_markdown_simple(html_text: str) -> str:
    # strip scripts/styles
    text = re.sub(r"(?is)<script.*?</script>", "", html_text)
    text = re.sub(r"(?is)<style.*?</style>", "", text)
    # paragraph / br → newlines
    text = re.sub(r"(?is)</p>", "\n\n", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    # convert links: <a href="">text</a> → [text](href)
    def _a(m):
        href = m.group(1)
        inner = re.sub(r"(?is)<.*?>", "", m.group(2))
        return f"[{inner}]({href})"
    text = re.sub(r'(?is)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', _a, text)
    # strip remaining tags
    text = re.sub(r"(?is)<.*?>", "", text)
    return html.unescape(text).strip()

# -----------------------------
# 1022A / slug helpers
# -----------------------------
def int_to_letters(n: int) -> str:
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
    return re.sub(r"\s+", " ", title or "").strip() or "Untitled"

def safe_filename(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", s or "").strip("-").lower() or "log"

def extract_substack_slug(url: str) -> str:
    path = urllib.parse.urlparse(url).path.strip("/")
    if not path:
        return ""
    parts = [p for p in path.split("/") if p]
    return safe_filename(parts[-1])

def dedupe_slug(base_slug: str, existing_slugs: set) -> str:
    slug = base_slug or "log"
    if slug not in existing_slugs:
        return slug
    i = 2
    while f"{slug}-{i}" in existing_slugs:
        i += 1
    return f"{slug}-{i}"

# -----------------------------
# Paths & ENV
# -----------------------------
ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".finch" / "state.json"
LOGS_DIR = ROOT / "logs"      # alias redirects live here
COLL_DIR = ROOT / "_logs"     # Jekyll collection entries live here
ARTIFACTS = ROOT / "artifacts"

for p in (STATE.parent, LOGS_DIR, COLL_DIR, ARTIFACTS):
    p.mkdir(parents=True, exist_ok=True)

SUBSTACK_RSS_URL   = os.environ.get("SUBSTACK_RSS_URL", "").strip()
IMPORT_LATEST_ONLY = os.environ.get("IMPORT_LATEST_ONLY", "1") == "1"  # default ON for seeding
IMPORT_DEBUG       = os.environ.get("IMPORT_DEBUG", "1") == "1"

# -----------------------------
# State
# -----------------------------
def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text("utf-8"))
    return {"next_seq": 1, "seen_guids": []}

def save_state(s):
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")

# -----------------------------
# Feed fetch (manual + fallbacks)
# -----------------------------
def fetch_and_parse_feed(url: str):
    # primary fetch
    log(f"Fetching feed (manual UA): {url}")
    raw = fetch_url(url)
    log(f"Fetched {len(raw)} bytes")
    feed = feedparser.parse(raw)
    cnt = len(feed.entries or [])
    log(f"Primary parsed entries: {cnt}")

    if cnt:
        return feed

    # try fallbacks if empty
    from urllib.parse import urlparse
    host = (urlparse(url).hostname or "").lower()
    pub = host.split(".")[0] if host.endswith(".substack.com") else host.replace("substack.com", "").strip("/")
    fallback_urls = []
    if pub:
        fallback_urls = [
            f"https://{pub}.substack.com/feed",     # retry same base
            f"https://substack.com/feeds/{pub}.rss",
            f"https://substack.com/feed/{pub}",
        ]

    for fu in fallback_urls:
        try:
            log(f"Fallback fetch: {fu}")
            raw2 = fetch_url(fu)
            log(f"Fetched {len(raw2)} bytes (fallback)")
            f2 = feedparser.parse(raw2)
            c2 = len(f2.entries or [])
            log(f"Fallback parsed entries: {c2}")
            if c2:
                return f2
        except Exception as ex:
            log(f"Fallback fetch error for {fu}: {ex}")

    return feed  # possibly empty

# -----------------------------
# Entry selection
# -----------------------------
def pick_entries(feed):
    entries = list(feed.entries or [])
    if IMPORT_LATEST_ONLY and entries:
        newest = max(entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0))
        return [newest]
    st = load_state()
    out = []
    for e in entries:
        gid = e.get("id") or e.get("guid") or e.get("link")
        if not gid:
            continue
        if gid in st["seen_guids"]:
            continue
        out.append(e)
    return out

# -----------------------------
# Import one entry
# -----------------------------
def import_post(entry, state):
    title = clean_title(entry.get("title"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")
    date  = entry.get("published") or entry.get("updated") or dt.datetime.utcnow().isoformat() + "Z"

    log(f"Importing: '{title}' url={url}")
    if not url:
        raise RuntimeError("Entry has no link URL")

    page_html = fetch_url(url)
    main_html = readability_extract(page_html)
    body_md   = html_to_markdown_simple(main_html)

    log_id = make_log_id(state["next_seq"])
    alias  = slugify_log_id(log_id)

    base_slug = extract_substack_slug(url) or f"log-{log_id.lower()}"
    existing  = {p.stem for p in COLL_DIR.glob("*.md")}
    slug      = dedupe_slug(base_slug, existing)

    esc_title = title.replace('"', '\\"')
    fm = [
        "---",
        "layout: post",
        f'title: "{esc_title}"',
        f'log_id: "{log_id}"',
        f'date: "{date}"',
        f'source_url: "{url}"',
        f'guid: "{guid}"',
        f'permalink: "/logs/{slug}/"',
        "---",
        ""
    ]
    md_path = COLL_DIR / f"{slug}.md"
    md_path.write_text("\n".join(fm) + body_md + "\n", encoding="utf-8")
    log(f"Wrote: {md_path}")

    alias_dir = LOGS_DIR / alias
    alias_dir.mkdir(parents=True, exist_ok=True)
    redirect_html = f"""<!doctype html><meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="/logs/{slug}/">
<meta http-equiv="refresh" content="0; url=/logs/{slug}/">
<a href="/logs/{slug}/">Redirecting to /logs/{slug}/</a>
<script>location.href="/logs/{slug}/";</script>"""
    (alias_dir / "index.html").write_text(redirect_html, encoding="utf-8")
    log(f"Wrote: {alias_dir / 'index.html'} (alias for {log_id})")

    state["seen_guids"].append(guid)
    state["next_seq"] += 1

# -----------------------------
# Main
# -----------------------------
def main():
    try:
        if not SUBSTACK_RSS_URL:
            raise RuntimeError("SUBSTACK_RSS_URL is empty")

        feed = fetch_and_parse_feed(SUBSTACK_RSS_URL)
        log(f"Feed entries reported (final): {len(feed.entries or [])}")

        candidates = pick_entries(feed)
        log(f"Entries selected for import: {len(candidates)} (latest_only={IMPORT_LATEST_ONLY})")

        if not candidates and (feed.entries or []):
            log("No entries selected after filtering; importing newest as failsafe.")
            newest = max(feed.entries, key=lambda x: x.get('published_parsed') or x.get('updated_parsed') or time.gmtime(0))
            candidates = [newest]

        if not candidates:
            log("No entries found in feed. Exiting without changes.")
            return

        state = load_state()
        for e in sorted(candidates, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0)):
            import_post(e, state)
        save_state(state)
        log("Done.")
    except Exception as e:
        log(f"ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
