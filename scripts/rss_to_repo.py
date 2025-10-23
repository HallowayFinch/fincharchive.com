# scripts/rss_to_repo.py
import os, sys, json, time, feedparser, datetime as dt
from pathlib import Path
import re, html, urllib.request, urllib.parse, shutil

def log(*args): print("[rss-sync]", *args, flush=True)

# ----- ENV & paths -----------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
STATE_FILE      = ROOT / ".finch" / "state.json"
LOGS_ALIAS_DIR  = ROOT / "logs"       # optional legacy alias redirects (log-1022x → /logs/:slug/)
COLL_DIR        = ROOT / "_logs"      # Jekyll collection items (source of truth)
ARTIFACTS_DIR   = ROOT / "artifacts"  # /artifacts/<slug>/*

for p in (STATE_FILE.parent, LOGS_ALIAS_DIR, COLL_DIR, ARTIFACTS_DIR):
    p.mkdir(parents=True, exist_ok=True)

SUBSTACK_RSS_URL     = os.environ.get("SUBSTACK_RSS_URL", "").strip()
IMPORT_LATEST_ONLY   = os.environ.get("IMPORT_LATEST_ONLY", "1") == "1"
IMPORT_DEBUG         = os.environ.get("IMPORT_DEBUG", "0") == "1"
RSS_PROXY_URL        = os.environ.get("RSS_PROXY_URL", "").strip()
GENERATE_LOG_ALIAS   = os.environ.get("GENERATE_LOG_ALIAS", "1") == "1"  # "0" disables /logs/log-1022x/
CLEAN_OLD_ALIASES    = os.environ.get("CLEAN_OLD_ALIASES", "1") == "1"   # remove stale alias folders for same slug

# File types we surface on the page
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

# ----- HTTP fetch (with retries) --------------------------------------------
def fetch_url(url: str, timeout=30, retries=3, backoff=2.0) -> str:
    headers = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://substack.com/",
        "Connection": "keep-alive",
    }
    last_err = None
    for i in range(max(1, retries)):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "ignore")
        except Exception as e:
            last_err = e
            if i < retries - 1:
                time.sleep(backoff ** i)  # 1s, 2s, 4s...
            else:
                raise last_err

# ----- Minimal readability & HTML→MD -----------------------------------------
def readability_extract(html_text: str) -> str:
    m = re.search(r"(?is)<article[^>]*>(.*?)</article>", html_text)
    if m: return m.group(1)
    m = re.search(r"(?is)<body[^>]*>(.*?)</body>", html_text)
    return m.group(1) if m else html_text

def strip_substack_chrome(html_text: str) -> str:
    """Remove Substack title/author chrome, comments link, Share buttons, etc."""
    t = html_text
    t = re.sub(r"(?is)<header[^>]*>.*?</header>", "", t)
    t = re.sub(r"(?is)^\s*<h1[^>]*>.*?</h1>", "", t, count=1)
    t = re.sub(r'(?is)<a[^>]+href="javascript:void\(0\)".*?</a>', "", t)
    t = re.sub(r'(?is)<a[^>]+href="[^"]*/comments[^"]*".*?</a>', "", t)
    t = re.sub(r'(?is)<a[^>]+href="https?://[^"]*substack\.com/@[^"]*".*?</a>', "", t)
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
    out = md
    out = re.sub(rf"(?im)^\s*{re.escape(title)}\s*$\n?", "", out)  # drop repeated H1 line
    out = re.sub(r"\[\s*\]\([^)]+\)", "", out)                    # remove empty links [](...)
    out = re.sub(r"(?m)^\s*Share\s*$", "", out)                   # remove lone 'Share'
    out = re.sub(r"\n{3,}", "\n\n", out)                          # collapse blank lines
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
    return entries  # upsert all so edits propagate

# ----- Content write helpers --------------------------------------------------
def write_text_if_changed(path: Path, content: str) -> bool:
    old = path.read_text("utf-8") if path.exists() else ""
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True

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
        m = re.search(r"(?s)^---(.*?)---", head)  # front matter
        if not m: return None
        fm = m.group(1)
        m2 = re.search(r"^\s*log_id:\s*\"?([A-Za-z0-9-]+)\"?\s*$", fm, re.M)
        if m2:
            return m2.group(1)
    except Exception:
        pass
    return None

