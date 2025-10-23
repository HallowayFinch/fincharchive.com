# scripts/rss_to_repo.py
import os, sys, json, time, feedparser, datetime as dt
from pathlib import Path
import re, html, urllib.request, urllib.parse

def log(*args): print("[rss-sync]", *args, flush=True)

# ----- ENV & paths -----------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".finch" / "state.json"
LOGS_DIR = ROOT / "logs"      # alias redirects
COLL_DIR = ROOT / "_logs"     # Jekyll collection items
for p in (STATE.parent, LOGS_DIR, COLL_DIR):
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
    """If url is already proxied (?url=...), return the original target; else return url."""
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
    """Wrap url through the proxy (if configured). Never double-wrap."""
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
def safe_filename(s: str) -> str: return re.sub(r"[^a-zA-Z0-9._-]+", "-", s or "").strip("-").lower() or "log"

def extract_substack_slug(url: str) -> str:
    path = urllib.parse.urlparse(url).path.strip("/")
    if not path: return ""
    parts = [p for p in path.split("/") if p]
    return safe_filename(parts[-1])

def dedupe_slug(base_slug: str, existing_slugs: set) -> str:
    slug = base_slug or "log"
    if slug not in existing_slugs: return slug
    i = 2
    while f"{slug}-{i}" in existing_slugs: i += 1
    return f"{slug}-{i}"

# ----- State -----------------------------------------------------------------
def load_state():
    if STATE.exists():
        try: return json.loads(STATE.read_text("utf-8"))
        except Exception: pass
    return {"next_seq": 1, "seen_guids": []}

def save_state(s): STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")

# ----- Feed fetch (proxy-aware + fallbacks) ----------------------------------
def fetch_and_parse_feed(url: str):
    # Always operate on the original Substack URL; fetch through proxy once.
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

    # Build fallbacks from the *true* Substack publication host
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
def pick_entries(feed):
    entries = list(feed.entries or [])
    if IMPORT_LATEST_ONLY and entries:
        newest = max(entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0))
        return [newest]
    st = load_state()
    out = []
    for e in entries:
        gid = e.get("id") or e.get("guid") or e.get("link")
        if not gid: continue
        if gid in st["seen_guids"]: continue
        out.append(e)
    return out

# ----- Import one entry -------------------------------------------------------
def import_post(entry, state):
    title = clean_title(entry.get("title"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")
    date  = entry.get("published") or entry.get("updated") or dt.datetime.utcnow().isoformat() + "Z"

    log(f"Importing: '{title}' url={url}")
    if not url: raise RuntimeError("Entry missing URL")

    html_text = fetch_url(proxied(url))
    main_html = readability_extract(html_text)
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
    log(f"Wrote alias redirect: {alias_dir/'index.html'}")

    state["seen_guids"].append(guid)
    state["next_seq"] += 1

# ----- Main -------------------------------------------------------------------
def main():
    if not SUBSTACK_RSS_URL:
        raise RuntimeError("SUBSTACK_RSS_URL not set")

    feed = fetch_and_parse_feed(SUBSTACK_RSS_URL)
    log(f"Final feed entries: {len(feed.entries or [])}")
    if not (feed.entries or []):
        log("No feed entries found. Aborting without change.")
        return

    candidates = pick_entries(feed)
    log(f"Entries selected for import: {len(candidates)}")
    if not candidates:
        log("No new entries to import.")
        return

    state = load_state()
    for e in sorted(candidates, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0)):
        import_post(e, state)
    save_state(state)
    log("Done.")

if __name__ == "__main__":
    main()
