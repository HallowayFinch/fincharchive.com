# scripts/rss_to_repo.py
import os, sys, json, time, feedparser, datetime as dt
from pathlib import Path
import re, html, urllib.request, urllib.parse

def log(*args): print("[rss-sync]", *args, flush=True)

# ----- ENV & paths -----------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
STATE_FILE    = ROOT / ".finch" / "state.json"
COLL_DIR      = ROOT / "_logs"         # Jekyll collection (source of truth)
ARTIFACTS_DIR = ROOT / "artifacts"     # sidecar files per slug

for p in (STATE_FILE.parent, COLL_DIR, ARTIFACTS_DIR):
    p.mkdir(parents=True, exist_ok=True)

SUBSTACK_RSS_URL   = os.environ.get("SUBSTACK_RSS_URL", "").strip()
IMPORT_LATEST_ONLY = os.environ.get("IMPORT_LATEST_ONLY", "1") == "1"
IMPORT_DEBUG       = os.environ.get("IMPORT_DEBUG", "0") == "1"
RSS_PROXY_URL      = os.environ.get("RSS_PROXY_URL", "").strip()

# File types we surface if present under /artifacts/:slug/
ARTIFACT_EXTS = [
    ".wav", ".flac", ".mp3",
    ".pdf",
    ".jpg", ".jpeg", ".png", ".gif", ".webp"
]

# ----- Proxy helpers ---------------------------------------------------------
def _proxy_host() -> str:
    if not RSS_PROXY_URL: return ""
    return urllib.parse.urlparse(RSS_PROXY_URL).netloc

def unproxy_url(url: str) -> str:
    try:
        u = urllib.parse.urlparse(url)
        if _proxy_host() and u.netloc == _proxy_host():
            qs = urllib.parse.parse_qs(u.query)
            if "url" in qs and qs["url"]:
                return urllib.parse.unquote(qs["url"][0])
    except Exception:
        pass
    return url

def proxied(url: str) -> str:
    raw = unproxy_url(url)
    if not RSS_PROXY_URL: return raw
    return f"{RSS_PROXY_URL}?url={urllib.parse.quote(raw, safe='')}"

# ----- HTTP fetch ------------------------------------------------------------
def fetch_url(url: str, timeout=30) -> str:
    headers = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://substack.com/",
        "Connection": "keep-alive",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")

# ----- Minimal readability & HTML→MD -----------------------------------------
def readability_extract(html_text: str) -> str:
    m = re.search(r"(?is)<article[^>]*>(.*?)</article>", html_text)
    if m: return m.group(1)
    m = re.search(r"(?is)<body[^>]*>(.*?)</body>", html_text)
    return m.group(1) if m else html_text

def strip_chrome(html_text: str) -> str:
    """
    Remove Substack header/title/author/share/comments etc.
    Then keep from the **first <p>** onward so the duplicate
    title/date line before the story never survives.
    """
    t = html_text
    t = re.sub(r"(?is)<header[^>]*>.*?</header>", "", t)
    t = re.sub(r"(?is)<h1[^>]*>.*?</h1>", "", t, count=1)
    t = re.sub(r'(?is)<a[^>]+href="javascript:void\(0\)".*?</a>', "", t)                 # “Share”
    t = re.sub(r'(?is)<a[^>]+href="[^"]*/comments[^"]*".*?</a>', "", t)                 # comments links
    t = re.sub(r'(?is)<a[^>]+href="https?://[^"]*substack\.com/@[^"]*".*?</a>', "", t)  # author profile
    t = re.sub(r'(?is)>(\s*Share\s*)<', "><", t)

    m = re.search(r"(?is)<p[^>]*>.*", t)  # keep from the first paragraph onward
    if m: t = m.group(0)
    return t

def html_to_markdown_simple(html_text: str) -> str:
    text = re.sub(r"(?is)<script.*?</script>", "", html_text)
    text = re.sub(r"(?is)<style.*?</style>", "", text)
    text = re.sub(r"(?is)</p>", "\n\n", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)

    def _a(m):
        href = m.group(1)
        inner = re.sub(r"(?is)<.*?>", "", m.group(2))
        return f"[{inner}]({href})"

    text = re.sub(r'(?is)<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', _a, text)
    text = re.sub(r"(?is)<.*?>", "", text)
    return html.unescape(text).strip()

