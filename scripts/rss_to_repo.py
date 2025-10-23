# scripts/rss_to_repo.py
import os, sys, json, time, feedparser, datetime as dt
from pathlib import Path
import re, html, urllib.request, urllib.parse

def log(*args): print("[rss-sync]", *args, flush=True)

# ----- ENV & paths -----------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / ".finch" / "state.json"
LOGS_ALIAS_DIR = ROOT / "logs"   # ONLY for one-time alias redirect folders
COLL_DIR = ROOT / "_logs"        # Jekyll collection items (source of truth)

for p in (STATE_FILE.parent, LOGS_ALIAS_DIR, COLL_DIR):
    p.mkdir(parents=True, exist_ok=True)

SUBSTACK_RSS_URL   = os.environ.get("SUBSTACK_RSS_URL", "").strip()
IMPORT_LATEST_ONLY = os.environ.get("IMPORT_LATEST_ONLY", "1") == "1"
IMPORT_DEBUG       = os.environ.get("IMPORT_DEBUG", "0") == "1"
RSS_PROXY_URL      = os.environ.get("RSS_PROXY_URL", "").strip()  # e.g. https://rss.fincharchive.com

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

def strip_substack_chrome(html_text: str) -> str:
    """
    Remove Substack title/header, author block, comments link, 'Share' button, etc.
    This happens BEFORE HTML→MD so they never appear in the Markdown.
    """
    t = html_text

    # kill header blocks and leading H1 (the title is already in front matter)
    t = re.sub(r"(?is)<header[^>]*>.*?</header>", "", t)
    t = re.sub(r"(?is)^\s*<h1[^>]*>.*?</h1>", "", t, count=1)

    # kill 'Share' buttons and comment links
    t = re.sub(r'(?is)<a[^>]+href="javascript:void\(0\)".*?</a>', "", t)
    t = re.sub(r'(?is)<a[^>]+href="[^"]*/comments[^"]*".*?</a>', "", t)

    # kill author/profile links like substack.com/@hallowayfinch
    t = re.sub(r'(?is)<a[^>]+href="https?://[^"]*substack\.com/@[^"]*".*?</a>', "", t)

    # stray 'Share' words wrapped in spans/divs
    t = re.sub(r'(?is)>(\s*Share\s*)<', "><", t)

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
    """
    Remove stray header line/empty links, standalone 'Share', collapse spacing.
    """
    out = md

    # remove a leading line that exactly matches the title (Substack sometimes repeats it)
    out = re.sub(rf"(?im)^\s*{re.escape(title)}\s*$\n?", "", out)

    # remove empty link artifacts like [](...)
    out = re.sub(r"\[\s*\]\([^)]+\)", "", out)

    # remove standalone 'Share' lines
    out = re.sub(r"(?m)^\s*Share\s*$", "", out)

    # collapse 3+ newlines to 2
    out = re.sub(r"\n{3,}", "\n\n", out)

    return out.strip() + "\n"

# ----- 1022 helpers ----------------------------------------------------------
def int_to_letters(n: int) -> str:
    s = ""
    while n > 0:
        n, rem = divmod(n-1, 26)
        s = chr(65 + rem) + s
    return s

def make_log_id(seq: int) -> str: return f"1022{int_to_letters(seq)}"
def slugify_log_id(log_id: str) -> str: return f"log-{log_id.lower()}"
def clean_title(title: str) -> str: return re.sub(r"\s+", " ", title or "").strip() or "Untitled"

def safe_filename(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9._/-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "log"

def extract_substack_slug(url: str) -> str:
    path = urllib.parse.urlparse(url).path.strip("/")
    if not path: return "log"
    parts = [p for p in path.split("/") if p]
    return safe_filename(parts[-1]) or "log"

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

# ----- Feed fetch (proxy-aware + fallbacks) ----------------------------------
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
    fallbacks = [
        f"https://{pub}.substack.com/api/v1/posts/rss",
        f"https://{pub}.substack.com/feed",
    ]
    for fu in fallbacks:
        try:
            f_url = proxied(fu)
            log(f"Fallback fetch: {f_url}")
            raw2 = fetch_url(f_url)
            f2 = parse_raw("Fallback", raw2)
            if f2.entries: return f2
        except Exception as ex:
            log(f"Fallback error for {fu}: {ex}")

    return feedparser.parse("")

# ----- Entry selection --------------------------------------------------------
def pick_entries(feed, state):
    entries = list(feed.entries or [])
    if IMPORT_LATEST_ONLY and entries:
        newest = max(entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0))
        return [newest]
    # Upsert all entries so edits propagate, but never create new filenames
    return entries

