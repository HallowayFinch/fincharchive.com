# scripts/import_field_notes.py
import os, json, re, datetime
from pathlib import Path

import feedparser
import frontmatter
from markdownify import markdownify as html_to_md
from slugify import slugify

# ======================
# CONFIG
# ======================

# Jekyll collection source dir for field-notes
FIELD_NOTES_DIR = Path("_field-notes")

# Ledger tracks which RSS entries we've written + last assigned sequence number
LEDGER_FILE = Path(".fieldnote-import-ledger.json")

# We'll number notes like "22-B.1", "22-B.2", etc.
ID_SERIES_PREFIX = "22-B."

# Offset string for Jekyll dates (match your site’s TZ)
TZ_OFFSET = os.environ.get("TZ_OFFSET", "-0500")

# Secret: Substack Notes RSS URL
RSS_URL = os.environ.get("SUBSTACK_NOTES_RSS")
if not RSS_URL:
    raise RuntimeError("Missing SUBSTACK_NOTES_RSS env var / secret.")


# ======================
# Helpers
# ======================

def load_ledger():
    if LEDGER_FILE.exists():
        with LEDGER_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "imported_ids": [],  # set of RSS entry ids we've already used
        "last_seq": 0        # last numeric counter we assigned
    }

def save_ledger(data):
    with LEDGER_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def next_fieldnote_id(seq_num: int) -> str:
    # e.g. 1 -> "22-B.1"
    return f"{ID_SERIES_PREFIX}{seq_num}"

def entry_pubdate(e):
    # Pull a datetime from RSS entry
    if hasattr(e, "published_parsed") and e.published_parsed:
        return datetime.datetime(*e.published_parsed[:6])
    if hasattr(e, "updated_parsed") and e.updated_parsed:
        return datetime.datetime(*e.updated_parsed[:6])
    return datetime.datetime.utcnow()

def jekyll_date(dt_obj: datetime.datetime) -> str:
    # Jekyll-style datetime with offset
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S ") + TZ_OFFSET

def sanitize_body(md: str) -> str:
    # collapse triple+ blank lines, strip ends
    cleaned = re.sub(r"\n{3,}", "\n\n", md).strip()
    return cleaned

def build_front_matter(title, dt_str, source, field_note_id, tags):
    post = frontmatter.Post("")
    post["layout"] = "fieldnote"
    post["title"] = title
    post["date"] = dt_str
    post["source"] = source
    post["field_note_id"] = field_note_id
    post["tags"] = tags
    return post

def write_markdown_file(date_prefix, slug, fm_post, body_md):
    # filename example:
    #   "2025-10-30-field-note-22-b-1-the-corridor.md"
    filename = f"{date_prefix}-{slug}.md"
    filepath = FIELD_NOTES_DIR / filename

    fm_post.content = body_md

    FIELD_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(fm_post))

    print(f"[import_field_notes] wrote {filepath}")


# ======================
# Main
# ======================

def main():
    ledger = load_ledger()
    imported_ids = set(ledger.get("imported_ids", []))
    last_seq = ledger.get("last_seq", 0)

    feed = feedparser.parse(RSS_URL)

    # collect only entries we haven't seen yet
    new_entries = []
    for entry in feed.entries:
        entry_key = getattr(entry, "id", None) or getattr(entry, "link", None)
        if not entry_key:
            continue
        if entry_key in imported_ids:
            continue
        new_entries.append(entry)

    # sort them oldest -> newest so we number them in order
    new_entries.sort(key=entry_pubdate)

    for entry in new_entries:
        # assign next canonical Finch ID
        last_seq += 1
        field_note_id = next_fieldnote_id(last_seq)

        ts = entry_pubdate(entry)

        # capture Substack Note body (HTML) and convert to md
        html_content = (
            getattr(entry, "summary", "")
            or getattr(entry, "content", [{"value": ""}])[0]["value"]
        )
        body_md = html_to_md(html_content)
        body_md = sanitize_body(body_md)

        # enforce Finch close marker
        if "[End of Field Note]" not in body_md:
            body_md = body_md.strip() + "\n\n[End of Field Note]"

        # derive title text
        raw_title_text = getattr(entry, "title", "").strip()
        if not raw_title_text:
            first_line = body_md.splitlines()[0]
            raw_title_text = first_line[:80]

        # shorten for slug/title
        words = raw_title_text.split()
        short_phrase = " ".join(words[:6]).strip(",. ")
        composed_title = f"Field Note {field_note_id} — {short_phrase}"

        # tags from feed.categories / feed.tags if present
        tags = ["fieldnote"]
        if hasattr(entry, "tags"):
            for t in entry.tags:
                t_name = t.get("term") if isinstance(t, dict) else getattr(t, "term", None)
                if t_name and t_name not in tags:
                    tags.append(t_name)

        fm_post = build_front_matter(
            title=composed_title,
            dt_str=jekyll_date(ts),
            source="Substack Notes RSS",
            field_note_id=field_note_id,
            tags=tags
        )

        # file slug
        date_prefix = ts.strftime("%Y-%m-%d")
        slug_bits = [
            "field-note",
            field_note_id.lower().replace(".", "-"),  # "22-b-1"
            slugify(short_phrase),
        ]
        slug_full = "-".join([b for b in slug_bits if b])

        # actually write `_field-notes/YYYY-MM-DD-field-note-...md`
        write_markdown_file(
            date_prefix=date_prefix,
            slug=slug_full,
            fm_post=fm_post,
            body_md=body_md
        )

        # mark imported
        entry_key = getattr(entry, "id", None) or getattr(entry, "link", None)
        imported_ids.add(entry_key)

    # update ledger with new state
    ledger["imported_ids"] = list(imported_ids)
    ledger["last_seq"] = last_seq
    save_ledger(ledger)

    print(f"[import_field_notes] imported {len(new_entries)} new note(s), last_seq={last_seq}")


if __name__ == "__main__":
    main()
