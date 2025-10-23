# scripts/validate_site.py
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLL = ROOT / "_logs"
ALIAS = ROOT / "logs"

slug_seen = set()
errors = 0

for md in sorted(COLL.glob("*.md")):
    slug = md.stem
    text = md.read_text("utf-8")
    # front matter
    m = re.search(r"(?s)^---(.*?)---", text)
    if not m:
        print(f"[ERR] {md}: missing front matter")
        errors += 1
        continue
    fm = m.group(1)
    if f'permalink: "/logs/{slug}/"' not in fm:
        print(f"[ERR] {md}: permalink mismatch or missing")
        errors += 1
    if slug in slug_seen:
        print(f"[ERR] duplicate slug: {slug}")
        errors += 1
    slug_seen.add(slug)

# orphan alias folders pointing nowhere valid
for d in ALIAS.glob("log-1022*/"):
    idx = d / "index.html"
    if not idx.exists():
        print(f"[ERR] alias missing index.html: {d}")
        errors += 1

print(f"[validate] done; errors={errors}")
sys.exit(1 if errors else 0)
