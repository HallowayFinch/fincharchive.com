import os, json, time, feedparser, datetime as dt
from pathlib import Path
from html_to_md import fetch_full_html, extract_main_html, html_to_markdown
from utils import make_log_id, slugify_log_id, clean_title, extract_substack_slug, dedupe_slug

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".finch" / "state.json"
LOGS_DIR = ROOT / "logs"          # for alias redirects only
COLL_DIR = ROOT / "_logs"         # Jekyll collection output
ARTIFACTS = ROOT / "artifacts"

SUBSTACK_RSS_URL = os.environ.get("SUBSTACK_RSS_URL", "").strip()

COLL_DIR.mkdir(exist_ok=True, parents=True)
LOGS_DIR.mkdir(exist_ok=True, parents=True)
ARTIFACTS.mkdir(exist_ok=True, parents=True)

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

    # Fetch full HTML and convert to MD
    full_html = fetch_full_html(url)
    main_html = extract_main_html(full_html)
    body_md   = html_to_markdown(main_html)

    # Assign log id
    log_id = make_log_id(state["next_seq"])
    log_alias = slugify_log_id(log_id)  # e.g., log-1022a

    # Derive pretty slug from Substack
    base_slug = extract_substack_slug(url) or f"log-{log_id.lower()}"
    existing = {p.stem for p in COLL_DIR.glob("*.md")}
    pretty_slug = base_slug if base_slug not in existing else dedupe_slug(base_slug, set(existing))

    # Write Jekyll collection item: _logs/<pretty-slug>.md
    esc_title = title.replace('"', '\"')
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
    (COLL_DIR / f"{pretty_slug}.md").write_text("\n".join(fm) + body_md + "\n", encoding="utf-8")

    # Create alias redirect folder: /logs/log-1022a/index.html
    alias_folder = LOGS_DIR / log_alias
    alias_folder.mkdir(parents=True, exist_ok=True)
    redirect_html = f'''<!doctype html><meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="/logs/{pretty_slug}/">
<meta http-equiv="refresh" content="0; url=/logs/{pretty_slug}/">
<a href="/logs/{pretty_slug}/">Redirecting to /logs/{pretty_slug}/</a>
<script>location.href="/logs/{pretty_slug}/";</script>'''
    (alias_folder / "index.html").write_text(redirect_html, encoding="utf-8")

    # Mark as seen & bump sequence
    state["seen_guids"].append(guid)
    state["next_seq"] += 1

def main():
    state = load_state()

    if not SUBSTACK_RSS_URL:
        print("No SUBSTACK_RSS_URL provided.")
        return

    feed = feedparser.parse(SUBSTACK_RSS_URL)
    new_entries = []
    for e in feed.entries:
        gid = e.get("id") or e.get("guid") or e.get("link")
        if not gid:
            continue
        if gid in state["seen_guids"]:
            continue
        new_entries.append(e)

    # Import oldest first for stable ordering
    for e in sorted(new_entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0)):
        import_post(e, state)

    save_state(state)

if __name__ == "__main__":
    main()
