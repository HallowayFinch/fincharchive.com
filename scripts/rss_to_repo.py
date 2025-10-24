# scripts/rss_to_repo.py
import os, sys, json, time, feedparser, datetime as dt
from pathlib import Path
import re, html, urllib.request, urllib.parse

def log(*args): print("[rss-sync]", *args, flush=True)

# ----- ENV & paths -----------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
STATE_FILE   = ROOT / ".finch" / "state.json"
COLL_DIR     = ROOT / "_logs"          # Jekyll collection items (source of truth)
ARTIFACTS_DIR= ROOT / "artifacts"      # one folder per slug
for p in (STATE_FILE.parent, COLL_DIR, ARTIFACTS_DIR):
    p.mkdir(parents=True, exist_ok=True)

SUBSTACK_RSS_URL   = os.environ.get("SUBSTACK_RSS_URL", "").strip()
IMPORT_LATEST_ONLY = os.environ.get("IMPORT_LATEST_ONLY", "1") == "1"
IMPORT_DEBUG       = os.environ.get("IMPORT_DEBUG", "0") == "1"
RSS_PROXY_URL      = os.environ.get("RSS_PROXY_URL", "").strip()

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

SUBSTACK_TRASH_PATTERNS = [
    r"(?is)<header[^>]*>.*?</header>",
    r"(?is)^\s*<h1[^>]*>.*?</h1>",         # top H1
    r'(?is)<a[^>]+href="javascript:void\(0\)".*?</a>',  # Share / JS anchors
    r'(?is)<a[^>]+href="[^"]*/comments[^"]*".*?</a>',
    r'(?is)<a[^>]+href="https?://[^"]*substack\.com/@[^"]*".*?</a>',  # profile links
    r'(?is)<button[^>]*>.*?</button>',
    r'(?is)<nav[^>]*>.*?</nav>',
    r'(?is)<aside[^>]*>.*?</aside>',
    r'(?is)<footer[^>]*>.*?</footer>',
    r'(?is)<div[^>]+class="[^"]*(subscribe|paywall|toolbar|signup|footer|share)[^"]*"[^>]*>.*?</div>',
    r'(?is)>(\s*Subscribe\s*|\\s*Sign in\\s*)<',
]

def strip_substack_chrome(html_text: str) -> str:
    t = html_text
    for pat in SUBSTACK_TRASH_PATTERNS:
        t = re.sub(pat, "", t)
    # remove repeated title/date line blocks frequently inserted before the body
    t = re.sub(r'(?is)^\s*(<p[^>]*>\s*)?(?:Halloway\s*Finch)?\s*(?:Subscribe)?\s*(?:Sign\s*in)?\s*(</p>)?\s*', '', t)
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

    # If the very first line repeats the title or contains author/subscribe/sign-in/date debris, drop it.
    first_two = "\n".join(out.splitlines()[:2])
    if re.search(rf"(?i)^{re.escape(title)}\b", first_two):
        out = "\n".join(out.splitlines()[1:])
    out = re.sub(r"(?m)^\s*(Halloway\s*Finch)?\s*(Subscribe)?\s*(Sign\s*in)?\s*$\n?", "", out)

    # remove empty link artifacts like [](...)
    out = re.sub(r"\[\s*\]\([^)]+\)", "", out)

    # remove standalone 'Share' lines
    out = re.sub(r"(?m)^\s*Share\s*$", "", out)

    # collapse 3+ newlines to 2
    out = re.sub(r"\n{3,}", "\n\n", out)

    return out.strip() + "\n"

# ----- Slug helpers ----------------------------------------------------------
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

# ----- Feed fetch ------------------------------------------------------------
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
    for fu in (f"https://{pub}.substack.com/api/v1/posts/rss", f"https://{pub}.substack.com/feed"):
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
    return entries  # upsert all so edits propagate

# ----- Helpers: files/artifacts ----------------------------------------------
def write_text_if_changed(path: Path, content: str) -> bool:
    old = path.read_text("utf-8") if path.exists() else ""
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True

def ensure_artifact_folder(slug: str):
    """Create /artifacts/<slug>/ with a tiny README so Git commits the folder even if empty."""
    dest = ARTIFACTS_DIR / slug
    dest.mkdir(parents=True, exist_ok=True)
    readme = dest / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# Artifacts for `{slug}`\n\n"
            "Drop audio/images/docs for this log here. "
            "This file exists so the directory is tracked in Git.\n",
            encoding="utf-8"
        )
        log(f"Created {readme}")

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
        f'  - "/logs/log-1022a.md"',  # legacy bad link safety
        "---",
        ""
    ]
    return "\n".join(lines)

# ----- Import one entry -------------------------------------------------------
def import_post(entry, state):
    title = clean_title(entry.get("title"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")
    if not url: raise RuntimeError("Entry missing URL")

    # ISO-8601 with local tz when available
    if entry.get("published_parsed"):
        date = dt.datetime.fromtimestamp(time.mktime(entry.published_parsed)).astimezone().isoformat()
    elif entry.get("updated_parsed"):
        date = dt.datetime.fromtimestamp(time.mktime(entry.updated_parsed)).astimezone().isoformat()
    else:
        date = dt.datetime.now().astimezone().isoformat()

    # Stable slug from URL
    slug = state["guid_to_slug"].get(guid) or extract_substack_slug(url)
    state["guid_to_slug"][guid] = slug

    # Stable log id (first time only)
    log_id = state["guid_to_log_id"].get(guid)
    if not log_id:
        # first import for this GUID
        seq = state["next_seq"]
        # 1022 + A/B/…; we only need the label for the homepage, keep it simple
        def int_to_letters(n: int) -> str:
            s = ""
            while n > 0:
                n, rem = divmod(n-1, 26)
                s = chr(65 + rem) + s
            return s
        log_id = f"1022{int_to_letters(seq)}"
        state["guid_to_log_id"][guid] = log_id
        state["next_seq"] = seq + 1

    log(f"Upserting: '{title}' slug={slug} log_id={log_id}")

    # Fetch & convert body with cleanup
    raw_html = fetch_url(proxied(url))
    article_html = readability_extract(raw_html)
    article_html = strip_substack_chrome(article_html)
    body_md = html_to_markdown_simple(article_html)
    body_md = tidy_markdown(body_md, title)

    # Ensure /artifacts/<slug>/ exists & is committed
    ensure_artifact_folder(slug)

    fm = build_front_matter(title=title, date=date, slug=slug, log_id=log_id, url=url, guid=guid)
    md_path = COLL_DIR / f"{slug}.md"
    changed = write_text_if_changed(md_path, fm + body_md + "\n")

    if changed:
        log(f"Wrote: {md_path}")
    else:
        log(f"No content change: {md_path}")

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
    if not candidates:
        log("No entries to process.")
        return

    for e in sorted(candidates, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0)):
        import_post(e, state)

    save_state(state)
    log("Done.")

if __name__ == "__main__":
    main()