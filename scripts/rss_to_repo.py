import os, json, time, feedparser, datetime as dt
from pathlib import Path
from html_to_md import fetch_full_html, extract_main_html, html_to_markdown
from utils import make_log_id, slugify_log_id, clean_title, extract_substack_slug, dedupe_slug

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".finch" / "state.json"
LOGS = ROOT / "logs"
ARTIFACTS = ROOT / "artifacts"

SUBSTACK_RSS_URL = os.environ.get("SUBSTACK_RSS_URL", "").strip()
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://fincharchive.com").rstrip("/")

LOGS.mkdir(exist_ok=True, parents=True)
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

def ensure_logs_index():
    # Build index linking to the pretty permalink dirs (non-alias)
    items = []
    for p in sorted(LOGS.glob("*/meta.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if p.parent.name.startswith("log-"):
            # skip alias folders in index
            continue
        meta = json.loads(p.read_text("utf-8"))
        url = f"/logs/{p.parent.name}/"
        items.append(f'<li><a href="{url}">{meta["log_id"]} — {meta["title"]}</a> <span style="opacity:.7;">({meta["date"]})</span></li>')
    html = """<!doctype html><meta charset="utf-8"><title>Logs — Finch Archive</title>
<style>body{background:#000;color:#e6e6e6;font-family:ui-monospace,monospace;margin:40px}a{color:#e6e6e6}</style>
<h1>Logs</h1>
<ul>
%s
</ul>""" % ("\n".join(items) if items else "<li>(none yet)</li>")
    (LOGS / "index.html").write_text(html, encoding="utf-8")

def import_post(entry, state):
    from build_log_page import build, build_redirect

    title = clean_title(entry.get("title", "Untitled"))
    guid  = entry.get("id") or entry.get("guid") or entry.get("link")
    url   = entry.get("link")
    date  = entry.get("published") or entry.get("updated") or dt.datetime.utcnow().isoformat() + "Z"

    # Fetch full HTML and convert to MD
    full_html = fetch_full_html(url)
    main_html = extract_main_html(full_html)
    body_md   = html_to_markdown(main_html)
    post_ck   = checksum(title + "\n" + body_md)

    # Assign log id and alias folder
    log_id = make_log_id(state["next_seq"])
    log_alias = slugify_log_id(log_id)  # e.g., log-1022a

    # Derive pretty slug from Substack
    base_slug = extract_substack_slug(url) or f"log-{log_id.lower()}"
    existing = {p.name for p in LOGS.glob("*") if p.is_dir()}
    pretty_slug = dedupe_slug(base_slug, existing)
    pretty_folder = LOGS / pretty_slug
    alias_folder  = LOGS / log_alias

    # meta.json in pretty folder
    meta = {
        "log_id": log_id,
        "slug": pretty_slug,
        "alias": log_alias,
        "title": title,
        "date": date,
        "source_url": url,
        "guid": guid,
        "content_checksum": post_ck,
        "permalink": f"/logs/{pretty_slug}/"
    }
    pretty_folder.mkdir(parents=True, exist_ok=True)
    (pretty_folder / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Markdown with basic front matter
    fm = [
        "---",
        f'log_id: "{log_id}"',
        f'title: "{title.replace("\"", "\\\"")}"',
        f'date: "{date}"',
        f'source_url: "{url}"',
        f'guid: "{guid}"',
        f'permalink: "/logs/{pretty_slug}/"',
        "---",
        ""
    ]
    (pretty_folder / "index.md").write_text("\n".join(fm) + body_md + "\n", encoding="utf-8")

    # Include artifacts if present (keyed by alias under /artifacts/)
    artifacts_manifest = None
    afolder = ARTIFACTS / log_alias
    if afolder.is_dir() and (afolder / "artifacts.json").exists():
        artifacts_manifest = str(afolder / "artifacts.json")

    # Build pretty page and alias redirect
    canonical_url = f"{SITE_BASE_URL}/logs/{pretty_slug}/"
    build(str(pretty_folder), meta, body_md, artifacts_manifest_path=artifacts_manifest, canonical_url=canonical_url)
    build_redirect(str(alias_folder), to_url=f"/logs/{pretty_slug}/")

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

    # Import oldest first
    for e in sorted(new_entries, key=lambda x: x.get("published_parsed") or x.get("updated_parsed") or time.gmtime(0)):
        import_post(e, state)

    ensure_logs_index()
    save_state(state)

if __name__ == "__main__":
    main()