def ensure_artifact_folder(slug: str, log_id: str) -> Path:
    """
    Ensure artifacts live under /artifacts/:slug/.
    If a legacy folder /artifacts/log-1022x/ exists and the slug folder doesn't,
    migrate it to the slug.
    """
    desired = ARTIFACTS_DIR / slug
    legacy  = ARTIFACTS_DIR / f"log-{(log_id or '').lower()}"
    try:
        if legacy.exists() and legacy.is_dir() and not desired.exists():
            legacy.rename(desired)
            log(f"Artifacts folder migrated: {legacy} → {desired}")
    except Exception as e:
        log(f"Artifacts migrate error ({legacy}→{desired}): {e}")
    desired.mkdir(parents=True, exist_ok=True)
    return desired

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
        f'  - "/logs/log-1022a.md"',
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

def ensure_alias_redirect(log_id: str, slug: str):
    if not GENERATE_LOG_ALIAS:
        return
    alias = slugify_log_id(log_id)  # e.g., log-1022a
    alias_dir = LOGS_ALIAS_DIR / alias
    alias_dir.mkdir(parents=True, exist_ok=True)
    redirect_html = f"""<!doctype html><meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="/logs/{slug}/">
<meta http-equiv="refresh" content="0; url=/logs/{slug}/">
<a href="/logs/{slug}/">Redirecting to /logs/{slug}/</a>
<script>location.href="/logs/{slug}/";</script>"""
    (alias_dir / "index.html").write_text(redirect_html, encoding="utf-8")
    log(f"Wrote alias redirect: {alias_dir/'index.html'}")

def cleanup_old_aliases_for_slug(current_log_id: str, slug: str):
    """Remove other /logs/log-1022*/ folders that point to this slug but aren't the current one."""
    if not CLEAN_OLD_ALIASES or not GENERATE_LOG_ALIAS:
        return
    want_alias = slugify_log_id(current_log_id)
    for d in LOGS_ALIAS_DIR.glob("log-1022*/"):
        if d.name == want_alias:
            continue
        idx = d / "index.html"
        try:
            if idx.exists():
                html_text = idx.read_text("utf-8")
                if f'href="/logs/{slug}/"' in html_text:
                    shutil.rmtree(d)
                    log(f"Removed stale alias folder: {d}")
        except Exception as e:
            log(f"Alias cleanup error for {d}: {e}")

# ----- Import one entry (IDEMPOTENT + CLEAN) ---------------------------------
def import_post(entry, state):
    title = clean_title(entry.get("title"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")
    if not url:
        raise RuntimeError("Entry missing URL")

    # ISO-8601 with timezone (prefer RSS published date)
    if entry.get("published_parsed"):
        date = dt.datetime.fromtimestamp(time.mktime(entry.published_parsed)).astimezone().isoformat()
    elif entry.get("updated_parsed"):
        date = dt.datetime.fromtimestamp(time.mktime(entry.updated_parsed)).astimezone().isoformat()
    else:
        date = dt.datetime.now().astimezone().isoformat()

    # Stable slug from URL; remember mapping
    slug = state["guid_to_slug"].get(guid) or extract_substack_slug(url)
    state["guid_to_slug"][guid] = slug

    # Reuse existing log_id from on-disk markdown if present; else allocate once
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

    # Ensure artifacts folder uses slug (auto-migrate legacy log-1022x/)
    ensure_artifact_folder(slug, log_id)

    log(f"Upserting: '{title}' slug={slug} log_id={log_id}")

    # Fetch & convert body with cleanup
    raw_html = fetch_url(proxied(url))
    article_html = readability_extract(raw_html)
    article_html = strip_substack_chrome(article_html)
    body_md = html_to_markdown_simple(article_html)
    body_md = tidy_markdown(body_md, title)

    # Collect artifacts under /artifacts/:slug/
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

    ensure_alias_redirect(log_id, slug)
    cleanup_old_aliases_for_slug(log_id, slug)

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
