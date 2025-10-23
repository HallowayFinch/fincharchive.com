import os, json, time, feedparser, datetime as dt, sys
from pathlib import Path
from html_to_md import fetch_full_html, extract_main_html, html_to_markdown
from utils import make_log_id, slugify_log_id, clean_title, extract_substack_slug, dedupe_slug

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".finch" / "state.json"
LOGS_DIR = ROOT / "logs"          # alias redirects
COLL_DIR = ROOT / "_logs"         # Jekyll collection
ARTIFACTS = ROOT / "artifacts"

SUBSTACK_RSS_URL = os.environ.get("SUBSTACK_RSS_URL", "").strip()
IMPORT_LATEST_ONLY = os.environ.get("IMPORT_LATEST_ONLY", "0") == "1"
IMPORT_DEBUG = os.environ.get("IMPORT_DEBUG", "0") == "1"

COLL_DIR.mkdir(exist_ok=True, parents=True)
LOGS_DIR.mkdir(exist_ok=True, parents=True)
ARTIFACTS.mkdir(exist_ok=True, parents=True)

def log(*args):
    print("[rss-sync]", *args, flush=True)

def load_state():
    STATE.parent.mkdir(exist_ok=True, parents=True)
    if STATE.exists():
        return json.loads(STATE.read_text("utf-8"))
    return {"next_seq": 1, "seen_guids": []}

def save_state(s):
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")

def checksum(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def import_post(entry, state):
    title = clean_title(entry.get("title", "Untitled"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")
    date  = entry.get("published") or entry.get("updated") or dt.datetime.utcnow().isoformat() + "Z"

    log(f"Importing: title='{title}', guid='{guid}', url='{url}'")

    full_html = fetch_full_html(url)
    main_html = extract_main_html(full_html)
    body_md   = html_to_markdown(main_html)

    log_id = make_log_id(state["next_seq"])
    log_alias = slugify_log_id(log_id)

    base_slug = extract_substack_slug(url) or f"log-{log_id.lower()}"
    existing = {p.stem for p in COLL_DIR.glob("*.md")}
    pretty_slug = base_slug if base_slug not in existing else dedupe_slug(base_slug, set(existing))

    esc_title = title.replace('"', '\\"')
    fm = [
        "---",
        'layout: post',
        f'title: "{esc_title}"',
        f'log_id: "{log_id}"',
        f'date: "{date}"',
        f'source_url: "{url}"',
        f'guid: "{guid}"',
        f'permalink: "/logs/{pretty_slug}/"',
        "---",
        ""
    ]
    md_path = COLL_DIR / f"{pretty_slug}.md"
    md_path.write_text("\n".join(fm) + body_md + "\n", encoding="utf-8")
    log(f"Wrote collection item: {md_path}")

    alias_folder = LOGS_DIR / log_alias
    alias_folder.mkdir(parents=True, exist_ok=True)
    redirect_html = f'''<!doctype html><meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="/logs/{pretty_slug}/">
<meta http-equiv="refresh" content="0; url=/logs/{pretty_slug}/">
<a href="/logs/{pretty_slug}/">Redirecting to /logs/{pretty_slug}/</a>
<script>location.href="/logs/{pretty_slug}/";</script>'''
    (alias_folder / "index.html").write_text(redirect_html, encoding="utf-8")
    log(f"Wrote alias redirect: {alias_folder / 'index.html'} -> /logs/{pretty_slug}/")

    state["seen_guids"].append(guid)
    state["next_seq"] += 1

def main():
    state = load_state()

    if not SUBSTACK_RSS_URL:
        log("No SUBSTACK_RSS_URL provided.")
        return

    feed = feedparser.parse(SUBSTACK_RSS_URL)
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
        candidates = [max(feed.entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0))]
        log("IMPORT_LATEST_ONLY enabled: forcing newest entry import.")

    log(f"Selected entries to import: {len(candidates)}")

    if not candidates and feed.entries:
        # Failsafe: import newest one anyway
        newest = max(feed.entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0))
        log("No candidates after filtering; importing newest as failsafe.")
        import_post(newest, state)
    else:
        for e in sorted(candidates, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0)):
            import_post(e, state)

    save_state(state)
    log("Done.")

if __name__ == "__main__":
    main()
