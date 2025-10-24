# scripts/rss_to_repo.py
import os, sys, json, time, feedparser, datetime as dt
from pathlib import Path
import re, html, urllib.request, urllib.parse, shutil

def log(*args): print("[rss-sync]", *args, flush=True)

# ----- ENV & paths -----------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
STATE_FILE     = ROOT / ".finch" / "state.json"
COLL_DIR       = ROOT / "_logs"            # Jekyll collection items (source of truth)
ARTIFACTS_DIR  = ROOT / "artifacts"        # Sidecar artifacts per slug

for p in (STATE_FILE.parent, COLL_DIR, ARTIFACTS_DIR):
    p.mkdir(parents=True, exist_ok=True)

SUBSTACK_RSS_URL     = os.environ.get("SUBSTACK_RSS_URL", "").strip()
IMPORT_LATEST_ONLY   = os.environ.get("IMPORT_LATEST_ONLY", "1") == "1"
IMPORT_DEBUG         = os.environ.get("IMPORT_DEBUG", "0") == "1"
RSS_PROXY_URL        = os.environ.get("RSS_PROXY_URL", "").strip()

# File types we’ll surface on the page
ARTIFACT_EXTS = [
    ".wav", ".flac", ".mp3",                 # audio
    ".pdf",                                  # docs
    ".jpg", ".jpeg", ".png", ".gif", ".webp" # images
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

# ----- Content extraction helpers -------------------------------------------
def _first(regex: str, text: str):
    m = re.search(regex, text, flags=re.I | re.S)
    return m.group(1) if m else None

def _largest_block(candidates) -> str:
    """Pick the candidate with the most non-whitespace text."""
    best = ""
    for c in candidates:
        if not c: continue
        # crude weight: visible chars + number of <p> blocks
        score = len(re.sub(r"\s+", " ", re.sub(r"(?is)<script.*?</script>|<style.*?</style>", "", c))) + 200*len(re.findall(r"(?i)<p\b", c))
        if score > len(best):
            best = c
    return best or ""

def readability_extract(html_text: str) -> str:
    """
    Try a few containers in order:
      - <article ...>...</article>
      - role="article"
      - <main ...>...</main>
      - common wrappers used by Substack (<div data-...>, .post, etc.)
      - fallback to <body>
    Then choose the *largest* candidate to avoid truncation.
    """
    t = html_text or ""
    candidates = []

    # 1) article (explicit)
    candidates.append(_first(r"(?is)<article[^>]*>(.*?)</article>", t))
    # 2) ARIA role=article
    candidates.append(_first(r'(?is)<(?:div|section)[^>]*\brole\s*=\s*["\']article["\'][^>]*>(.*?)</(?:div|section)>', t))
    # 3) main
    candidates.append(_first(r"(?is)<main[^>]*>(.*?)</main>", t))
    # 4) common substack wrappers
    candidates.append(_first(r'(?is)<div[^>]*\bclass=["\'][^"\']*(?:post|body|content)[^"\']*["\'][^>]*>(.*?)</div>', t))
    candidates.append(_first(r'(?is)<section[^>]*\bclass=["\'][^"\']*(?:post|body|content)[^"\']*["\'][^>]*>(.*?)</section>', t))
    # 5) fallback to body
    candidates.append(_first(r"(?is)<body[^>]*>(.*?)</body>", t) or t)

    return _largest_block(candidates)

def strip_substack_chrome(html_text: str) -> str:
    """
    Remove Substack title/header, author blocks, comments link, 'Share', etc.
    Do this BEFORE HTML→MD so they never appear in Markdown.
    """
    t = html_text

    # kill header blocks and leading H1 (we render the title separately)
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
    Also remove a repeated leading line that exactly matches the title.
    """
    out = md
    out = re.sub(rf"(?im)^\s*{re.escape(title)}\s*$\n?", "", out)
    out = re.sub(r"\[\s*\]\([^)]+\)", "", out)
    out = re.sub(r"(?m)^\s*Share\s*$", "", out)
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
    return entries  # upsert all so edits propagate

# ----- Artifacts helpers -----------------------------------------------------
def ensure_artifact_dir(slug: str) -> Path:
    """Always create /artifacts/<slug>/ so you have a place to drop files."""
    folder = ARTIFACTS_DIR / slug
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def nice_label_from_path(p: Path) -> str:
    base = p.stem.replace("_", " ").replace("-", " ").strip() or "Artifact"
    ext = p.suffix.upper().lstrip(".")
    return f"{base} ({ext})"

def find_artifacts_for_slug(slug: str):
    """Return a list of {'path': str, 'label': str} under /artifacts/:slug/ for supported exts."""
    folder = ARTIFACTS_DIR / slug
    items = []
    if folder.exists() and folder.is_dir():
        for ext in ARTIFACT_EXTS:
            for p in sorted(folder.glob(f"*{ext}"), key=lambda x: x.name.lower()):
                items.append({
                    "path": f"/artifacts/{slug}/{p.name}",
                    "label": nice_label_from_path(p)
                })
    return items

def read_existing_log_id_from_md(slug: str):
    """If _logs/:slug.md exists and has log_id in front matter, return it."""
    md_path = COLL_DIR / f"{slug}.md"
    if not md_path.exists():
        return None
    try:
        head = md_path.read_text("utf-8")
        m = re.search(r"(?s)^---(.*?)---", head)
        if not m: return None
        fm = m.group(1)
        m2 = re.search(r"^\s*log_id:\s*\"?([A-Za-z0-9-]+)\"?\s*$", fm, re.M)
        if m2:
            return m2.group(1)
    except Exception:
        pass
    return None

# ----- Content write helpers --------------------------------------------------
def write_text_if_changed(path: Path, content: str) -> bool:
    old = path.read_text("utf-8") if path.exists() else ""
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True

def build_front_matter(*, title, date, slug, log_id, url, guid, artifacts=None) -> str:
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
    ]
    if artifacts:
        lines += ["artifacts:"]
        for a in artifacts:
            lines += [
                f'  - path: "{a["path"]}"',
                f'    label: "{a.get("label","Artifact")}"'
            ]
    lines += ["---", ""]
    return "\n".join(lines)

# ----- Import one entry (IDEMPOTENT + CLEAN) ---------------------------------
def import_post(entry, state):
    title = clean_title(entry.get("title"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")

    # ISO-8601 with timezone (prefer published)
    if entry.get("published_parsed"):
        date = dt.datetime.fromtimestamp(time.mktime(entry.published_parsed)).astimezone().isoformat()
    elif entry.get("updated_parsed"):
        date = dt.datetime.fromtimestamp(time.mktime(entry.updated_parsed)).astimezone().isoformat()
    else:
        date = dt.datetime.now().astimezone().isoformat()

    if not url: raise RuntimeError("Entry missing URL")

    # Stable slug from URL; remember mapping
    slug = state["guid_to_slug"].get(guid) or extract_substack_slug(url)
    state["guid_to_slug"][guid] = slug

    # Reuse existing log_id if present on disk; else assign
    existing_log_id = read_existing_log_id_from_md(slug)
    if existing_log_id:
        log_id = existing_log_id
        state["guid_to_log_id"][guid] = log_id
    else:
        log_id = state["guid_to_log_id"].get(guid)
        if not log_id:
            log_id = make_log_id(state["next_seq"])
            state["guid_to_log_id"][guid] = log_id
            state["next_seq"] += 1

    log(f"Upserting: '{title}' slug={slug} log_id={log_id}")

    # Fetch & convert body with cleanup (more robust extractor)
    raw_html = fetch_url(proxied(url))
    article_html = readability_extract(raw_html)
    article_html = strip_substack_chrome(article_html)
    body_md = html_to_markdown_simple(article_html)
    body_md = tidy_markdown(body_md, title)

    # Ensure artifacts folder exists (even if empty) so you can drop files
    ensure_artifact_dir(slug)
    artifacts = find_artifacts_for_slug(slug)

    fm = build_front_matter(
        title=title, date=date, slug=slug, log_id=log_id,
        url=url, guid=guid, artifacts=artifacts
    )
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