# ----- Content write helpers --------------------------------------------------
def write_text_if_changed(path: Path, content: str) -> bool:
    old = path.read_text("utf-8") if path.exists() else ""
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True

def build_front_matter(*, title, date, slug, log_id, url, guid) -> str:
    esc_title = title.replace('"', '\\"')
    lines = [
        "---",
        "layout: log",
        f'title: "{esc_title}"',
        f'log_id: "{log_id}"',
        f'date: "{date}"',
        f'source_url: "{url}"',
        f'guid: "{guid}"',
        f'permalink: "/logs/{slug}/"',
        "redirect_from:",
        f'  - "/logs/{slug}-2/"',
        f'  - "/logs/{slug}-2.md"',
        f'  - "/logs/{slug}-3/"',
        f'  - "/logs/{slug}-3.md"',
        f'  - "/logs/log-1022a.md"',
        "---",
        ""
    ]
    return "\n".join(lines)

def ensure_alias_redirect(log_id: str, slug: str):
    alias = slugify_log_id(log_id)  # e.g., log-1022a
    alias_dir = LOGS_ALIAS_DIR / alias
    if alias_dir.exists() and (alias_dir / "index.html").exists():
        return
    alias_dir.mkdir(parents=True, exist_ok=True)
    redirect_html = f"""<!doctype html><meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="/logs/{slug}/">
<meta http-equiv="refresh" content="0; url=/logs/{slug}/">
<a href="/logs/{slug}/">Redirecting to /logs/{slug}/</a>
<script>location.href="/logs/{slug}/";</script>"""
    (alias_dir / "index.html").write_text(redirect_html, encoding="utf-8")
    log(f"Wrote alias redirect: {alias_dir/'index.html'}")

# ----- Import one entry (IDEMPOTENT + CLEAN) ---------------------------------
def import_post(entry, state):
    title = clean_title(entry.get("title"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")

    # --- NEW: always store ISO-8601 with timezone ---
    if entry.get("published_parsed"):
        date = dt.datetime.fromtimestamp(time.mktime(entry.published_parsed)).astimezone().isoformat()
    elif entry.get("updated_parsed"):
        date = dt.datetime.fromtimestamp(time.mktime(entry.updated_parsed)).astimezone().isoformat()
    else:
        date = dt.datetime.now().astimezone().isoformat()
    # -----------------------------------------------

    if not url: raise RuntimeError("Entry missing URL")

    # Stable slug from URL; remember mapping
    slug = state["guid_to_slug"].get(guid) or extract_substack_slug(url)
    state["guid_to_slug"][guid] = slug

    # Assign a 1022 sequence only once per GUID
    log_id = state["guid_to_log_id"].get(guid)
    if not log_id:
        log_id = make_log_id(state["next_seq"])
        state["guid_to_log_id"][guid] = log_id
        state["next_seq"] += 1

    log(f"Upserting: '{title}' slug={slug} log_id={log_id}")

    # Fetch & convert body with cleanup
    raw_html = fetch_url(proxied(url))
    article_html = readability_extract(raw_html)
    article_html = strip_substack_chrome(article_html)
    body_md = html_to_markdown_simple(article_html)
    body_md = tidy_markdown(body_md, title)

    fm = build_front_matter(title=title, date=date, slug=slug, log_id=log_id, url=url, guid=guid)
    md_path = COLL_DIR / f"{slug}.md"
    changed = write_text_if_changed(md_path, fm + body_md + "\n")

    if changed:
        log(f"Wrote: {md_path}")
    else:
        log(f"No content change: {md_path}")

    ensure_alias_redirect(log_id, slug)

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

    candidates = pick_entries(feed, state)
    log(f"Entries selected for import (upsert): {len(candidates)}")
    if not candidates:
        log("No entries to process.")
        return

    for e in sorted(candidates, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0)):
        import_post(e, state)

    save_state(state)
    log("Done.")

if __name__ == "__main__":
    main()