def tidy_markdown(md: str, title: str) -> str:
    out = md
    out = re.sub(rf"(?im)^\s*{re.escape(title)}\s*$\n?", "", out)  # stray leading title
    out = re.sub(r"\[\s*\]\([^)]+\)", "", out)                    # empty []() links
    out = re.sub(r"(?m)^\s*Share\s*$", "", out)                   # naked “Share”
    out = re.sub(r"\n{3,}", "\n\n", out)                          # collapse spacing
    return out.strip() + "\n"

# ----- Helpers ----------------------------------------------------------------
def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title or "").strip() or "Untitled"

def safe_filename(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9._/-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "log"

def extract_slug_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path.strip("/")
    if not path: return "log"
    return safe_filename(path.split("/")[-1]) or "log"

def find_artifacts_for_slug(slug: str):
    folder = ARTIFACTS_DIR / slug
    items = []
    if folder.exists():
        for ext in ARTIFACT_EXTS:
            for p in sorted(folder.glob(f"*{ext}"), key=lambda x: x.name.lower()):
                label = f"{p.stem.replace('_',' ').replace('-',' ').strip()} ({p.suffix.upper()[1:]})"
                items.append({"path": f"/artifacts/{slug}/{p.name}", "label": label})
    return items

def primary_image_from_entry(entry) -> str:
    """Try common places feedparser exposes an image (enclosure or media)."""
    try:
        if getattr(entry, "enclosures", None):
            for enc in entry.enclosures:
                url = enc.get("url")
                if url and re.search(r"\.(png|jpe?g|gif|webp)(\?.*)?$", url, re.I):
                    return url
        if entry.get("media_content"):
            for m in entry.media_content:
                url = m.get("url")
                if url and re.search(r"\.(png|jpe?g|gif|webp)(\?.*)?$", url, re.I):
                    return url
        if entry.get("media_thumbnail"):
            for m in entry.media_thumbnail:
                url = m.get("url")
                if url and re.search(r"\.(png|jpe?g|gif|webp)(\?.*)?$", url, re.I):
                    return url
    except Exception:
        pass
    return ""

# ----- State -----------------------------------------------------------------
DEFAULT_STATE = {
    "next_seq": 1,
    "guid_to_slug": {},
    "guid_to_log_id": {},
    "seen_guids": []
}

def load_state():
    if STATE_FILE.exists():
        try:
            s = json.loads(STATE_FILE.read_text("utf-8"))
            for k, v in DEFAULT_STATE.items():
                if k not in s: s[k] = v
            return s
        except Exception:
            pass
    return DEFAULT_STATE.copy()

def save_state(s): STATE_FILE.write_text(json.dumps(s, indent=2), encoding="utf-8")

# ----- Feed fetch -------------------------------------------------------------
def fetch_and_parse_feed(url: str):
    raw_feed_url = unproxy_url(url)

    def parse_raw(label: str, raw: str):
        feed = feedparser.parse(raw)
        log(f"{label} parsed entries: {len(feed.entries or [])}")
        return feed

    try:
        primary = proxied(raw_feed_url)
        log(f"Fetching feed: {primary}")
        raw = fetch_url(primary)
        if IMPORT_DEBUG: log(f"Feed head: {raw[:250].replace(chr(10),' ')}")
        feed = parse_raw("Primary", raw)
        if feed.entries: return feed
        log("Primary feed empty; trying fallbacks…")
    except Exception as e:
        log(f"Primary fetch failed: {e}")

    host = urllib.parse.urlparse(raw_feed_url).hostname or ""
    pub = host.split(".")[0] if host.endswith(".substack.com") else host
    for fu in (f"https://{pub}.substack.com/api/v1/posts/rss",
               f"https://{pub}.substack.com/feed"):
        try:
            raw2 = fetch_url(proxied(fu))
            f2 = parse_raw("Fallback", raw2)
            if f2.entries: return f2
        except Exception as ex:
            log(f"Fallback error for {fu}: {ex}")

    return feedparser.parse("")

# ----- Entry selection --------------------------------------------------------
def pick_entries(feed):
    entries = list(feed.entries or [])
    if IMPORT_LATEST_ONLY and entries:
        newest = max(entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0))
        return [newest]
    return entries

