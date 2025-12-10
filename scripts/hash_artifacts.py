# scripts/hash_artifacts.py
import os, json, hashlib, pathlib, time

ARTIFACTS_ROOT = pathlib.Path("artifacts").resolve()

# File types we care about (extend if needed)
WHITELIST_EXT = {
    ".wav", ".flac", ".mp3", ".m4a", ".aiff", ".mp4", ".mov",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".tif", ".tiff",
    ".pdf", ".txt", ".csv",
}

# Files we NEVER hash or include (prevents self-referential churn)
SKIP_BASENAMES = {"metadata.json", "SHA256SUMS.txt", ".DS_Store", "Thumbs.db"}

def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def list_artifacts(folder: pathlib.Path):
    items = []
    for child in sorted(folder.iterdir(), key=lambda x: x.name.lower()):
        if child.is_dir():
            continue
        if child.name in SKIP_BASENAMES:
            continue
        if child.suffix.lower() not in WHITELIST_EXT:
            continue
        items.append(child)
    return items

def write_if_changed(path: pathlib.Path, content: str) -> bool:
    old = path.read_text("utf-8") if path.exists() else ""
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True

def build_metadata(folder: pathlib.Path):
    """Return a deterministic JSON string for metadata.json in `folder`."""
    entries = []
    for f in list_artifacts(folder):
        entries.append({
            "file": f.name,
            "bytes": f.stat().st_size,
            "sha256": sha256_file(f),
        })
    # Deterministic order & formatting
    data = {
        "folder": folder.name,
        "artifact_count": len(entries),
        "artifacts": sorted(entries, key=lambda x: x["file"]),
    }
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

def build_sha256sums(folder: pathlib.Path):
    """Return content for SHA256SUMS.txt (excludes metadata.json)."""
    lines = []
    for f in list_artifacts(folder):
        lines.append(f"{sha256_file(f)}  {f.name}")
    return "\n".join(lines) + ("\n" if lines else "")

def main():
    if not ARTIFACTS_ROOT.exists():
        print("No artifacts/ folder; nothing to do.")
        return

    changed_any = False

    for sub in sorted(ARTIFACTS_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not sub.is_dir():
            continue

        meta_path = sub / "metadata.json"
        sums_path = sub / "SHA256SUMS.txt"

        meta = build_metadata(sub)
        sums = build_sha256sums(sub)

        if write_if_changed(meta_path, meta):
            print(f"wrote {meta_path}")
            changed_any = True
        if write_if_changed(sums_path, sums):
            print(f"wrote {sums_path}")
            changed_any = True

    if not changed_any:
        print("No artifact changes detected.")

if __name__ == "__main__":
    main()
