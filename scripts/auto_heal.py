# scripts/auto_heal.py
"""
Auto-heal repo state from on-disk _logs/*.md.

- Rebuilds .finch/state.json from markdown front matter (guid, log_id, slug)
- Reconciles /logs/log-1022*/ alias folders:
    * If GENERATE_LOG_ALIAS=0 -> removes all alias folders
    * If GENERATE_LOG_ALIAS=1 -> ensures exactly one alias per _logs file and removes stale ones
"""

import os, re, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLL = ROOT / "_logs"
ALIAS_DIR = ROOT / "logs"
STATE_FILE = ROOT / ".finch" / "state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

GENERATE_LOG_ALIAS = os.environ.get("GENERATE_LOG_ALIAS", "1") == "1"

FM_RE = re.compile(r"(?s)^---(.*?)---")
KV_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*)\s*$", re.M)

def parse_front_matter(text: str) -> dict:
    m = FM_RE.search(text)
    if not m:
        return {}
    raw = m.group(1)
    out = {}
    for k, v in KV_RE.findall(raw):
        v = v.strip().strip('"').strip("'")
        out[k] = v
    return out

def letter_val(ch: str) -> int:
    return ord(ch.upper()) - 64  # A=1

def log_id_to_int(log_id: str) -> int:
    m = re.match(r"^1022([A-Z]+)$", (log_id or "").upper())
    if not m:
        return 0
    total = 0
    for c in m.group(1):
        total = total * 26 + letter_val(c)
    return total

def slugify_log_id(log_id: str) -> str:
    return f"log-{(log_id or '').lower()}"

def write_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def ensure_alias(slug: str, log_id: str):
    alias = slugify_log_id(log_id)
    d = ALIAS_DIR / alias
    d.mkdir(parents=True, exist_ok=True)
    idx = d / "index.html"
    html = f"""<!doctype html><meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="/logs/{slug}/">
<meta http-equiv="refresh" content="0; url=/logs/{slug}/">
<a href="/logs/{slug}/">Redirecting to /logs/{slug}/</a>
<script>location.href="/logs/{slug}/";</script>"""
    idx.write_text(html, encoding="utf-8")

def main():
    guid_to_slug = {}
    guid_to_log_id = {}
    seen_guids = []
    highest = 0

    # Rebuild maps from _logs/*.md
    for md in sorted(COLL.glob("*.md")):
        slug = md.stem
        fm = parse_front_matter(md.read_text("utf-8"))
        guid = fm.get("guid") or fm.get("source_url")
        log_id = fm.get("log_id")
        if not guid or not log_id:
            continue
        guid_to_slug[guid] = slug
        guid_to_log_id[guid] = log_id
        if guid not in seen_guids:
            seen_guids.append(guid)
        v = log_id_to_int(log_id)
        if v > highest:
            highest = v

    next_seq = max(highest + 1, 1)
    state = {
        "next_seq": next_seq,
        "seen_guids": seen_guids,
        "guid_to_slug": guid_to_slug,
        "guid_to_log_id": guid_to_log_id,
    }
    write_state(state)
    print(f"[auto-heal] wrote state: next_seq={next_seq}, posts={len(guid_to_slug)}")

    # Reconcile alias folders
    # Map wanted alias -> slug
    want = {}
    for guid, slug in guid_to_slug.items():
        log_id = guid_to_log_id.get(guid)
        if not log_id:
            continue
        want[slugify_log_id(log_id)] = slug

    if not GENERATE_LOG_ALIAS:
        # Remove all log-1022* aliases
        for d in ALIAS_DIR.glob("log-1022*/"):
            try:
                shutil.rmtree(d)
                print(f"[auto-heal] removed alias (disabled): {d}")
            except Exception as e:
                print(f"[auto-heal] alias remove error {d}: {e}")
        return

    # Ensure desired aliases exist & point to the correct slug
    for alias_name, slug in want.items():
        try:
            ensure_alias(slug, alias_name.replace("log-", ""))
            print(f"[auto-heal] ensured alias {alias_name} -> /logs/{slug}/")
        except Exception as e:
            print(f"[auto-heal] ensure alias error {alias_name}: {e}")

    # Remove stale aliases that point to mismatched or missing slugs
    for d in ALIAS_DIR.glob("log-1022*/"):
        alias_name = d.name
        idx = d / "index.html"
        if alias_name not in want:
            # alias refers to no live post
            try:
                shutil.rmtree(d)
                print(f"[auto-heal] removed stale alias (no live post): {d}")
            except Exception as e:
                print(f"[auto-heal] alias remove error {d}: {e}")
            continue

        # If exists, verify it points to the right slug
        try:
            if idx.exists():
                html = idx.read_text("utf-8")
                target = want[alias_name]
                if f'href="/logs/{target}/"' not in html:
                    shutil.rmtree(d)
                    ensure_alias(target, alias_name.replace("log-", ""))
                    print(f"[auto-heal] fixed alias {alias_name} -> /logs/{target}/")
        except Exception as e:
            print(f"[auto-heal] alias verify error {d}: {e}")

if __name__ == "__main__":
    main()
