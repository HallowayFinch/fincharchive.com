import os, json, time, feedparser, datetime as dt
from pathlib import Path
from urllib.parse import urlparse
from html_to_md import fetch_full_html, extract_main_html, html_to_markdown
from utils import make_log_id, slugify_log_id, clean_title

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".finch" / "state.json"
LOGS_DIR = ROOT / "logs"     # alias redirects (static)
COLL_DIR = ROOT / "_logs"    # Jekyll collection
ARTIFACTS = ROOT / "artifacts"

SUBSTACK_RSS_URL = os.environ.get("SUBSTACK_RSS_URL", "").strip()
IMPORT_LATEST_ONLY = os.environ.get("IMPORT_LATEST_ONLY", "0") == "1"
IMPORT_DEBUG = os.environ.get("IMPORT_DEBUG", "0") == "1"

COLL_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def log(*a):
    if IMPORT_DEBUG:
        print("[rss-sync]", *a, flush=True)

def load_state():
    STATE.parent.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        return json.loads(STATE.read_text("utf-8"))
    return {"next_seq": 1, "seen_guids": []}

def save_state(s):
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")

def slug_from_substack_url(url: str) -> str:
    """
    Robust slug extraction:
    - https://<sub>.substack.com/p/the-voice-in-the-static
    - https://substack.com/@hallowayfinch/p/the-voice-in-the-static
    - Allow trailing '/' and querystrings
    """
    path = urlparse(url).path.strip("/")
    if not path:
        return ""
    parts = [p for p in path.split("/") if p]
    # typical patterns: ['p', '<slug>'] or ['@user','p','<slug>']
    if parts[-2:-1] == ["p"] and len(parts) >= 2:
        return parts[-1].strip().lower()
    if len(parts) >= 3 and parts[-3:-2] == ["p"]:
        return parts[-1].strip().lower()
    # fall back: last segment
    return parts[-1].strip().lower()

def import_post(entry, state):
    title = clean_title(entry.get("title", "Untitled"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")
    date  = entry.get("published") or entry.get("updated") or dt.datetime.utcnow().isoformat() + "Z"

    log(f"Importing: title='{title}'")
    log(f"  guid={guid}")
    log(f"  link={url}")

    # Fetch & convert content
    full_html = fetch_full_html(url)
    main_html = extract_main_html(full_html)
    body_md   = html_to_markdown(main_html)

    # IDs and slugs
    log_id    = make_log_id(state["next_seq"])
    alias_dir = slugify_log_id(log_id)  # e.g. log-1022a
    slug      = slug_from_substack_url(url) or alias_dir   # fallback to alias if no slug
    log(f"  log_id={log_id}, slug={slug}, alias={alias_dir}")

    # Write Jekyll collection item: _logs/<slug>.md
    esc_title = title.replace('"', '\\"')
    front_matter = [
        "---",
        'layout: post',
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
    md_path.write_text("\n".join(front_matter) + body_md + "\n", encoding="utf-8")
    log(f"  wrote: {md_path}")

    # Alias redirect: /logs/log-1022a/index.html → /logs/<slug>/
    alias_folder = LOGS_DIR / alias_dir
    alias_folder.mkdir(parents=True, exist_ok=True)
    redirect_html = f"""<!doctype html><meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="/logs/{slug}/">
<meta http-equiv="refresh" content="0; url=/logs/{slug}/">
<a href="/logs/{slug}/">Redirecting to /logs/{slug}/</a>
<script>location.href="/logs/{slug}/";</script>"""
    (alias_folder / "index.html").write_text(redirect_html, encoding="utf-8")
    log(f"  wrote: {alias_folder / 'index.html'}")

    # Advance state
    state["seen_guids"].append(guid)
    state["next_seq"] += 1

def main():
    state = load_state()
    if not SUBSTACK_RSS_URL:
        print("No SUBSTACK_RSS_URL provided.")
        return

    feed = feedparser.parse(SUBSTACK_RSS_URL)
    log(f"Feed URL: {SUBSTACK_RSS_URL}")
    log(f"Feed entries: {len(feed.entries)}")

    candidates = []
    for e in feed.entries:
        gid = e.get("id") or e.get("guid") or e.get("link")
        if not gid:
            continue
        if gid in state["seen_guids"] and not IMPORT_LATEST_ONLY:
            continue
        candidates.append(e)

    if IMPORT_LATEST_ONLY and feed.entries:
        # Force newest one only
        newest = max(feed.entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0))
        candidates = [newest]
        log("IMPORT_LATEST_ONLY=1 → forcing newest entry import.")

    log(f"Selected entries to import: {len(candidates)}")

    if not candidates and feed.entries:
        log("No candidates after filtering; importing newest as failsafe.")
        newest = max(feed.entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0))
        import_post(newest, state)
    else:
        for e in sorted(candidates, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0)):
            import_post(e, state)

    save_state(state)
    log("Done.")

if __name__ == "__main__":
    main()
