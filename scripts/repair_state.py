# scripts/repair_state.py
import re, json, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLL_DIR = ROOT / "_logs"
STATE_FILE = ROOT / ".finch" / "state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

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
    ch = ch.upper()
    return ord(ch) - 64  # A=1, B=2...

def log_id_to_int(log_id: str) -> int:
    # expects "1022A", "1022D", etc.
    m = re.match(r"^1022([A-Z]+)$", log_id or "", re.I)
    if not m:
        return 0
    letters = m.group(1).upper()
    # base-26: A=1 ... Z=26, then AA=27, etc.
    total = 0
    for c in letters:
        total = total * 26 + letter_val(c)
    return total

def main(write: bool):
    guid_to_slug = {}
    guid_to_log_id = {}
    seen_guids = []
    highest = 0

    for md in sorted(COLL_DIR.glob("*.md")):
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
        val = log_id_to_int(log_id)
        if val > highest:
            highest = val

    next_seq = max(highest + 1, 1)
    new_state = {
        "next_seq": next_seq,
        "seen_guids": seen_guids,
        "guid_to_slug": guid_to_slug,
        "guid_to_log_id": guid_to_log_id,
    }

    if write:
        STATE_FILE.write_text(json.dumps(new_state, indent=2), encoding="utf-8")
        print(f"[state-repair] wrote {STATE_FILE} with next_seq={next_seq}")
    else:
        print(json.dumps(new_state, indent=2))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Rebuild .finch/state.json from _logs/*.md")
    ap.add_argument("--write", action="store_true", help="Write the rebuilt state to disk")
    args = ap.parse_args()
    main(write=args.write)