# ----- Write helpers ----------------------------------------------------------
def write_text_if_changed(path: Path, content: str) -> bool:
    old = path.read_text("utf-8") if path.exists() else ""
    if old == content: return False
    path.write_text(content, encoding="utf-8")
    return True

def build_front_matter(*, title, date_iso, slug, log_id, url, guid, hero_image, artifacts):
    esc_title = title.replace('"', '\\"')
    lines = [
        "---",
        "layout: log",
        f'title: "{esc_title}"',
        f'log_id: "{log_id}"',
        f'date: "{date_iso}"',
        f'source_url: "{url}"',
        f'guid: "{guid}"',
        f'permalink: "/logs/{slug}/"',
    ]
    if hero_image:
        lines.append(f'hero_image: "{hero_image}"')
    if artifacts:
        lines.append("artifacts:")
        for a in artifacts:
            lines.append(f'  - path: "{a["path"]}"')
            lines.append(f'    label: "{a["label"]}"')
    lines += ["---", ""]
    return "\n".join(lines)

# ----- Import one -------------------------------------------------------------
def import_post(entry, state):
    title = clean_title(entry.get("title"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")
    if not url: raise RuntimeError("Entry missing URL")

    # ISO-8601 w/ local timezone
    if entry.get("published_parsed"):
        date_iso = dt.datetime.fromtimestamp(time.mktime(entry.published_parsed)).astimezone().isoformat()
    elif entry.get("updated_parsed"):
        date_iso = dt.datetime.fromtimestamp(time.mktime(entry.updated_parsed)).astimezone().isoformat()
    else:
        date_iso = dt.datetime.now().astimezone().isoformat()

    # slug from Substack URL
    slug = state["guid_to_slug"].get(guid) or extract_slug_from_url(url)
    state["guid_to_slug"][guid] = slug

    # assign stable 1022A/B/C… if new
    log_id = state["guid_to_log_id"].get(guid)
    if not log_id:
        n = state["next_seq"]
        s = ""
        while n > 0:
            n, r = divmod(n-1, 26)
            s = chr(65+r) + s
        log_id = f"1022{s}"
        state["next_seq"] += 1
        state["guid_to_log_id"][guid] = log_id

    # Prefer RSS content:encoded; fallback to fetched page
    content_html = ""
    try:
        if entry.get("content") and entry.content:
            content_html = entry.content[0].value or ""
    except Exception:
        pass
    if not content_html:
        raw_html = fetch_url(proxied(url))
        content_html = readability_extract(raw_html)

    # Clean and keep from the first paragraph only
    content_html = strip_chrome(content_html)
    body_md = html_to_markdown_simple(content_html)
    body_md = tidy_markdown(body_md, title)

    # hero image (enclosure/media)
    hero = primary_image_from_entry(entry)

    # ensure artifacts folder exists for this slug
    (ARTIFACTS_DIR / slug).mkdir(parents=True, exist_ok=True)
    artifacts = find_artifacts_for_slug(slug)

    fm = build_front_matter(
        title=title, date_iso=date_iso, slug=slug, log_id=log_id,
        url=url, guid=guid, hero_image=hero, artifacts=artifacts
    )

    md_path = COLL_DIR / f"{slug}.md"
    changed = write_text_if_changed(md_path, fm + body_md + "\n")
    log(("Wrote" if changed else "No change") + f": {md_path}")

    if guid not in state["seen_guids"]:
        state["seen_guids"].append(guid)

# ----- Main -------------------------------------------------------------------
def main():
    if not SUBSTACK_RSS_URL:
        raise RuntimeError("SUBSTACK_RSS_URL not set")

    state = load_state()
    feed = fetch_and_parse_feed(SUBSTACK_RSS_URL)
    log(f"Final feed entries: {len(feed.entries or [])}")
    if not (feed.entries or []):
        log("No feed entries found. Aborting without change.")
        return

    candidates = pick_entries(feed)
    log(f"Entries selected for import (upsert): {len(candidates)}")
    for e in sorted(candidates, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0)):
        import_post(e, state)

    save_state(state)
    log("Done.")

if __name__ == "__main__":
    main()
